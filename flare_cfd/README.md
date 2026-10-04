# Flare CFD e radiação

Simulação de um flare industrial (radiação térmica e segurança) no Google Colab: clima de vento do local
(atlas eólico), LES 3D em GPU com perfil de camada limite, gráficos atualizados em tempo real durante a
solução, varredura das 16 direções do vento com mapas de probabilidade de excedência e vídeo MP4 no final.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GabrielRozo123/Programacao/blob/claude/nifty-franklin-fkhhua/flare_cfd/flare_les_colab.ipynb)

## Conteúdo

| Caminho | O que é |
|---|---|
| `flare_les_colab.ipynb` | Notebook do Colab, autocontido (o pacote é gravado por células `%%writefile`) |
| `flarekit/props.py` | Combustível puro ou **mistura** (gás de refinaria: H₂, C1–C5, olefinas, CO, CO₂, N₂, H₂S), estequiometria, equilíbrio em Z (Cantera), relação de estado da fuligem, tabela β-PDF, pressão pela altitude |
| `flarekit/semiempirical.py` | API 521 (fonte pontual), Chamberlain/Shell (1987) com fator de vista vetorial, Delichatsios, Heskestad, Molina, transmissividade (Wayne; Bagster–Pittblado) |
| `flarekit/les.py` | LES 3D de baixo Mach em PyTorch: malha esticada, Poisson direto, Smagorinsky, Z̃ TVD, vento log, radiação no solo |
| `flarekit/wind.py` | Clima de vento: Global Wind Atlas (clima generalizado WAsP `.lib`) → NASA POWER (MERRA-2, 10/50 m) → Open-Meteo (ERA5, 10/100 m) → rosa sintética; ajuste da lei log (z0), Weibull, rosa de 16 setores, rotação das pegadas e mapas P(q ≥ nível) |
| `flarekit/render.py` | Gravação dos quadros da LES e vídeo: chama em zoom (câmera sintética), painel ampliado, varredura das direções, figura de risco |
| `flarekit/hd.py` | Pós-processamento HD (1080p/1440p/4K) da chama: cor de emissão da fuligem pela temperatura, tone mapping fílmico, bloom, realce visual opcional abaixo da malha; abertura e cartões de texto em HD; codificação direta no ffmpeg |
| `flarekit/dashboard.py` | Painel ao vivo durante a solução |
| `flarekit/safety.py` | Zonas da API 521, dose térmica, probits, fuga, temperatura de aço |
| `flarekit/report.py` | Tabela de validação, figura-resumo, composição do vídeo final |
| `docs/revisao_flare_cfd.html` | Revisão da literatura e álgebra completa |
| `scripts/exemplo_trabalhado.py` | Exemplo numérico da seção 6 da revisão |
| `tests/` | Testes das identidades e dos solvers (`pytest -q`) |
| `build_notebook.py` | Regenera o notebook a partir de `flarekit/` |

## Uso

No Colab: abra o notebook, escolha *Ambiente de execução → GPU T4* e execute tudo. Na célula 1, informe
local, latitude/longitude, altura do flare e rugosidade do terreno (z0). A célula 4 roda 60 s de LES
(o log mostra o tempo de parede e os ms/passo; o preset `gpu` ainda não foi cronometrado numa T4) e grava
os quadros em `flare_quadros.npz`. Na mesma sessão, a célula 7 pode ser refeita (outro FPS, outro corte)
sem rodar a LES de novo; o `.npz` guarda os quadros para uso posterior com `render.Recorder.load`.

**Caso padrão (REPLAN, ilustrativo).** Local: centro da REPLAN (22°43′42″ S, 47°07′54″ O), terreno a
~600 m, tocha de 115 m e z0 = 0,5 m (valores de fontes abertas; confira com o projeto). Combustível: não
há composição medida pública da REPLAN; o padrão usa os pontos médios das faixas da FISPQ "Gás Residual de
Refinaria" da Refinaria de Mataripe (ex-RLAM, Acelen): H₂ 33 · CH₄ 29 · C₂H₆ 15 · C₂H₄ 10,5 · C₃H₈ 1,5 ·
C₃H₆ 1 · n-C₄ 2,5 · n-C₅ 0,5 · N₂ 3,5 · CO₂ 1,5 · CO 1,5 · H₂S 0,5 % molar (M ≈ 17,9 g/mol,
PCI ≈ 45 MJ/kg ≈ 35,9 MJ/Nm³). Também há a média de gás de tocha de Emam (2015), um caso hipotético rico em
H₂ e composição personalizada. A fração radiante de Chamberlain (ajustada a gás natural) é corrigida pela
composição com a tendência da tabela da API 521 (H₂ ≈ 0,7 ×, butano ≈ 1,25 × gás natural) — interpolação
de engenharia, desligável. Com 12,6 kg/s (≈ 570 MW, chama de 30–50 m) e tocha de 115 m, nenhum nível da
API 521 é atingido no solo; para alívios de emergência aumente a `VAZAO` (a malha da LES acompanha o
tamanho da chama).

Fluxo do notebook: vento do local → cenário e modelos de referência → termoquímica → LES 3D ao vivo →
validação → varredura das direções (Chamberlain por setor × classe de velocidade) → vídeo
`flare_linkedin.mp4` de cerca de 2 min para gestores e tomadores de decisão: título e subtítulo, três
cartões de contexto, capítulos numerados (local e vento, gás e cenário, chama em HD, comparação com a
referência, todas as direções, resultados) com legendas temporizadas, quatro números-chave, o que o
resultado significa, próximos passos e encerramento. Os cartões têm a própria chama em movimento ao fundo
(`FUNDO_ANIMADO`), o endereço do LinkedIn (`LINKEDIN`) aparece nas faixas de legenda e no encerramento, e a
célula também gera `capa_linkedin.png` (miniatura do vídeo), `capa_chama.png`, o texto sugerido para o post e
o primeiro comentário (com o link do notebook). Todos os textos ficam na célula 7 (`ROTEIRO`, gerada de `video_roteiro.json`), com campos como
`{q_pico}` preenchidos pela rodada e números com vírgula decimal. Com `USAR_QUADROS_SALVOS` na célula 4,
um `flare_quadros.npz` de uma rodada anterior refaz figuras e vídeo sem rodar a LES de novo.

Limitações a ter em mente: perfil log neutro (sem correção de estabilidade de Monin–Obukhov); a rotação
da pegada é exata só para flare isolado em terreno aberto; o endpoint do Global Wind Atlas não é
documentado oficialmente (por isso há a cadeia de alternativas); o uso comercial da API do Open-Meteo
exige chave.

Localmente:

```bash
pip install numpy scipy torch matplotlib cantera pytest
cd flare_cfd
python -m pytest -q tests
python build_notebook.py        # depois de editar flarekit/
```
