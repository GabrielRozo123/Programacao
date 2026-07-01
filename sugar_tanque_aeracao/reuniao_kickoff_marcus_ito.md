# Kick-off Sugar — Notas (Marcus Ito, 2026-07-01)

> Reunião de abertura. Processo entendido: clarificação de xarope por flotação
> (fosfatação-flotação) com micro-bolhas geradas por ejetor tipo venturi.

## Objetivo do processo
- **Flotação para clarificar xarope** (produto = xarope de açúcar).
- Remover impurezas do xarope fazendo-as flutuar → skim na superfície → xarope limpo.
- Sequência: forma-se floco de **fosfato de cálcio** (captura impurezas) → **aera-se** com
  micro-bolhas → bolhas grudam nos flocos → flotam → remove.
- Proteger a sacarose enquanto flota (não degradar o açúcar).

## Como o EJETOR funciona (venturi / micronizador de ar)
1. **Xarope** = fluido motriz, bombeado pelo manifold superior.
2. Acelera nos bocais → pressão cai (venturi).
3. **Ar comprimido** injetado nos **bicos de 1 mm** na zona de baixa pressão.
4. Jato cisalha o ar em **micro-bolhas (< 200 µm)**.
5. Mistura desce pelas 4 lanças → tanque de aeração (roxo).
6. Micro-bolhas aderem aos flocos (200–400 µm) → flotam.
→ Bolha DEVE ser menor que o floco (200–400 µm).

## Propriedades do fluido (xarope, Brix 70)
| Propriedade | Valor |
|---|---|
| Brix | 70 |
| Densidade | **1,35 kg/L** (1350 kg/m³) |
| Viscosidade | **65 POISE = 6,5 Pa·s** (⚠️ NÃO centipoise! ~6500× água, tipo mel) |
| Temperatura | 75 °C |

## ⚠️ Desafio central: VISCOSIDADE (números de Stokes)
Velocidade de subida (Stokes, ρ_l=1350, μ=6,5 Pa·s):
| Bolha | Xarope (65 poise) | Água (ref) |
|---|---|---|
| 50 µm | 0,28 µm/s = **1 mm/h** | — |
| 100 µm | 1,13 µm/s = **4 mm/h** | 5,44 mm/s |
| 200 µm | 4,5 µm/s = **16 mm/h** | — |
→ Micro-bolha ~**5000× mais lenta** que na água (4 mm/HORA!). Flotação quase inviável
sem ajuda. Por isso: temperatura (75°C reduz μ), energia cinética dos impelidores,
e bolhas/agregados maiores são cruciais. Argumento técnico forte para a proposta.

## Tanques (mapa do CAD)
- **Roxo** = tanque AERADOR (fundo cônico) → flotação, recebe as 4 lanças do ejetor.
- **Verde/água** = Reator A e B → formação dos flocos, agitadores.

## Agitação / impelidores
- **10–15 rev/min, duplo impelidor** (atualmente **hydrofoil duplo**).
- Impelidor ~no nível do transbordo; talvez aumentar headspace.
- Energia cinética importante para a flotação.
- Podem: mudar a pá, mudar tipo de impelidor, redesenhar o cilindro.
- Sem mancal de fundo; buchas bi-partidas no suporte das pás.
- Motor: FS mínimo 1,2; IP57; redutor eixos paralelos FS 2,3 (torque) / 1,6 (lubrific.).
- **Potência: não se preocupar** (por ora).

## Escala de tamanhos
- Molécula/floco: **200–400 µm** → bolha menor que isso.
- Bicos de ar: **1 mm**.
- (Geometria dos tanques/ejetor: escala ×10 confirmada — ver analise_iges_tanques.md.)

## Dados PENDENTES (Marcus Ito vai enviar)
- ⭐ **Curva vazão × pressão por cm² de ar** (essencial para dimensionar o ejetor)
- Confirmar dimensões / quebra-ondas (desenho lateral)
- Teste de bécker 1 L: influência da temperatura na formação dos flocos

## Provável escopo CFD
1. Ejetor venturi: geração de micro-bolhas (xarope + ar, multifásico, alta viscosidade).
2. Aeração/flotação no tanque: distribuição de bolhas, mistura, zonas mortas.
3. Otimização: impelidor (hydrofoil → outro?), geometria, headspace, para melhorar
   aeração no meio viscoso.
