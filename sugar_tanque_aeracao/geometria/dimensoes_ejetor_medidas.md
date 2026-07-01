# Dimensões do Ejetor — medidas do CAD (Star 3D-CAD)

> Medições via Query Properties (exato) de 1 ejetor isolado. Atualizado: 2026-07-01.

## 🔑 ESCALA: modelo Star ÷ 25,4 = real
Provado pelos rótulos ASME (verdade absoluta):
- Lança "ANSI B36.10M **2½"** Sch40" → OD real = **73 mm**. Star mostra 1,8548 m → 1,8548/0,073 = **25,4**.
- Redutor "**4×2**" → 4" = 114,3 mm. Star 2,9032 m /25,4 = 114,3 mm ✓.
→ **Real = valor do Star ÷ 25,4.** (A estimativa anterior ÷10 estava ERRADA; rótulos ASME corrigiram.)

## Dimensões reais (÷25,4 + rótulos ASME)
| Peça | Star (m) | Real | Nota |
|---|---|---|---|
| Bicos (7×) | raio 0,1143 | **Ø 9 mm** (×7) | 7 faces cilíndricas idênticas |
| BICO corpo | 1,27 | ~50 mm | |
| Fechamento câmara (flange) | 3,9116 dia | ~154 mm | placa/flange |
| Câmara (entre fechamentos) | ~1,43 | **~56 mm** compr. | z: -19,57 a -21,00 |
| Redutor | dz 2,5806 | ~102 mm compr. | **4"→2"** (ID 102→52) |
| Lança (TUBO 2½" Sch40) | OD 1,8548 / L 76,2 | OD **73**, ID **62,7**, L **3,0 m** | rótulo ASME |
| Flange | (raw 5806) | ~229 mm (9") | |
| Ar (bicos) | — | **1 mm** | Marcus Ito |

Rótulos ASME dão os IDs de graça: 2½" Sch40 → ID 62,7 mm ; 4" Sch40 → ID 102,3 mm ; 2" → ID 52,5 mm.

## Domínio fluido v1 (construído — eductor_dominio_fluido_v1.step)
Caminho: entrada Ø52 (2") → 7 bicos Ø9 (hex) → câmara Ø60 × 56 → lança ID 62,7 (stub 500, real 3,0 m).
BCs: entrada = xarope (motriz); ar 1mm = inlet na câmara; saída = tanque.
v1 = representativa; refinar Ø/compr. da câmara e posição do ar quando confirmado (GA).

## Pendente
- [ ] Confirmar Ø interno da câmara e posição/quantidade dos bicos de ar (1mm)
- [ ] Manifold/header (TAMPA HEADER) — Ø (distribuição do xarope) se relevante
- [ ] Escala do arquivo dos TANQUES (separado; conferir — Sinatub dá T~4,3 m do reator)
