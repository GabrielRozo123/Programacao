"""Gera o notebook do Colab (pirolise_reator_colab.ipynb) embutindo o pacote pyrokit em células %%writefile.

Uso:  python build_notebook.py          (gera o notebook)
      python build_notebook.py --script (gera também scripts/rodar_local.py, as mesmas células em sequência)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
MODULES = ["__init__.py", "ops.py", "geometry.py", "kinetics.py", "rheology.py", "chemistry.py", "flow.py",
           "turbulence.py", "scalar.py", "reactor.py", "video.py", "figures.py", "validation.py", "render3d.py",
           "story.py"]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str, hidden: bool = False) -> dict:
    meta = {"cellView": "form"} if hidden else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


INTRO = r"""
# ♻️ Reator de pirólise de plástico em 3D: escoamento, calor e química (Colab)

Simulação de um **reator agitado contínuo** que recebe **plástico pós-consumo derretido** (poliolefinas: HDPE, LDPE e PP) vindo de uma extrusora e o **craqueia a ~400 °C** em vapores de óleo e cera. Tudo em Python, com **GPU** no Colab, e com **validação** contra dados abertos da literatura.

| Etapa | O que faz |
|---|---|
| 1 | **Cinética e propriedades**: cisão aleatória de cadeias calibrada com termogravimetria (TGA), reologia do fundido (Cross + lei de Raju, ramo de ceras) |
| 2 | **Reator ideal 0-D**: curva de capacidade (vazão × temperatura da parede) |
| 3 | **CFD 3D** no referencial da fita helicoidal: Navier–Stokes, turbulência **k-ω SST** com lei de parede, viscosidade μ(γ̇, T, Mw), temperatura e estado do polímero em regime permanente, controle de nível |
| 4 | Resultados: cortes (T, Mw, viscosidade, velocidade), mapa de calor na parede, números do ponto de operação |
| 5 | **Validação** em três níveis (componentes, química, sistema) com veredito por item |
| 6 | **Imagem 3D** do reator em corte (ray marching na GPU) |
| 7 | **Vídeo em HD** com o resultado logo nos primeiros segundos (versão completa ~1 min e versão curta ~25 s) e texto sugerido para o post |

**Antes de rodar:** *Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4*. Sem GPU use o preset `teste` (malha grossa; roda, mas demora mais e os números mudam alguns %).

Hipóteses, equações e referências: `docs/design_brief_en.md` e `docs/parameters.json` no repositório.
"""

SETUP = r"""
#@title Ambiente: GPU e pacote `pyrokit`
import os, sys, torch
gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""
print("GPU:", gpu or "nenhuma (use o preset 'teste')")
os.makedirs("pyrokit", exist_ok=True)
os.makedirs("saida", exist_ok=True)
"""

IMPORT = r"""
#@title Carrega o pacote (recarrega se as células acima mudarem)
import importlib, sys
for m in [m for m in sys.modules if m == "pyrokit" or m.startswith("pyrokit.")]:
    del sys.modules[m]
sys.path.insert(0, ".")
import numpy as np, matplotlib.pyplot as plt, torch
from IPython.display import Image, Video, display
import pyrokit
from pyrokit import chemistry as ch, figures as FG, validation as VAL, kinetics as kin
from pyrokit.geometry import ribbon_tank, standard_anchor_tank
from pyrokit.reactor import Reactor, ReactorConfig
from pyrokit.video import br
print("pyrokit", pyrokit.__version__)
"""

PARAMS = r"""
#@title Parâmetros do caso
PRESET = "gpu"            #@param ["teste", "gpu", "gpu_fino"]
CARGA = "F3"              #@param ["F1", "F2", "F3"]
T_PAREDE = 480.0          #@param {type:"slider", min:440, max:540, step:5}
RPM = 30.0                #@param {type:"number"}
AGITADOR = "fita"         #@param ["fita", "ancora"]
AUTOR = "Gabriel Rozo · CAExperts"   #@param {type:"string"}
LINKEDIN = "linkedin.com/in/gabrielhrozo"   #@param {type:"string"}

