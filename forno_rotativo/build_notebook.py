"""Gera o notebook do Colab (tambor_pirolise_colab.ipynb) embutindo o pacote tamborkit em células %%writefile.

Uso:  python build_notebook.py          (gera o notebook)
      python build_notebook.py --script (gera também scripts/rodar_local.py, as mesmas células em sequência)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
MODULES = ["__init__.py", "geometry.py", "feed.py", "furnace.py", "batch.py", "dem.py", "phasedem.py", "combustion.py",
           "furnace_les.py", "flames.py", "video.py", "scene.py", "timelapse.py", "compare.py", "story.py",
           "validation.py"]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str, hidden: bool = False) -> dict:
    meta = {"cellView": "form"} if hidden else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


INTRO = r"""
# 🔥 Tambor rotativo de pirólise em batelada: combustão, troca térmica, cinética e carvão (Colab)

Uma batelada inteira de **lixo marinho misto** (o resíduo pós-consumo que a UFRJ/IVIG processa, recolhido na Baía de Guanabara) num **tambor rotativo aquecido por fora**, do tamanho do equipamento do vídeo (classe Beston BLJ-3, Ø 1,4 m × 4,9 m, aletas internas). Tudo em Python, com **GPU** no Colab, e com **validação** contra a literatura aberta.

| Etapa | O que faz |
|---|---|
| 1 | **Cinética** de 9 componentes do lixo (PE, PP, PS, PET, PVC em duas etapas, borracha, celulósicos, água, areia) e TGA |
| 2 | **Batelada de 6–8 h**: fornalha (zonas de Hottel, WSGG), casco girando, contato parede-carga (penetração), radiação interna, secagem, fusão, pirólise, carvão, craqueamento no espaço livre, condensador e **gás próprio voltando ao queimador** — **girando × parado**, com e sem aletas, várias rotações |
| 3 | **DEM** da carga: pedaços de lixo girando com o tambor e as aletas (GPU) |
| 4 | **LES 3D da fornalha**: chamas dos queimadores, gases quentes em volta do tambor e fluxo de calor no casco |
| 5 | **Validação** (Suzuki, Faussone, Fulgencio-Medrano, Beston, UFRJ) com veredito por item |
| 6 | **Vídeo em HD**: o time-lapse da batelada com o **gráfico se atualizando ao vivo**, parado × girando, DEM e chamas |

**Antes de rodar:** *Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4*. Sem GPU use o preset `teste`.

Hipóteses, equações e referências: `docs/brief_tambor_batelada.md` e `docs/pesquisa/` no repositório.
"""

SETUP = r"""
#@title Ambiente: GPU, Cantera e pacote `tamborkit`
import os, sys, subprocess, torch
gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""
print("GPU:", gpu or "nenhuma (use o preset 'teste')")
try:
    import cantera
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "cantera"], check=False)
os.makedirs("tamborkit", exist_ok=True)
os.makedirs("saida", exist_ok=True)
"""

IMPORT = r"""
#@title Carrega o pacote
import importlib, os, sys, json, pickle, math
os.makedirs("saida", exist_ok=True)
for m in [m for m in sys.modules if m == "tamborkit" or m.startswith("tamborkit.")]:
    del sys.modules[m]
