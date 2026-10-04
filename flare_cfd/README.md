# Flare CFD e radiação

Simulação de um flare industrial (radiação térmica e segurança) no Google Colab: clima de vento do local
(atlas eólico), LES 3D em GPU com perfil de camada limite, gráficos atualizados em tempo real durante a
solução, varredura das 16 direções do vento com mapas de probabilidade de excedência e vídeo MP4 no final.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GabrielRozo123/Programacao/blob/claude/nifty-franklin-fkhhua/flare_cfd/flare_les_colab.ipynb)

## Conteúdo

| Caminho | O que é |
|---|---|
| `flare_les_colab.ipynb` | Notebook do Colab, autocontido (o pacote é gravado por células `%%writefile`) |
| `flarekit/props.py` | Estequiometria, equilíbrio em Z (Cantera), relação de estado da fuligem, tabela β-PDF |
| `flarekit/semiempirical.py` | API 521 (fonte pontual), Chamberlain/Shell (1987) com fator de vista vetorial, Delichatsios, Heskestad, Molina, transmissividade (Wayne; Bagster–Pittblado) |
| `flarekit/les.py` | LES 3D de baixo Mach em PyTorch: malha esticada, Poisson direto, Smagorinsky, Z̃ TVD, vento log, radiação no solo |
| `flarekit/wind.py` | Clima de vento: Global Wind Atlas (clima generalizado WAsP `.lib`) → NASA POWER (MERRA-2, 10/50 m) → Open-Meteo (ERA5, 10/100 m) → rosa sintética; ajuste da lei log (z0), Weibull, rosa de 16 setores, rotação das pegadas e mapas P(q ≥ nível) |
| `flarekit/render.py` | Gravação dos quadros da LES e vídeo: chama em zoom (câmera sintética), painel ampliado, varredura das direções, figura de risco |
| `flarekit/dashboard.py` | Painel ao vivo durante a solução |
| `flarekit/safety.py` | Zonas do API 521, dose térmica, probits, fuga, temperatura de aço |
| `flarekit/report.py` | Tabela de validação, figura-resumo, composição do vídeo final |
| `docs/revisao_flare_cfd.html` | Revisão da literatura e álgebra completa |
| `scripts/exemplo_trabalhado.py` | Exemplo numérico da seção 6 da revisão |
| `tests/` | Testes das identidades e dos solvers (`pytest -q`) |
| `build_notebook.py` | Regenera o notebook a partir de `flarekit/` |

## Uso

No Colab: abra o notebook, escolha *Ambiente de execução → GPU T4* e execute tudo. Na célula 1, informe
local, latitude/longitude, altura do flare e rugosidade do terreno (z0). A célula 4 roda 60 s de LES
(o log mostra o tempo de parede e os ms/passo; o preset `gpu` ainda não foi cronometrado numa T4) e grava
os quadros em `flare_quadros.npz`, de modo que o vídeo (célula 7) pode ser refeito sem rodar a LES de novo.

Fluxo do notebook: vento do local → cenário e modelos de referência → termoquímica → LES 3D ao vivo →
validação → varredura das direções (Chamberlain por setor × classe de velocidade) → vídeo
`flare_linkedin.mp4` (abertura, chama em zoom, painel, varredura, resumos).

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
