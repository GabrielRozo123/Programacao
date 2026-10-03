"""Exemplo numérico: flare elevado de propano (verificação das equações do documento)."""
import numpy as np
from scipy.optimize import brentq

R_u, g, sigma = 8.314462, 9.80665, 5.670374e-8
P_atm = 101325.0

# ---------------- entradas ----------------
mdot = 12.6          # kg/s
M_f = 0.044097       # kg/mol (propano)
LHV = 46.35e6        # J/kg
gam = 1.13
T_j = 311.0          # K
Mach = 0.5
u_w = 8.9            # m/s (vento na altura do tip)
T_inf, RH = 298.15, 0.5
M_air = 0.028965
rho_air = P_atm * M_air / (R_u * T_inf)

# ---------------- tip ----------------
rho_j = P_atm * M_f / (R_u * T_j)
c_j = np.sqrt(gam * R_u * T_j / M_f)
u_j = Mach * c_j
A_tip = mdot / (rho_j * u_j)
d_j = np.sqrt(4 * A_tip / np.pi)
Q = mdot * LHV
print(f"rho_j={rho_j:.3f} kg/m3  c={c_j:.1f} m/s  u_j={u_j:.1f} m/s  d_tip={d_j:.3f} m  Q={Q/1e6:.0f} MW")
Re = rho_j * u_j * d_j / 8.0e-6
print(f"Re_tip ~ {Re:.2e}  (mu_propano ~8e-6 Pa.s)")

# ---------------- API 521 (ajuste de Beychok) ----------------
Q_btu = Q * 3.412142
L_api = 0.0059 * Q_btu**0.478 * 0.3048
print(f"L_API(Beychok) = {L_api:.1f} m")

# ---------------- estequiometria / Delichatsios-Schefer ----------------
s_air = 5 * (31.998 + 3.76 * 28.013) / 44.097
Z_st = 1 / (1 + s_air)
T_ad = 2267.0   # K, propano-ar estequiométrico (equilíbrio, literatura)
Fr_f = u_j * Z_st**1.5 / ((rho_j / rho_air)**0.25 * np.sqrt((T_ad - T_inf) / T_inf * g * d_j))
Lstar = 13.5 * Fr_f**0.4 / (1 + 0.07 * Fr_f**2)**0.2 if Fr_f < 5 else 23.0
dstar = d_j * np.sqrt(rho_j / rho_air)
L_del = Lstar * dstar / Z_st
print(f"s={s_air:.2f} Z_st={Z_st:.4f} Fr_f={Fr_f:.1f} L*={Lstar:.1f} d*={dstar:.3f} m  L_vis={L_del:.1f} m")

# ---------------- Molina et al. (2007) X_rad ----------------
def ap_H2O(T):
    t = 1000 / T
    return -0.23093 - 1.12390*t + 9.41530*t**2 - 2.99880*t**3 + 0.51382*t**4 - 1.86840e-5*t**5
def ap_CO2(T):
    t = 1000 / T
    return 18.741 - 121.310*t + 273.500*t**2 - 194.050*t**3 + 56.310*t**4 - 5.8169*t**5
x_CO2, x_H2O = 3/25.8, 4/25.8
a_p = x_CO2 * ap_CO2(T_ad) + x_H2O * ap_H2O(T_ad)
M_prod = (3*44.01 + 4*18.015 + 18.8*28.013) / 25.8 / 1000
rho_f = P_atm * M_prod / (R_u * T_ad)
W_f = 0.17 * L_del
tau_f = np.pi/12 * rho_f * W_f**2 * L_del * Z_st / mdot * 1000  # ms
X_rad_molina = 9.45e-9 * (tau_f * a_p * T_ad**4)**0.47
print(f"a_p={a_p:.3f} 1/m  tau_f={tau_f:.0f} ms  X_rad(Molina)={X_rad_molina:.3f}")

