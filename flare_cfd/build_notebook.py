"""Gera o notebook do Colab (flare_les_colab.ipynb) embutindo o pacote flarekit em células %%writefile.

Uso:  python build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
MODULES = ["__init__.py", "props.py", "semiempirical.py", "les.py", "dashboard.py", "safety.py", "report.py",
           "wind.py", "render.py"]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str, hidden: bool = False) -> dict:
    meta = {"cellView": "form"} if hidden else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


INTRO = r"""
# 🔥 Flare industrial: LES 3D, vento de atlas eólico e radiação térmica (Colab)

Simulação de um **flare elevado de propano (584 MW)** com o vento típico do local tirado de um **atlas eólico**, gráficos atualizados **em tempo real** enquanto o CFD resolve e um **vídeo MP4** no final, com a chama em zoom.

| Etapa | O que faz |
|---|---|
| 1 | **Clima de vento do local**: Global Wind Atlas (clima generalizado, Weibull por setor), NASA POWER (MERRA-2) ou Open-Meteo (ERA5) → perfil de camada limite (lei log) e rosa dos ventos na altura do tip |
| 2 | Referências: **API 521** (fonte pontual), **Chamberlain/Shell (1987)**, correlações de comprimento de chama e fração radiante |
| 3 | Termoquímica: equilíbrio (Cantera) na fração de mistura Z e tabela **β-PDF** de submalha |
| 4 | **LES 3D de baixo Mach em PyTorch (GPU)**, 60 s simulados, malha fina ajustada à chama, gravando um quadro a cada 0,1 s |
| 5 | Validação (LES × Chamberlain/API) e segurança no vento de projeto |
| 6 | **Varredura das direções do vento**: pegada de radiação girando pela rosa dos ventos → probabilidade de excedência dos níveis do API 521 e envoltória |
| 7 | Vídeo final: abertura, chama em zoom, painel com validação, varredura do vento e resumos |

**Antes de rodar:** *Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4*. Sem GPU o notebook usa o preset `cpu` (Δ = 0,7 m), que roda, mas encurta um pouco a chama.

A teoria, a álgebra e as referências estão no documento de revisão que acompanha o notebook (`docs/revisao_flare_cfd.html`).
"""

SETUP = r"""
#@title Ambiente: GPU, Cantera e pacote `flarekit`
import subprocess, sys, os
import torch
gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""
print("GPU:", gpu or "nenhuma (vai rodar em CPU, com malha mais grossa)")
try:
    import cantera
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "cantera"], check=False)
os.makedirs("flarekit", exist_ok=True)
"""

WIND = r"""
#@title 1 · Local e clima de vento (atlas eólico)
import numpy as np
import matplotlib.pyplot as plt
from flarekit import wind

LOCAL = "Paulínia (SP)"     #@param {type:"string"}
LAT = -22.75                #@param {type:"number"}
LON = -47.15                #@param {type:"number"}
ALTURA = 30.0               #@param {type:"number"}
FONTE_VENTO = "auto"        #@param ["auto", "gwa", "nasa", "open-meteo", "sintetico"]
Z0_LOCAL = 0.3              #@param {type:"number"}
MODO_VENTO_LES = "dominante_p90"  #@param ["dominante_p90", "dominante_media", "projeto"]

# auto: Global Wind Atlas → NASA POWER → Open-Meteo (ERA5) → rosa sintética (só sem internet)
# Z0_LOCAL escolhe a classe de rugosidade do GWA (NBR 6123: cat. II 0,07 m · III 0,3 m · IV 1,0 m)
serie = wind.get_wind_series(LAT, LON, FONTE_VENTO, z0_site=Z0_LOCAL)
clima = wind.WindClimate.from_series(serie, ALTURA)
print(clima.describe())
if serie.synthetic:
    print("\nATENÇÃO: sem acesso às fontes de vento; usando uma rosa SINTÉTICA de exemplo.")

U_LES, TH_LES = clima.design_wind(MODO_VENTO_LES)
SETOR = wind.sector_name(TH_LES)
wind_label = f"vento de {SETOR} · {U_LES:.1f} m/s a {ALTURA:.0f} m"
print(f"\nLES: {wind_label} (modo {MODO_VENTO_LES})")

fig = plt.figure(figsize=(12, 4.2))
ax = fig.add_subplot(1, 2, 1, projection="polar")
ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
bottom = np.zeros(16)
for b in range(clima.freq.shape[1]):
    ax.bar(np.radians(np.arange(16) * 22.5), 100 * clima.freq[:, b], width=np.radians(20), bottom=bottom)
    bottom += 100 * clima.freq[:, b]
