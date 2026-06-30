# Análise do IGES — Conjunto Tanques Reator A/B + Aerador

> Inspeção via OpenCASCADE do arquivo `dados_cliente/Conjunto_Tanques_Reator_AB_Aerador.iges`
> (16 MB, AutoCAD Plant 3D 2025). Atualizado: 2026-06-30.

## Cabeçalho IGES
- Produto: "Conjunto de Tanques Reator A e B e Tanque Aerador"
- Sistema: AutoCAD Plant 3D 2025 (Autodesk ATF DWG producer)
- **Unidade declarada: INCH** (flag 1) — porém SUSPEITA (ver escala)
- 22.561 entidades, 404 shells

## Geometria encontrada (isolando shells)
Dois tanques cilíndricos grandes e quase idênticos (= Reator A e B), lado a lado:
| Peça | dx | dy | dz | centro (x,y,z) |
|---|---|---|---|---|
| Tanque 1 | 51.126 | 54.638 | 68.580 | (2000, −63.361, −22.087) |
| Tanque 2 | 51.126 | 53.420 | 68.580 | (2000, −130.255, −22.087) |
+ discos (dz~1.600 / ~160) nos topos = tampas/fundos.

Fatos robustos (independente de unidade):
- dx ≈ dy → seção circular (cilíndricos)
- H/D ≈ 68.580/52.000 ≈ **1,3** (mais alto que largo)
- Separação em Y entre os 2 tanques ≈ 67.000 (lado a lado) → Reator A e B
- 3º tanque (Aerador) não apareceu nos maiores → menor ou agrupado; confirmar.

## ⚠️ UNIDADES/ESCALA — incerto (PERGUNTA Nº1 DO KICK-OFF)
Valores ~52.000–68.000. Cabeçalho diz INCH, mas:
- polegada → ~1.380 m (absurdo)
- mm → ~54 m (grande demais p/ tanque)
- com fator ×10 (erro comum DWG→IGES Plant 3D) → ~5,4 m D × 6,9 m H = **reator realista**
Hipótese: há fator de escala (0,1 mm ou ×10). **Confirmar escala real com Jadir/Marcus Ito.**

## Implicações para o CFD
- Geometria Plant 3D detalhada (tubulação, bocais, suportes) → extrair só o **domínio
  fluido** (interior dos tanques) e limpar o resto antes de malhar.
- Bounding box bruto do conjunto é dominado por coordenadas de planta/entidades soltas
  (não usar como tamanho de tanque).

## Pendente
- [ ] Confirmar ESCALA/UNIDADE real (kick-off)
- [ ] Localizar/medir o tanque Aerador
- [ ] Receber e analisar o Ejetor (.iges)
- [ ] Definir o domínio fluido a extrair
