"""Gera o notebook Colab ``notebooks/Analise_Vibracional_Peneira.ipynb`` (sem saídas).

    python scripts/build_notebook.py
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook()
C = []


def md(s):
    C.append(nbf.v4.new_markdown_cell(s.strip()))


def code(s):
    C.append(nbf.v4.new_code_cell(s.strip()))


md(r"""
# Análise vibracional de peneira — reprocessamento dos dados Pulse VA

**Objetivo:** a partir dos dados brutos dos 8 acelerômetros triaxiais do sistema **Pulse VA** (Haver & Boecker),
recalcular em Python os parâmetros do relatório do fabricante (G-Force, curso/stroke, frequência, ângulo de força,
fase, corpo central, desvios de corpo rígido), entender a modelagem por trás deles e verificar a qualidade da medição.

| Etapa | Conteúdo |
|---|---|
| 0 | Configuração (Colab ou local) e carregamento dos arquivos |
| 1 | Leitura e inspeção dos dados brutos |
| 2 | Modelo físico: movimento harmônico, órbita elíptica, curso |
| 3 | Rastreamento de ordem (rotação variável) |
| 4 | Resultados por sensor, órbitas e corpo rígido |
| 5 | Validação contra o relatório Pulse |
| 6 | Diagnóstico: integridade dos sensores, eixo Z, ordens fracionárias |
| 7 | Geração do relatório PDF e da planilha Excel |

> Código-fonte: pacote `pulseva/` (leitura, rastreamento de ordem, métricas, diagnósticos, figuras, relatório).
""")

md("## 0. Configuração")
code(r"""
import os, sys, glob, pathlib
IN_COLAB = "google.colab" in sys.modules

REPO_URL = "https://github.com/GabrielRozo123/Programacao.git"
BRANCH = "claude/kind-babbage-c3hqit"      # após o merge na main, troque para "main"

if IN_COLAB:
    if not pathlib.Path("Programacao").exists():
        !git clone -q -b {BRANCH} {REPO_URL}
    !pip -q install reportlab
    PROJ = pathlib.Path("Programacao/peneira_vibracional").resolve()
else:
    here = pathlib.Path.cwd()
    PROJ = here.parent if here.name == "notebooks" else here
sys.path.insert(0, str(PROJ))

import numpy as np, pandas as pd, matplotlib.pyplot as plt
from IPython.display import display
import pulseva as pv
from pulseva import plots as pl

pd.set_option("display.precision", 3)
def show(fig):
    display(fig); plt.close(fig)
print("pulseva", pv.__version__, "| projeto:", PROJ)
""")

md(r"""
### Arquivos de entrada
* **XML** exportado pelo Pulse DAQ (obrigatório).
* **JSON** com os números do relatório Pulse a comparar (opcional; formato em `README.md`).

No Colab, a célula abaixo abre o seletor de arquivos. Localmente, ela procura em `privado/dados/`.
""")
code(r"""
XML_PATH = os.environ.get("PULSEVA_XML")
REF_PATH = os.environ.get("PULSEVA_REF")
if IN_COLAB and not XML_PATH:
    from google.colab import files
    print("Selecione o XML do Pulse e, se tiver, o JSON de referência do relatório:")
    up = files.upload()
    XML_PATH = next(k for k in up if k.lower().endswith(".xml"))
    REF_PATH = next((k for k in up if k.lower().endswith(".json")), None)
elif not XML_PATH:
    XML_PATH = sorted(glob.glob(str(PROJ / "privado/dados/*.xml")))[0]
    refs = sorted(glob.glob(str(PROJ / "privado/dados/*.json")))
    REF_PATH = refs[0] if refs else None
print("XML :", XML_PATH, "\nJSON:", REF_PATH)
""")

md(r"""
## 1. Leitura e inspeção dos dados

Cada `<DataList Source="L1">` traz os pontos `X, Y, Z` (em **g**) de um sensor. A taxa é de **800 Hz** durante
**10 s**, o que dá **8000 amostras por canal** (800 medições por segundo), em 24 canais.

Os sensores são MEMS acoplados em DC, então a **gravidade aparece na média** (≈ −0,92 g em Y). Isso serve de
referência de calibração. No lado esquerdo, os sensores estão montados espelhados: X e Z têm sinal invertido.
""")
code(r"""
rec = pv.load_pulse_xml(XML_PATH)
print(rec.summary())
raw = pd.DataFrame({f"{n}-{ax}": rec.sensors[n][:, i] for n in rec.names for i, ax in enumerate("XYZ")})
display(raw.describe().T[["mean", "std", "min", "max"]].round(3))
""")
code(r"""
t = rec.time(); sl = slice(800, 1200)        # 0,5 s
fig, ax = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
for i, a in enumerate("XYZ"):
    ax[i].plot(t[sl], rec.sensors["R1"][sl, i], color=pl.C_R, lw=1, label="R1")
    ax[i].plot(t[sl], rec.sensors["L1"][sl, i], color=pl.C_L, lw=1, label="L1")
    ax[i].set_ylabel(f"{a} (g)")
