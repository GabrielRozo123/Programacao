# Referências

| Arquivo | Descrição |
|---|---|
| `desenho_egisa_tag3500.png` | Desenho de fabricação EGISA (055.2254) do **TAG 3.500 L** (Ø1.659 mm, H 2.991 mm, fundo cônico). É o tanque do **novo cenário**. |
| `croqui_cliente_arrefecimento.pdf` | Croqui do cliente com as cotas rabiscadas: nível 1,53 m, sucção ao chiller 0,85 m → **1,35 m**, retorno ao tanque perto do fundo, e a bomba de recirc **12 m³/h**. |
| `v3_1_medido_69m3.png` | Medição (via CAD) do `chiller_tank_fluid_v3_1.step` — tanque **grande** (Ø4,21 m, ~69 m³) do **preliminar**. Outro vaso, ver `../01_contexto.md`. |

## Arquivos de origem que NÃO estão versionados aqui (grandes / de fabricação)
- `chiller_tank_fluid_v3_1.step` — domínio de fluido do preliminar (tanque grande).
- `GreyBeer_2040-01-00TK.stp` (12 MB) e `.dwg` (9 MB) — CAD de fabricação enviado pelo cliente.
  Observação técnica: o `.stp` é um export **tesselado** (8.550 faces planas, sem sólidos, com
  molduras de desenho embutidas) → não é medível nem malhável diretamente. Por isso a geometria
  do estudo é **reconstruída parametricamente** a partir das cotas (ver `../geometria/`).