# ---------------- Chamberlain (1987) ----------------
D_s = np.sqrt(4 * mdot / (np.pi * rho_air * u_j))
W = M_f / (15.816 * M_f + 0.0395)
Ca = 0.024 * (g * D_s / u_j**2)**(1/3)
Cb, Cc = 0.2, (2.85 / W)**(2/3)
Y = brentq(lambda y: Ca*y**(5/3) + Cb*y**(2/3) - Cc, 1e-3, 1e5)
L_b0 = Y * D_s
theta_jv = 90.0
L_b = L_b0 * (0.51*np.exp(-0.4*u_w) + 0.49) * (1 - 6.07e-3*(theta_jv - 90))
Ri = lambda L: (g / (D_s**2 * u_j**2))**(1/3) * L
Rr = u_w / u_j
if Rr <= 0.05:
    alpha = (theta_jv - 90)*(1 - np.exp(-25.6*Rr)) + 8000*Rr/Ri(L_b0)
else:
    alpha = (theta_jv - 90)*(1 - np.exp(-25.6*Rr)) + (134 + 1726*np.sqrt(Rr - 0.026))/Ri(L_b0)
# checagem de continuidade em R=0.05
print(f"continuidade tilt em R=0.05: 8000R={8000*0.05:.1f}  134+1726*sqrt(0.024)={134+1726*np.sqrt(0.024):.1f}")
K = 0.185*np.exp(-20*Rr) + 0.015
a_r = np.radians(alpha)
b = L_b * np.sin(K*a_r) / np.sin(a_r) if alpha > 1e-6 else 0.2*L_b
R_l = np.sqrt(L_b**2 - b**2*np.sin(a_r)**2) - b*np.cos(a_r)
Cp_ = 1000*np.exp(-100*Rr) + 0.8
W1 = D_s*(13.5*np.exp(-6*Rr) + 1.5)*(1 - (1 - np.sqrt(rho_air/rho_j)/15)*np.exp(-70*Ri(D_s)*Cp_*Rr))
W2 = L_b*(0.18*np.exp(-1.5*Rr) + 0.31)*(1 - 0.47*np.exp(-25*Rr))
A_f = np.pi/4*(W1**2 + W2**2) + np.pi/2*(W1 + W2)*np.sqrt(R_l**2 + ((W2 - W1)/2)**2)
F_s = 0.21*np.exp(-0.00323*u_j) + 0.11
SEP = F_s * Q / A_f
print(f"D_s={D_s:.3f} W={W:.4f} Y={Y:.1f} L_b0={L_b0:.1f} L_b={L_b:.1f} R={Rr:.4f} Ri(Lb0)={Ri(L_b0):.1f} "
      f"alpha={alpha:.1f} deg K={K:.3f} b={b:.1f} R_l={R_l:.1f} W1={W1:.2f} W2={W2:.2f} A={A_f:.0f} m2 F_s={F_s:.3f} SEP={SEP/1e3:.0f} kW/m2")

# ---------------- transmissividade ----------------
p_sat = np.exp(23.18986 - 3816.42/(T_inf - 46.13))   # Pa (Antoine, Yellow Book)
p_w = RH * p_sat
tau_bp = lambda X: np.minimum(1.0, 2.02*(p_w*np.maximum(X, 1e-3))**-0.09)
def tau_wayne(X):
    psat_mmHg = np.exp(20.386 - 5132/T_inf)
    XH2O = RH*X*psat_mmHg*2.88651e2/T_inf
    XCO2 = X*273/T_inf
    lw, lc = np.log10(XH2O), np.log10(XCO2)
    return 1.006 - 0.01171*lw - 0.02368*lw**2 - 0.03188*lc + 0.001164*lc**2
print(f"p_w={p_w:.0f} Pa  tau(50 m): Bagster-Pittblado={tau_bp(50.):.3f}  Wayne={tau_wayne(50.):.3f}")

