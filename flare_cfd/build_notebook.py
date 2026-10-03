"""Gera o notebook do Colab (flare_les_colab.ipynb) embutindo o pacote flarekit em células %%writefile.

Uso:  python build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
MODULES = ["__init__.py", "props.py", "semiempirical.py", "les.py", "dashboard.py", "safety.py", "report.py"]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str, hidden: bool = False) -> dict:
    meta = {"cellView": "form"} if hidden else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


INTRO = r"""
# 🔥 Flare industrial: LES 3D, radiação térmica e segurança (Colab)

Simulação de um **flare elevado de propano (584 MW)** sob vento cruzado, com os gráficos atualizados **em tempo real** enquanto o CFD resolve, e gravação de um **vídeo MP4** no final.

| Etapa | O que faz |
|---|---|
| 1 | Modelos de referência do **API 521** (fonte pontual) e de **Chamberlain/Shell (1987)**, mais as correlações de comprimento de chama e fração radiante |
| 2 | Termoquímica: equilíbrio (Cantera) em função da fração de mistura Z e tabela com **β-PDF** de submalha |
| 3 | **LES 3D de baixo Mach em PyTorch (GPU)**: Smagorinsky, Z̃ com TVD, Poisson direto em malha esticada, vento com perfil log, radiação no solo com transmissividade atmosférica |
| 4 | Validação (LES × Chamberlain/API) e segurança: zonas do API 521, dose térmica, probits e temperatura de aço |
| 5 | Vídeo final (simulação + resumo) pronto para o LinkedIn |

**Antes de rodar:** *Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4*. Na GPU, o preset `gpu` (Δ = 0,5 m perto da chama, ~0,8 M células) leva poucos minutos; `gpu_fino` (0,35 m) e `gpu_ultra` (0,25 m) refinam a malha. Sem GPU, o preset `cpu` (Δ = 0,7 m) roda em ~30–60 min e encurta um pouco a chama (veja o estudo de malha na seção 6).

A teoria, a álgebra completa e as referências estão no documento de revisão que acompanha este notebook (`docs/revisao_flare_cfd.html`).
"""

SETUP = r"""
#@title Ambiente: GPU, Cantera e pacote `flarekit`
import subprocess, sys, os
import torch
gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""
print("GPU:", gpu or "nenhuma (vai rodar em CPU, com malha grossa)")
try:
    import cantera
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "cantera"], check=False)
os.makedirs("flarekit", exist_ok=True)
"""

SCENARIO = r"""
#@title 1 · Cenário e modelos de referência (API 521, Chamberlain, correlações)
import numpy as np
from flarekit.props import PROPANE, stoichiometry, state_relation, beta_pdf_table
from flarekit.semiempirical import Scenario

# --- cenário (o mesmo do exemplo numérico do documento) -----------------------------
VENTO = 8.9    #@param {type:"number"}
ALTURA = 30.0  #@param {type:"number"}
VAZAO = 12.6   #@param {type:"number"}
sc = Scenario(PROPANE, mdot=VAZAO, T_j=311.0, mach=0.5, H=ALTURA, u_w=VENTO, T_inf=298.15, RH=0.5)

tip, ch, ch0 = sc.tip, sc.cham, sc.cham0
print(f"Tip: u_j = {tip['u_j']:.1f} m/s · d = {tip['d_j']:.3f} m · Q = {sc.Q/1e6:.0f} MW")
print(f"API 521 (Beychok):      L = {sc.L_api:5.1f} m")
print(f"Chamberlain, sem vento: L = {ch0.L_b:5.1f} m")
print(f"Chamberlain, {sc.u_w} m/s: L = {ch.L_b:5.1f} m · α = {ch.alpha:4.1f}° · b = {ch.b:.1f} m · "
      f"W1 = {ch.W1:.2f} m · W2 = {ch.W2:.1f} m · F_s = {ch.F_s:.3f} · SEP = {ch.SEP/1e3:.0f} kW/m²")
"""

THERMO = r"""
#@title 2 · Termoquímica: equilíbrio em Z e tabela β-PDF
import matplotlib.pyplot as plt
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
#@title 3 · LES 3D com painel ao vivo e gravação do vídeo
import torch
from flarekit.les import FlareLES, LESConfig
from flarekit.dashboard import run_live

PRESET = "gpu" if torch.cuda.is_available() else "cpu"   #@param ["gpu", "gpu_fino", "gpu_ultra", "cpu", "teste"] {allow-input: true}
T_END = 30.0       #@param {type:"number"}
T_AVG = 12.0       #@param {type:"number"}
FRAME_DT = 0.1     #@param {type:"number"}

cfg = LESConfig.preset(PRESET, H=sc.H, u_ref=sc.u_w, mdot=sc.mdot, u_jet=tip["u_j"], X_rad=ch.F_s,
                       T_inf=sc.T_inf, RH=sc.RH)
