"""Reator de pirólise 3-D: escoamento RANS no referencial do agitador + temperatura e química estacionárias.

Laço externo (Picard), como no documento de projeto:
  0. reator 0-D (tanque ideal) → campos uniformes iniciais e vazão de alimentação;
  1. escoamento com propriedades congeladas (viscosidade μ(γ̇, T, Mw) e massa específica ρ(T, Mn)),
     algumas voltas do agitador no referencial girante até o torque estabilizar;
  2. temperatura e espécies em regime permanente sobre o escoamento (implícito, GPU);
  3. controle de nível: alimentação = vapor + purga (modo B, parede com temperatura imposta) ou ajuste da
     temperatura da parede para uma vazão dada (modo A);
  4. atualiza viscosidade (relaxada em log) e empuxo e volta a 1.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np
import torch

from . import rheology as rh
from .chemistry import (CLOSURE, M_LO, MBAR, S_CHAR, SOLIDS_TARGET, FeedSpec, class_rates, nagata_h,
                        product_slate, solve_cstr)
from .flow import FlowConfig, TankFlow
from .kinetics import POLYMERS, R_GAS
from .ops import avg, extend_into_solid, to_faces
from .scalar import SteadyScalar
from .turbulence import BETA_STAR, SST

G = 9.81


@dataclass
class ReactorConfig:
    n_diam: int = 64                 # células no diâmetro do vaso
    T_wall_C: float = 480.0          # temperatura da parede (modo B)
    feed_kgph: float | None = None   # vazão imposta (modo A): a parede vira incógnita
    turbulence: str = "sst"          # "sst" ou "laminar"
    mu_cap: float = 3.0              # teto da viscosidade no momento [Pa s] (passo explícito)
    spin0: float = 0.9               # partida: líquido girando a 0,9 Ω (a fita arrasta quase todo o líquido)
    feed_r: float = 0.20             # raio do anel de alimentação [m]
    rho0: float = 620.0              # massa específica de referência [kg/m³]
    Sc_t: float = 0.7
    Pr_t: float = 0.85
    buoyancy: bool = True
    revs_first: float = 15.0         # voltas do agitador na primeira passada do escoamento
    revs_next: float = 4.0           # voltas nas passadas seguintes
    outer: int = 4                   # iterações externas
    device: str = "auto"
    dtype: str = "float32"


def _riazi_Mstar(T):
    """Massa molar [g/mol] do n-alcano que ferve a T (torch)."""
    return ((6.98291 - torch.log(1070.0 - T)) / 0.02013) ** 1.5


class Reactor:
    def __init__(self, tank, feed: FeedSpec, cfg: ReactorConfig):
        self.tank, self.feed, self.cfg = tank, feed, cfg
        self.items = feed.items()
        V = math.pi * tank.R ** 2 * tank.H_L
        A = 2 * math.pi * tank.R * tank.H_L + math.pi * tank.R ** 2
        self.V_liq, self.A_wall = V, A
        self.T_wall = cfg.T_wall_C + 273.15
        # ---- 0-D: ponto de partida (h pela correlação de Nagata, iterado com a viscosidade do fundido)
        N, d = tank.rpm / 60.0, tank.impeller_diameter
        h = 300.0
        for _ in range(4):
            r0 = solve_cstr(feed, V, A, h, T_wall=self.T_wall, feed_rate=None if cfg.feed_kgph is None
                            else cfg.feed_kgph / 3600.0, rho=cfg.rho0)
            h = nagata_h(r0.rho, N, d, r0.eta, 3240.0, 0.11, tank.T)[0]
        self.cstr0, self.h_nagata0 = r0, h
        if cfg.feed_kgph is not None:
            self.T_wall = r0.T_wall
        # ---- escoamento
        fcfg = FlowConfig(n_diam=cfg.n_diam, rho=cfg.rho0, mu_max=cfg.mu_cap, spin0=cfg.spin0, device=cfg.device,
                          dtype=cfg.dtype, vessel_ibm="wallfn" if cfg.turbulence == "sst" else "diffuse")
        self.flow = TankFlow(tank, fcfg, mu_fn=self._mu)
        f = self.flow
        self.flm = (f.fluid > 0.5).to(f.ft)               # células de fluido (máscara dos escalares)
        if cfg.turbulence == "sst":
            f.turb = SST(f)
        t = f._t
        # ---- campos escalares uniformes do 0-D
        P0 = f.P
        self.T = torch.full_like(P0, r0.T)
        self.state = []
        for s in r0.states:
            self.state.append({"Y": torch.full_like(P0, s["Y"]), "Z": torch.full_like(P0, s["Z"]),
                               "E": [torch.full_like(P0, e) for e in s["E"]]})
        self.F = r0.feed                                   # alimentação [kg/s]
        # anel de alimentação junto à superfície (no referencial girante, o bocal fixo vira um anel)
        r = f.r_c
        zc = t(f.P_c[..., 2])
        ring = ((r - cfg.feed_r).abs() < f.h) & (zc > tank.H_L - 2.0 * f.hz) & (f.fluid > 0.5)
        self.feed_mask = ring.to(f.ft)
        self.V_feed = float(self.feed_mask.sum()) * f.vol
        # paredes aquecidas: células sólidas do vaso (não do agitador) e fundo
        self.vessel_solid = t((tank.vessel_sdf(f.P_c) > 0).astype(float)) * (f.fluid < 0.5).to(f.ft)
        self._side_area_factor = None
        self.cp0 = self._cp_bulk(r0.T)
        self.history = []
        self.flow_rho_body()

    # ---------------------------------------------------------------- propriedades
    def _cp_bulk(self, T):
        cps = {"HDPE": rh.heat_capacity("HDPE", T), "LDPE": rh.heat_capacity("LDPE", T),
               "PP": rh.heat_capacity("PP", T)}
        return float(sum(w * cps[c.key] for c, w in self.items))

    def _k_c(self, c, T):
        p = POLYMERS[c.key]
        return c.f * p.A * torch.exp(-p.E / (R_GAS * T))

    def _n_star(self, c, T):
        return _riazi_Mstar(T) / 1000.0 / c.m0

    def _Mw(self, c, s):
        Y = s["Y"].clamp(min=1e-12)
        E = s["E"]
        Es = E[0] + E[1] + E[2]
        matrix = (Y - Es).clamp(min=1e-12)
        zm = (s["Z"] - sum(2 * e / m for e, m in zip(E, MBAR))).clamp(min=1e-12)
        Mn_m = matrix / zm
        return (sum(e * m for e, m in zip(E, MBAR)) + matrix * 1.5 * Mn_m) / Y          # kg/mol

    def eta0_field(self):
        """Viscosidade a taxa nula da mistura [Pa s] (média logarítmica pela massa)."""
        T = self.T
        lnmix, wsum = 0.0, 0.0
        for (c, _), s in zip(self.items, self.state):
            Mw = (self._Mw(c, s) * 1000.0).clamp(100.0, 1e7)
            r = rh.RHEO[c.rheo]
            ent = rh.eta0(r, T, Mw, xp=torch)
            wax = 0.015 * (Mw / 1080.0) ** 1.9 * torch.exp((27e3 / R_GAS) * (1.0 / T - 1.0 / 422.15))
            e0 = torch.nan_to_num(torch.maximum(ent, wax), nan=1e-3, posinf=1e6).clamp(1e-6, 1e8)
            Yw = s["Y"].clamp(min=0.0)
            lnmix = lnmix + Yw * torch.log(e0)
            wsum = wsum + Yw
        e = torch.exp(lnmix / wsum.clamp(min=1e-12))
        # fora do líquido (paredes, agitador): o valor do fluido vizinho
        return extend_into_solid(torch.where(wsum > 1e-9, e, torch.full_like(e, 1e-3)), self.flm > 0, passes=4)

    def _mu(self, gamma):
        if not hasattr(self, "_eta0"):
            return torch.full_like(gamma, max(self.cstr0.eta, rh.ETA_FLOOR))
        main = max(self.items, key=lambda cw: cw[1])[0]
        r = rh.RHEO[main.rheo]
        e0 = self._eta0
        mu = rh.ETA_FLOOR + e0 / (1.0 + (e0 * gamma / r.tau_star) ** (1.0 - r.n))
        return mu.clamp(rh.ETA_FLOOR, self.cfg.mu_cap)

    def density_field(self):
        T = self.T
        rho, wsum = 0.0, 0.0
        Tc = T - 273.15
        for (c, _), s in zip(self.items, self.state):
            Mn = s["Y"] / s["Z"].clamp(min=1e-12) * 1000.0                     # g/mol
            if c.key in ("HDPE", "LDPE"):
                ri = 1000.0 / (1.1595 + 8.0e-4 * Tc)
            else:
                ri = 738.6 / (1.0 + 6.7e-4 * (Tc - 230.0))
            fb = ((Mn - 500.0) / 1500.0).clamp(0.0, 1.0)
            ri = fb * ri + (1 - fb) * 610.0
            rho = rho + s["Y"] * ri
            wsum = wsum + s["Y"]
        return rho / wsum.clamp(min=1e-12)

    def flow_rho_body(self, relax: float = 1.0):
        """Congela viscosidade (relaxada em log) e empuxo para a próxima passada do escoamento."""
        e0 = self.eta0_field()
        if hasattr(self, "_eta0") and relax < 1.0:
            e0 = torch.exp(relax * torch.log(e0) + (1 - relax) * torch.log(self._eta0))
        self._eta0 = e0
        f = self.flow
        if self.cfg.buoyancy:
            rho = self.density_field()
            rho_bulk = float((rho * f.fluid).sum() / f.fluid.sum())
            b = (rho - rho_bulk) / self.cfg.rho0 * (f.fluid > 0.5).to(f.ft)
            om2 = f.omega ** 2
            X, Y = f._t(f.P_c[..., 0]), f._t(f.P_c[..., 1])
            f.body = [to_faces(b * om2 * X, 0), to_faces(b * om2 * Y, 1), to_faces(-G * b, 2)]
        f.update_viscosity()

    # ------------------------------------------------------------------ escoamento
    def run_flow(self, revs: float, log_every: float = 1.0, callback=None):
        f = self.flow
        N = self.tank.rpm / 60.0
        t_end = f.time + revs / N
        t_avg0 = t_end - min(1.0, revs) / N                    # média na última volta
        acc, n_acc = None, 0
        next_log = f.time + log_every / N
        while f.time < t_end:
            f.step()
            f.record()
            if f.time >= t_avg0:
                cur = (f.u, f.v, f.w)
                acc = [c.clone() for c in cur] if acc is None else [a + c for a, c in zip(acc, cur)]
                n_acc += 1
            if callback is not None and f.time >= next_log:
                callback(self)
                next_log += log_every / N
        self.mean_uvw = [a / n_acc for a in acc]
        return self

    def power_number(self, n_avg=200):
        f = self.flow
        N, d = self.tank.rpm / 60.0, self.tank.impeller_diameter
        return f.power(n_avg) / (self.cfg.rho0 * N ** 3 * d ** 5)

    # ------------------------------------------------------------------ escalares
    def _wall_cond(self):
        """Condutância de parede por área [W/(m² K)] nas células de fluido junto ao vaso."""
        f = self.flow
        k_mol = 0.11
        if f.turb is not None:
            mu = f.mu
            h = f.turb.wall_heat_transfer(self.cp0, k_mol)
        else:
            h = k_mol / f.wall_dist.clamp(min=0.25 * f.h)
        return h

    def _side_factor(self, sc):
        """Correção da área em escada da parede lateral: área exata / área das faces."""
        if self._side_area_factor is None:
            f = self.flow
            A_true = 2 * math.pi * self.tank.R * self.tank.H_L
            fl = sc.fluid
            dm = self.vessel_solid
            A_st = 0.0
            for axis in (0, 1):
                from .ops import sl
                a_lo, a_hi = sl(fl, axis, 0, -1), sl(fl, axis, 1, None)
                d_lo, d_hi = sl(dm, axis, 0, -1), sl(dm, axis, 1, None)
                A_st += float((a_lo * d_hi + d_lo * a_hi).sum()) * sc.A[axis]
            self._side_area_factor = A_true / max(A_st, 1e-12)
        return self._side_area_factor

    def _vapour(self, T):
        """S_v de cada polímero [kg/(m³ s)] e d S_v/dT, com ψ limitado ao comprimento de corte."""
        rho0 = self.cfg.rho0
        Sv, dSv = [], []
        for (c, _), s in zip(self.items, self.state):
            kc = self._k_c(c, T)
            ns = self._n_star(c, T)
            Zc = torch.minimum(s["Z"], s["Y"] / (ns * c.m0))
            sv = rho0 * kc * ns ** 2 * c.m0 * Zc * self.flm
            p = POLYMERS[c.key]
            dlnN = 1.5 * (1.0 / (1070.0 - T)) / (6.98291 - torch.log(1070.0 - T))     # d ln N*/dT
            Sv.append(sv)
            dSv.append(sv * (p.E / (R_GAS * T ** 2) + 2 * dlnN))
        return Sv, dSv

    def solve_scalars(self, picard: int = 6, relax: float = 0.6, verbose: bool = False):
        """Temperatura e estado do polímero em regime permanente sobre o escoamento médio (Picard
        sub-relaxado: espécies → temperatura → controle de nível)."""
        f = self.flow
        cfg = self.cfg
        rho0 = cfg.rho0
        sc = SteadyScalar(f, *self.mean_uvw)
        nu_t = f.turb.nu_t if f.turb is not None else torch.zeros_like(f.P)
        Gs = nu_t / cfg.Sc_t + 1e-9
        k_mol = 0.11
        GT = k_mol / (rho0 * self.cp0) + nu_t / cfg.Pr_t
        hw = self._wall_cond()
        fac = self._side_factor(sc)
        # bottom: área exata (faces alinhadas); lateral: corrigida pela área em escada
        wall_cond = hw * fac / (rho0 * self.cp0)
        bottom_cond = hw / (rho0 * self.cp0)
        Tf = self.feed.T_feed
        info = {}
        fl = self.flm > 0
        for it in range(picard):
            Sf = self.F * self.feed_mask / self.V_feed                 # kg/(m³ s)
            T = self.T
            Sv, _ = self._vapour(T)
            Svt = sum(Sv)
            # ---- espécies (Picard nos acoplamentos, PTC + BiCGSTAB em cada uma)
            for (c, w), s, sv in zip(self.items, self.state, Sv):
                kc = self._k_c(c, T)
                ns = self._n_star(c, T)
                r1, r2, r3 = class_rates_torch(c, kc)
                spf = Sf / rho0
                ex = Svt / rho0
                Yf, Zf = w * (1 - self.feed.ash), w * (1 - self.feed.ash) / c.Mn0
                Y = self._solve(sc, Gs, spf, spf * Yf - (1 + S_CHAR) * sv / rho0 + ex * s["Y"], s["Y"])
                Z = self._solve(sc, Gs, spf + 2 * kc * ns, spf * Zf + kc * Y / c.m0 + ex * s["Z"], s["Z"])
                E1 = self._solve(sc, Gs, spf + r1, spf * Yf + ex * s["E"][0], s["E"][0])
                E2 = self._solve(sc, Gs, spf + r2, r1 * E1 + ex * s["E"][1], s["E"][1])
                E3 = self._solve(sc, Gs, spf + r3, r2 * E2 + ex * s["E"][2], s["E"][2])
                mix = lambda new, old: torch.where(fl, old + relax * (new - old), old)  # noqa: E731
                s["Y"] = mix(Y.clamp(min=1e-9), s["Y"])
                s["Z"] = torch.minimum(mix(Z.clamp(min=1e-12), s["Z"]), s["Y"] / (ns * c.m0))
                s["E"] = [mix(e.clamp(min=0), e0) for e, e0 in zip((E1, E2, E3), s["E"])]
                Es = s["E"][0] + s["E"][1] + s["E"][2]                 # as classes cabem na massa do polímero
                scale = torch.where(Es > 0.98 * s["Y"], 0.98 * s["Y"] / Es.clamp(min=1e-30), torch.ones_like(Es))
                s["E"] = [e * scale for e in s["E"]]
            # ---- energia (linearização de Newton do sumidouro endotérmico, com o estado novo)
            Sv, dSv = self._vapour(T)
            dH = [c.dH for c, _ in self.items]
            sinkT = sum(h_ * d for h_, d in zip(dH, dSv))
            src = -sum(h_ * s_ for h_, s_ in zip(dH, Sv)) + sinkT * T + self._dissipation()
            SpT = Sf / rho0 + sinkT / (rho0 * self.cp0)
            ScT = Sf * Tf / rho0 + src / (rho0 * self.cp0)
            sc.setup(GT, SpT, ScT, dirichlet_mask=self.vessel_solid > 0, dirichlet_value=self.T_wall,
                     bottom_value=self.T_wall, wall_cond=self._blend_wall(wall_cond, bottom_cond))
            Tn, res, nit = sc.solve_ptc(torch.where(fl, self.T, torch.full_like(self.T, self.T_wall)), dtau0=5.0)
            Tn = torch.where(fl, self.T + relax * (Tn - self.T), Tn)
            # fora do fluido: parede do vaso na temperatura imposta; agitador com a do fluido vizinho
            Ts = extend_into_solid(Tn, fl, passes=3)
            self.T = torch.where(self.vessel_solid > 0, torch.full_like(Tn, self.T_wall), Ts)
            self._last_sc = sc
            # ---- controle de nível com o vapor da temperatura e do estado novos
            V = float(sum(self._vapour(self.T)[0]).sum()) * f.vol
            F_lvl = V * (1 + S_CHAR / SOLIDS_TARGET) / (1 - self.feed.ash / SOLIDS_TARGET)
            if cfg.feed_kgph is None:
                self.F = self.F + relax * (F_lvl - self.F)
            else:                                   # modo A: ajusta a parede para a vazão pedida
                target = cfg.feed_kgph / 3600.0
                self.T_wall += relax * (target - F_lvl) / max(F_lvl, 1e-9) * 40.0
                self.F = target
            info = {"vapour": V, "feed_level": F_lvl, "res_T": res, "it_T": nit}
            if verbose:
                print(f"  química {it}: vapor {3600 * V:.1f} kg/h, alimentação {3600 * self.F:.1f} kg/h, "
                      f"T média {self.T_mean() - 273.15:.1f} °C, resíduo T {res:.1e}")
        return info

    def _blend_wall(self, side, bottom):
        """Condutância de parede: lateral (corrigida) em geral, a do fundo na primeira camada."""
        out = side.clone()
        out[:, :, 0] = bottom[:, :, 0]
        return out

    def _solve(self, sc, Gamma, Sp, Sc, x0):
        sc.setup(Gamma, Sp * torch.ones_like(x0), Sc * torch.ones_like(x0))
        x, _, _ = sc.solve_ptc(x0 * sc.fluid, dtau0=5.0)
        return torch.where(sc.fluid > 0, x.clamp(min=0.0), x0)

    def _dissipation(self):
        """Φ = 2μS:S + ρβ*kω [W/m³] (a potência do agitador vira calor)."""
        f = self.flow
        phi = f.mu * f.gamma ** 2
        if f.turb is not None:
            phi = phi + self.cfg.rho0 * BETA_STAR * f.turb.k * f.turb.w
        return phi * (f.fluid > 0.5)

    # ------------------------------------------------------------------ resultados
    def T_mean(self):
        return float((self.T * self.flm).sum() / self.flm.sum())

    def kpis(self) -> dict:
        """Indicadores do reator e fechamento dos balanços de massa e energia."""
        f = self.flow
        fl = self.flm > 0
        sc = self._last_sc
        T = self.T
        rho0, cp = self.cfg.rho0, self.cp0
        Sv = []
        for (c, _), s in zip(self.items, self.state):
            kc = self._k_c(c, T)
            ns = self._n_star(c, T)
            Sv.append(rho0 * kc * ns ** 2 * c.m0 * torch.minimum(s["Z"], s["Y"] / (ns * c.m0)) * self.flm)
        Svt = sum(Sv)
        V = float(Svt.sum()) * f.vol
        T_vap = float((Svt * T).sum() / Svt.sum().clamp(min=1e-30))
        # energia: calor que entra pelas paredes (+ dissipação) = aquecimento da carga + pirólise
        Qw = rho0 * cp * float(sc.wall_flux(T).sum())
        Phi = float(self._dissipation().sum()) * f.vol
        Sf = self.F * self.feed_mask / self.V_feed
        Q_sens = float((Sf * cp * (T - self.feed.T_feed) * self.flm).sum()) * f.vol
        Q_react = sum(float(s_.sum()) * f.vol * c.dH for (c, _), s_ in zip(self.items, Sv))
        e_err = (Qw + Phi - Q_sens - Q_react) / max(abs(Qw), 1e-9)
        drain = (self.F * self.feed.ash + S_CHAR * V) / SOLIDS_TARGET
        eta = self._mu(f.gamma) if hasattr(self, "_eta0") else None
        Mw = sum(s["Y"] * self._Mw(c, s) for (c, _), s in zip(self.items, self.state)) / \
            sum(s["Y"] for s in self.state).clamp(min=1e-12)
        N, d = self.tank.rpm / 60.0, self.tank.impeller_diameter
        n_fl = float(self.flm.sum())
        mu_b = float((eta * self.flm).sum()) / n_fl if eta is not None else self.cstr0.eta
        Tb = self.T_mean()
        return {
            "T_bulk_C": Tb - 273.15, "T_max_C": float(T[fl].max()) - 273.15, "T_min_C": float(T[fl].min()) - 273.15,
            "T_wall_C": self.T_wall - 273.15, "feed_kgph": 3600 * self.F, "vapour_kgph": 3600 * V,
            "drain_kgph": 3600 * drain, "mass_balance_err": (self.F - V - drain) / max(self.F, 1e-12),
            "duty_kW": Qw / 1e3, "dissipation_kW": Phi / 1e3, "energy_balance_err": e_err,
            "h_mean": Qw / (self.A_wall * max(self.T_wall - Tb, 1e-6)),
            "Np": self.power_number(), "power_kW": f.power() / 1e3,
            "Mw_bulk_kgmol": float((Mw * self.flm).sum()) / n_fl,
            "eta_bulk": mu_b, "Re": rho0 * N * d ** 2 / mu_b,
            "slate": product_slate(T_vap), "T_vapour_C": T_vap - 273.15,
            "residence_h": rho0 * self.V_liq / max(self.F, 1e-12) / 3600.0,
        }

    def run(self, verbose: bool = True, callback=None):
        cfg = self.cfg
        t0 = time.perf_counter()
        for k in range(cfg.outer):
            revs = cfg.revs_first if k == 0 else cfg.revs_next
            self.run_flow(revs, callback=callback)
            info = self.solve_scalars(verbose=verbose)
            self.flow_rho_body(relax=0.5)
            kp = self.kpis()
            kp.update(info)
            kp["outer"] = k
            kp["wall_s"] = time.perf_counter() - t0
            self.history.append(kp)
            if verbose:
                print(f"[{k + 1}/{cfg.outer}] T fundido {kp['T_bulk_C']:.1f} °C (máx {kp['T_max_C']:.1f}), "
                      f"alimentação {kp['feed_kgph']:.0f} kg/h, calor {kp['duty_kW']:.1f} kW, "
                      f"Np {kp['Np']:.2f}, μ {kp['eta_bulk']:.2e} Pa s, {kp['wall_s'] / 60:.1f} min")
        return self.history[-1]


def class_rates_torch(c, kc):
    r1 = (kc / (2 * c.m0)) / (1.0 / 64.0 - 1.0 / c.Mw0)
    r2 = kc * M_LO[1] / (1.5 * c.m0)
    r3 = kc * M_LO[2] / (1.5 * c.m0)
    return r1, r2, r3