sys.path.insert(0, ".")
import numpy as np, matplotlib.pyplot as plt, torch
from IPython.display import Image, Video, display
from tamborkit import feed as fd, validation as VAL, story as ST
from tamborkit.geometry import Drum
from tamborkit.batch import BatchDrum, BatchConfig, Control
from tamborkit.furnace import Furnace
from tamborkit.video import br
"""

PARAMS = r"""
#@title Parâmetros do caso
PRESET = "gpu"            #@param ["teste", "gpu"]
CARGA = "base"            #@param ["base", "plastico_triado", "rejeito_rio"]
MASSA_KG = 1000.0         #@param {type:"number"}
UMIDADE = 0.15            #@param {type:"number"}
RPM = 0.8                 #@param {type:"number"}
ALETAS = 6                #@param {type:"integer"}
T_PAREDE = 500.0          #@param {type:"slider", min:420, max:580, step:10}
AUTOR = "Gabriel Rozo · CAExperts"   #@param {type:"string"}
LINKEDIN = "linkedin.com/in/gabrielhrozo"   #@param {type:"string"}
import os
PRESET = os.environ.get("PRESET", PRESET)
PRESETS = {
    # DEM: rotação simulada, tamanho dos pedaços e fatia periódica; LES: malha e tempos; vídeo: segundos do time-lapse
    # o DEM grava um terço de volta (duas passagens de aleta): o laço do vídeo não tem emenda
    # DEM com mudança de fase: rotação simulada (regime de rolamento), fatia, voltas para a batelada inteira e
    # duração do contato; LES: malha e tempos; vídeo: segundos do time-lapse
    "teste": dict(dem_rpm=3.0, dem_slab=0.4, dem_rev=4.0, dem_tc=0.010, les="teste", les_t=17.0, les_rec=3.0,
                  timelapse_s=30.0),
    "gpu": dict(dem_rpm=2.0, dem_slab=0.5, dem_rev=6.0, dem_tc=0.006, les="gpu", les_t=24.0, les_rec=4.0,
                timelapse_s=40.0),
}
P = PRESETS[PRESET]
drum = Drum(R=0.70, L=4.9, rpm=RPM, n_lifters=ALETAS, lifter_h=0.12, lifter_t=0.012)
charge = fd.Charge(**{**fd.CHARGES[CARGA].__dict__, "mass": MASSA_KG, "moisture": UMIDADE, "fill": 0.65})
control = Control(setpoint_C=T_PAREDE)
print(charge.describe())
print(br(f"tambor Ø {drum.D:.2f} m × {drum.L:.1f} m, {ALETAS} aletas de {drum.lifter_h * 1000:.0f} mm, {RPM} rpm, Fr = {drum.froude():.1e}"))
"""

KINETICS = r"""
#@title 1 · Cinética e TGA (picos de DTG, rendimentos finais)
rows_kin = VAL.chemistry_checks() + VAL.furnace_checks()
print(VAL.summary(rows_kin))
fig, ax = plt.subplots(figsize=(10, 5))
for k in ["LDPE", "HDPE", "PP", "PS", "PET", "PVC", "CELL", "RUBc"]:
    T, m, d = fd.tga(k, 10)
    ax.plot(T - 273.15, d * 100, label=fd.COMPONENTS[k].name)
T, m, d = fd.tga(charge.masses(), 10)
ax.plot(T - 273.15, d * 100, "k", lw=3, label="carga (mistura)")
ax.set_xlim(100, 650); ax.set_xlabel("T (°C)"); ax.set_ylabel("−dm/dT (%/K) a 10 K/min"); ax.legend(fontsize=8)
fig.savefig("saida/fig_tga.png", dpi=120, bbox_inches="tight"); plt.show()
y = fd.ultimate_yields(charge)
print(br("rendimentos finais (isoterma, sem craqueamento secundário): " +
         ", ".join(f"{k} {100 * v:.1f}%" for k, v in y.items() if v > 0.001)))
"""

BATCH = r"""
#@title 2 · Batelada completa: girando × parado, sem aletas e outras rotações
def roda(mode="rotativo", rpm=None, n_lifters=None, snap=120.0, t_max=14.0):
    d = Drum(R=drum.R, L=drum.L, rpm=rpm or drum.rpm, n_lifters=drum.n_lifters if n_lifters is None else n_lifters,
             lifter_h=drum.lifter_h, lifter_t=drum.lifter_t)
    b = BatchDrum(d, charge, cfg=BatchConfig(mode=mode, t_max_h=t_max, snap_every=snap, control=control))
    s = b.run(verbose=False)
    s["h_mean"] = float(np.mean([r["h_wb"] for r in b.log]))
    s["Tmax"] = max(r["T_casco_max"] for r in b.log)
    return b, s