ax.set_xticks(np.radians(np.arange(16) * 22.5)); ax.set_xticklabels(wind.SECTORS, fontsize=8)
ax.set_title(f"Rosa dos ventos a {ALTURA:.0f} m [% do tempo]")
ax2 = fig.add_subplot(1, 2, 2)
z = np.linspace(1, 120, 100)
ax2.plot(clima.profile(z), z, label=f"lei log, z0 = {clima.z0:.2f} m")
ax2.plot(clima.profile(z, U_LES), z, "--", label=f"perfil da LES ({U_LES:.1f} m/s no tip)")
ax2.plot([serie.U1.mean(), serie.U2.mean()], [serie.z1, serie.z2], "o", label="médias dos dados")
ax2.axhline(ALTURA, ls=":", c="k"); ax2.set_xlabel("U [m/s]"); ax2.set_ylabel("z [m]"); ax2.legend()
ax2.set_title("Perfil de camada limite")
plt.tight_layout(); plt.show()
"""

SCENARIO = r"""
#@title 2 · Cenário e modelos de referência (API 521, Chamberlain, correlações)
from flarekit.props import PROPANE, stoichiometry, state_relation, beta_pdf_table
from flarekit.semiempirical import Scenario, flame_box

VAZAO = 12.6   #@param {type:"number"}
sc = Scenario(PROPANE, mdot=VAZAO, T_j=311.0, mach=0.5, H=ALTURA, u_w=U_LES, T_inf=298.15, RH=0.5)
tip, ch, ch0 = sc.tip, sc.cham, sc.cham0
print(f"Tip: u_j = {tip['u_j']:.1f} m/s · d = {tip['d_j']:.3f} m · Q = {sc.Q/1e6:.0f} MW")
print(f"API 521 (Beychok):      L = {sc.L_api:5.1f} m")
print(f"Chamberlain, sem vento: L = {ch0.L_b:5.1f} m")
print(f"Chamberlain, {sc.u_w:.1f} m/s: L = {ch.L_b:5.1f} m · α = {ch.alpha:4.1f}° · b = {ch.b:.1f} m · "
      f"W1 = {ch.W1:.2f} m · W2 = {ch.W2:.1f} m · F_s = {ch.F_s:.3f} · SEP = {ch.SEP/1e3:.0f} kW/m²")
"""

THERMO = r"""
#@title 3 · Termoquímica: equilíbrio em Z e tabela β-PDF
st = sc.st
sr = state_relation(PROPANE, sc.T_j, sc.T_inf, chi_loss=ch.F_s)   # perda radiativa = fração radiante
tab = beta_pdf_table(sr, st["Z_st"])
refs = sc.references(sr.T_ad_st)
print(f"{sr.source} · Z_st = {st['Z_st']:.4f} · T_ad = {sr.T_ad_st:.0f} K")
print(f"Delichatsios: Fr_f = {refs['delichatsios']['Fr_f']:.2f}, L = {refs['delichatsios']['L']:.1f} m · "
      f"Heskestad: L = {refs['L_heskestad']:.1f} m · Molina: X_rad = {refs['molina']['X_rad']:.3f}")
fig, ax = plt.subplots(1, 2, figsize=(12, 3.6))
ax[0].plot(sr.Z, sr.T, lw=2); ax[0].axvline(st["Z_st"], ls="--", c="k", lw=1)
ax[0].set_xlim(0, 0.4); ax[0].set_xlabel("Z"); ax[0].set_ylabel("T [K]"); ax[0].set_title("Relação de estado")
for j in (0, 4, 8, 16):
    ax[1].plot(tab.Zt, tab.T[:, j], label=f"s = {tab.s[j]:.2f}")
ax[1].set_xlim(0, 0.4); ax[1].set_xlabel("Z̃"); ax[1].set_ylabel("T̃ [K]"); ax[1].legend()
ax[1].set_title("Média na β-PDF (variância de submalha)")
plt.tight_layout(); plt.show()
"""

RUN = r"""
#@title 4 · LES 3D (60 s) com painel ao vivo, gravando os quadros do vídeo
from flarekit.les import FlareLES, LESConfig
from flarekit.render import run_and_record

PRESET = "gpu" if torch.cuda.is_available() else "cpu"   #@param ["gpu", "gpu_fino", "gpu_ultra", "cpu", "teste"] {allow-input: true}
T_END = 60.0        #@param {type:"number"}
T_AVG = 15.0        #@param {type:"number"}
FRAME_DT = 0.1      #@param {type:"number"}
LIVE_EVERY = 5      #@param {type:"integer"}

