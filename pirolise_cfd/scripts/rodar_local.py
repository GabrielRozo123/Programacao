# Gerado por build_notebook.py: as células do notebook em sequência (para rodar fora do Colab).
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
def display(*a, **k):
    pass

#@title Carrega o pacote (recarrega se as células acima mudarem)
import importlib, sys
for m in [m for m in sys.modules if m == "pyrokit" or m.startswith("pyrokit.")]:
    del sys.modules[m]
sys.path.insert(0, ".")
import numpy as np, matplotlib.pyplot as plt, torch
import pyrokit
from pyrokit import chemistry as ch, figures as FG, validation as VAL, kinetics as kin
from pyrokit.geometry import ribbon_tank, standard_anchor_tank
from pyrokit.reactor import Reactor, ReactorConfig
from pyrokit.video import br
print("pyrokit", pyrokit.__version__)

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

#@title 1 · Cinética e propriedades (validação da química)
display(FG.tga_figure("saida/fig_tga.png") and Image("saida/fig_tga.png", width=960))
cheq = VAL.chemistry_checks()
for c in cheq:
    print(("✔" if c["ok"] else "✘"), c["item"], "→", br(str(c["valor"])), "| alvo:", br(str(c["alvo"])))

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

#@title Roteiro do vídeo (textos editáveis; {chaves} são preenchidas com os resultados)
import json
ROTEIRO = json.load(open("video_roteiro.json", encoding="utf-8"))

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