ax[0].legend(ncol=2); ax[-1].set_xlabel("tempo (s)")
ax[0].set_title("Sinais brutos (0,5 s) — note o X de L com sinal invertido e a gravidade em Y", loc="left")
show(fig)
""")

md(r"""
## 2. Modelo físico

O excitador de massas desbalanceadas impõe uma força harmônica na rotação $f$. Em cada ponto e eixo, a aceleração
é dominada pela componente 1×:

$$a_i(t) \approx G_i\,g_0\cos(\omega t - \phi_i),\qquad \omega = 2\pi f$$

* **G-Force** do eixo $i$: amplitude $G_i$ (g de pico) da componente 1×.
* **Curso (stroke)**: deslocamento pico-a-pico, $\;s_i = \dfrac{2\,G_i\,g_0}{\omega^2}$.
* **Órbita X–Y**: elipse $x=G_x\cos\theta,\ y=G_y\cos(\theta-\varphi)$, com $\varphi$ = atraso de Y em relação a X.
  O semi-eixo maior é o **Main G** e sua inclinação é o **Force Angle** $\alpha$:

$$a^2=\tfrac{G_x^2+G_y^2}{2}+\tfrac12\sqrt{(G_x^2+G_y^2)^2-4G_x^2G_y^2\sin^2\varphi},\qquad
\tan 2\alpha=\frac{2G_xG_y\cos\varphi}{G_x^2-G_y^2}$$

* **Regime supercrítico:** muito acima da frequência natural da suspensão, a amplitude de deslocamento tende a
  $m e / M$ (independe da rotação) e a aceleração cresce com $f^2$. Isso permite comparar gravações feitas em
  rotações diferentes.

Teste rápido das fórmulas com os números impressos no relatório Pulse (sensor L4: X = 1,99 g, Y = 2,80 g,
fase 34,9° → o relatório diz Main G 3,29 g e ângulo 56,4°):
""")
code(r"""
el = pv.ellipse_from_amplitudes(1.99, 2.80, 34.9)
print(f"Main G = {el['main']:.3f} g   |  Force angle = {el['angle']:.2f}°   |  stroke = {pv.stroke_mm(el['main'], 11.90):.2f} mm")
""")

md(r"""
## 3. Rastreamento de ordem

A rotação **não é constante** ao longo dos 10 s (alimentação de material, escorregamento do motor). Para 122 ciclos,
uma deriva de 0,1 Hz acumula dezenas de graus de fase. Um ajuste senoidal com frequência fixa "borra" o fasor e
subestima o fundamental.

Solução: estimar a **fase de rotação instantânea** $\theta(t)$ de cada sensor (passa-banda → direção principal →
Hilbert → frequência instantânea suavizada → integração) e calcular os fasores no domínio angular:

$$P_n = \frac{2}{N}\sum_k x(t_k)\,e^{-j n\theta(t_k)}\quad\Rightarrow\quad x(t)\approx\mathrm{Re}\{P_n e^{jn\theta(t)}\}$$

Referências: Boashash (1992), *Proc. IEEE* 80(4); Fyfe & Munck (1997), *MSSP* 11(2).
""")
code(r"""
an = pv.analyze(rec)
print({k: round(v, 3) for k, v in an.speed.items() if not k.startswith("profile")})
show(pl.fig_speed(an))
fig, comp = pl.fig_method(an); show(fig)
""")

md(r"""
## 4. Resultados por sensor, órbitas e corpo rígido

* **Sincronização:** os sensores Wi-Fi não compartilham relógio (veja as defasagens de R2/R3 acima). Por isso,
  como no Pulse, as fases de todos os sensores são referidas ao **eixo X** de cada um.
* **Corpo central** (centro de gravidade): média dos fasores dos 4 cantos (L1, R1, L4, R4).
* **G-Force Z (definição Pulse):** amplitude do **maior pico do espectro**, em qualquer frequência (não o 1×).
* **Desvios:** combinações de corpo rígido dos 4 cantos divididas por $|\Sigma Y|$:
  *Pitch* $|(Y_{L1}+Y_{R1})-(Y_{L4}+Y_{R4})|$, *Roll* $|(Y_{L1}+Y_{L4})-(Y_{R1}+Y_{R4})|$,
  *Twist* $|(Y_{L1}+Y_{R4})-(Y_{R1}+Y_{L4})|$ (confirmadas); *Yaw* $|(Z_{L1}+Z_{R1})-(Z_{L4}+Z_{R4})|$ e
  *Z* $|\Sigma Z|$ (compatíveis com o relatório Pulse).
