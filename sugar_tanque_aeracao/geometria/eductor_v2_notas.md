# Eductor — domínio fluido v2 (revisado) · `gen_eductor_v2.py`

> Revisão do `eductor_dominio_fluido_v1.step`. Agora **paramétrico, validado (BRepCheck OK) e em mm reais**
> (escala Star ÷25,4 já aplicada). Sólido único fundido — sem faces coincidentes (overlap 0,8 mm nos boolean).

## Topologia — CONFIRMADA: 7 bicos Ø9 (não venturi único)
O esquema `venturi_o_que_medir.png` (venturi único) era o **modelo mental ANTES de medir**. As medidas ASME do
CAD acharam **7 faces cilíndricas Ø9 idênticas** → a geometria real é de **7 bicos**. O v1 acertou a topologia;
o v2 limpa e parametriza.

Fluxo: entrada **Ø52** (2", pós redutor 4→2) → **7 bicos Ø9** (1 central + 6 hex) → **câmara Ø60 × 56** (6 furos
de ar Ø1) → **lança ID62,7** (stub 500 mm; real 3,0 m). Datum z=0 = boca da lança. Volume = **1780 cm³**.

## Cotas: ✓ confirmadas (ASME) vs 🟡 [SUPOSTO] (confirmar GA/Marcus/Ito)
| Cota | Valor | Status |
|---|---|---|
| Entrada Ø | 52 mm (2" ID) | ✓ ASME |
| Bicos | 7 × Ø9 mm | ✓ ASME (7 faces) |
| Comprimento do bico | 50 mm | ✓ (BICO corpo) |
| Câmara comprimento | 56 mm | ✓ (z −19,57→−21,0) |
| Lança ID | 62,7 mm (2½" Sch40) | ✓ ASME |
| **Pitch dos 6 bicos** | **R 14 mm** | 🟡 **[SUPOSTO]** — falta o pitch do GA |
| **Câmara Ø** | **60 mm** | 🟡 [SUPOSTO ~60] |
| **Furos de ar** | **6 × Ø1, anel a 8 mm do topo da câmara** | 🟡 [SUPOSTO] — confirmar nº/posição |
| Entrada comprimento | 25 mm | 🟡 [SUPOSTO ~1"] |

## O que muda com cada [SUPOSTO] (pra saber o que priorizar confirmar)
- **Pitch dos bicos** → afeta a interação entre os 7 jatos (coalescência dos jatos na câmara). *Médio impacto.*
- **Câmara Ø** → afeta a razão de expansão jato→câmara e a queda de pressão (arraste de ar). *Alto impacto.*
- **Nº/posição dos furos de ar** → onde e quanto ar entra. *Alto impacto no multifásico.*
- Comprimento da entrada → desprezível (só desenvolve o perfil antes dos bicos).

## Para o CFD (faces = BCs)
- **Entrada Ø52 (topo):** Mass-Flow Inlet (xarope motriz, duty da bomba / split das lanças).
- **6 furos Ø1 (câmara):** Pressure/Mass-Flow Inlet do ar (soprado, 1/2/3 kgf/cm²).
- **Boca da lança Ø62,7 (fundo):** Pressure Outlet (hidrostática + ΔP laminar da lança).
- **Paredes:** no-slip; ângulo de contato nos furos (sensibilidade VOF).

*(Ver metodologia completa em `../fase2/ejetor/01_metodologia_cfd_ejetor.md`.)*