# ---------------- geometria 3D do frustum + fator de vista vetorial ----------------
def frustum_panels(H, n_ax=60, n_th=72):
    """Painéis (centro, normal, área) do frustum inclinado no plano x-z (vento em +x)."""
    base = np.array([0.0, 0.0, H]) + b*np.array([0, 0, 1.0])          # lift-off ao longo do eixo do tip (vertical)
    ax = np.array([np.sin(a_r), 0, np.cos(a_r)])
    e1 = np.array([np.cos(a_r), 0, -np.sin(a_r)]); e2 = np.array([0, 1.0, 0])
    s = (np.arange(n_ax) + 0.5)/n_ax; th = (np.arange(n_th) + 0.5)/n_th*2*np.pi
    S, TH = np.meshgrid(s, th, indexing="ij")
    r = (W1 + (W2 - W1)*S)/2
    slope = (W2 - W1)/2/R_l
    ct, st = np.cos(TH)[..., None], np.sin(TH)[..., None]
    radial = ct*e1 + st*e2
    pts = base + (S[..., None]*R_l)*ax + r[..., None]*radial
    nrm = radial - slope*ax; nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    dA = r*(2*np.pi/n_th)*(R_l/n_ax)*np.sqrt(1 + slope**2)
    P = [pts.reshape(-1, 3)]; N = [nrm.reshape(-1, 3)]; Aa = [dA.ravel()]
    for frac, rad, sgn in ((0.0, W1/2, -1), (1.0, W2/2, +1)):          # discos das extremidades
        nr = 20; rr = (np.arange(nr) + 0.5)/nr*rad
        RR, TT = np.meshgrid(rr, th, indexing="ij")
        c = base + frac*R_l*ax
        p = c + RR[..., None]*(np.cos(TT)[..., None]*e1 + np.sin(TT)[..., None]*e2)
        P.append(p.reshape(-1, 3)); N.append(np.tile(sgn*ax, (p.size//3, 1)))
        Aa.append((RR*(rad/nr)*(2*np.pi/n_th)).ravel())
    return np.vstack(P), np.vstack(N), np.concatenate(Aa), base, ax

def q_chamberlain(rec, H, normal=None):
    P, N, dA, *_ = frustum_panels(H)
    d = P - rec; r = np.linalg.norm(d, axis=1); e = d/r[:, None]
    cos_s = np.einsum("ij,ij->i", N, -e)
    vis = cos_s > 0
    V = ((cos_s*dA/(np.pi*r**2))[vis, None]*e[vis]).sum(0)          # vetor fator de vista
    F = np.linalg.norm(V) if normal is None else max(0.0, V @ normal)
    Xc = np.linalg.norm(P[vis].mean(0) - rec)
    return SEP*F*tau_bp(Xc - (W1 + W2)/4), F

def flame_center(H):
    _, _, _, base, ax = frustum_panels(H, 4, 4)
    return base + 0.5*R_l*ax

def q_point(rec, H, F=0.3, center=None):
    c = flame_center(H) if center is None else center
    D = np.linalg.norm(c - rec)
    return tau_bp(D)*F*Q/(4*np.pi*D**2)

H = 50.0
c = flame_center(H)
print(f"centro da chama (H=50 m): x={c[0]:.1f} m z={c[2]:.1f} m")
print(" x[m] | q_pt(F=0.3) | q_pt(F=Fs) | q_Chamberlain(max) [kW/m2]  (grade, a jusante/montante)")
for x in (-60, -30, 0, 15, 30, 45, 60, 90, 120):
    rec = np.array([float(x), 0, 0])
    qc, F = q_chamberlain(rec, H)
    print(f"{x:5d} | {q_point(rec,H)/1e3:8.2f} | {q_point(rec,H,F_s)/1e3:8.2f} | {qc/1e3:8.2f}   (F_view={F:.4f})")

# altura mínima para 6.31 kW/m2 no pé da chaminé (pior ponto do solo) e 1.58 a 60 m
def worst_ground(H, fn):
    xs = np.linspace(-20, 120, 71)
    return max(fn(np.array([x, 0, 0]), H) for x in xs)
for lim in (9.46e3, 6.31e3, 4.73e3):
    Hp = brentq(lambda h: worst_ground(h, lambda r, hh: q_point(r, hh)) - lim, 5, 300)
    Hc = brentq(lambda h: worst_ground(h, lambda r, hh: q_chamberlain(r, hh)[0]) - lim, 5, 300)
    print(f"H_min p/ q_max_solo <= {lim/1e3:.2f} kW/m2:  ponto-fonte(F=0.3) {Hp:.1f} m | Chamberlain {Hc:.1f} m")

# ---------------- dose, probit e fuga ----------------
from scipy.special import erf
def prob(Y): return 0.5*(1 + erf((Y - 5)/np.sqrt(2)))
q0 = 6.31e3; t_r = 5.0; u_esc = 2.5
rec = np.array([30.0, 0, 0]); r0 = np.linalg.norm(flame_center(H) - rec)
t_eff = t_r + 0.6*r0/u_esc
D = t_eff*q0**(4/3)
print(f"r0={r0:.1f} m  t_eff={t_eff:.1f} s  dose={D/1e4:.0f} x1e4 (W/m2)^(4/3)s = {t_eff*(q0/1e3)**(4/3):.0f} TDU")
for nm, a, bb in (("1o grau", -39.83, 3.0186), ("2o grau", -43.14, 3.0186), ("fatal TNO", -36.38, 2.56)):
    Yp = a + bb*np.log(D); print(f"  {nm}: Y={Yp:.2f} P={prob(Yp)*100:.2f}%")
Y_eis = -14.9 + 2.56*np.log(D/1e4); print(f"  fatal Eisenberg: Y={Y_eis:.2f} P={prob(Y_eis)*100:.3f}%")

# ---------------- temperatura de superfície de aço ----------------
for qinc in (4.73e3, 9.46e3, 20e3):
    f = lambda Ts: 0.9*qinc - 15*(Ts - T_inf) - 0.9*sigma*(Ts**4 - T_inf**4)
    Ts = brentq(f, T_inf, 2000)
    print(f"q_inc={qinc/1e3:.2f} kW/m2 -> T_s(regime)={Ts-273.15:.0f} C (alpha=eps=0.9, h=15)")

# ---------------- TRI ----------------
for I in (0.1, 0.2, 0.3):
    print(f"I_T={I}: <T^4>/T^4 = {1 + 6*I**2 + 3*I**4:.3f}")

# ---------------- soot Planck mean ----------------
n, k = 1.57, 0.56
C0 = 36*np.pi*n*k/((n**2 - k**2 + 2)**2 + 4*n**2*k**2)
print(f"C0={C0:.3f}  kappa_P,soot = {3.83*C0/1.4388e-2:.0f} f_v T")
D_star = (Q/(rho_air*1005*T_inf*np.sqrt(g)))**0.4
print(f"D* (FDS) = {D_star:.1f} m  -> dx entre {D_star/16:.2f} e {D_star/4:.2f} m")

# ---------------- caso de projeto consistente ----------------
Hd = brentq(lambda h: worst_ground(h, lambda r, hh: q_chamberlain(r, hh)[0]) - 6.31e3, 5, 300)
xs = np.linspace(-20, 120, 141)
qs = np.array([q_chamberlain(np.array([x, 0, 0]), Hd)[0] for x in xs])
xm = xs[qs.argmax()]
print(f"\nH_d={Hd:.1f} m: q_max={qs.max()/1e3:.2f} kW/m2 em x={xm:.0f} m")
for lim in (4.73e3, 3.0e3, 1.58e3):
    xd = brentq(lambda x: q_chamberlain(np.array([x, 0, 0]), Hd)[0] - lim, xm, 400)
    xu = brentq(lambda x: q_chamberlain(np.array([x, 0, 0]), Hd)[0] - lim, -400, xm)
    print(f"  q={lim/1e3:.2f} kW/m2: jusante x={xd:.0f} m | montante x={xu:.0f} m")
rec = np.array([xm, 0, 0]); r0 = np.linalg.norm(flame_center(Hd) - rec); q0 = qs.max()
for t_r, u_esc in ((5.0, 2.5), (5.0, 1.0), (30.0, 2.5)):
    t_eff = t_r + 0.6*r0/u_esc
    D = t_eff*q0**(4/3)
    out = [f"t_r={t_r:.0f}s u={u_esc}m/s r0={r0:.0f}m t_eff={t_eff:.0f}s dose={D/1e4:.0f} TDU"]
    for nm, a, bb in (("1o", -39.83, 3.0186), ("2o", -43.14, 3.0186), ("fatal TNO", -36.38, 2.56)):
        out.append(f"{nm}:{prob(a + bb*np.log(D))*100:.2f}%")
    print("  " + " | ".join(out))