b_rot, s_rot = roda("rotativo")
print(br(f"girando: {s_rot['duracao_h']:.1f} h, óleo {100 * s_rot['oleo']:.0f} %, casco máx {s_rot['Tmax']:.0f} °C"))
b_est, s_est = roda("estatico", t_max=16.0)
print(br(f"parado:  {s_est['duracao_h']:.1f} h, óleo {100 * s_est['oleo']:.0f} %, não convertido {100 * s_est['nao_convertido']:.1f} %, casco máx {s_est['Tmax']:.0f} °C"))
sweep = {}
for nome, kw in (("sem_aletas", dict(n_lifters=0)), ("rpm0.4", dict(rpm=0.4)), ("rpm2", dict(rpm=2.0))):
    _, sweep[nome] = roda(snap=1800.0, **kw)
    print(br(f"{nome:10s}: {sweep[nome]['duracao_h']:.2f} h, h parede-carga {sweep[nome]['h_mean']:.0f} W/m²K"))
ST.curves_figure({f"girando {RPM} rpm": b_rot.log, "parado": b_est.log}, "saida/fig_curvas.png",
                 "Girando × parado: mesma carga, mesma fornalha")
display(Image("saida/fig_curvas.png", width=1100))
for k in ("oleo", "aquoso", "gas", "carvao", "cinzas"):
    print(br(f"  {k:8s} {100 * s_rot[k]:5.1f} % da carga úmida"))
print(br(f"combustível auxiliar: {s_rot['aux_kg']:.0f} kg de GLP ({s_rot['aux_GJ_por_t']:.2f} GJ/t); gás para o flare: {s_rot['Q_flare_GJ']:.2f} GJ"))
"""

DEM = r"""
#@title 3 · DEM da carga com mudança de fase: da partida ao carvão
from tamborkit.phasedem import PhaseDEM, PhaseConfig, NAMES
pdem = PhaseDEM(drum, charge, b_rot.log, PhaseConfig(slab=P["dem_slab"], rpm=P["dem_rpm"], n_rev=P["dem_rev"],
                                                    contact_time=P["dem_tc"]))
print(pdem.describe())
recs = pdem.run_batch()
st_pre = pdem.stats().as_dict()
fase = dict(recs=recs, label=pdem.label.cpu().numpy(), names=NAMES)
# trecho frio (antes do relógio da batelada): lixo solto girando com as aletas, para o segmento "dentro do tambor"
pre = pdem.pre_records
dem_solto = dict(frames=pre, r=pre[0]["r"], label=pdem.label.cpu().numpy(), names=NAMES, rpm=P["dem_rpm"],
                 fill=charge.fill, stats=st_pre, lacey=float("nan"))