box = flame_box(ch, sc.H)          # malha fina ajustada à chama prevista por Chamberlain
cfg = LESConfig.for_flame(PRESET, box, H=sc.H, u_ref=U_LES, z0=clima.z0, mdot=sc.mdot, u_jet=tip["u_j"],
                          X_rad=ch.F_s, T_inf=sc.T_inf, RH=sc.RH)
les = FlareLES(cfg, tab, sc.Q)
print(les.summary())
title = f"Flare de propano · {sc.Q/1e6:.0f} MW · LES 3D · {LOCAL}"
dash_sub = (f"{les.summary()} · {wind_label} · perfil log z0 = {clima.z0:.2f} m · "
            f"Smagorinsky + Z̃/β-PDF (equilíbrio) + fuligem · média a partir de {T_AVG:.0f} s")
rec = run_and_record(les, sc, title, T_END, T_AVG, FRAME_DT, LIVE_EVERY, dash_title=title, dash_sub=dash_sub,
                     wind_label=wind_label)
rec.save("flare_quadros.npz")     # permite refazer o vídeo sem rodar a LES de novo
print(f"Concluído: {les.step_n} passos, {les.wall/60:.1f} min de solver, {les.wall/les.step_n*1e3:.0f} ms/passo")
"""

VALID = r"""
#@title 5 · Validação e segurança no vento da LES
from flarekit.report import summary_figure, print_validation
from IPython.display import Image, display
fig, rows, zones = summary_figure(les, sc, refs, "flare_resumo.png", title)
print_validation(rows)
print()
for zz in zones:
    print(f"{zz['nivel_kW_m2']:5.2f} kW/m² · área {zz['area_m2']:7.0f} m² · alcance {zz['raio_max_m']:5.0f} m · {zz['descricao']}")
display(Image("flare_resumo.png"))
"""

SWEEP = r"""
#@title 6 · Varredura das direções: probabilidade de excedência e envoltória
from flarekit import render
RAIO_MAPA = 150.0    #@param {type:"number"}
grid = wind.SiteGrid.square(RAIO_MAPA, 121)
mapas = wind.exceedance_maps(sc, clima, grid)            # Chamberlain por classe de velocidade × setor
R_dw = RAIO_MAPA * 1.45
les_down = wind.les_footprint_downwind(les.rec_x, les.rec_y, rec.final["q_mean"], sc, U_LES, R_dw,
                                       2 * int(R_dw / 2.0) + 1)
linhas = render.risk_summary_figure(clima, mapas, sc, "flare_risco.png",
                                    f"Zonas de radiação ponderadas pela rosa dos ventos · {LOCAL}")
print("nível [kW/m²]  envoltória [m]  P ≥ 1% [m]  P ≥ 10% [m]")
for lev, e, p1, p10 in linhas:
    print(f"   {lev:5.2f}        {e:6.0f}        {p1:6.0f}      {p10:6.0f}")
display(Image("flare_risco.png"))
"""

VIDEO = r"""
#@title 7 · Vídeo final: abertura, chama em zoom, painel, varredura do vento e resumos
from IPython.display import Video
AUTOR = ""            #@param {type:"string"}
FPS = 30              #@param {type:"integer"}
PAINEL_ACELERADO = 2  #@param {type:"integer"}
sub_hero = f"LES 3D em GPU · {wind_label} · {LOCAL}"
segs = [
    render.render_title("v0_titulo.mp4", f"Flare de propano · {sc.Q/1e6:.0f} MW",
                        f"LES 3D · vento do atlas eólico · {LOCAL}", AUTOR, fps=FPS),
    render.render_hero(rec, ch, "v1_chama.mp4", f"Flare de propano · {sc.Q/1e6:.0f} MW", sub_hero, fps=FPS),
    render.ZoomDashboard(rec, sc, ch, title, dash_sub, t_end=T_END).render("v2_painel.mp4", fps=FPS,
                                                                          every=PAINEL_ACELERADO),
    render.render_wind_sweep(clima, mapas, les_down, "v3_vento.mp4", U_LES,
                             f"Varredura das direções do vento · {LOCAL}", fps=FPS),
    render.render_still("flare_resumo.png", "v4_resumo.mp4", 5, FPS),
    render.render_still("flare_risco.png", "v5_risco.mp4", 6, FPS),
]
render.assemble(segs, "flare_linkedin.mp4", fps=FPS)
display(Video("flare_linkedin.mp4", embed=True, width=960))
try:
    from google.colab import files
    files.download("flare_linkedin.mp4")
except Exception:
    print("Arquivo salvo em flare_linkedin.mp4")
