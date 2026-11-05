# Coluna de Bolhas — Seminário de Cinética

Scripts de apoio para o caso Euler–Euler no STAR-CCM+. O passo a passo da simulação está em `Literatura/07_Reator_Coluna_de_Bolhas/SETUP_StarCCM.md`.

| Arquivo | O que faz |
|---------|-----------|
| `projeto_coluna_bolhas.py` | Correlações (εG, d32, a, kLa, D_L, V_L) e dois modelos de projeto do reator (gás pistonado + líquido misturado; dispersão axial com reação de 1ª ordem) |
| `compara_cfd_literatura.py` | Lê os monitores exportados do STAR (`star_exports/holdup_Ug*.csv`), calcula a média temporal e compara com as correlações e com `dados_experimentais.csv` |
| `dados_experimentais.csv` | Modelo para os dados da literatura recente (a preencher a partir dos PDFs) |
| `geometria/` | STEP da coluna (3D: D = 150 mm, H = 1200 mm; e 2D axissimétrico) com faces nomeadas + script CadQuery `gera_geometria.py` |
| `resultados/` | Tabela, resumo e figura das correlações para D = 0,15 m |

```bash
pip install numpy matplotlib
python projeto_coluna_bolhas.py                       # D=0.15 m, H0=0.9 m, Ug=1,2,4 cm/s
python projeto_coluna_bolhas.py --D 0.24 --H0 1.5     # outra coluna
python compara_cfd_literatura.py --pasta star_exports --t-media 20
```
