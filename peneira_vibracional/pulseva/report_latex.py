"""Gera um projeto LaTeX (Overleaf) com o relatório técnico completo.

Uso::

    from pulseva.report_latex import build_latex
    build_latex(an, "relatorio_latex/", equipamento="PN-131_04, NS 8958", documento="RT-VIB-001")

O resultado é uma pasta com ``main.tex`` e ``figuras/``, e um ``.zip`` pronto para importar no Overleaf
(New Project, Upload Project). Compila com pdfLaTeX.
"""
from __future__ import annotations

import datetime as _dt
import shutil
import zipfile
from pathlib import Path

import numpy as np

from . import plots as pl
from .metrics import CORNERS, KV_ONE_PERIOD, PULSE_LIMITS

KEYS = ("pitch", "roll", "yaw", "twist", "z")
LABEL = {"pitch": "Pitch", "roll": "Roll", "yaw": "Yaw", "twist": "Twist", "z": "Z"}


def n(v, d=2):
    """Número com vírgula decimal e sinal de menos tipográfico (modo texto)."""
    s = f"{v:.{d}f}".replace(".", ",")
    return s.replace("-", "\\textminus{}") if s.startswith("-") else s


def esc(s: str) -> str:
    for a, b in (("\\", "\\textbackslash{}"), ("_", "\\_"), ("%", "\\%"), ("&", "\\&"), ("#", "\\#")):
        s = s.replace(a, b)
    return s


def atende(v, lim):
    return "Atende" if v <= lim else "\\textcolor{crit}{Não atende}"


