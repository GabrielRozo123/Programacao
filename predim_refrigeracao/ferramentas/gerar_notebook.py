"""Gera o notebook do Google Colab a partir do código-fonte do pacote ``predimref``.

O notebook é autocontido: cada módulo do pacote vira uma célula ``%%writefile``, então ele roda
no Colab sem clonar o repositório. O código-fonte em ``predimref/`` continua sendo a única fonte
da verdade — depois de alterar o pacote, rode:

    python ferramentas/gerar_notebook.py
"""
from __future__ import annotations

import json
import os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAIDA = os.path.join(RAIZ, "PreDimensionamento_Refrigeracao_Colab.ipynb")

MODULOS = [
    "predimref/constantes.py", "predimref/avisos.py", "predimref/propriedades.py",
    "predimref/correlacoes/__init__.py", "predimref/correlacoes/monofasico.py",
    "predimref/correlacoes/bifasico.py", "predimref/correlacoes/lado_ar.py",
    "predimref/gabinete.py", "predimref/ciclo.py", "predimref/compressor.py",
    "predimref/trocador.py", "predimref/capilar.py", "predimref/carga_fluido.py",
    "predimref/projeto.py", "predimref/relatorio.py", "predimref/graficos.py", "predimref/__init__.py",
]


def md(texto: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": texto.strip("\n").splitlines(keepends=True)}


def code(texto: str, titulo_oculto: bool = False) -> dict:
    meta = {"cellView": "form"} if titulo_oculto else {}
    return {"cell_type": "code", "execution_count": None, "metadata": meta, "outputs": [],
            "source": texto.strip("\n").splitlines(keepends=True)}


INTRO = r"""
# ❄️ Pré-dimensionamento de ciclos de refrigeração para visi-coolers

**CAExperts × IMBERA** — rotina de pré-dimensionamento termodinâmico de refrigeradores comerciais de
bebidas (porta de vidro), cujas saídas alimentam o modelo de sistema no **Simcenter Amesim**.

| Entradas do usuário | Saídas (entradas do Amesim) |
|---|---|
| COP desejado (capacidade / potência elétrica do compressor) | potência elétrica e deslocamento do compressor, η_v, η_is |
| Capacidade: litros **ou** nº de garrafas de 600 mL | condensador e evaporador: área, comprimento de tubo, diâmetros, fileiras, tubos, face, vazão de ar |
| Temperatura ambiente T∞ | tubo capilar: diâmetro interno e comprimento |
| Temperatura alvo interna (ex.: 2,5 °C) | carga de refrigerante, estados do ciclo, balanços de energia e exergia |
| Eficácia ε do condensador e do evaporador (padrão 0,65) | velocidade de face e nº de fileiras que atendem ε, UA, NTU |

**Papel da rotina:** é o *step-down* do modelo do Amesim. Gera parâmetros físicos e coerentes entre si para montar
o modelo de sistema; as curvas de pull-down, consumo, fuga térmica e água drenada saem depois do próprio Amesim.

**Fluxo de cálculo:** capacidade do gabinete → carga térmica → ciclo (equação de estado de referência via
CoolProp) → verificação do COP contra Carnot e contra o compressor real → compressor → trocadores tubo-aleta
dimensionados **segmento a segmento** (ε-NTU local, correlações locais, queda de pressão acoplada ao ciclo) →
capilar pelo **modelo homogêneo com blocagem crítica** → carga de fluido → exergia → avisos de projeto.

> **Natureza do resultado.** É um *pré-dimensionamento*: as correlações empíricas têm incerteza típica de
> ±15–30 % no coeficiente local e as premissas de uso (aberturas de porta, reposição de produto) dominam a
> carga térmica. O notebook mostra essa incerteza (seção 7); a conferência em regime permanente é feita contra o
> modelo do Amesim (bloco `amesim.alvo_validacao`, seção 6).

**Como usar:** `Ambiente de execução → Executar tudo`. Altere as entradas na seção 3 e rode de novo da seção 4
em diante. Para premissas avançadas (geometria dos trocadores, fluido, perfil de uso), edite a célula
*Parâmetros avançados*.

**Índice:** 0. Ambiente · 1. Código do pacote · 2. Fundamentação teórica · 3. Entradas · 4. Dimensionamento ·
5. Gráficos · 6. Saídas para o Amesim · 7. Sensibilidade e incerteza · 8. Verificação e validação ·
9. Hipóteses e limitações
"""

AMBIENTE = r"""
#@title 0. Ambiente: CoolProp e estrutura do pacote `predimref`
import os, subprocess, sys
try:
    import CoolProp
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "CoolProp"], check=True)
    import CoolProp
os.makedirs("predimref/correlacoes", exist_ok=True)
print("CoolProp", CoolProp.__version__)
"""

SECAO_CODIGO = r"""
## 1. Código-fonte do pacote `predimref`

As células abaixo gravam os módulos do pacote no disco do Colab (`%%writefile`). Não é preciso lê-las para
usar a ferramenta — podem ficar recolhidas. Cada módulo traz no cabeçalho as equações e as referências usadas.

| Módulo | Conteúdo |
|---|---|
| `propriedades` | refrigerante (CoolProp/HEOS), saturação com cache, ar seco e psicrometria (ASHRAE RP-1485) |
| `correlacoes.monofasico` | Churchill (atrito), Gnielinski (Nusselt) |
| `correlacoes.bifasico` | Shah 2013/2022, Chato 1962 (condensação); Gungor-Winterton 1987, Liu-Winterton 1991 (ebulição); Müller-Steinhagen & Heck; Rouhani-Axelsson |
| `correlacoes.lado_ar` | Wang, Chi & Chang 2000 (j, f), eficiência de aleta de Schmidt, ΔP de Kays & London |
| `gabinete` | litros ↔ garrafas, transmissão com fatores de forma, porta, gaxeta, infiltração, produto |
| `ciclo` / `compressor` | estados, COP × Carnot, rendimentos, exergia; deslocamento e ponto de catálogo |
| `trocador` | condensador e evaporador por zonas e segmentos |
| `capilar` | modelo homogêneo, flash isentálpico, blocagem, problema inverso, seleção de diâmetro |
| `projeto` / `relatorio` / `graficos` | orquestração iterativa, JSON para o Amesim, figuras |
"""

TEORIA = r"""
## 2. Fundamentação teórica

### 2.1 Capacidade: litros ↔ garrafas
A conversão "200 L ↔ 333 garrafas" (200 / 0,6) dá o **volume de líquido**, não o volume de gabinete. Cada garrafa
ocupa o envelope $D^2H$ (≈ 1,01 L para 65 × 239 mm) e só uma fração $\phi$ do volume interno é aproveitável
(prateleiras, folgas de circulação de ar, caixa do evaporador). Com $\phi = 0{,}55$:
$$n_{garrafas} = \left\lfloor \frac{\phi\,V_{int}}{D^2 H}\right\rfloor \qquad (200\ \text{L} \Rightarrow 108\ \text{garrafas};\ 333\ \text{garrafas} \Rightarrow 611\ \text{L})$$
A rotina avisa quando as garrafas informadas não cabem no volume ($\phi > 0{,}70$).

### 2.2 Carga térmica
**Transmissão** por face isolada $i$ (resistências em série, fatores de forma de condução de Incropera, Tab. 4.1):
$$Q_i = \frac{f_{pt}\,\Delta T_i}{\dfrac{1}{h_{int}A_{int,i}} + \dfrac{1}{k\,S_i} + \dfrac{1}{h_{ext}A_{ext,i}}},\qquad
S_i = \frac{A_{int,i}}{\delta_i} + \sum_{arestas}\tfrac12\,0{,}54\,L_a + \sum_{cantos}\tfrac13\,0{,}15\,\delta$$
com fator de pontes térmicas $f_{pt}$ e $\Delta T$ maior na base (compartimento do compressor). **Porta de vidro**:
$Q = U_p A_p \Delta T$. **Gaxeta**: $Q = \psi\,P_{porta}\,\Delta T$ (literatura: ψ ≈ 0,05–0,2 W/m·K).

**Infiltração** por abertura de porta — Gosney & Olama (1975), adotada pela ASHRAE:
$$\dot V = 0{,}221\,A\sqrt{gH}\sqrt{1-\frac{\rho_e}{\rho_i}}\,F_m,\qquad F_m=\left[\frac{2}{1+(\rho_i/\rho_e)^{1/3}}\right]^{1{,}5}$$
O fluxo estabelecido de Gosney-Olama trocaria ~6× o ar de um visi-cooler numa abertura de 8 s, o que é
fisicamente impossível. Por isso a massa trocada por abertura é
$m = \min\left(\rho_i \dot V D_f t_{ab},\; n_{ren}\,V_{livre}/v_e\right)$, e a carga é $m\,(h_e-h_i)$ com entalpias
de ar úmido (sensível + latente).

**Produto:** $c_p$ da bebida por Choi & Okos (1986) (água + carboidrato), integrado entre a temperatura de entrada
e a alvo. **Casos de projeto:**
$$Q_{proj} = (1+m_s)\,\max\!\left(\frac{Q_{regime}}{f_{util}},\;Q_{transm}+Q_{int}+\frac{E_{carga\ cheia}}{t_{pull\text{-}down}}\right)$$

### 2.3 Ciclo termodinâmico
Temperaturas: $T_{evap} = T_{ar,evap} - \Delta T_{evap}$, $T_{cond} = T_{ar,cond} + \Delta T_{cond}$, superaquecimento
na saída do evaporador, sub-resfriamento na saída do condensador e trocador interno opcional. Todas as
propriedades vêm de equações de estado de referência (Helmholtz) via CoolProp.

**Verificação do COP pedido** (o ponto que protege a CAExperts de vender o impossível):
$$COP < COP_{Carnot} = \frac{T_{evap}}{T_{cond}-T_{evap}},\qquad COP < COP_{ideal} = \frac{h_1-h_4}{h_{2s}-h_{1s}}$$
$$\eta_{global} = \frac{COP}{COP_{ideal}} = \frac{\dot m(h_{2s}-h_{1s})}{\dot W_{el}},\quad \eta_{is}=\frac{\eta_{global}}{\eta_{em}},\quad
h_2 = h_{1s}+\frac{h_{2s}-h_{1s}}{\eta_{is}},\quad \dot Q_{carc} = \dot W_{el} - \dot m(h_2-h_{1s})\ge 0$$
Compressores herméticos alternativos pequenos têm $\eta_{global}$ ≈ 0,35–0,70. Fora disso a rotina avisa; acima do ciclo
ideal ela recusa e informa quais $\Delta T$ dos trocadores seriam necessários. Fechamento:
$\dot Q_{evap}+\dot W_{el} = \dot Q_{cond}+\dot Q_{carc}$.

**Exergia** (estado morto = ambiente): $\dot W_{el} = \dot Q_{evap}\left(\frac{T_0}{T_{frio}}-1\right) + \sum T_0\dot S_{ger}$,
com $\dot S_{ger}$ por componente; $\eta_{II} = COP/COP_{Carnot}(T_{frio},T_0)$.

### 2.4 Compressor
$$\eta_v = f_v\left[1 + C - C\,(P_{desc}/P_{suc})^{1/n}\right],\qquad V_{desl} = \frac{\dot m}{\rho_{suc}\,\eta_v\,N}$$
(motor de 2 polos em 60 Hz, N ≈ 3500 rpm). O mesmo compressor é reavaliado na condição de catálogo
(EN 12900 MBP −10/45 °C, retorno 20 °C) para facilitar a seleção comercial.

### 2.5 Trocadores tubo-aleta (condensador e evaporador)
O circuito é dividido em zonas (dessuperaquecimento / condensação / sub-resfriamento; evaporação /
superaquecimento) e cada zona em segmentos. Em cada segmento:
$$\frac{1}{UA'} = \frac{1}{\xi\,h_o\,\eta_o A_o'} + \frac{R_{f,o}}{A_o'} + \frac{\ln(D_o/D_i)}{2\pi k_t} + \frac{1}{h_i A_i'} + \frac{R_{f,i}}{A_i'},\qquad
\dot C'_{ar} = \frac{\xi\,\rho V_{face} P_t c_p}{N_{fileiras}}$$
* **Bifásico** ($C_r=0$): $\varepsilon = 1-e^{-UA'/\dot C'_{ar}}$ e $L = \dot Q/(\varepsilon\,\dot C'_{ar}\,\Delta T)$.
* **Monofásico**: ε de escoamento cruzado (refrigerante misturado, ar não misturado), $L$ obtido por raiz.
* **Lado do ar**: Wang, Chi & Chang (2000) para $j$ e $f$; $h_o = j\,G_{max}c_p\,Pr^{-2/3}$; aleta de Schmidt (1949),
  a mesma usada na redução dos dados de Wang. ΔP do ar por Kays & London.
* **Condensação**: Shah (2022), que para hidrocarbonetos usa a forma de Shah (2013) com os regimes I, II e III
  (estratificado, $h=h_{Nu}$). Os fluxos mássicos destes sistemas são muito baixos (G ≈ 10–40 kg/m²s).
* **Ebulição**: Gungor & Winterton (1987) com correção de estratificação (Fr < 0,05) e secagem acima de $x_{di}$.
* **Queda de pressão**: Müller-Steinhagen & Heck (atrito) + aceleração com fração de vazio de Rouhani-Axelsson;
  a pressão é atualizada ao longo do tubo e realimenta o ciclo até convergir.
* **Desumidificação** (evaporador): fator de umidade $\xi = Q_{total}/Q_{sens}$ (analogia de Lewis, Threlkeld).

**Eficácia como entrada (padrão 0,65).** A eficácia é a do lado do ar referida à saturação — a definição usual para
condensadores e evaporadores, em que o refrigerante bifásico tem $C\to\infty$ e $C_{min}=\dot C_{ar}$:
$$\varepsilon = \frac{T_{ar,s}-T_{ar,e}}{T_{sat}-T_{ar,e}} = \frac{Q_{sens}}{\dot C_{ar}\,(T_{sat}-T_{ar,e})}
\quad\Rightarrow\quad \dot C_{ar} = \frac{Q/\xi}{\varepsilon\,\Delta T_{aprox}}$$
Com $Q$ e $\Delta T_{aprox}$ fixados pelo ciclo, ε define a **vazão de ar**; a geometria precisa então entregar o NTU
correspondente. Na zona bifásica $\varepsilon_{zona} \le 1-e^{-NTU_{zona}}$ (igualdade com coeficiente uniforme); no
**condensador** a ε global referida a $T_{sat}$ inclui o ar aquecido no dessuperaquecimento (acima de $T_{sat}$) e
**não** segue $1-e^{-NTU}$ — por isso os valores por zona (UA, NTU, ε) também são exportados.
Na distribuição paralela de ar, ε independe do comprimento; depende da velocidade de face $V$, do nº de fileiras $N$,
do coeficiente interno e, no condensador, da temperatura de descarga. Para cada $N$ a busca de $V$ percorre uma grade
de $V_{max}$ para $V_{min}$ e refina por Brent a primeira troca de sinal (a raiz de maior $V$: menos tubo e menos perda de
carga — com perda de carga relevante ε(V) pode não ser monotônica); escolhe-se o $N\le 6$ (faixa de Wang) cuja $V$ fica
mais perto da velocidade preferida. O comprimento sai da marcha segmentada nessa $(V,N)$. Pontos com pinch (a perda de
carga levando a saturação para o lado errado do ar) ou queda de pressão excessiva são rejeitados.

**Duas serpentinas.** A *de projeto* (sem margem) com a vazão de ar requerida entrega exatamente $Q$, $T_{cond}$ e
$T_{evap}$ do ciclo — é a que reproduz `amesim.alvo_validacao`. A *construtiva* tem a margem de área (padrão 10 %), o
mesmo nº de fileiras e de tubos por fileira e o comprimento do passe ajustado; na mesma velocidade de face tem a mesma ε,
mas 10 % mais vazão de ar e UA — num modelo de sistema ela condensa abaixo de $T_{cond}$ e evapora acima de $T_{evap}$
(é a folga, não um erro).
Também se reporta a eficácia estrita $Q/Q_{max}$ com o $Q_{max}$ termodinâmico, caso o componente do Amesim use essa
definição. ε **não** altera o ciclo (as temperaturas de evaporação e condensação vêm de $\Delta T_{evap}$ e $\Delta T_{cond}$):
ela troca vazão de ar (ventilador) por área (trocador).

### 2.6 Tubo capilar — modelo homogêneo de equilíbrio (HEM)
$$G=\dot m/A,\qquad h+\tfrac12 G^2v^2 = h_0,\qquad -dP = \frac{f\,G^2 v}{2D}\,dL + G^2\,dv$$
O líquido escoa isentalpicamente até o ponto de flash $h_l(P_{flash})+\tfrac12G^2v_l^2=h_0$ (para o propano a ~40 °C,
$T\beta>1$ e o flash ocorre **abaixo** de $P_{sat}(T_{in})$). Na região bifásica, o título sai da equação da energia
(quadrática em $x$) e $dL$ da quantidade de movimento. Há **blocagem** quando $-dv/dP \ge 1/G^2$ (máximo de
entropia na linha de Fanno) antes de atingir a pressão do evaporador. Viscosidade bifásica de McAdams
(Cicchitti e Dukler na análise de incerteza); atrito de Churchill. Validado com os dados de Li et al. (1990):
erro de vazão de −1 % a −3 %.

### 2.7 Carga de refrigerante
$m = \sum \rho_{in\,situ} V$, com $\rho_{in\,situ} = \alpha\rho_v + (1-\alpha)\rho_l$ e α de Rouhani-Axelsson nos trechos bifásicos,
mais linhas, filtro, gás na carcaça e refrigerante dissolvido no óleo. Comparada com 150 g, 8×LFL e 13×LFL
(IEC 60335-2-89; confirmar a edição e a regulamentação local).

### 2.8 Referências principais
* ASHRAE Handbook — Refrigeration (caps. *Refrigeration Load*, *Thermal Properties of Foods*, *Refrigerant-Control Devices*).
* Bell, I.H. et al. (2014). Pure and pseudo-pure fluid thermophysical property evaluation… CoolProp. *Ind. Eng. Chem. Res.* 53:2498.
* Choi, Y., Okos, M.R. (1986). Effects of temperature and composition on the thermal properties of foods.
* Chato, J.C. (1962). Laminar condensation inside horizontal and inclined tubes. *ASHRAE J.* 4:52.
* Churchill, S.W. (1977). Friction-factor equation spans all fluid-flow regimes. *Chem. Eng.* 84(24):91.
* Gnielinski, V. (1976). *Int. Chem. Eng.* 16:359; VDI Heat Atlas (2010), G1.
* Gosney, W.B., Olama, H.A.L. (1975). Heat and enthalpy gains through cold room doorways. *Proc. Inst. Refrig.* 72:31.
* Gungor, K.E., Winterton, R.H.S. (1987). *Chem. Eng. Res. Des.* 65:148.
* Incropera, F.P. et al. *Fundamentals of Heat and Mass Transfer* (fatores de forma, ε-NTU, aletas).
* Kays, W.M., London, A.L. (1984). *Compact Heat Exchangers*, 3ª ed.
* Li, R.Y., Lin, S., Chen, Z.H. (1990). *Int. J. Refrig.* 13:181; *ASHRAE Trans.* 96:542.
* Liu, Z., Winterton, R.H.S. (1991). *Int. J. Heat Mass Transfer* 34:2759.
* Müller-Steinhagen, H., Heck, K. (1986). *Chem. Eng. Process.* 20:297.
* Rouhani, Z., Axelsson, E. (1970). *Int. J. Heat Mass Transfer* 13:383; Steiner (1993), VDI Heat Atlas.
* Schmidt, T.E. (1949). Heat transfer calculations for extended surfaces. *Refrig. Eng.* 57:351.
* Shah, M.M. (2009) *HVAC&R Res.* 15:889; (2013) *ASHRAE Trans.* 119(2); (2022) *Int. J. Heat Mass Transfer* 194:123069.
* Stoecker, W.F., Jones, J.W. (1982). *Refrigeration and Air Conditioning*, 2ª ed.
* Wang, C.C., Chi, K.Y., Chang, C.J. (2000). *Int. J. Heat Mass Transfer* 43:2693.
* Wongwises, S. et al. (2002). Pressure distribution of refrigerant flow in an adiabatic capillary tube. *ScienceAsia* 28:71.
"""

ENTRADAS = r"""
#@title 3. Entradas do cliente { run: "auto" }
COP = 2.0  #@param {type:"number"}
informar_COP = True  #@param {type:"boolean"}
T_ambiente_C = 32.0  #@param {type:"number"}
T_alvo_C = 2.5  #@param {type:"number"}
tipo_capacidade = "litros"  #@param ["litros", "garrafas de 600 mL"]
capacidade = 200  #@param {type:"number"}
UR_ambiente = 0.60  #@param {type:"slider", min:0.2, max:0.95, step:0.05}
fluido = "R290"  #@param ["R290", "R600a", "R1270", "R134a", "R1234yf", "R152a", "R404A", "R507A"]
#@markdown **Eficácia dos trocadores** — ε = (T_ar,saída − T_ar,entrada)/(T_sat − T_ar,entrada); desmarque para usar velocidade de face fixa
usar_eficacia = True  #@param {type:"boolean"}
eficacia_condensador = 0.65  #@param {type:"slider", min:0.30, max:0.90, step:0.01}
eficacia_evaporador = 0.65  #@param {type:"slider", min:0.30, max:0.90, step:0.01}

from predimref import EntradasProjeto
entradas = EntradasProjeto(
    COP=COP if informar_COP else None,
    T_ambiente_C=T_ambiente_C, T_alvo_C=T_alvo_C, UR_ambiente=UR_ambiente, fluido=fluido,
    volume_interno_L=capacidade if tipo_capacidade == "litros" else None,
    n_garrafas=int(capacidade) if tipo_capacidade != "litros" else None,
    eficacia_condensador=eficacia_condensador if usar_eficacia else None,
    eficacia_evaporador=eficacia_evaporador if usar_eficacia else None,
)
entradas
"""

AVANCADOS = r"""
#@title Parâmetros avançados (premissas de projeto) — edite se necessário
from predimref import ParametrosProjeto
from predimref.gabinete import Garrafa, Gabinete, Uso
from predimref.ciclo import ParametrosCiclo
from predimref.compressor import ParametrosCompressor
from predimref.capilar import ParametrosCapilar
from predimref.trocador import condensador_padrao, evaporador_padrao

params = ParametrosProjeto(
    garrafa=Garrafa(diametro_m=0.065, altura_m=0.239, acucar_g_por_L=106.0),
    gabinete=Gabinete(fator_ocupacao=0.55, k_isolamento=0.022, esp_lateral_m=0.050, U_porta=2.0,
                      psi_gaxeta=0.10, fator_pontes_termicas=1.10),
    uso=Uso(aberturas_por_dia=100, tempo_abertura_s=8, UR_interna=0.75, tempo_pulldown_h=24,
            fracao_reposicao_diaria=0.5, potencia_iluminacao_W=10, potencia_ventilador_evap_W=8,
            fator_utilizacao_max=0.70, margem_seguranca=0.10),
    ciclo=ParametrosCiclo(dT_evap=10.0, dT_cond=13.0, superaquecimento=5.0, subresfriamento=3.0,
                          eficacia_ihx=0.0, eta_eletromecanica=0.72),
    compressor=ParametrosCompressor(rotacao_rpm=3500, condicao_catalogo="EN12900_MBP"),
    condensador=condensador_padrao(),   # tubo 3/8", aleta 2,5 mm (10 FPI), V preferida 2 m/s
    evaporador=evaporador_padrao(),     # tubo 3/8", aleta 4,23 mm (6 FPI), V preferida 1,5 m/s
    capilar=ParametrosCapilar(serie="polegada", L_min=1.0, L_max=5.0, L_alvo=2.5),
)
# Exemplos de ajuste:
# params.condensador.velocidade_face = 1.5          # velocidade preferida (com ε, guia a escolha de fileiras)
# params.condensador.fileiras_automaticas = False   # com ε, fixa o nº de fileiras e resolve só a velocidade
# params.condensador.geometria.n_fileiras = 4
# params.condensador.comprimento_passe_m = 0.25
# params.evaporador.geometria.passo_aleta = 5.0e-3
# params.evaporador.n_circuitos = 2
print("parâmetros prontos")
"""

RODAR = r"""
#@title 4. Dimensionamento
from predimref import dimensionar, ErroProjeto
try:
    res = dimensionar(entradas, params)
    print(res.resumo())
except ErroProjeto as erro:
    res = None
    print("ENTRADA INVIÁVEL:\n", erro)
"""

GRAFICOS = r"""
#@title 5. Gráficos do ciclo, trocadores, capilar, carga e exergia
import matplotlib.pyplot as plt
from IPython.display import display
from predimref.graficos import painel
if res is not None:
    for nome, fig in painel(res).items():
        display(fig)
        plt.close(fig)
"""

ALTERNATIVAS = r"""
#@title Alternativas de geometria para a eficácia escolhida (nº de fileiras × velocidade de face)
import pandas as pd
from predimref.projeto import alternativas_fileiras
if res is not None and entradas.eficacia_condensador is not None:
    for tipo in ("condensador", "evaporador"):
        tab = pd.DataFrame(alternativas_fileiras(res, tipo, range(1, 9)))
        print(f"\n{tipo.upper()} — ε = {getattr(res, tipo).eficacia_alvo:.2f}; escolhido: {getattr(res, tipo).n_fileiras} fileiras"
              " (acima de 6 fileiras a correlação de Wang é extrapolada)")
        display(tab.round(3))
"""

MAPA = r"""
#@title COP alcançável em função da temperatura ambiente
import numpy as np
from predimref.graficos import mapa_cop
fig = mapa_cop(entradas.fluido, entradas.T_alvo_C, np.arange(20.0, 44.0, 1.0), params.ciclo,
               cop_pedido=entradas.COP)
display(fig)
plt.close(fig)
"""

AMESIM_MD = r"""
## 6. Saídas para o Amesim

`res.para_dict()` devolve todos os resultados em um dicionário JSON-serializável. O bloco **`amesim`** reúne,
em SI e por componente, os parâmetros de entrada típicos de um modelo de sistema (compressor volumétrico,
trocadores tubo-aleta, capilar, condições iniciais) e os valores-alvo para conferir o modelo do Amesim em regime
permanente. O mapeamento para os nomes dos parâmetros de cada submodelo do Amesim fica com a equipe de
integração (Diego e Pedro).

Na integração em Python (fora do notebook):
```python
from predimref import EntradasProjeto, dimensionar
res = dimensionar(EntradasProjeto(COP=2.0, T_ambiente_C=32, T_alvo_C=2.5, volume_interno_L=200))
parametros_amesim = res.para_dict()["amesim"]
```
O núcleo de cálculo depende só de `numpy`, `scipy` e `CoolProp` (matplotlib apenas para gráficos).
"""

EXPORTAR = r"""
#@title Exportar JSON / CSV / Excel e baixar
import csv, json
from predimref.relatorio import tabela_estados, perfil_trocador
if res is not None:
    d = res.para_dict()
    print(json.dumps(d["amesim"], indent=2, ensure_ascii=False))
    res.exportar_json("predim_resultado.json")
    with open("predim_estados.csv", "w", newline="", encoding="utf-8") as fh:
        linhas = tabela_estados(res)
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader(); w.writerows(linhas)
    arquivos = ["predim_resultado.json", "predim_estados.csv"]
    try:
        import pandas as pd
        with pd.ExcelWriter("predim_resultado.xlsx") as xl:
            pd.DataFrame(tabela_estados(res)).to_excel(xl, sheet_name="estados", index=False)
            pd.DataFrame(perfil_trocador(res.condensador)).to_excel(xl, sheet_name="condensador", index=False)
            pd.DataFrame(perfil_trocador(res.evaporador)).to_excel(xl, sheet_name="evaporador", index=False)
            pd.DataFrame([{"componente": k, "W": v} for k, v in res.carga.componentes.items()]).to_excel(
                xl, sheet_name="carga_termica", index=False)
        arquivos.append("predim_resultado.xlsx")
    except Exception as e:
        print("Excel não gerado:", e)
    try:
        from google.colab import files
        for a in arquivos:
            files.download(a)
    except ImportError:
        print("Arquivos gravados:", arquivos)
"""

SENS_MD = r"""
## 7. Sensibilidade e incerteza

Duas perguntas distintas:
1. **Sensibilidade às entradas/premissas** — como o projeto muda com a temperatura ambiente, o COP pedido e o
   perfil de uso (a carga térmica é, de longe, a maior fonte de incerteza);
2. **Incerteza de modelo** — o mesmo problema resolvido com correlações alternativas (o resumo da seção 4 já mostra
   evaporador GW1987 × LW1991, condensador Shah 2022 × Chato 1962 e capilar com três viscosidades).
"""

SENS = r"""
#@title Varredura de temperatura ambiente e de COP
import copy
import pandas as pd
from predimref import ParametrosProjeto
linhas = []
p_rapido = copy.deepcopy(params); p_rapido.analise_sensibilidade = False
for Ta in (25.0, 30.0, 32.0, 35.0, 38.0, 43.0):
    for cop in ((entradas.COP,) if entradas.COP else (None,)):
        e = copy.deepcopy(entradas); e.T_ambiente_C = Ta; e.COP = cop
        try:
            r = dimensionar(e, p_rapido)
            linhas.append({"T_amb [°C]": Ta, "Q_proj [W]": r.carga.Q_projeto, "W_el [W]": r.balanco.W_el,
                           "η_global": r.ciclo.eta_global, "desloc. [cm³]": r.compressor.deslocamento_cm3,
                           "L_cond [m]": r.condensador.L_requerido, "L_evap [m]": r.evaporador.L_requerido,
                           "capilar": f'{r.capilar.escolhido.D*1e3:.3f} mm × {r.capilar.escolhido.L:.2f} m',
                           "carga [g]": r.carga_refrigerante["total_kg"] * 1e3, "kWh/dia": r.energia["total_kWh_dia"]})
        except ErroProjeto as err:
            linhas.append({"T_amb [°C]": Ta, "Q_proj [W]": None, "capilar": "inviável: " + str(err)[:60]})
pd.set_option("display.precision", 2)
pd.DataFrame(linhas)
"""

SENS_EPS = r"""
#@title Efeito da eficácia escolhida (mesma eficácia nos dois trocadores)
linhas = []
for eps in (0.45, 0.55, 0.65, 0.75):
    e = copy.deepcopy(entradas); e.eficacia_condensador = e.eficacia_evaporador = eps
    try:
        r = dimensionar(e, p_rapido)
        linhas.append({"ε": eps,
                       "cond: fileiras × V [m/s]": f"{r.condensador.n_fileiras} × {r.condensador.velocidade_face:.2f}",
                       "cond: L [m]": r.condensador.L_requerido, "cond: ar [m³/h]": r.condensador.vazao_ar_requerida_m3h,
                       "evap: fileiras × V [m/s]": f"{r.evaporador.n_fileiras} × {r.evaporador.velocidade_face:.2f}",
                       "evap: L [m]": r.evaporador.L_requerido, "evap: ar [m³/h]": r.evaporador.vazao_ar_requerida_m3h,
                       "T ar insuflado [°C]": r.evaporador.T_ar_out - 273.15,
                       "carga R [g]": r.carga_refrigerante["total_kg"] * 1e3})
    except ErroProjeto as err:
        linhas.append({"ε": eps, "cond: fileiras × V [m/s]": "inviável: " + str(err)[:70]})
pd.DataFrame(linhas)
"""

SENS2 = r"""
#@title Efeito das premissas de uso (aberturas de porta e reposição de produto)
linhas = []
for ab in (25, 100, 300):
    for rep in (0.2, 0.5, 1.0):
        p2 = copy.deepcopy(p_rapido); p2.uso.aberturas_por_dia = ab; p2.uso.fracao_reposicao_diaria = rep
        try:
            r = dimensionar(entradas, p2)
            linhas.append({"aberturas/dia": ab, "reposição/dia": rep, "Q_proj [W]": r.carga.Q_projeto,
                           "caso": r.carga.caso_governante, "desloc. [cm³]": r.compressor.deslocamento_cm3,
                           "kWh/dia": r.energia["total_kWh_dia"]})
        except ErroProjeto as err:
            linhas.append({"aberturas/dia": ab, "reposição/dia": rep, "caso": "inviável"})
pd.DataFrame(linhas)
"""

VALID_MD = r"""
## 8. Verificação e validação

**Verificação** (o código resolve certo as equações): fechamento dos balanços de energia e de exergia, 2ª lei por
componente, independência de malha dos trocadores e do capilar, consistência do problema inverso do capilar,
eficiência de aleta de Schmidt contra a solução exata (Bessel), eficácia alvo atingida, limite ε ≤ 1 − e^(−NTU) no
evaporador só bifásico, coerência do bloco do Amesim (ε·Ċ_ar·ΔT = Q na serpentina de projeto) e casos-limite (título final
exato, pinch por perda de carga, alvo de ε acima/abaixo do atingível). O repositório tem testes automatizados
(`pytest`) com essas e outras verificações.

**Validação** (as equações certas): capilar contra os dados experimentais de Li et al. (1990). O próximo passo
recomendado é validar o sistema completo contra ensaios de um visi-cooler IMBERA existente (ver seção 9).
"""

VALID = r"""
#@title Verificações do caso atual e validação do capilar (Li et al., 1990 — R12, D = 0,66 mm, L = 1,5 m)
from predimref.propriedades import Fluido
from predimref.capilar import ParametrosCapilar, vazao_capilar
if res is not None:
    print(f"balanço de energia: erro relativo = {res.balanco.erro_balanco:.1e}")
    print(f"balanço de exergia: erro relativo = {res.exergia['erro_fechamento']:.1e}")
    print(f"2ª lei por componente: min(Ex_destruída) = {min(res.exergia['destruicao_W'].values()):.3f} W (≥ 0)")
    print(f"COP {res.ciclo.COP:.3f} < ciclo ideal {res.ciclo.COP_ciclo_ideal:.3f} < Carnot {res.ciclo.COP_carnot_ciclo:.3f}")
fl12 = Fluido("R12")
print("\nCapilar — vazão prevista × medida (Li et al. 1990):")
for Ti, Pi, m_exp in ((31.40, 9.67e5, 1.13e-3), (23.40, 7.17e5, 0.844e-3)):
    h = fl12.estado_PT(Pi, Ti + 273.15).h
    for visc in ("mcadams", "cicchitti", "dukler"):
        m = vazao_capilar(fl12, 0.66e-3, 1.5, Pi, h, 1.5e5, ParametrosCapilar(rugosidade_m=0.003 * 0.66e-3,
                                                                              modelo_viscosidade=visc))
        print(f"  T_in {Ti:5.1f} °C  {visc:9s}  medida {m_exp*1e3:.3f} g/s  HEM {m*1e3:.3f} g/s  ({m/m_exp-1:+.1%})")
"""

LIMITES = r"""
## 9. Hipóteses, limitações e próximos passos

**Hipóteses principais (todas editáveis em *Parâmetros avançados*):**
* regime permanente na condição de projeto; o compressor cicla em regime e opera 100 % no pull-down;
* trocadores tubo-aleta de aletas planas, tubos escalonados, ar com distribuição paralela por trecho;
  curvas de retorno fora da perda de carga; coeficientes de correlações para tubo liso e refrigerante sem óleo;
* capilar adiabático e sem metaestabilidade (com trocador interno, o capilar real é não adiabático);
* compressor: modelo de espaço morto para η_v e η_eletromecânica constante — substituir por mapa de catálogo
  (polinômio AHRI 540 / EN 12900) assim que o compressor candidato for escolhido;
* geada no evaporador tratada só por resistência de incrustação (padrão zero) e pelo fator de umidade.

**Relação com o Amesim (a rotina é o *step-down* do modelo de sistema):**
1. Esta rotina gera, em regime permanente, parâmetros coerentes entre si (balanços fechados, 2ª lei, COP viável)
   para montar o modelo do Amesim: compressor, trocadores com a eficácia escolhida, capilar e carga de fluido.
2. As curvas de **pull-down, consumo, fuga térmica e água drenada** vêm do Amesim. Primeiro passo de conferência:
   montado com as serpentinas `projeto_sem_margem` e a vazão de ar requerida, o modelo do Amesim deve reproduzir
   `amesim.alvo_validacao` (Q_evap, W_el, ṁ, T_evap, T_cond). Com as `construtiva_com_margem` (a geometria que se
   fabrica), T_cond fica abaixo e T_evap acima do alvo — é a folga de área, não um erro de mapeamento. Fora isso,
   diferenças grandes indicam parâmetro mapeado de forma diferente: definição de eficácia (aqui referida à saturação,
   de bulbo seco; a estrita Q/Q_max também é exportada), UA úmido × seco no evaporador (ambos exportados) e a carga
   (o bloco separa circuito, gás na carcaça e refrigerante dissolvido no óleo).
3. Quando o compressor for escolhido, troque o modelo genérico (espaço morto + η constante) pelo mapa de catálogo
   nos dois lados (aqui e no Amesim).
4. Se mais tarde houver ensaio de um produto IMBERA, ele calibra os dois modelos ao mesmo tempo (UA do gabinete,
   ΔT dos trocadores, rendimentos do compressor).
"""


def main():
    cells = [md(INTRO), code(AMBIENTE, True), md(SECAO_CODIGO)]
    for mod in MODULOS:
        with open(os.path.join(RAIZ, mod), encoding="utf-8") as fh:
            src = fh.read()
        cells.append(code(f"%%writefile {mod}\n{src}"))
    cells.append(code("import importlib, predimref\nprint('predimref', predimref.__version__, 'pronto')"))
    cells += [md(TEORIA), md("## 3. Entradas"), code(ENTRADAS, True), code(AVANCADOS, True),
              md("## 4. Dimensionamento"), code(RODAR, True),
              md("## 5. Gráficos e alternativas de geometria"), code(GRAFICOS, True), code(ALTERNATIVAS, True),
              code(MAPA, True),
              md(AMESIM_MD), code(EXPORTAR, True),
              md(SENS_MD), code(SENS, True), code(SENS_EPS, True), code(SENS2, True),
              md(VALID_MD), code(VALID, True), md(LIMITES)]
    nb = {"cells": cells, "metadata": {"colab": {"provenance": [], "toc_visible": True},
                                       "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    with open(SAIDA, "w", encoding="utf-8") as fh:
        json.dump(nb, fh, ensure_ascii=False, indent=1)
    print("notebook gerado:", SAIDA, f"({len(cells)} células)")


if __name__ == "__main__":
    main()