"""

MESH = r"""
#@title 8 · (Opcional) Estudo de malha: comprimento da chama vs. Δ
RUN_MESH_STUDY = False  #@param {type:"boolean"}
if RUN_MESH_STUDY:
    res = []
    for d in (1.0, 0.7, 0.5, 0.35):
        c = LESConfig.for_flame("gpu", box, d_fine=d, H=sc.H, u_ref=U_LES, z0=clima.z0, mdot=sc.mdot,
                                u_jet=tip["u_j"], X_rad=ch.F_s)
        m = FlareLES(c, tab, sc.Q)
        while m.time < 20.0:
            m.step()
            if m.step_n % 20 == 0:
                m.diagnostics(m.time > 8.0)
        res.append((d, m.mean_flame_length(), m.mean_tilt()))
        print(f"Δ = {d:.2f} m → L = {res[-1][1]:.1f} m, inclinação = {res[-1][2]:.0f}°")
    d, L, a = map(np.array, zip(*res))
    plt.plot(d, L, "o-", label="LES"); plt.axhline(ch.L_b, ls="--", label="Chamberlain")
    plt.gca().invert_xaxis(); plt.xlabel("Δ fino [m]"); plt.ylabel("L [m]"); plt.legend(); plt.show()
"""

OUTRO = r"""
## Notas de modelagem e limitações

- **Vento:** o Global Wind Atlas dá o clima *generalizado* (terreno plano, rugosidade padrão) por setor de 30°, como Weibull A/k em várias alturas; o notebook usa a classe de rugosidade mais próxima de `Z0_LOCAL` e amostra horas equivalentes. NASA POWER (MERRA-2, ~0,5°) e Open-Meteo (ERA5, 0,25°) dão séries horárias a 10/50 m e 10/100 m; o perfil log é ajustado às duas alturas. Estabilidade atmosférica não é considerada (perfil neutro). O endpoint do GWA não é documentado oficialmente, e o Open-Meteo exige chave para uso comercial.
- **Direções:** para um flare isolado em terreno aberto a física não depende da direção, então a pegada é girada para cada setor (exato nesse caso). Com estruturas no entorno, cada direção pediria uma LES própria. A probabilidade de excedência é condicional ao flare estar queimando na vazão simulada.
- **Química rápida + equilíbrio** em fração de mistura; a perda radiativa entra como fração radiante constante (F_s de Chamberlain), como no FDS. Eficiência de combustão (CE/DRE) exigiria EDC/FPV.
- **Radiação no solo:** emissão da zona luminosa (fuligem, relação de estado no lado rico), escalada para X_rad·Q, com transmissividade de Wayne em cada caminho; sem reabsorção dentro da chama.
- **Tip:** o jato real (0,27 m, 129 m/s) é sub-malha; a fonte injeta a vazão e o fluxo de quantidade de movimento reais num bloco de 2×2 células finas.
- **Numérica e malha:** com Superbee (o limitador do FDS), Smagorinsky C_s = 0,1 e Sc_t = 0,7, a chama converge para Chamberlain com o refino. Estudo com 8,9 m/s (Chamberlain: L = 27,4 m, α = 51°): Δ = 0,7 m → 21,9 m; Δ = 0,5 m → 27,9 m e α = 56°.

**Próximo passo (PINNeAPPle):** com LES em algumas classes de velocidade, treinar um surrogate (vento, vazão → mapa de radiação) com incerteza para zonas de exclusão em tempo real.
"""


def build(out: Path = HERE / "flare_les_colab.ipynb") -> Path:
    cells = [md(INTRO), code(SETUP, hidden=True)]
    for mod in MODULES:
        src = (HERE / "flarekit" / mod).read_text()
        cells.append(code(f"%%writefile flarekit/{mod}\n{src}", hidden=True))
    cells += [code("import importlib, flarekit\nprint('flarekit pronto')"),
              md("## 1 · Local e clima de vento"), code(WIND),
              md("## 2 · Cenário e referências"), code(SCENARIO),
              md("## 3 · Termoquímica"), code(THERMO),
              md("## 4 · LES com gráficos em tempo real\nO painel abaixo é atualizado durante a solução; cada quadro "
                 "(a cada 0,1 s simulado) é gravado para o vídeo."), code(RUN),
              md("## 5 · Validação e segurança"), code(VALID),
              md("## 6 · Varredura das direções do vento"), code(SWEEP),
              md("## 7 · Vídeo para o LinkedIn"), code(VIDEO),
              md("## 8 · Estudo de malha (opcional)"), code(MESH),
              md(OUTRO)]
    nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
                                       "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    out.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    print(build())