TEMPLATE = r"""\documentclass[11pt,a4paper]{article}

% ---------------------------------------------------------------------------
% Pacotes
% ---------------------------------------------------------------------------
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[brazil]{babel}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage[a4paper,top=2.6cm,bottom=2.4cm,left=2.5cm,right=2.3cm,headheight=15pt]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs,tabularx,array,multirow}
\usepackage[table]{xcolor}
\usepackage[font=small,labelfont=bf,labelsep=period,justification=justified,singlelinecheck=false]{caption}
\usepackage{float}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{titlesec}
\usepackage{setspace}
\usepackage{tocloft}
\setlength{\cftbeforesecskip}{5pt}
\setlength{\cftbeforesubsecskip}{0pt}
\setcounter{tocdepth}{2}
\usepackage[hidelinks]{hyperref}

\definecolor{ink}{HTML}{0B0B0B}
\definecolor{ink2}{HTML}{52514E}
\definecolor{accent}{HTML}{1C5CAB}
\definecolor{crit}{HTML}{B42318}
\definecolor{rule}{HTML}{D9D8D3}
\definecolor{band}{HTML}{F4F3F0}

\setstretch{1.12}
\setlength{\parskip}{0.45em}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.18}
\newcolumntype{L}{>{\raggedright\arraybackslash}X}
\newcolumntype{C}{>{\centering\arraybackslash}X}

\titleformat{\section}{\large\bfseries\color{ink}}{\thesection}{0.8em}{}
\titleformat{\subsection}{\normalsize\bfseries\color{ink}}{\thesubsection}{0.8em}{}
\titlespacing*{\section}{0pt}{1.4em}{0.6em}
\titlespacing*{\subsection}{0pt}{1.0em}{0.4em}

% ---------------------------------------------------------------------------
% Dados do documento (editáveis)
% ---------------------------------------------------------------------------
\newcommand{\docnum}{<<DOCNUM>>}
\newcommand{\docrev}{0}
\newcommand{\equipamento}{<<EQUIP>>}
\newcommand{\cliente}{<<CLIENTE>>}
\newcommand{\dataemissao}{<<DATA>>}
\newcommand{\titulocurto}{Análise vibracional de peneira vibratória}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\color{ink2}\docnum\ \ Rev.~\docrev}
\fancyhead[R]{\small\color{ink2}\titulocurto}
\fancyfoot[R]{\small\color{ink2}Página \thepage\ de \pageref{LastPage}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}

\hypersetup{pdftitle={Análise vibracional de peneira vibratória}, pdfsubject={\equipamento}}

\begin{document}

% ===========================================================================
% CAPA
% ===========================================================================
\begin{titlepage}
\thispagestyle{empty}
\vspace*{1.5cm}
{\small\color{ink2}RELATÓRIO TÉCNICO \docnum}\par
\vspace{0.6cm}
{\fontsize{24}{29}\selectfont\bfseries\color{ink} Análise Vibracional de\\[2pt] Peneira Vibratória\par}
\vspace{0.6cm}
{\large\color{ink2} Determinação dos parâmetros de movimento e dos desvios de corpo rígido a partir dos dados brutos de aceleração do sistema Pulse VA\par}
\vspace{1.4cm}
\begin{tabularx}{\textwidth}{@{}p{4.6cm}L@{}}
\toprule
Equipamento & \equipamento \\
Cliente & \cliente \\
Gravação analisada & <<REC_TIME>>, <<REC_FEED>> \\
Sistema de medição & Pulse VA, 8 acelerômetros triaxiais sem fio \\
Data de emissão & \dataemissao \\
Revisão & \docrev \\
\bottomrule
\end{tabularx}

\vfill
{\small\bfseries Controle do documento}\par\vspace{0.2cm}
\begin{tabularx}{\textwidth}{@{}p{1.2cm}p{2.2cm}Lp{2.6cm}p{2.6cm}p{2.6cm}@{}}
\toprule
Rev. & Data & Descrição & Elaborado & Verificado & Aprovado \\
\midrule
\docrev & \dataemissao & Emissão inicial & & & \\[6pt]
\bottomrule
\end{tabularx}
\end{titlepage}

\pagenumbering{roman}
{\setstretch{1.0}\tableofcontents}
\clearpage
\pagenumbering{arabic}

% ===========================================================================
\section{Resumo executivo}
% ===========================================================================
Este relatório apresenta a análise vibracional de uma peneira vibratória a partir dos dados brutos de aceleração registrados pelo sistema Pulse VA durante a operação com carga. Os sinais dos oito acelerômetros triaxiais foram processados com rotinas próprias em Python, e todos os parâmetros que compõem o relatório padrão do sistema foram calculados: aceleração e curso por ponto de medição, frequência de operação, ângulo de força, fase entre componentes, movimento do centro de gravidade e desvios de corpo rígido. Paralelamente, foi avaliada a integridade da própria medição.

A máquina operou a <<RPM>>~rpm (<<FREQ>>~Hz). No centro de gravidade, a aceleração principal resultou em <<C_MAIN>>~g, com curso de <<C_STROKE>>~mm, ângulo de força de <<C_ANGLE>>° e defasagem de <<C_PHASE>>° entre as componentes vertical e longitudinal. O curso nos oito pontos de medição variou entre <<STROKE_MIN>> e <<STROKE_MAX>>~mm, e os desvios de corpo rígido calculados segundo as definições do sistema ficaram dentro dos limites de aceitação (Tabela~\ref{tab:resumo}).

\begin{table}[H]
\centering
\caption{Principais resultados da gravação analisada.}
\label{tab:resumo}
\begin{tabularx}{0.92\textwidth}{@{}Lrr@{}}
\toprule
Parâmetro & Valor & Limite de aceitação \\
\midrule
Rotação & <<RPM>>~rpm & \\
Aceleração principal no centro (Main G) & <<C_MAIN>>~g & \\
Curso no centro (Stroke) & <<C_STROKE>>~mm & \\
Ângulo de força no centro & <<C_ANGLE>>° & \\
Desvio de Pitch & <<D_pitch>>~\% & <<L_pitch>>~\% \\
Desvio de Roll & <<D_roll>>~\% & <<L_roll>>~\% \\
Desvio de Yaw & <<D_yaw>>~\% & <<L_yaw>>~\% \\
Desvio de Twist & <<D_twist>>~\% & <<L_twist>>~\% \\
Desvio Z (lateral) & <<D_z>>~\% & <<L_z>>~\% \\
\bottomrule
\end{tabularx}
\end{table}

<<SUMMARY_L1>>

Foram identificados ainda três aspectos que merecem atenção. A rotação variou <<VAR_PP>>~\% entre o mínimo e o máximo ao longo dos dez segundos de registro, o que exigiu técnicas de rastreamento de ordem para a obtenção correta das amplitudes. A leitura estática de gravidade ficou entre <<G_MIN>> e <<G_MAX>>~g em todos os sensores, em vez de 1,000~g, o que sugere erro sistemático de calibração. Por fim, o espectro revela componentes de ordem fracionária (meia rotação e uma vez e meia a rotação) presentes em toda a máquina, compatíveis com o regime de lançamento do material ou com folga mecânica. As ações recomendadas estão consolidadas na Seção~\ref{sec:recomendacoes}.

\clearpage

% ===========================================================================
\section{Introdução}
% ===========================================================================
\subsection{Objetivo}
Determinar, a partir dos dados brutos de aceleração do sistema Pulse VA, os parâmetros de movimento de uma peneira vibratória em operação e avaliar a sua conformidade com os limites de aceitação adotados pelo fabricante do sistema de medição.

\subsection{Escopo}
O escopo compreende a leitura e a verificação dos dados, a estimativa da rotação, o cálculo das grandezas por ponto de medição, a determinação do movimento do centro de gravidade e dos desvios de corpo rígido, a análise espectral e a avaliação da integridade da instrumentação. Não fazem parte do escopo a inspeção física do equipamento nem a análise de desempenho de peneiramento.

\subsection{Dados de entrada}
Foi utilizado o arquivo de gravação no formato XML exportado pelo sistema Pulse VA (<<XML_NAME>>), que contém as acelerações dos oito sensores nos três eixos. As definições das grandezas reportadas pelo sistema foram identificadas previamente por engenharia reversa de um relatório Pulse VA do mesmo equipamento, conforme descrito na Seção~\ref{sec:metodologia}.

% ===========================================================================
\section{Sistema de medição e dados}
% ===========================================================================
\subsection{Instrumentação}
O sistema Pulse VA é composto por oito acelerômetros triaxiais do tipo MEMS, com faixa de medição de $\pm$11~g, alimentação por bateria e comunicação sem fio (Wi-Fi), fixados à estrutura da peneira por bases magnéticas. Cada sensor registra dez segundos de dados brutos, posteriormente transferidos ao computador de aquisição. Por serem acoplados em corrente contínua, os sensores registram também a aceleração da gravidade, o que permite utilizá-la como referência de verificação estática.

\subsection{Pontos de medição e convenção de eixos}
Os sensores estão distribuídos em quatro posições ao longo de cada lateral: L1 a L4 no lado esquerdo e R1 a R4 no lado direito, sendo a posição 1 a extremidade de alimentação e a posição 4 a extremidade de descarga. Os quatro sensores de canto (L1, R1, L4 e R4) definem o movimento de corpo rígido. Adota-se o eixo X na direção longitudinal, no sentido do fluxo de material, o eixo Y na vertical e o eixo Z na direção lateral.

Os sensores do lado esquerdo estão montados de forma espelhada em relação aos do lado direito, de modo que os eixos X e Z apresentam sinal invertido nos dados brutos. Essa condição foi confirmada pela correlação entre os eixos X e Y, positiva em todos os sensores do lado direito e negativa em todos os do lado esquerdo, e pela componente estática de X, de sinal oposto entre os lados. Para os cálculos, os dados do lado esquerdo foram convertidos ao referencial da máquina pela transformação $(X, Y, Z) \rightarrow (-X, Y, -Z)$.

\subsection{Características da gravação}
\begin{table}[H]
\centering
\caption{Características da gravação analisada.}
\begin{tabularx}{0.85\textwidth}{@{}Lr@{}}
\toprule
Data e hora de início & <<REC_TIME>> \\
Condição de operação & <<REC_FEED>> \\
Taxa de amostragem & <<FS>>~Hz \\
Amostras por canal & <<NSAMP>> \\
Duração & <<DUR>>~s \\
Número de canais & <<NCH>> (<<NSENS>> sensores $\times$ 3 eixos) \\
Inclinação do deck informada & <<INCL>>° \\
Rotação informada no cabeçalho & <<RPM_HDR>>~rpm \\
\bottomrule
\end{tabularx}
\end{table}

% ===========================================================================
\section{Metodologia}\label{sec:metodologia}
% ===========================================================================
\subsection{Estimativa da rotação e rastreamento de ordem}
A rotação do excitador não é constante durante a gravação, em razão da variação de carga e do escorregamento do motor de indução. Ao longo de cerca de 120 ciclos, uma variação de apenas 0,1~Hz acumula dezenas de graus de defasagem, e um ajuste senoidal com frequência fixa subestima a amplitude da componente fundamental. Por esse motivo, adotou-se o rastreamento de ordem computacional \cite{fyfe1997,randall2011}.

Para cada sensor, os sinais X e Y são filtrados por um passa-banda Butterworth de fase nula em torno da rotação e projetados na direção principal do movimento. A fase analítica do sinal resultante, obtida pela transformada de Hilbert, fornece a frequência instantânea \cite{boashash1992}, que é suavizada por um filtro passa-baixa de 2~Hz e integrada para obter a fase de rotação $\theta(t)$. Descartam-se 0,75~s em cada extremidade do registro, para eliminar transientes de filtragem, e utiliza-se um número inteiro de rotações. O fasor complexo da ordem $n$ de um canal $x(t)$ é então
\begin{equation}
P_n = \frac{2}{N}\sum_{k=1}^{N} x(t_k)\, e^{-j n \theta(t_k)}, \qquad x(t) \approx \operatorname{Re}\left\{ P_n\, e^{j n \theta(t)} \right\},
\end{equation}
em que $|P_n|$ é a amplitude, em g, e $\arg P_n$ a fase da ordem $n$. A Figura~\ref{fig:metodo} compara as amplitudes obtidas pelos dois procedimentos: com frequência fixa, a componente fundamental resulta, em média, <<FIX_ERR>>~\% abaixo do valor eficaz do sinal; com rastreamento de ordem, a diferença reduz-se a <<TRK_ERR>>~\%, atribuível às harmônicas e ao ruído.

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{figuras/metodo.png}
\caption{Amplitude da componente fundamental do eixo Y por sensor, obtida por ajuste senoidal com frequência fixa e por rastreamento de ordem. O traço preto indica $\sqrt{2}$ vezes o valor eficaz do sinal.}
\label{fig:metodo}
\end{figure}

\subsection{Grandezas por ponto de medição}
As definições adotadas reproduzem as do sistema Pulse VA e estão resumidas na Tabela~\ref{tab:definicoes}. A classificação \emph{confirmada} indica que a definição reproduz os valores de um relatório Pulse dentro da precisão de arredondamento; \emph{compatível} indica concordância com o relatório, com exclusão estatística das alternativas fisicamente plausíveis, porém sem prova definitiva.

\begin{table}[H]
\centering
\caption{Definições das grandezas reportadas.}
\label{tab:definicoes}
\begin{tabularx}{\textwidth}{@{}p{3.3cm}Lp{2.2cm}@{}}
\toprule
Grandeza & Definição & Situação \\
\midrule
G-Force (X e Y) & Amplitude de pico da componente fundamental (1$\times$), em g & Confirmada \\
G-Force (Z) & Amplitude do maior pico do espectro do sinal, em qualquer frequência & Confirmada \\
RMS & Valor eficaz do sinal multiplicado por $\sqrt{2}$ (equivalente de pico) & Confirmada \\
Stroke & Deslocamento pico a pico $s = 2\,G\,g_0/\omega^2$, com $\omega$ igual à frequência angular de rotação & Confirmada \\
Main G e Force Angle & Semieixo maior e inclinação da elipse descrita pela componente fundamental no plano X--Y & Confirmada \\
Fase Y em relação a X & Atraso da componente vertical em relação à longitudinal & Confirmada \\
Kurtosis Z & Curtose de Pearson do sinal lateral & Confirmada \\
\bottomrule
\end{tabularx}
\end{table}

A órbita da componente fundamental no plano X--Y é a elipse $x = G_x\cos\theta$, $y = G_y\cos(\theta - \varphi)$, em que $\varphi$ é o atraso de Y em relação a X. O semieixo maior $a$ (Main G) e a sua inclinação $\alpha$ (Force Angle) são
\begin{equation}
a^2 = \frac{G_x^2+G_y^2}{2} + \frac{1}{2}\sqrt{\left(G_x^2+G_y^2\right)^2 - 4G_x^2G_y^2\sin^2\varphi}, \qquad \tan 2\alpha = \frac{2G_xG_y\cos\varphi}{G_x^2-G_y^2},
\end{equation}
resultado equivalente ao da elipse de polarização \cite{bornwolf}. No cálculo, ambos são obtidos pela decomposição em valores singulares da matriz formada pelas partes real e imaginária dos fasores.

\subsection{Sincronização de fase, corpo central e corpo máximo}
Os sensores sem fio não compartilham um relógio comum. Os perfis de rotação mostram defasagens temporais de até <<LAG_MAX>>~ms entre sensores (Figura~\ref{fig:rotacao}). Por esse motivo, e em conformidade com o procedimento do sistema Pulse, as fases de cada sensor são referidas ao seu próprio eixo X. O movimento do centro de gravidade (\emph{Center Body}) é a média dos fasores sincronizados dos quatro sensores de canto, e o corpo máximo (\emph{Maximum Body}) corresponde aos maiores valores entre os oito pontos de medição.

\subsection{Desvios de corpo rígido}
Os desvios são combinações dos fasores dos quatro cantos que isolam os modos de corpo rígido, normalizadas pelo movimento vertical total:
\begin{equation}
D = \frac{|N|}{\left|Y_{L1}+Y_{R1}+Y_{L4}+Y_{R4}\right|}\times 100\,\%,
\end{equation}
com os numeradores $N$ da Tabela~\ref{tab:desvios_def}. Nos desvios Yaw e Z, o módulo de cada fasor lateral é o G-Force Z e a fase é a da componente fundamental sincronizada. Como no sistema original, todos os canais participam do cálculo.

\begin{table}[H]
\centering
\caption{Definição dos desvios de corpo rígido.}
\label{tab:desvios_def}
\begin{tabularx}{\textwidth}{@{}p{1.5cm}p{4.6cm}Lp{2.0cm}@{}}
\toprule
Desvio & Numerador $N$ & Significado físico & Situação \\
\midrule
Pitch & $(Y_{L1}+Y_{R1})-(Y_{L4}+Y_{R4})$ & Rotação em torno do eixo lateral & Confirmada \\
Roll & $(Y_{L1}+Y_{L4})-(Y_{R1}+Y_{R4})$ & Rotação em torno do eixo longitudinal & Confirmada \\
Twist & $(Y_{L1}+Y_{R4})-(Y_{R1}+Y_{L4})$ & Torção da estrutura & Confirmada \\
Yaw & $(Z_{L1}+Z_{R1})-(Z_{L4}+Z_{R4})$ & Rotação em torno do eixo vertical & Compatível \\
Z & $Z_{L1}+Z_{R1}+Z_{L4}+Z_{R4}$ & Translação lateral & Compatível \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{Índice de lançamento}
O índice de lançamento \cite{schmidt2003} relaciona a aceleração normal ao deck com a componente normal da gravidade:
\begin{equation}
K_v = \frac{\Gamma\,\sin(\alpha+\beta)}{\cos\beta},
\end{equation}
em que $\Gamma$ é a aceleração principal no centro, em g, $\alpha$ é o ângulo de força em relação à horizontal e $\beta$ é a inclinação do deck. A componente estática da gravidade indica que o eixo X dos sensores está próximo da horizontal, razão pela qual $\alpha$ foi tomado em relação a ela. Para um leito de material perfeitamente plástico, o tempo de voo iguala um período de oscilação quando $K_v = \sqrt{1+\pi^2} \approx 3{,}30$; acima desse valor, o material passa a tocar o deck em ciclos alternados.

\subsection{Verificação da integridade dos sinais}
Antes da interpretação dos resultados, cada canal foi submetido a verificações automáticas: componente estática compatível com a gravidade e com a faixa do sensor, nível dinâmico coerente com os demais sensores, ausência de saturação, módulo do vetor gravidade próximo de 1~g, uniformidade da inclinação estática entre sensores, curtose do sinal lateral e estabilidade da rotação.

% ===========================================================================
\section{Resultados}
% ===========================================================================
\subsection{Rotação}
A rotação média foi de <<RPM>>~rpm (<<FREQ>>~Hz), com variação entre <<FMIN>> e <<FMAX>>~Hz, ou seja, <<VAR_PP>>~\% entre mínimo e máximo (Figura~\ref{fig:rotacao}). As oscilações têm período de alguns segundos e são típicas de variações na alimentação de material. Os perfis dos sensores R2 e R3 aparecem deslocados no tempo em relação aos demais, o que evidencia a ausência de sincronismo de relógio entre sensores. A parte inferior da figura mostra a aceleração principal calculada rotação a rotação nos cantos; a alternância entre valores altos e baixos em rotações consecutivas, mais nítida em L1 e R1, é discutida na Seção~\ref{sec:discussao}.

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{figuras/rotacao.png}
\caption{Rotação instantânea por sensor (acima) e aceleração principal por rotação nos sensores de canto (abaixo).}
\label{fig:rotacao}
\end{figure}

\subsection{Parâmetros por ponto de medição}
A Tabela~\ref{tab:orbit} reúne os parâmetros de cada ponto de medição no formato do relatório Pulse, e a Figura~\ref{fig:orbitas} apresenta as respectivas órbitas no plano X--Y. As órbitas são praticamente lineares na extremidade de alimentação, com defasagem de 9° a 11° entre os eixos, e tornam-se elípticas na descarga, onde a defasagem atinge cerca de 36°. Esse comportamento decorre do movimento de arfagem (pitch), que adiciona às extremidades uma componente vertical defasada da translação.

\begin{table}[H]
\centering
\caption{Parâmetros por ponto de medição a <<RPM>>~rpm.}
\label{tab:orbit}
\small
\setlength{\tabcolsep}{3.6pt}
\begin{tabular}{@{}lrrrrrrrrrr@{}}
\toprule
& Main G & Stroke & Ângulo & \multicolumn{3}{c}{G-Force (g)} & \multicolumn{3}{c}{RMS (g)} & Kurtosis \\
\cmidrule(lr){5-7}\cmidrule(lr){8-10}
Sensor & (g) & (mm) & (°) & X & Y & Z & X & Y & Z & Z \\
\midrule
<<ORBIT_ROWS>>
\bottomrule
\end{tabular}
\par\vspace{2pt}
{\footnotesize\raggedright <<ORBIT_NOTE>>\par}
\end{table}

\begin{figure}[H]
\centering
\includegraphics[height=0.80\textheight]{figuras/orbitas.png}
\caption{Órbitas X--Y por sensor: sinal medido em cinco rotações (cinza) e componente fundamental (cor). Os sensores do lado esquerdo são representados com o eixo X invertido, como vistos pelo lado externo.}
\label{fig:orbitas}
\end{figure}

\subsection{Centro de gravidade, corpo máximo e desvios}
Os resultados do movimento global estão nas Tabelas~\ref{tab:corpo} e~\ref{tab:desvios}, e a Figura~\ref{fig:fase} apresenta a síntese gráfica: as órbitas de deslocamento em escala sobre um esquema da máquina, as ondas verticais sincronizadas, a órbita do centro de gravidade e os desvios em proporção aos limites de aceitação.

\begin{table}[H]
\centering
\caption{Movimento do centro de gravidade e corpo máximo.}
\label{tab:corpo}
\begin{tabular}{@{}lrrrrrrrr@{}}
\toprule
& \multicolumn{3}{c}{Stroke (mm)} & \multicolumn{3}{c}{Aceleração (g)} & Ângulo & Fase \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
& X & Y & Main & X & Y & Main & (°) & (°) \\
\midrule
Centro de gravidade & <<C_SX>> & <<C_SY>> & <<C_STROKE>> & <<C_GX>> & <<C_GY>> & <<C_MAIN>> & <<C_ANGLE>> & <<C_PHASE>> \\
Corpo máximo & <<M_SX>> & <<M_SY>> & <<M_STROKE>> & <<M_GX>> & <<M_GY>> & <<M_MAIN>> & & \\
\bottomrule
\end{tabular}
\par\vspace{4pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
Fase Y em relação a X (°) & L4 & R4 & L1 & R1 \\
\midrule
& <<PH_L4>> & <<PH_R4>> & <<PH_L1>> & <<PH_R1>> \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[H]
\centering
\caption{Desvios de corpo rígido.}
\label{tab:desvios}
\begin{tabularx}{0.95\textwidth}{@{}p{4.3cm}CCCCC@{}}
\toprule
& Pitch & Roll & Yaw & Twist & Z \\
\midrule
Valor calculado (\%) & <<D_pitch>> & <<D_roll>> & <<D_yaw>> & <<D_twist>> & <<D_z>> \\
Limite de aceitação (\%) & <<L_pitch>> & <<L_roll>> & <<L_yaw>> & <<L_twist>> & <<L_z>> \\
Situação & <<S_pitch>> & <<S_roll>> & <<S_yaw>> & <<S_twist>> & <<S_z>> \\
\bottomrule
\end{tabularx}
\end{table}

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{figuras/fase.png}
\caption{Síntese do movimento global: (a) órbitas de deslocamento em escala sobre esquema da máquina; (b) ondas verticais sincronizadas pelo eixo X; (c) órbita do centro de gravidade; (d) desvios em porcentagem do limite de aceitação. O losango indica o valor estimado sem o canal defeituoso.}
\label{fig:fase}
\end{figure}

\subsection{Conteúdo espectral}
O espectro de ordens médio (Figura~\ref{fig:ordens}) apresenta, além da componente fundamental e das harmônicas inteiras, linhas bem definidas nas ordens 0,5, 1,5, 2,5 e 3,5. A amplitude vertical na ordem 0,5 é praticamente a mesma nos oito sensores, entre <<SUB_MIN>> e <<SUB_MAX>>~g, o que caracteriza um movimento do corpo inteiro na metade da frequência de rotação.

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{figuras/ordens.png}
\caption{Espectro de ordens médio dos oito sensores nos eixos X e Y. As linhas tracejadas indicam as ordens fracionárias.}
\label{fig:ordens}
\end{figure}

No eixo lateral (Figura~\ref{fig:espectro_z}), o conteúdo é de banda larga e a componente fundamental é pequena, inferior a <<Z1X_MAX>>~g. O maior pico do espectro, que define o G-Force Z, ocorre em frequências distintas da rotação: <<ZPEAKS>>.

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{figuras/espectro_z.png}
\caption{Espectros de amplitude do eixo lateral Z. O ponto indica o pico utilizado no cálculo do G-Force Z; as linhas verticais marcam as harmônicas da rotação.}
\label{fig:espectro_z}
\end{figure}

% ===========================================================================
\section{Avaliação da integridade da medição}\label{sec:integridade}
% ===========================================================================
<<INTEGRITY>>

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{figuras/integridade.png}
\caption{Módulo do vetor de aceleração estática (gravidade) e inclinação estática do eixo X de cada sensor.}
\label{fig:integridade}
\end{figure}

% ===========================================================================
\section{Discussão}\label{sec:discussao}
% ===========================================================================
<<DISCUSSION_L1>>

\subsection{Significado físico do G-Force e do stroke laterais}
Nos eixos X e Y o maior pico do espectro coincide com a rotação, e a definição do sistema Pulse equivale à amplitude da componente fundamental. No eixo Z, porém, o maior pico ocorre em frequências de duas a cinco vezes a rotação, e o stroke lateral do relatório é obtido convertendo essa amplitude como se ela ocorresse na frequência de rotação. Como o deslocamento varia com o inverso do quadrado da frequência, esse procedimento superestima o deslocamento lateral real, que, considerando apenas a componente fundamental, não ultrapassa <<Z1X_STROKE>>~mm. Os valores de stroke lateral devem, portanto, ser interpretados como um indicador de nível vibratório e não como curso físico.

\subsection{Componentes de ordem fracionária}
Componentes nas ordens 0,5 e 1,5 indicam uma excitação que se repete a cada duas rotações. Em peneiras vibratórias, a causa clássica é o regime de lançamento do material: com índice de lançamento $K_v = <<KV>>$, superior ao valor crítico $\sqrt{1+\pi^2} \approx 3{,}30$, o tempo de voo excede um período e o leito pode passar a tocar o deck em ciclos alternados, fenômeno conhecido como duplicação de período. A uniformidade da componente de meia ordem em toda a máquina favorece essa hipótese em relação a uma folga localizada, que também produz componentes fracionárias, porém concentradas próximo à sua origem. A distinção entre as duas causas requer uma gravação sem carga ou com rotação reduzida, condição em que a contribuição do material desaparece ou se altera.

\subsection{Limitações}
As definições de Yaw e Z são compatíveis com o relatório do sistema Pulse, mas não foram comprovadas de forma definitiva. A comprovação exige a comparação direta entre um arquivo XML e o relatório gerado a partir da mesma gravação. Além disso, os resultados referem-se a uma única gravação de dez segundos e estão sujeitos ao possível erro de calibração discutido na Seção~\ref{sec:integridade}.

% ===========================================================================
\section{Conclusões}
% ===========================================================================
\begin{enumerate}[leftmargin=*,itemsep=0.35em]
\item Os parâmetros de movimento foram determinados a partir dos dados brutos com as definições adotadas pelo sistema Pulse VA. No centro de gravidade, a aceleração principal é de <<C_MAIN>>~g, o curso é de <<C_STROKE>>~mm e o ângulo de força é de <<C_ANGLE>>°, a <<RPM>>~rpm.
\item O movimento é coerente com o de um corpo rígido: curso entre <<STROKE_MIN>> e <<STROKE_MAX>>~mm em todos os pontos, ângulo de força crescente da alimentação para a descarga e movimento lateral fundamental desprezível.
\item Os desvios de Pitch, Roll e Twist atendem aos limites de aceitação com folga.
<<CONC_L1>>
\item A medição apresenta indícios de erro sistemático de calibração e de montagem não uniforme dos sensores, que não alteram as conclusões acima mas devem ser corrigidos nas próximas campanhas.
\end{enumerate}

% ===========================================================================
\section{Recomendações}\label{sec:recomendacoes}
% ===========================================================================
As recomendações estão listadas na Tabela~\ref{tab:recomendacoes} em ordem de prioridade.

\begin{table}[H]
\centering
\caption{Recomendações.}
\label{tab:recomendacoes}
\small
\begin{tabularx}{\textwidth}{@{}p{0.75cm}p{4.9cm}Lp{1.75cm}@{}}
\toprule
Item & Ação recomendada & Justificativa & Prioridade \\
\midrule
<<RECS>>
\bottomrule
\end{tabularx}
\end{table}

% ===========================================================================
\begin{thebibliography}{9}
\bibitem{boashash1992} BOASHASH, B. Estimating and interpreting the instantaneous frequency of a signal. Part 1: Fundamentals. \emph{Proceedings of the IEEE}, v.~80, n.~4, p.~520--538, 1992.
\bibitem{fyfe1997} FYFE, K. R.; MUNCK, E. D. S. Analysis of computed order tracking. \emph{Mechanical Systems and Signal Processing}, v.~11, n.~2, p.~187--205, 1997.
\bibitem{randall2011} RANDALL, R. B. \emph{Vibration-based condition monitoring}: industrial, aerospace and automotive applications. Chichester: Wiley, 2011.
\bibitem{brandt2011} BRANDT, A. \emph{Noise and vibration analysis}: signal analysis and experimental procedures. Chichester: Wiley, 2011.
\bibitem{schmidt2003} SCHMIDT, P.; KÖRBER, R.; COPPERS, M. \emph{Sieben und Siebmaschinen}: Grundlagen und Anwendung. Weinheim: Wiley-VCH, 2003.
\bibitem{rao2017} RAO, S. S. \emph{Mechanical vibrations}. 6.~ed. Hoboken: Pearson, 2017.
\bibitem{bornwolf} BORN, M.; WOLF, E. \emph{Principles of optics}. 7.~ed. Cambridge: Cambridge University Press, 1999.
\bibitem{pulse} HAVER \& BOECKER. \emph{PULSE Vibrationsanalyse}. Folheto técnico. Oelde: Haver \& Boecker, s.d.
\end{thebibliography}

% ===========================================================================
\clearpage
\appendix
\section{Relatórios por ponto de medição}
% ===========================================================================
Cada figura apresenta a órbita X--Y, a tabela de grandezas, os espectros de amplitude e três rotações das formas de onda nos três eixos.

<<SENSOR_FIGS>>

% ===========================================================================
\clearpage
\section{Dados complementares}
% ===========================================================================
\begin{table}[H]
\centering
\caption{Dados complementares por ponto de medição.}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lrrrrrrrr@{}}
\toprule
& Fase Y--X & Freq. & \multicolumn{2}{c}{Pico de Z} & Z 1$\times$ & Stroke Z & \multicolumn{2}{c}{Ordens fracionárias Y (g)} \\
\cmidrule(lr){4-5}\cmidrule(lr){8-9}
Sensor & (°) & (Hz) & (Hz) & (g) & (g) & 1$\times$ (mm) & 0,5$\times$ & 1,5$\times$ \\
\midrule
<<COMP_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\end{document}
"""


