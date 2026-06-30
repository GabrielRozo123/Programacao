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

---

# Análise do IGES — Conjunto Ejetor
Arquivo `dados_cliente/Conjunto_Ejetor.iges` (11 MB, AutoCAD Architecture 2023, INCH).
9.724 entidades, 136 shells.

## Sistema: 4 ejetores (eductores) em manifold (jet aeration)
| Componente | Qtd | raw | ÷10 = real (mm) |
|---|---|---|---|
| Lanças/tubos longos | 4 | D=1.855, L=76.200 | D≈185 mm, L≈7,62 m |
| Manifolds (topo+fundo) | 2 | ~35.560 compr. | ~3,56 m |
| Flanges/conexões | vários | ~5.565–5.806 | ~556–580 mm |
| Bocais/gargantas (menores) | 4+ | ~144–395 | ~14–40 mm |

Funcionamento: líquido motriz no manifold → acelera nos bocais (~14 mm) → arrasta ar →
mistura desce pelas 4 lanças para o tanque. = jet aeration / eductor.

## ESCALA — confirmação cruzada (forte evidência de ×10)
Com ÷10: lança L≈7,62 m ≈ altura do tanque (6,9 m); bocal ≈14 mm; lança D≈185 mm.
Tudo realista E consistente entre os 2 arquivos → **fator ×10 muito provável** (real ≈ raw/10 em mm).
Confirmar no kick-off, mas agora com 2 evidências independentes.

## Implicações CFD
- Multifásico **gás-líquido** (ejetor arrasta ar → bolhas → aeração/mistura).
- Bocal ~14 mm em tanque ~5 m → razão ~350:1 → **malha refinada local no bocal**
  (como o gargalo do chiller). Pesa no esforço/proposta.

## Pendente
- [ ] Confirmar ESCALA real (×10?) no kick-off — pergunta nº1
- [ ] Localizar/medir o tanque Aerador (3º tanque)
- [ ] Definir domínio fluido a extrair (interior dos tanques + lanças/bocais)
- [ ] Dados de operação: vazão motriz, vazão de ar induzida, pressão (kick-off)