rows_dem = VAL.dem_checks(st_pre, charge.fill, Drum(R=drum.R, L=drum.L, rpm=P["dem_rpm"]))
rows_fase = VAL.phase_checks(fase, b_rot.log, drum, P["dem_slab"])
print(VAL.summary(rows_dem + rows_fase))
"""

LES = r"""
#@title 4 · LES 3D da fornalha (chamas de GLP na partida, com o casco a 500 °C)
from tamborkit.furnace_les import FurnaceLES, FurnaceLESConfig
from tamborkit.flames import FlameRecorder, FlameRenderer
Q_LES = 400e3
les = FurnaceLES(FurnaceLESConfig.preset(P["les"], Q_fire=Q_LES, T_shell=T_PAREDE + 273.15, rpm=RPM))
print(br(f"LES: {les.n_cells / 1e3:.0f} mil células de {les.h * 100:.0f} cm; {les.tab['source']}"))
gravador = FlameRecorder(les, t_start=P["les_t"] - P["les_rec"])
les.run(P["les_t"], t_avg=P["les_rec"], frame_dt=1 / 30, on_frame=gravador)
eb = les.energy_balance()
flux = les.drum_flux_map()
chamas = gravador.data()
dev = "cuda" if torch.cuda.is_available() else "cpu"
fl_corte = FlameRenderer(chamas, view="corte", device=dev)
fl_lateral = FlameRenderer(chamas, view="lateral", device=dev)
les_frames = dict(Q=Q_LES, Tmean=les.mean("T"), xc=les.xc, yc=les.yc, zc=les.zc)
ST.flux_figure(flux, les_frames, "saida/fig_fornalha.png")
display(Image("saida/fig_fornalha.png", width=1100))
print(br(f"calor para o tambor: {eb['Q_paredes'] / 1e3:.0f} kW de {Q_LES / 1e3:.0f} kW ({100 * eb['Q_paredes'] / Q_LES:.0f} %); "
         f"T máx {eb['T_max'] - 273:.0f} °C; massa: saída/entrada = {eb['m_out'] / eb['m_in']:.2f}"))
"""

VALID = r"""
#@title 5 · Validação
rows_batch = VAL.batch_checks(s_rot, s_est, sweep, log=b_rot.log)
rows_les = [VAL._row("N1 LES", "conservação de massa na fornalha (saída/entrada)", eb["m_out"] / eb["m_in"], "1 ± 0,1",
                     0.9, 1.1, "", "projeção na continuidade discreta")]
resumo = rows_kin + rows_dem + rows_fase + rows_les + rows_batch
print(VAL.summary(resumo))
ST.validation_figure(resumo, "saida/fig_validacao.png")
display(Image("saida/fig_validacao.png", width=1100))
json.dump(dict(rotativo=s_rot, estatico=s_est, sweep=sweep, validacao=[{k: (bool(v) if k == "ok" else v) for k, v in r.items()} for r in resumo]),
          open("saida/resultados.json", "w"), ensure_ascii=False, indent=1, default=float)
"""

ROTEIRO_CELL = r"""
#@title Roteiro do vídeo (textos editáveis)
ROTEIRO = json.load(open("video_roteiro.json", encoding="utf-8"))
"""

VIDEO = r"""
#@title 6 · Vídeo em HD: time-lapse com gráfico ao vivo, parado × girando, DEM e chamas
from tamborkit import video as hd
from tamborkit.timelapse import BatchScene
from tamborkit.compare import render_compare
FPS = 30                  #@param {type:"integer"}
RESOLUCAO = "1080p"       #@param ["720p", "1080p"]
size = {"720p": (1280, 720), "1080p": (1920, 1080)}[RESOLUCAO]
nf = lambda x, dd=0: br(f"{x:.{dd}f}")  # noqa: E731
V = dict(massa=nf(MASSA_KG / 1000, 1), D=nf(drum.D, 1), L=nf(drum.L, 1), rpm=nf(RPM, 1), Tw=nf(T_PAREDE), autor=AUTOR,
         t_rot=nf(s_rot["duracao_h"], 1), t_est=nf(s_est["duracao_h"], 0), Tmax_est=nf(s_est["Tmax"]),
         oleo=nf(s_rot["oleo_kg"]), rpm_dem=nf(P["dem_rpm"], 1), Q_les=nf(Q_LES / 1e3),
         T_chama=nf(eb["T_max"] - 273.15), Q_tambor=nf(eb["Q_paredes"] / 1e3), ef=nf(100 * eb["Q_paredes"] / Q_LES),
         g_rpm=nf(100 * (s_rot["duracao_h"] - sweep["rpm2"]["duracao_h"]) / s_rot["duracao_h"]),
         g_aleta=nf(100 * (sweep["sem_aletas"]["duracao_h"] - s_rot["duracao_h"]) / sweep["sem_aletas"]["duracao_h"]),
         n_ok=sum(r["ok"] for r in resumo), n=len(resumo))