def build_latex(an, outdir, equipamento="Peneira vibratória", documento="RT-VIB-001", cliente="",
                data=None, zip_project=True):
    outdir = Path(outdir)
    figdir = outdir / "figuras"
    figdir.mkdir(parents=True, exist_ok=True)
    old = pl.PUBLICATION
    pl.PUBLICATION = True
    try:
        pl.save(pl.fig_orbit_summary(an), figdir / "orbitas.png")
        pl.save(pl.fig_phase_report(an, None), figdir / "fase.png")
        pl.save(pl.fig_speed(an), figdir / "rotacao.png")
        pl.save(pl.fig_integrity(an), figdir / "integridade.png")
        pl.save(pl.fig_z_spectra(an), figdir / "espectro_z.png")
        pl.save(pl.fig_order_spectrum(an), figdir / "ordens.png")
        fm, md = pl.fig_method(an)
        pl.save(fm, figdir / "metodo.png")
        for name in an.sensors:
            pl.save(pl.fig_sensor_report(an, name), figdir / f"sensor_{name}.png")
    finally:
        pl.PUBLICATION = old

    rec, meta = an.record, an.record.meta
    c, mx, dv, alt, th = an.center, an.maximum, an.deviations, an.deviations_alt, an.throw
    S = an.sensors
    t_rec = meta.get("StartDateTime", "")[:19]
    try:
        t_rec = _dt.datetime.fromisoformat(t_rec).strftime("%d/%m/%Y, %H:%M:%S")
    except ValueError:
        pass
    feed = "com alimentação de material" if meta.get("MaterialFeed") == "true" else "sem alimentação de material"
    sub = np.array([s.sub[:, 1] for s in S.values()])
    good = [k for k in S if k not in an.excluded]
    grav = [np.linalg.norm(rec.sensors[k].mean(axis=0)) for k in good]
    tilts = {k: S[k].tilt_deg for k in good}
    tmin_k, tmax_k = min(tilts, key=tilts.get), max(tilts, key=tilts.get)
    lag_k = max(an.lags, key=lambda k: abs(an.lags[k][0]))

    v = {
        "DOCNUM": esc(documento), "EQUIP": esc(equipamento), "CLIENTE": esc(cliente) if cliente else "Não informado",
        "DATA": data or _dt.date.today().strftime("%d/%m/%Y"), "REC_TIME": t_rec, "REC_FEED": feed,
        "XML_NAME": "\\texttt{" + esc(rec.path.name).replace("\\_", "\\_\\allowbreak{}") + "}",
        "RPM": n(an.rpm, 0), "FREQ": n(an.f_mean), "FMIN": n(an.speed["f_min"]), "FMAX": n(an.speed["f_max"]),
        "VAR_PP": n(an.speed["var_pp_pct"], 1), "RPM_HDR": n(rec.rpm_header or 0, 0),
        "FS": n(rec.fs, 0), "NSAMP": str(rec.n_samples), "DUR": n(rec.duration, 0),
        "NCH": str(3 * len(S)), "NSENS": str(len(S)), "INCL": n(th["inclination"], 0),
        "C_MAIN": n(c["main_g"]), "C_STROKE": n(c["stroke_main"], 1), "C_ANGLE": n(c["angle"], 1),
        "C_PHASE": n(c["phase"], 1), "C_SX": n(c["stroke"][0], 1), "C_SY": n(c["stroke"][1], 1),
        "C_GX": n(c["g"][0]), "C_GY": n(c["g"][1]),
        "M_SX": n(mx["stroke"][0], 1), "M_SY": n(mx["stroke"][1], 1), "M_STROKE": n(mx["stroke_main"], 1),
        "M_GX": n(mx["g"][0]), "M_GY": n(mx["g"][1]), "M_MAIN": n(mx["main_g"]),
        "STROKE_MIN": n(min(s.stroke_main for s in S.values()), 1),
        "STROKE_MAX": n(max(s.stroke_main for s in S.values()), 1),
        "G_MIN": n(min(grav), 2), "G_MAX": n(max(grav), 2),
        "FIX_ERR": n(abs(np.mean(md["fixed"] / md["rms"] - 1) * 100), 0),
        "TRK_ERR": n(abs(np.mean(md["tracked"] / md["rms"] - 1) * 100), 1),
        "LAG_MAX": n(abs(an.lags[lag_k][0]) * 1e3, 0),
        "SUB_MIN": n(sub[:, 0].min()), "SUB_MAX": n(sub[:, 0].max()),
        "Z1X_MAX": n(max(S[k].g[2] for k in good) + 0.005, 2),
        "Z1X_STROKE": n(max(S[k].stroke[2] for k in good), 2),
        "KV": n(th["kv_horizontal_ref"]).replace(",", "{,}"),
    }
    for k in KEYS:
        v[f"D_{k}"] = n(dv[k], 1)
        v[f"L_{k}"] = n(PULSE_LIMITS[k], 0)
        v[f"S_{k}"] = atende(dv[k], PULSE_LIMITS[k])
    for k in ("L4", "R4", "L1", "R1"):
        v[f"PH_{k}"] = n(S[k].phase_yx, 1)

    # tabela Orbit Report
    rows = []
    for name, s in S.items():
        gr, bad = s.g_report, name in an.excluded
        mark = "\\textsuperscript{a}" if bad else ""
        rows.append(f"{name} & {n(s.main_g)} & {n(s.stroke_main, 1)} & {n(s.angle, 1)} & {n(gr[0])} & {n(gr[1])} & "
                    f"{n(gr[2])}{mark} & {n(s.rms_pk[0])} & {n(s.rms_pk[1])} & {n(s.rms_pk[2])}{mark} & "
                    f"{n(s.z_kurtosis)}{mark} \\\\")
    v["ORBIT_ROWS"] = "\n".join(rows)
    note = ("Frequência de rotação comum a todos os pontos: " + n(an.f_mean) + "~Hz. G-Force Z: maior pico do espectro "
            "lateral, convertido em stroke na frequência de rotação, conforme o sistema Pulse.")
    if an.excluded:
        note += (" \\textsuperscript{a}~Canal com defeito; valor sem significado físico (Seção~\\ref{sec:integridade}).")
    v["ORBIT_NOTE"] = note

    # picos de Z
    zp = sorted(((S[k].f_peak[2], k) for k in good))
    groups = {}
    for f, k in zp:
        groups.setdefault(round(f, 1), []).append(k)
    v["ZPEAKS"] = "; ".join(f"{n(f, 1)}~Hz em {', '.join(ks)}" for f, ks in sorted(groups.items()))

    # resumo e discussão do canal defeituoso
    l1 = "L1" in an.excluded and alt
    if l1:
        v["SUMMARY_L1"] = (
            "O principal achado, contudo, refere-se à própria medição. O canal lateral (Z) do sensor L1 está com "
            f"defeito: registra valor constante de {n(rec.sensors['L1'][:, 2].mean(), 1)}~g, fora da faixa do sensor, "
            "sem sinal dinâmico. Os desvios de Yaw e Z dependem desse canal, e o fato de atenderem aos limites não pode "
            "ser considerado conclusivo. Quando o canal defeituoso é substituído pelo seu simétrico no lado oposto "
            f"(R1), os desvios passam a {n(alt['yaw'], 1)}~\\% e {n(alt['z'], 1)}~\\%, acima dos limites de "
            f"{n(PULSE_LIMITS['yaw'], 0)}~\\% e {n(PULSE_LIMITS['z'], 0)}~\\%, respectivamente. Recomenda-se, por "
            "isso, reparar o sensor e repetir a medição antes da liberação do equipamento.")
        v["DISCUSSION_L1"] = (
            "\\subsection{Influência do canal defeituoso nos desvios Yaw e Z}\n"
            "Os desvios Yaw e Z dependem exclusivamente dos fasores laterais dos quatro cantos. Com o canal Z do "
            "sensor L1 travado, sua contribuição é praticamente nula, e os valores calculados representam apenas "
            "três dos quatro cantos. Para estimar a sensibilidade do resultado, o fasor lateral de L1 foi substituído "
            "pelo de R1, hipótese de translação lateral idêntica nas duas laterais da extremidade de alimentação, "
            "coerente com o comportamento observado nos pares L2/R2 e L4/R4. Os resultados constam da "
            "Tabela~\\ref{tab:sensibilidade}.\n\n"
            "\\begin{table}[H]\n\\centering\n\\caption{Sensibilidade dos desvios ao canal defeituoso.}\n"
            "\\label{tab:sensibilidade}\n\\begin{tabularx}{0.9\\textwidth}{@{}Lrrr@{}}\n\\toprule\n"
            "Desvio & Calculado (\\%) & Sem o canal L1-Z (\\%) & Limite (\\%) \\\\\n\\midrule\n"
            + "\n".join(f"{LABEL[k]} & {n(dv[k], 1)} & {n(alt[k], 1)} & {n(PULSE_LIMITS[k], 0)} \\\\" for k in ("yaw", "z"))
            + "\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
            "Ambos os desvios passam a exceder os limites de aceitação. Embora a substituição seja uma aproximação, "
            "o resultado indica que o defeito do sensor pode estar ocultando um movimento lateral ou de guinada "
            "relevante, e que a conformidade desses dois itens não pode ser atestada com a medição atual.")
        v["CONC_L1"] = (
            f"\\item Os desvios de Yaw ({n(dv['yaw'], 1)}~\\%) e Z ({n(dv['z'], 1)}~\\%) atendem aos limites, mas "
            "esse resultado depende do canal lateral do sensor L1, que está inoperante. Com o canal substituído pelo "
            "seu simétrico, ambos excedem os limites, de modo que a conformidade desses itens não pode ser confirmada.")
    else:
        v["SUMMARY_L1"] = "Não foram identificados canais com defeito."
        v["DISCUSSION_L1"] = ""
        v["CONC_L1"] = f"\\item Os desvios de Yaw e Z também atendem aos limites de aceitação."

    # integridade (prosa)
    parts = []
    if "L1" in an.excluded:
        parts.append(
            "\\subsection{Canal lateral do sensor L1}\n"
            f"O eixo Z do sensor L1 apresenta valor médio de {n(rec.sensors['L1'][:, 2].mean(), 2)}~g, incompatível "
            "com a gravidade e superior à faixa nominal do sensor, e sinal dinâmico de "
            f"{n(S['L1'].rms_pk[2], 3)}~g, muito inferior ao dos demais sensores. O canal está saturado ou travado e não "
            "representa o movimento. Foi excluído do cálculo do movimento lateral do centro de gravidade e tratado "
            "separadamente na avaliação dos desvios.")
    parts.append(
        "\\subsection{Referência estática de gravidade}\n"
        f"O módulo do vetor de aceleração estática nos sensores sem defeito ficou entre {n(min(grav), 3)} e "
        f"{n(max(grav), 3)}~g, quando o valor esperado é 1,000~g. A uniformidade do desvio, cerca de "
        f"{n((1 - np.mean(grav)) * 100, 0)}~\\%, indica erro sistemático de sensibilidade ou de deslocamento de zero, "
        "ou ainda um fator de escala no firmware. Se o mesmo fator afetar o sinal dinâmico, as acelerações e os "
        "cursos reais seriam maiores na mesma proporção.")
    parts.append(
        "\\subsection{Montagem dos sensores}\n"
        f"A direção da gravidade indica inclinação estática do eixo X entre {n(tilts[tmin_k], 1)}° ({tmin_k}) e "
        f"{n(tilts[tmax_k], 1)}° ({tmax_k}). Em um corpo rígido, sensores montados de forma idêntica apresentariam a "
        "mesma inclinação; a diferença observada decorre da montagem e se soma diretamente ao ângulo de força "
        "medido em cada ponto.")
    parts.append(
        "\\subsection{Sincronismo entre sensores}\n"
        f"Os perfis de rotação dos sensores apresentam defasagens de até {n(abs(an.lags[lag_k][0]) * 1e3, 0)}~ms "
        f"({lag_k}), coerentes com a comunicação sem fio sem sincronismo de hardware. As fases foram, por isso, "
        "referidas ao eixo X de cada sensor, conforme o procedimento do sistema Pulse.")
    v["INTEGRITY"] = "\n\n".join(parts)

    # recomendações
    recs = []
    if "L1" in an.excluded:
        recs.append((
            "Reparar ou substituir o sensor L1 e repetir a medição antes da liberação do equipamento.",
            "O canal Z está inoperante; sem ele, os desvios de Yaw e Z excedem os limites de aceitação.", "Alta"))
    recs.append((
        "Verificar a calibração estática dos oito sensores por ensaio de inversão ($\\pm$1~g) em cada eixo e "
        "conferir o fator de escala do firmware.",
        f"Leitura de gravidade entre {n(min(grav), 2)} e {n(max(grav), 2)}~g em todos os sensores, com desvio "
        "sistemático de cerca de " + n((1 - np.mean(grav)) * 100, 0) + "~\\%.", "Alta"))
    recs.append((
        "Padronizar a fixação dos sensores, com bases niveladas e orientação registrada.",
        f"Inclinação estática variando de {n(tilts[tmin_k], 1)}° a {n(tilts[tmax_k], 1)}° entre pontos, com efeito "
        "direto no ângulo de força.", "Média"))
    recs.append((
        "Realizar gravações complementares sem carga e com rotação reduzida.",
        "Identificar a origem das componentes de ordem 0,5 e 1,5 (regime de lançamento do material ou folga mecânica).",
        "Média"))
    zr = sorted(good, key=lambda k: S[k].rms_pk[2], reverse=True)[:2]
    recs.append((
        f"Inspecionar a estrutura lateral e as fixações próximas às posições {zr[0]} e {zr[1]}.",
        f"Maior nível vibratório lateral da máquina ({n(S[zr[0]].rms_pk[2])} e {n(S[zr[1]].rms_pk[2])}~g RMS), com "
        "conteúdo concentrado acima de 50~Hz.", "Baixa"))
    recs.append((
        "Verificar a regularidade da alimentação de material e o estado do acionamento.",
        f"Variação de rotação de {n(an.speed['var_pp_pct'], 1)}~\\% durante a gravação.", "Baixa"))
    v["RECS"] = "\n\\addlinespace\n".join(f"R{i + 1} & {a} & {b} & {p} \\\\" for i, (a, b, p) in enumerate(recs))

    # apêndices
    figs = []
    for name in S:
        figs.append("\\begin{figure}[H]\n\\centering\n"
                    f"\\includegraphics[width=\\textwidth,height=0.82\\textheight,keepaspectratio]{{figuras/sensor_{name}.png}}\n"
                    f"\\caption{{Relatório do ponto de medição {name}.}}\n\\end{{figure}}\n\\clearpage")
    v["SENSOR_FIGS"] = "\n".join(figs)
    comp = []
    for name, s in S.items():
        bad = name in an.excluded
        comp.append(f"{name} & {n(s.phase_yx, 1)} & {n(s.f_mean)} & "
                    + ("\\multicolumn{4}{c}{canal com defeito}" if bad else
                       f"{n(s.f_peak[2], 1)} & {n(s.g_pulse[2], 3)} & {n(s.g[2], 3)} & {n(s.stroke[2], 2)}")
                    + f" & {n(s.sub[0, 1], 3)} & {n(s.sub[1, 1], 3)} \\\\")
    v["COMP_ROWS"] = "\n".join(comp)

    tex = TEMPLATE
    for k, val in v.items():
        tex = tex.replace(f"<<{k}>>", str(val))
    left = [m for m in __import__("re").findall(r"<<[A-Z_0-9a-z]+>>", tex)]
    if left:
        raise ValueError(f"marcadores não preenchidos: {left}")
    (outdir / "main.tex").write_text(tex, encoding="utf-8")
    if zip_project:
        zp = outdir.with_suffix(".zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(outdir / "main.tex", "main.tex")
            for f in sorted(figdir.glob("*.png")):
                z.write(f, f"figuras/{f.name}")
        return outdir / "main.tex", zp
    return outdir / "main.tex", None