""")
code(r"""
display(an.table().round(3))
""")
code(r"""
show(pl.fig_orbit_summary(an))
""")
code(r"""
REF = pv.load_reference(REF_PATH) if REF_PATH else None
c = an.center
print(f"Centro: Main {c['main_g']:.3f} g | stroke {c['stroke_main']:.2f} mm | ângulo {c['angle']:.2f}° | fase {c['phase']:.2f}°")
print("Desvios (%):", {k: round(v, 2) for k, v in an.deviations.items()})
if an.deviations_alt:
    print("Sem o canal defeituoso:", {k: round(v, 2) for k, v in an.deviations_alt.items()})
print(f"K_v = {an.throw['kv_horizontal_ref']:.2f} (ângulo vs horizontal) | {an.throw['kv_deck_ref']:.2f} (vs deck)")
show(pl.fig_phase_report(an, REF))
""")

md(r"""
## 5. (Opcional) Validação contra um relatório Pulse

**5.1 Consistência interna:** os números do relatório (G-Force, fases) passam pelas fórmulas e são comparados com os
demais números do próprio relatório. Diferenças apenas de arredondamento confirmam a modelagem.

**5.2 Dados brutos × relatório:** se o relatório for de outra gravação (outra rotação), strokes, ângulos, fases e
desvios são comparados diretamente e as acelerações são corrigidas por $(f_{ref}/f_{xml})^2$. Sem JSON, esta seção é
pulada.
""")
code(r"""
if REF:
    cons = pv.reference_consistency(REF)
    display(cons.round(3))
    print("Maior |diferença| em Main G:", cons[cons.Item.str.contains("Main G")]["Diferença"].abs().max().round(4))
""")
code(r"""
if REF:
    cmp = pv.compare_with_reference(an, REF)
    print(f"f_xml = {cmp.attrs['f_xml']:.3f} Hz | f_ref = {cmp.attrs['f_ref']:.2f} Hz | fator G = {cmp.attrs['scale']:.4f}")
    display(cmp.round(3))
    show(pl.fig_validation(cmp, an))
""")

md(r"""
## 6. Diagnóstico

Verificações automáticas: canal travado/fora de faixa, calibração estática (|g| = 1), montagem (inclinação estática),
impactos (kurtosis), estabilidade de rotação e sincronismo.

O **espectro de ordens** revela componentes em **0,5× e 1,5×** (excitação de período 2). Para um leito plástico, o
tempo de voo é igual a um período quando $K_v=\sqrt{1+\pi^2}\approx 3{,}30$. Acima disso o material pousa em ciclos
alternados. A folga mecânica é a hipótese alternativa; uma gravação **sem carga** decide.
""")
code(r"""
for f in an.findings:
    print(f, "\n")
show(pl.fig_integrity(an))
show(pl.fig_order_spectrum(an))
show(pl.fig_z_spectra(an))
""")
code(r"""
# relatório de um sensor (troque o nome para ver outro)
show(pl.fig_sensor_report(an, "R1"))
""")

md("## 7. Relatório PDF e planilha Excel")
code(r"""
from pulseva.report_pdf import build_report
from pulseva.export import to_excel
out = pathlib.Path("saida"); out.mkdir(exist_ok=True)
pdf = build_report(an, out / "Relatorio_Tecnico_Peneira.pdf", ref=REF, figdir=out / "figuras")
xls = to_excel(an, out / "Resultados_Peneira.xlsx", ref=REF)
print(pdf, xls, sep="\n")
if IN_COLAB:
    from google.colab import files
    files.download(str(pdf)); files.download(str(xls))
""")

md(r"""
## Referências
* Boashash, B. (1992). Estimating and interpreting the instantaneous frequency of a signal. *Proc. IEEE*, 80(4), 520–538.
* Fyfe, K. R.; Munck, E. D. S. (1997). Analysis of computed order tracking. *MSSP*, 11(2), 187–205.
* Randall, R. B. (2011). *Vibration-based Condition Monitoring*. Wiley.
* Brandt, A. (2011). *Noise and Vibration Analysis*. Wiley.
* Schmidt, P.; Körber, R.; Coppers, M. (2003). *Sieben und Siebmaschinen*. Wiley-VCH.
* Rao, S. S. (2017). *Mechanical Vibrations*, 6ª ed. Pearson.
* Haver & Boecker. *PULSE Vibrationsanalyse* (folheto técnico).
""")

nb["cells"] = C
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}, "colab": {"provenance": []}}
out = ROOT / "notebooks" / "Analise_Vibracional_Peneira.ipynb"
nbf.write(nb, out)
print("notebook:", out)