PRESETS = {   # células no diâmetro, voltas do agitador e iterações externas
    "teste":    dict(n_diam=40,  revs_first=8,  revs_next=2, outer=2),
    "gpu":      dict(n_diam=96,  revs_first=12, revs_next=3, outer=3),
    "gpu_fino": dict(n_diam=128, revs_first=14, revs_next=3, outer=3),
}
tank = ribbon_tank(rpm=RPM) if AGITADOR == "fita" else standard_anchor_tank(T=0.8, rpm=RPM)
feed = ch.FEEDS[CARGA]
print(tank.describe())
print("carga:", feed.name, "—", feed.describe(), "| entra a", round(feed.T_feed - 273.15), "°C")
"""

KINETICS = r"""
#@title 1 · Cinética e propriedades (validação da química)
display(FG.tga_figure("saida/fig_tga.png") and Image("saida/fig_tga.png", width=960))
cheq = VAL.chemistry_checks()
for c in cheq:
    print(("✔" if c["ok"] else "✘"), c["item"], "→", br(str(c["valor"])), "| alvo:", br(str(c["alvo"])))
"""

ZERO_D = r"""
#@title 2 · Reator ideal 0-D: quanto plástico o reator processa
import math
V_liq = math.pi * tank.R ** 2 * tank.H_L
A_wall = 2 * math.pi * tank.R * tank.H_L + math.pi * tank.R ** 2
N, d = tank.rpm / 60, tank.impeller_diameter
h0 = 300.0
for _ in range(4):        # coeficiente interno pela correlação de Nagata, iterado com a viscosidade do fundido
    r0 = ch.solve_cstr(feed, V_liq, A_wall, h0, T_wall=T_PAREDE + 273.15)
    h0 = ch.nagata_h(r0.rho, N, d, r0.eta, 3240.0, 0.11, tank.T)[0]
curva = ch.capacity_curve(feed, V_liq, A_wall, h0)
print(br(f"h (Nagata) = {h0:.0f} W/m²K | T fundido {r0.T - 273.15:.1f} °C | {3600 * r0.feed:.0f} kg/h | "
         f"{r0.duty / 1e3:.1f} kW | residência {r0.residence_h:.2f} h | viscosidade {1e3 * r0.eta:.1f} mPa s"))
"""

RUN = r"""
#@title 3 · CFD 3D (GPU): escoamento ↔ temperatura e química, até o regime permanente
import time
cfg = ReactorConfig(T_wall_C=T_PAREDE, **PRESETS[PRESET])
R = Reactor(tank, feed, cfg)
print(R.flow.summary(), "|", f"Δ = {1e3 * R.flow.h:.1f} mm, folga da fita = {(tank.R - tank.impeller_diameter / 2) / R.flow.h:.1f} células")
t0 = time.time()
kp = R.run(verbose=True)
print(br(f"\nPronto em {(time.time() - t0) / 60:.1f} min"))
torch.save({"T": R.T.cpu(), "state": [{k: (v.cpu() if torch.is_tensor(v) else [e.cpu() for e in v]) for k, v in s.items()}
            for s in R.state], "kpis": kp}, "saida/resultado.pt")
"""

RESULTS = r"""
#@title 4 · Resultados: números do ponto de operação, cortes e mapa de parede
q_med = kp["duty_kW"] / R.A_wall
linhas = [("plástico processado", f"{kp['feed_kgph']:.0f} kg/h"), ("vapor (óleo, cera e gás)", f"{kp['vapour_kgph']:.0f} kg/h"),
          ("temperatura do fundido", f"{kp['T_bulk_C']:.1f} °C (de {kp['T_min_C']:.0f} a {kp['T_max_C']:.0f} °C)"),
          ("calor pela camisa", f"{kp['duty_kW']:.1f} kW ({q_med:.1f} kW/m²)"),
          ("coeficiente interno h", f"{kp['h_mean']:.0f} W/m²K"),
          ("massa molar no seio", f"{kp['Mw_bulk_kgmol']:.2f} kg/mol"),
          ("viscosidade no seio", f"{1e3 * kp['eta_bulk']:.1f} mPa s (Re = {kp['Re']:.0f})"),
          ("potência do agitador", f"{1e3 * kp['power_kW']:.1f} W (Np = {kp['Np']:.2f})"),
          ("tempo de residência", f"{kp['residence_h']:.2f} h"),
          ("vapor: gás / óleo / cera / coque", " / ".join(f"{100 * v:.0f}%" for v in kp["slate"].values()))]