F = lambda t: t.format(**V) if isinstance(t, str) else [F(x) for x in t]  # noqa: E731
RT = ROTEIRO
seg, curto = [], []
tl = RT["timelapse"]
scene = BatchScene(b_rot, {"fase": fase}, None, size=size, fps=FPS, seconds=P["timelapse_s"], title=F(tl["title"]),
                   subtitle=F(tl["subtitle"]), flames=fl_corte, flames_Q=Q_LES)
seg.append(scene.render("saida/s00_timelapse.mp4")); curto.append(seg[-1])
tc = RT["title_card"]
fundo = hd.Backdrop("saida/s00_timelapse.mp4", size)
seg.append(hd.render_title_card("saida/s01_titulo.mp4", F(tc["title"]), F(tc["subtitle"]), F(tc["credit"]),
                                F(tc["disclaimer"]), size=size, fps=FPS, seconds=4.5, backdrop=fundo))
cards = [{k: F(v) for k, v in c.items()} for c in RT["context_cards"]]
seg.append(hd.render_text_cards("saida/s02_contexto.mp4", cards, size=size, fps=FPS, seconds=5.5, backdrop=fundo))
rt = RT["rates"]
seg.append(ST.render_rates_segment(drum, b_rot.log, fase, "saida/s025_taxas.mp4", seconds=20.0, fps=FPS, size=size,
                                   title=F(rt["title"]), subtitle=F(rt["subtitle"])))
seg.append(render_compare(b_rot, b_est, "saida/s03_comparacao.mp4", seconds=16.0, fps=FPS, size=size,
                          flames=fl_corte, flames_Q=Q_LES))
curto.append(seg[-1])
cp = RT["compare"]
seg.append(hd.caption_segment("saida/fig_curvas.png", "saida/s04_curvas.mp4", F(cp["captions"]), F(cp["chapter"]),
                              size=size, fps=FPS, seconds=8.0, handle=LINKEDIN))
dm = RT["dem"]
seg.append(ST.render_dem_segment(drum, dem_solto, "saida/s05_dem.mp4", seconds=9.0, fps=FPS, size=size,
                                 title=F(dm["title"]), captions=F(dm["captions"]), speed_label=F(dm["speed"])))
fl = RT["flame"]
seg.append(ST.render_flame_views(drum, fl_corte, fl_lateral, chamas["meta"], "saida/s06_chamas.mp4", Ts_C=T_PAREDE,
                                 seconds=9.0, fps=FPS, size=size, title=F(fl["title"]), captions=F(fl["captions"]),
                                 info=F(fl["info"])))
seg.append(hd.caption_segment("saida/fig_fornalha.png", "saida/s07_fluxo.mp4", F(fl["captions"])[1:], "Fornalha",
                              size=size, fps=FPS, seconds=6.0, handle=LINKEDIN))
cv = RT["curves"]
va = RT["validation"]
seg.append(hd.caption_segment("saida/fig_validacao.png", "saida/s08_validacao.mp4", F(va["captions"]), F(va["chapter"]),
                              size=size, fps=FPS, seconds=7.0, handle=LINKEDIN))
kv = [dict(value=s_rot["duracao_h"], fmt="{:.1f}", unit="h"), dict(value=s_rot["oleo_kg"], fmt="{:.0f}", unit="kg"),
      dict(value=s_rot["carvao_kg"] + s_rot["cinzas_kg"], fmt="{:.0f}", unit="kg"),
      dict(value=s_rot["aux_kg"] / (MASSA_KG / 1000), fmt="{:.0f}", unit="kg")]
for d_, lab in zip(kv, RT["kpis"]["labels"]):
    d_["label"] = lab
seg.append(hd.render_kpi_card("saida/s09_numeros.mp4", F(RT["kpis"]["title"]), kv, size=size, fps=FPS, seconds=6.0, backdrop=fundo))
curto.append(seg[-1])
seg.append(hd.render_text_cards("saida/s10_gestao.mp4", [{k: F(v) for k, v in RT["closing"].items()}], size=size,
                                fps=FPS, seconds=7.0, backdrop=fundo))
