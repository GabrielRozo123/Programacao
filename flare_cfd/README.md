# Flare CFD e radiação

Material de partida para simular um flare industrial (radiação térmica e segurança) no Google Colab.

- `docs/revisao_flare_cfd.html`: revisão da literatura e das práticas da indústria, com a álgebra completa
  (API 521, Chamberlain/Shell, modelo integral, CFD com k-ε/LES, flamelet/FGM/EDC, RTE/DOM/WSGG, fuligem),
  critérios de segurança (API 521, dose, probits), exemplo numérico e plano de código.
  Abra no navegador; as equações são renderizadas pelo MathJax via CDN.
- `scripts/exemplo_trabalhado.py`: recalcula o exemplo numérico da seção 6 (flare de propano, 584 MW)
  a partir das equações do documento. Requer `numpy` e `scipy`.

```bash
pip install numpy scipy
python flare_cfd/scripts/exemplo_trabalhado.py
```