for a, b in linhas:
    print(f"{a:34s} {br(b)}")
FG.capacity_figure(curva, kp, "saida/fig_capacidade.png")
FG.sections_figure(R, "saida/fig_cortes.png")
FG.wall_map_figure(R, "saida/fig_parede.png")
for p in ("saida/fig_capacidade.png", "saida/fig_cortes.png", "saida/fig_parede.png"):
    display(Image(p, width=960))
"""

VALID = r"""
#@title 5 · Validação (L1 componentes · L2 química · L3 sistema)
RODAR_KP_LAMINAR = True   #@param {type:"boolean"}
kp_lam = None
if RODAR_KP_LAMINAR and AGITADOR == "fita":
    n_kp = {"teste": 32, "gpu": 48, "gpu_fino": 64}[PRESET]
    kp_lam = VAL.kp_ribbon(lambda: ribbon_tank(rpm=RPM), n_diam=n_kp, Re=8.0)
    print(br(f"Kp laminar da fita: {kp_lam['Kp']:.0f} (Re = 8, {kp_lam['steps']} passos, {kp_lam['wall_s']:.0f} s)"))
flow_c = VAL.flow_checks(kp_lam, kp, h_nagata=h0)
sys_c, ideal = VAL.system_checks(R, kp)
checks = flow_c + cheq + sys_c
VAL.dashboard(checks, "saida/fig_validacao.png", "Validação: modelo × literatura")
n_ok = sum(c["ok"] for c in checks)
print(f"{n_ok}/{len(checks)} verificações dentro do alvo")
display(Image("saida/fig_validacao.png", width=960))
"""

RENDER = r"""
#@title 6 · Imagem 3D do reator em corte (GPU)
from pyrokit.render3d import Cutaway
f = R.flow
fl = (f.fluid > 0.5)
cw = Cutaway(tank, f.xc, f.yc, f.zc)
Tc = (R.T - 273.15)
cw.set_field("T", Tc, cmap="inferno", vmin=float(Tc[fl].min()), vmax=float(Tc[fl].max()) + 1.0, fluid=fl)
Mw = FG._bulk_Mw(R)
cw.set_field("Mw", Mw, cmap="viridis", fluid=fl.cpu())
eta = R._mu(f.gamma)
cw.set_field("eta", eta, cmap="magma", log=True, fluid=fl)
for name in ("T", "Mw", "eta"):
    from PIL import Image as PILImage
    PILImage.fromarray(cw.render(name, theta=0.6, size=(1920, 1080), ssaa=1.5)).save(f"saida/reator_{name}.png")
display(Image("saida/reator_T.png", width=960))
"""

ROTEIRO_CELL = r"""
#@title Roteiro do vídeo (textos editáveis; {chaves} são preenchidas com os resultados)
import json
ROTEIRO = json.load(open("video_roteiro.json", encoding="utf-8"))
"""

VIDEO = r"""
#@title 7 · Vídeo em HD: resultado nos primeiros segundos (completo ~1 min + curto ~25 s)
import os
from pyrokit import video as hd, story
FPS = 30                  #@param {type:"integer"}
RESOLUCAO = "1080p"       #@param ["720p", "1080p"]
size = {"720p": (1280, 720), "1080p": (1920, 1080)}[RESOLUCAO]
ssaa = 1.25 if torch.cuda.is_available() else 1.0

def nf(x, dd=0):
    return br(f"{x:.{dd}f}")