ec = RT["end_card"]
seg.append(hd.render_title_card("saida/s11_final.mp4", F(ec["line"]), "", F(ec["author"]), "", size=size, fps=FPS,
                                seconds=4.0, backdrop=fundo, contact=LINKEDIN))
curto.append(seg[-1])
hd.assemble(seg, "saida/tambor_pirolise.mp4", fps=FPS, size=size)
hd.assemble(curto, "saida/tambor_pirolise_curto.mp4", fps=FPS, size=size)
hd.still_of("saida/s00_timelapse.mp4", "saida/capa.png", P["timelapse_s"] * 0.55)
for p in ("saida/tambor_pirolise.mp4", "saida/tambor_pirolise_curto.mp4"):
    print(br(f"{p}: {os.path.getsize(p) / 1e6:.1f} MB"))
display(Video("saida/tambor_pirolise_curto.mp4", embed=True, width=960))
print("\nTexto sugerido para o post:\n")
print(br(F(RT["caption"])))
"""

OUTRO = r"""
## Limitações e próximos passos

* **Carga**: em cada fatia o leito girando é bem misturado na seção (o DEM mostra que a mistura leva poucas voltas, minutos contra horas de batelada) e troca calor pelo modelo de penetração; o tambor parado é uma pilha que só conduz (camadas). A fusão é tratada como colapso do volume aparente, sem escoamento do fundido entre fatias.
* **DEM**: esferas macias (rigidez reduzida) numa fatia periódica, nos estados "lixo solto" e "carvão"; no preset `teste` a rotação simulada é 3× a real (mesmo regime de rolamento).
* **Fornalha**: o modelo zonal (Hottel + WSGG) conduz a batelada; a LES 3D mostra as chamas e a distribuição do calor no casco para um estado de queima (o refratário é tratado como rerradiante).
* **Química**: lumps de produtos por componente com rendimentos da literatura; craqueamento secundário simples no espaço livre; sem cloro no óleo (8–30 % do Cl do PVC iria para o óleo, Fulgencio-Medrano 2022).
* **Próximos passos**: medir no equipamento da UFRJ a temperatura da carga e da parede ao longo da batelada; calibrar a composição real do lixo; espaço livre 3D com o refluxo da cera.
"""


def build(script: bool = False):
    cells = [md(INTRO), code(SETUP, hidden=True)]
    for m in MODULES:
        src = (HERE / "tamborkit" / m).read_text(encoding="utf-8")
        cells.append(code(f"%%writefile tamborkit/{m}\n" + src, hidden=True))
    roteiro = (HERE / "video_roteiro.json").read_text(encoding="utf-8")
    cells.append(code("%%writefile video_roteiro.json\n" + roteiro, hidden=True))
    body = [IMPORT, PARAMS, KINETICS, BATCH, DEM, LES, VALID, ROTEIRO_CELL, VIDEO]
    titles = [None, "## Parâmetros", "## 1 · Cinética", "## 2 · Batelada", "## 3 · DEM da carga", "## 4 · LES da fornalha",
              "## 5 · Validação", None, "## 6 · Vídeo"]
    for t, c in zip(titles, body):
        if t:
            cells.append(md(t))
        cells.append(code(c, hidden=c in (IMPORT, ROTEIRO_CELL)))
    cells.append(md(OUTRO))
    nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
                                       "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    out = HERE / "tambor_pirolise_colab.ipynb"
    out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("notebook:", out)
    if script:
        lines = ["# Gerado por build_notebook.py: as células do notebook em sequência (para rodar fora do Colab).",
                 "import os, sys", "os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')",
                 "def display(*a, **k):\n    pass", "Image = Video = lambda *a, **k: None", ""]
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
