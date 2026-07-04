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

## TANQUE AERADOR (roxo) — CONFIRMADO pela casca real `aerador_wall.step`
**D = 2,08 m** (OD), **H cilindro = 5,588 m**. Eixo em (x=0,20 ; y=−0,44). Borda z=+1,22.
Escala ÷10 (do arquivo TANQUES) agora CONFIRMADA — a casca real bate com a estimativa prévia.
z: −4,368 → +1,220 (cilindro). Cone abaixo de −4,368 (ainda não veio o STEP do cone do aerador).
Casca v1 estimada anterior: `aerador_casca_v1.step` (substituir pela real ao acoplar ejetor).
Acoplar ejetor: redimensionar o ejetor (÷25,4) para a escala do tanque (÷10) ao combinar.

## PASSAGEM (calha de transbordo reator→aerador) — `reator_passagem.step`
Canal no topo ligando os 2 tanques. Interior ~**1,52 (larg) × 1,29 (alt) × 2,69 m (compr)**.
z: −0,21 → +1,08 (parte alta). Alinhado ao eixo x=0,20. Xarope transborda reator → aerador.
Só 2 paredes laterais no STEP (16 mm) — canal retangular.

## NÍVEL DE LÍQUIDO: "até o transbordo" (Marcus Castro Neves confirmou)
Ambos os tanques cheios **até a borda z=+1,22**. Domínio do reator refeito p/ esse nível
(144,7 m³ bruto, antes de descontar internos).

## INJETORES DE AR (lanças do ejetor no aerador) — injetor_1/2/3.step
3 lanças verticais **OD 84,8 mm / ID 70,8 mm**, comprimento **7,112 m** (topo z=+1,8655 →
**boca/face circular z=−5,2465**). Posições (m): (0,464,−0,288), (−0,064,−0,288), (0,200,−0,745)
→ **r=0,305 m do eixo do aerador (0,20/−0,44), 120° entre si** (triângulo).
⚠️ A boca fica **0,646 m ACIMA da saída do cone** (−5,2465 vs −5,892): a lança termina
DENTRO do cone, não no bico. Face circular Ø84,8 (56,5 cm²) = **inlet do ar/microbolhas** no CFD.
Penetração submersa (abaixo do nível 1,22) = 6,47 m. (v1 tinha cortado até −5,9 = erro, corrigido.)

## CONE DE FUNDO DO AERADOR — aerador_cone_fundo.step
Cone: topo **R 1,016 m** (=ID cilindro) → saída **R 0,258 m (Ø 0,516 m)**, **H 1,524 m**,
z −5,892 → −4,368. Eixo (0,20/−0,44). Aerador completo: cilindro ID2,032×H5,588 + cone.

## ⭐ ENTREGÁVEL: `sugar_dominio_fluido_completo.step` (em METROS, validado 2×)
4 sólidos, todos válidos (BRepCheck OK), no referencial de montagem:
| Sólido | Vol (m³) | Descrição |
|---|---|---|
| `Fluido_Reator` | 125,09 | interior − 5 baffles − defletor − haste − cilindro MRF |
| `MRF_Impelidores` | 4,3545 | cilindro rotativo **R 0,55 m** (corrigido de R1,15 em 2026-07-04 — escala real Agimix AGX-PBW800 Ø800mm) eixo (0,327/−6,282) z[−4,85,−0,25] − haste |
| `Fluido_Aerador` | 20,17 | cilindro+cone − 3 lanças |
| `Fluido_Passagem` | 5,31 | calha de transbordo reator→aerador |
Companheiro: **`impelidor_3pas.step`** (impelidor corrigido 3 pás/estágio, 6 total, real Agimix
AGX-PBW800 — substitui `impelidor_em_metros.step`, MESMO referencial, pré-alinhado ao MRF, raio
de ponta 0,4144m < 0,55m ✓). ⚠️ IMPORTAR AMBOS EM **METROS** no Star.
Reator+MRF = 129,44 m³ (125,09+4,3545, conformais, sem overlap). MRF: impelidor entra como wall (subtrair no Star).

## ESCOPO (Marcus gerente) + PAPÉIS CORRIGIDOS (usuário confirmou olhando o CAD)
Simular **2 tanques**, **ambos CHEIOS**, 3º não precisa:
- 🟣 **Aerador (roxo):** tem o **EJETOR (4 lanças) + cone**. **SEM impelidor/baffles.**
  → CFD multifásico (micro-bolhas). Domínio = casca (v1) + cone + lanças (escalar do ejetor).
  Geometria quase pronta (não precisa MRF/rotação).
- 🟢 **Reator (verde):** tem **IMPELIDOR (hydrofoil duplo) + BAFFLES + eixo**.
  → CFD de agitação (MRF) → **potência <25 kW**. Precisa medir: shell, impelidor (Ø/nº pás),
  baffles, eixo.
(O cilindro 85mm "28E" no aerador = lança/tubo, NÃO eixo de agitador — aerador não tem agitador.)

## TANQUE REATOR (verde) — 4 STEPs reais (wall, cone, baffles, defletor) + impelidores
> Escala do arquivo TANQUES fixada: **model ÷ 10.000 = metros** (unidade model = 0,1 mm).
> Prova: defletor mede 3,628 × 4,665 × 0,01626 m e o volume bate exato 0,275 m³.
> Todas as peças no MESMO referencial de montagem → encaixam sozinhas.
> **Eixo do tanque: x = 0,200 m ; y = −6,282 m** (coords de montagem).

| Peça | Medida real | Nota |
|---|---|---|
| Casca cilíndrica | **ID 5,080 m** (OD 5,113, parede 16 mm) | z: −5,638 → +1,220 (H_cil = 6,858 m) |
| Bocal topo | Ø 1,60 m | abertura/manway no topo |
| Cone inferior | topo Ø5,08 → **saída Ø 0,30 m**, **H 0,793 m** | z: −6,431 → −5,638; semiângulo ~17° |
| Baffles (quebra-vortex) | **5 chapas**, larg **0,508 m (=T/10)**, alt **4,318 m**, esp 16 mm | r≈2,16 m, folga parede ~0,13 m; 2 inclinadas ~35° |
| Defletor | chapa **3,628 × 4,665 m × 16 mm** | z −4,34 → +0,32 (do meio ao topo), lado y− |
| Impelidores | **DUPLO hydrofoil**, **Ø ≈ 1,98 m** (D/T=0,39) | inferior z=−4,47 ; superior z=−0,57 ; espaç. 3,9 m; eixo sai pelo topo |
| Altura interna total | saída→borda = **7,65 m** | |

Coerência: D/T=0,39 na faixa Sinatub (0,35–0,50); D=5,08 m ≈ estimativa prévia ~5,4 m.
Potência Sinatub p/ esse porte ~22–25 kW (alvo <25 kW). ✅
Domínio interno limpo construído: `reator_dominio_fluido_v1.step` (cilindro ID5,08 + cone, no referencial de montagem). Internos (baffles/defletor/impelidor/eixo) = subtrair via boolean p/ MRF.

## Pendente
- [ ] Confirmar **D real do aerador** com Marcus/Ito (fixa a escala dos tanques)
- [ ] Cone do aerador: junção cilindro-cone + Ø saída (2 medidas rápidas) ou GA
- [x] Reator verde: D=5,08, H_cil=6,86, cone H=0,79/saída Ø0,30, 5 baffles, defletor, impelidor duplo Ø1,98
- [ ] Confirmar Ø câmara + bicos de ar (1mm) do ejetor
- [ ] Ao acoplar: escalar ejetor (÷25,4) → tanque (÷10)
