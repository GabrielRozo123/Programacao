# Análise vibracional de peneiras — reprocessamento de dados Pulse VA

Pacote Python (`pulseva`) e notebook Colab que leem os dados brutos (XML) dos 8 acelerômetros triaxiais do
sistema **Pulse VA** (Haver & Boecker), recalculam os parâmetros do relatório do fabricante e geram um relatório
técnico em PDF, uma planilha Excel e figuras de engenharia.

## O que o código faz

| Etapa | Implementação |
|---|---|
| Leitura | `<DataFile SampleRate=…>` → 8 sensores × 3 eixos (g). 800 Hz × 10 s = 8000 amostras por canal |
| Referencial | Sensores do lado L montados espelhados: (X, Y, Z) → (−X, Y, −Z) |
| Rotação | Fase instantânea θ(t) por sensor (passa-banda → Hilbert → frequência suavizada → integração) |
| Fasores | Rastreamento de ordem: `P_n = 2·mean(x·e^(−jnθ))` sobre rotações inteiras, robusto à variação de rotação |
| Grandezas Pulse | G-Force (1×), RMS√2, stroke `2·G·g0/ω²`, Main G / Force Angle (elipse 1×), fase Y–X |
| Corpo rígido | Sincronização pela fase de X; centro = média dos cantos L1/R1/L4/R4; máximo; desvios |
| Diagnóstico | Canal travado/fora de faixa, calibração estática pela gravidade, montagem, kurtosis, estabilidade de rotação, sincronismo, ordens fracionárias (0,5×/1,5×) |
| Saídas | Relatório PDF (A4), Excel multi-abas, figuras PNG, notebook Colab |

## Modelagem do relatório Pulse identificada

| Termo do relatório | Definição | Status |
|---|---|---|
| G-Force (X, Y) | amplitude da componente 1× (g de pico) | confirmado |
| RMS | √2 × RMS do sinal AC (equivalente de pico) | confirmado |
| Stroke | `2·A·g0/(2πf)²` (pico-a-pico) | confirmado |
| Main G / Force Angle | semi-eixo maior e inclinação da elipse X–Y da componente 1× | confirmado |
| Phase Y rel. X | atraso de Y em relação a X | confirmado |
| Center Body | média dos fasores dos 4 cantos, fases referidas ao eixo X | confirmado |
| Maximum Body | máximo entre os 8 sensores | confirmado |
| Pitch / Roll / Twist | `|a−b|/|a+b|` dos fasores Y (alimentação×descarga / esquerda×direita / diagonais) | confirmado |
| Yaw / Z | fórmulas de corpo rígido implementadas como **hipótese** | não confirmado |
| G-Force Z | estimador do Pulse não é o 1× (Z é de banda larga) | não confirmado |

"Confirmado" significa que, recalculado a partir dos números impressos no relatório, o valor bate dentro do
arredondamento (ex.: Main G ±0,006 g, ângulos ±0,1°, Pitch 23,81 % × 23,8 %).

## Como usar

### Google Colab
1. Abra `notebooks/Analise_Vibracional_Peneira.ipynb` no Colab (*File → Open notebook → GitHub*).
2. Rode as células em ordem. A primeira clona este repositório e instala o `reportlab`; a segunda abre o
   seletor de arquivos para enviar o **XML** e, opcionalmente, o **JSON** do relatório de referência.
3. A última célula gera e baixa o PDF e o Excel.

### Local
```bash
pip install -r requirements.txt
python scripts/run_analysis.py gravacao.xml --ref pulse_ref.json --out saida/
python -m pytest -q tests
```

### JSON de referência (valores transcritos do relatório Pulse)
```json
{
  "meta": {"freq_hz": 11.90, "rpm": 714, "record_start": "AAAA-MM-DD hh:mm:ss", "source": "Pulse VA report"},
  "sensors": {"L4": {"main_g": 0.0, "stroke_main": 0.0, "angle": 0.0, "g": [0, 0, 0], "stroke": [0, 0, 0],
                      "rms": [0, 0, 0], "z_kurtosis": 0.0}, "...": {}},
  "phase_yx": {"L4": 0.0, "R4": 0.0, "L1": 0.0, "R1": 0.0},
  "center": {"g": [0, 0], "main_g": 0.0, "stroke": [0, 0], "stroke_main": 0.0, "angle": 0.0, "phase": 0.0},
  "maximum": {"g": [0, 0], "main_g": 0.0, "stroke": [0, 0], "stroke_main": 0.0},
  "deviations": {"pitch": 0.0, "roll": 0.0, "yaw": 0.0, "twist": 0.0, "z": 0.0},
  "limits": {"z": 3, "pitch": 45, "roll": 4, "yaw": 4, "twist": 3}
}
```

Para comparar gravações feitas em rotações diferentes, o código usa o regime supercrítico: strokes, ângulos,
fases e desvios são comparados diretamente, e as acelerações são corrigidas por `(f_ref/f_xml)²`.

## Estrutura
```
pulseva/        io.py · tracking.py · metrics.py · diagnostics.py · plots.py · report_pdf.py · export.py
scripts/        run_analysis.py (CLI) · build_notebook.py (gera o notebook)
notebooks/      Analise_Vibracional_Peneira.ipynb
tests/          testes com sinais sintéticos (deriva de rotação, espelhamento, corpo rígido, canal travado)
privado/        dados de campo e saídas — fora do git (.gitignore)
```

## Referências
* Boashash, B. (1992). Estimating and interpreting the instantaneous frequency of a signal. *Proc. IEEE*, 80(4).
* Fyfe, K. R.; Munck, E. D. S. (1997). Analysis of computed order tracking. *Mech. Syst. Signal Process.*, 11(2).
* Randall, R. B. (2011). *Vibration-based Condition Monitoring*. Wiley.
* Brandt, A. (2011). *Noise and Vibration Analysis*. Wiley.
* Schmidt, P.; Körber, R.; Coppers, M. (2003). *Sieben und Siebmaschinen*. Wiley-VCH.
* Rao, S. S. (2017). *Mechanical Vibrations*, 6ª ed. Pearson.