les = FlareLES(cfg, tab, sc.Q)
print(les.summary())
title = (f"Flare de propano · {sc.Q/1e6:.0f} MW · LES 3D · vento {sc.u_w:.1f} m/s" if sc.u_w > 0
         else f"Flare de propano · {sc.Q/1e6:.0f} MW · LES 3D · sem vento")
dash = run_live(les, sc, title, t_end=T_END, t_avg=T_AVG, frame_dt=FRAME_DT,
                video_path="flare_les.mp4", live=True, fps=20)
print(f"Concluído: {les.step_n} passos, {les.wall/60:.1f} min de solver, "
      f"{les.wall/les.step_n*1e3:.0f} ms/passo")
"""

VALID = r"""
#@title 4 · Validação e segurança
from flarekit.report import summary_figure, print_validation, compose_video
from flarekit import safety
from IPython.display import Image, display

fig, rows, zones = summary_figure(les, sc, refs, "flare_resumo.png", title)
print_validation(rows)
print()
for z in zones:
    print(f"{z['nivel_kW_m2']:5.2f} kW/m² · área {z['area_m2']:7.0f} m² · alcance {z['raio_max_m']:5.0f} m · {z['descricao']}")
display(Image("flare_resumo.png"))
"""

VIDEO = r"""
#@title 5 · Vídeo final (simulação + resumo) e download
from IPython.display import Video, display
compose_video("flare_les.mp4", "flare_resumo.png", "flare_linkedin.mp4", seconds=6, fps=20)
display(Video("flare_linkedin.mp4", embed=True, width=960))
try:
    from google.colab import files
    files.download("flare_linkedin.mp4")
except Exception:
    print("Arquivo salvo em flare_linkedin.mp4")
"""

MESH = r"""
#@title 6 · (Opcional) Estudo de malha: comprimento da chama vs. Δ
RUN_MESH_STUDY = False  #@param {type:"boolean"}
if RUN_MESH_STUDY:
    import matplotlib.pyplot as plt
    res = []
    for d in (1.0, 0.7, 0.5, 0.35):
        c = LESConfig.preset("gpu_fino", d_fine=d, H=sc.H, u_ref=sc.u_w, mdot=sc.mdot, u_jet=tip["u_j"], X_rad=ch.F_s)
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

- **Química rápida + equilíbrio** com fração de mistura; a perda radiativa entra como fração radiante constante (F_s de Chamberlain), como no FDS. Extinção local e eficiência de combustão (CE/DRE) exigiriam EDC/FPV.
- **Radiação no solo:** a emissão vem da zona luminosa (fuligem, relação de estado no lado rico) e é escalada para X_rad·Q, com transmissividade de Wayne em cada caminho. Não há solução da RTE com reabsorção dentro da chama.
- **Tip:** o jato real (0,27 m, 129 m/s) é sub-malha. A fonte injeta a vazão e o fluxo de quantidade de movimento reais num bloco de 2×2 células finas.
- **Numérica e malha:** o resultado é sensível à difusão numérica do transporte de Z. Com o limitador van Leer, a chama sob vento saía 35% mais curta; com Superbee (o do FDS) e Smagorinsky C_s = 0,1, Sc_t = 0,7, o comprimento converge para o de Chamberlain com o refino. Estudo de malha com vento de 8,9 m/s (Chamberlain: L = 27,4 m, α = 51°): Δ = 1,0 m → 10 m (van Leer); Δ = 0,7 m → 21,9 m; Δ = 0,5 m → 27,9 m e α = 56°. Sem vento, Δ = 0,7 m → 41,7 m (correlações: 47–54 m).
- **Validação:** comprimento e inclinação da chama e fluxo no solo comparados com Chamberlain (1987), o modelo industrial para flares sob vento, e com o API 521.

**Próximo passo (PINNeAPPle):** com algumas LES em velocidades de vento diferentes, treinar um surrogate (vento, vazão → mapa de radiação) com incerteza, para zonas de exclusão em tempo real.
"""


def build(out: Path = HERE / "flare_les_colab.ipynb") -> Path:
    cells = [md(INTRO), code(SETUP, hidden=True)]
    for mod in MODULES:
        src = (HERE / "flarekit" / mod).read_text()
        cells.append(code(f"%%writefile flarekit/{mod}\n{src}", hidden=True))
    cells += [code("import importlib, flarekit\nprint('flarekit pronto')"),
              md("## 1 · Cenário e referências"), code(SCENARIO),
              md("## 2 · Termoquímica"), code(THERMO),
              md("## 3 · LES com gráficos em tempo real\nO painel abaixo é o mesmo quadro gravado no vídeo. "
                 "Ele é atualizado a cada 0,1 s de tempo simulado."), code(RUN),
              md("## 4 · Validação e segurança"), code(VALID),
              md("## 5 · Vídeo para o LinkedIn"), code(VIDEO),
              md("## 6 · Estudo de malha (opcional)"), code(MESH),
              md(OUTRO)]
    nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
                                       "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    out.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    print(build())