V = dict(rpm=nf(RPM), Tw=nf(T_PAREDE), vazao=nf(kp["feed_kgph"]), T=nf(kp["T_bulk_C"], 0), T_min=nf(kp["T_min_C"]),
         T_max=nf(kp["T_max_C"]), autor=AUTOR, T_vaso=nf(tank.T, 1), vol=nf(R.V_liq, 1),
         Mw0=nf(R.items[0][0].Mw0), Mw=nf(kp["Mw_bulk_kgmol"], 1), eta=nf(1e3 * kp["eta_bulk"], 1),
         q=nf(kp["duty_kW"] / R.A_wall, 1), duty=nf(kp["duty_kW"]), h=nf(kp["h_mean"]),
         h_vs=br(f"{100 * (kp['h_mean'] / h0 - 1):+.0f}% em relação à correlação de Nagata"),
         cap_lo=nf(3600 * curva[0].feed), cap_hi=nf(3600 * curva[-1].feed), n_ok=n_ok, n=len(checks))
F = lambda t: t.format(**V) if isinstance(t, str) else [F(x) for x in t]  # noqa: E731
RT = ROTEIRO
seg, curto = [], []
hk = RT["hook"]
big = [(F(a), F(b)) for a, b in hk["big"]]
seg.append(story.render_rotation(cw, "saida/s00_gancho.mp4", "T", F(hk["title"]), F(hk["subtitle"]), F(hk["kicker"]),
                                 cbar_label="T [°C]", seconds=6.0, fps=FPS, size=size, ssaa=ssaa, big=big,
                                 handle=LINKEDIN, clean_path="saida/fundo.mp4", turns=0.35))
curto.append(seg[-1])
fundo = hd.Backdrop("saida/fundo.mp4", size)
tc = RT["title_card"]
seg.append(hd.render_title_card("saida/s01_titulo.mp4", F(tc["title"]), F(tc["subtitle"]), F(tc["credit"]),
                                F(tc["disclaimer"]), size=size, fps=FPS, seconds=4.0, backdrop=fundo))
cards = [{k: F(v) for k, v in c.items()} for c in RT["context_cards"]]
seg.append(hd.render_text_cards("saida/s02_contexto.mp4", cards, size=size, fps=FPS, seconds=5.5, backdrop=fundo))
ro = RT["rotation"]
seg.append(story.render_rotation(cw, "saida/s03_rotacao.mp4", "T", F(ro["title"]), F(ro["subtitle"]), F(ro["chapter"]),
                                 captions=F(ro["captions"]), cbar_label="T [°C]", seconds=8.0, fps=FPS, size=size,
                                 ssaa=ssaa, handle=LINKEDIN, az0=-40, az1=-100, turns=0.5))
curto.append(seg[-1])
for key, fig in (("sections", "saida/fig_cortes.png"), ("wall", "saida/fig_parede.png"),
                 ("capacity", "saida/fig_capacidade.png"), ("validation", "saida/fig_validacao.png")):
    sx = RT[key]
    out = f"saida/s_{key}.mp4"
    seg.append(hd.caption_segment(fig, out, F(sx["captions"]), F(sx["chapter"]), size=size, fps=FPS,
                                  seconds=6.5, handle=LINKEDIN))
    if key in ("capacity",):
        curto.append(out)
kv = [dict(value=kp["feed_kgph"], fmt="{:.0f}", unit="kg/h"), dict(value=kp["T_bulk_C"], fmt="{:.0f}", unit="°C"),
      dict(value=kp["duty_kW"], fmt="{:.0f}", unit="kW"),
      dict(value=100 * (kp["slate"]["óleo"] + kp["slate"]["cera"]), fmt="{:.0f}", unit="%")]
for d_, lab in zip(kv, RT["kpis"]["labels"]):
    d_["label"] = lab
seg.append(hd.render_kpi_card("saida/s08_numeros.mp4", RT["kpis"]["title"], kv, size=size, fps=FPS, seconds=6.0,
                              backdrop=fundo))
