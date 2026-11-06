# Coluna de Bolhas — Seminário de Cinética

Scripts de apoio para o caso Euler–Euler no STAR-CCM+. O passo a passo da simulação está em `Literatura/07_Reator_Coluna_de_Bolhas/SETUP_StarCCM.md`.

| Arquivo | O que faz |
|---------|-----------|
| `projeto_coluna_bolhas.py` | Correlações (εG, d32, a, kLa, D_L, V_L) e dois modelos de projeto do reator (gás pistonado + líquido misturado; dispersão axial com reação de 1ª ordem) |
| `compara_cfd_literatura.py` | Lê os monitores exportados do STAR (`star_exports/holdup_Ug*.csv`), calcula a média temporal e compara com as correlações e com `dados_experimentais.csv` |
| `dados_experimentais.csv` | Modelo para os dados da literatura recente (a preencher a partir dos PDFs) |
| `sensibilidade_diametro.py` | εG ≈ U_G/U∞(d) pelo arrasto de Tomiyama: mostra quanto o diâmetro de bolha controla o resultado e "inverte" um εG do CFD para o d equivalente |
| `perfis_radiais.py` | Plota εG(r) e V_L(r) médios (line probe) com Riquarts e a inversão em r/R ≈ 0,7; confere a vazão líquida ≈ 0 |
| `monta_animacao.py` | Junta os hardcopies PNG do STAR em MP4 + GIF (1 ou 2 cenas lado a lado, com o tempo escrito) |
| `cfd_para_projeto.py` | **Leva o CFD às equações de projeto**: kLa (Higbie + a = 6εG/d), Hatta, taxa global com resistências em série, D_L (Joshi) → Pe → conversão; compara com o projeto só por correlações |
| `figura_resumo_rodadas.py` | Figura-resumo das 4 rodadas 2D (εG × correlações, α(r), V_L(r)) a partir de `resultados_cfd_2D/` |
| `resultados_cfd_2D/` | Exportações do STAR das rodadas 1–4 (U_G = 2 cm/s) + `resumo_rodadas.csv` |
| `geometria/` | STEP da coluna (3D: D = 150 mm, H = 1200 mm; e 2D axissimétrico) com faces nomeadas + script CadQuery `gera_geometria.py` |
| `resultados/` | Tabela, resumo e figura das correlações para D = 0,15 m |

```bash
pip install numpy matplotlib imageio imageio-ffmpeg pillow
python projeto_coluna_bolhas.py                       # D=0.15 m, H0=0.9 m, Ug=1,2,4 cm/s
python projeto_coluna_bolhas.py --D 0.24 --H0 1.5     # outra coluna
python compara_cfd_literatura.py --pasta star_exports --t-media 20
```
