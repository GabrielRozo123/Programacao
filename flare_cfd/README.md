# Flare CFD e radiação

Simulação de um flare industrial (radiação térmica e segurança) no Google Colab: LES 3D em GPU com
gráficos atualizados em tempo real durante a solução e vídeo MP4 no final.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GabrielRozo123/Programacao/blob/claude/nifty-franklin-fkhhua/flare_cfd/flare_les_colab.ipynb)

## Conteúdo

| Caminho | O que é |
|---|---|
| `flare_les_colab.ipynb` | Notebook do Colab, autocontido (o pacote é gravado por células `%%writefile`) |
| `flarekit/props.py` | Estequiometria, equilíbrio em Z (Cantera), relação de estado da fuligem, tabela β-PDF |
| `flarekit/semiempirical.py` | API 521 (fonte pontual), Chamberlain/Shell (1987) com fator de vista vetorial, Delichatsios, Heskestad, Molina, transmissividade (Wayne; Bagster–Pittblado) |
| `flarekit/les.py` | LES 3D de baixo Mach em PyTorch: malha esticada, Poisson direto, Smagorinsky, Z̃ TVD, vento log, radiação no solo |
| `flarekit/dashboard.py` | Painel ao vivo e gravação do vídeo |
| `flarekit/safety.py` | Zonas do API 521, dose térmica, probits, fuga, temperatura de aço |
| `flarekit/report.py` | Tabela de validação, figura-resumo, composição do vídeo final |
| `docs/revisao_flare_cfd.html` | Revisão da literatura e álgebra completa |
| `scripts/exemplo_trabalhado.py` | Exemplo numérico da seção 6 da revisão |
| `tests/` | Testes das identidades e dos solvers (`pytest -q`) |
| `build_notebook.py` | Regenera o notebook a partir de `flarekit/` |

## Uso

No Colab: abra o notebook, escolha *Ambiente de execução → GPU T4* e execute tudo.

Localmente:

```bash
pip install numpy scipy torch matplotlib cantera pytest
cd flare_cfd
python -m pytest -q tests
python build_notebook.py        # depois de editar flarekit/
```