curto.append(seg[-1])
seg.append(hd.render_text_cards("saida/s09_gestao.mp4", [{k: F(v) for k, v in RT["closing"].items()}], size=size,
                                fps=FPS, seconds=7.0, backdrop=fundo))
ec = RT["end_card"]
seg.append(hd.render_title_card("saida/s10_final.mp4", F(ec["line"]), "", F(ec["author"]), "", size=size, fps=FPS,
                                seconds=4.0, backdrop=fundo, contact=LINKEDIN))
curto.append(seg[-1])
hd.assemble(seg, "saida/pirolise_reator.mp4", fps=FPS, size=size)
hd.assemble(curto, "saida/pirolise_reator_curto.mp4", fps=FPS, size=size)
story.cover_image(cw, "saida/capa.png", "T", F(hk["title"]), big, size=(1920, 1080), ssaa=ssaa)
for p in ("saida/pirolise_reator.mp4", "saida/pirolise_reator_curto.mp4"):
    print(br(f"{p}: {os.path.getsize(p) / 1e6:.1f} MB"))
display(Video("saida/pirolise_reator_curto.mp4", embed=True, width=960))
display(Image("saida/capa.png", width=640))
print("\nTexto sugerido para o post:\n")
print(br(F(RT["caption"])))
"""

OUTRO = r"""
## Limitações e próximos passos

* **Escoamento**: RANS k-ω SST com lei de parede numa malha cartesiana com fronteira imersa; a parede curva do vaso usa uma camada de deslizamento com a tensão de Spalding aplicada na área real. O balanço de torque fecha melhor a cada refinamento (o resíduo cai de forma aproximadamente linear com Δ).
* **Química**: cisão aleatória com fechamento em três classes de cadeias (em vez do balanço populacional completo); seletividade de gás calibrada para tanque agitado; sem craqueamento secundário no vapor.
* **Fases**: o vapor sai do líquido no ponto em que é gerado (sem bolhas nem espuma resolvidas); superfície livre plana.
* **Próximos passos**: espaço de vapor e condensador; âncora × fita; PS e PET na carga; estudo de malha (GCI) no preset `gpu_fino`.
"""


def build(script: bool = False):
    cells = [md(INTRO), code(SETUP, hidden=True)]
    for m in MODULES:
        src = (HERE / "pyrokit" / m).read_text(encoding="utf-8")
        cells.append(code(f"%%writefile pyrokit/{m}\n" + src, hidden=True))
    roteiro = (HERE / "video_roteiro.json").read_text(encoding="utf-8")
    cells.append(code("%%writefile video_roteiro.json\n" + roteiro, hidden=True))
    body = [IMPORT, PARAMS, KINETICS, ZERO_D, RUN, RESULTS, VALID, RENDER, ROTEIRO_CELL, VIDEO]
    titles = [None, "## Parâmetros", "## 1 · Cinética", "## 2 · Reator ideal", "## 3 · CFD 3D", "## 4 · Resultados",
              "## 5 · Validação", "## 6 · Imagem 3D", "## 7 · Vídeo", None]
    for t, c in zip(titles, body):
        if t:
            cells.append(md(t))
        cells.append(code(c, hidden=c in (IMPORT, ROTEIRO_CELL)))
    cells.append(md(OUTRO))
    nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
                                       "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    out = HERE / "pirolise_reator_colab.ipynb"
    out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("notebook:", out)
    if script:
        lines = ["# Gerado por build_notebook.py: as células do notebook em sequência (para rodar fora do Colab).",
                 "import os, sys", "os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')",
                 "def display(*a, **k):\n    pass", ""]
        for c in body:
            src = "\n".join(ln for ln in c.strip("\n").splitlines() if not ln.startswith("from IPython"))
            lines.append(src)
            lines.append("")
        p = HERE / "scripts" / "rodar_local.py"
        p.parent.mkdir(exist_ok=True)
        p.write_text("\n".join(lines), encoding="utf-8")
        print("script:", p)


if __name__ == "__main__":
    build(script="--script" in sys.argv)
