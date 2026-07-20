# 02 — Tensão superficial ar-xarope de cana (σ) — revisão de literatura

> **Dado nº 1 do ejetor** (entra ~linear no Ca e no We → controla a quebra da bolha). O Ito não tem medição;
> este é o valor de literatura recomendado até uma medição direta. Revisão multi-fonte (4 ângulos) + síntese
> verificada. **Confiança: MÉDIA** (não existe medição publicada de xarope de cana 60-70 Brix a 60-85 °C).

## ⭐ Recomendação
| | σ (N/m) | Uso |
|---|---|---|
| **Valor-base** | **0,058** | central no setup do ejetor |
| **Faixa realista** | **0,050 – 0,065** | xarope real quente (60-70 Brix, 60-85 °C) |
| **Varredura de sensibilidade** | **0,045 – 0,072** | obrigatória (σ entra linear no Ca/We) |

**❌ Não usar 0,072 N/m como central** — é água **fria** / sacarose **pura fria**; é um **LIMITE SUPERIOR**.

## Por que 0,058 (a cadeia de 3 efeitos)
1. **Brix ↑ (sobe σ, fraco):** a sacarose é **superficialmente INATIVA** — é *expulsa* da interface e **eleva** σ
   acima da água (+5-7%). Sacarose PURA 60-70 Brix ≈ **77-78 mN/m a 20 °C**. *(Corrige suposição anterior: o Brix
   não abaixa σ; ele sobe — mas isso é só a sacarose pura.)*
2. **Temperatura ↓ (abaixa σ, dominante):** dσ/dT ≈ −0,15 a −0,17 mN/m/°C. De 20 → 60-85 °C perde ~6-11 mN/m.
   Licor **puro quente** 60-70 Brix ≈ **66-72 mN/m** (o ganho por Brix é quase cancelado pela temperatura).
3. **Impurezas tensoativas ↓ (abaixa σ, a variável de 1ª ordem):** o xarope **real** carrega **saponinas** (glicosídeos
   anfifílicos, o surfactante mais forte da cana — sozinhas levam a água de 72 → ~37-50 mN/m; causam a espuma do
   caldo), **proteínas, coloides/gomas, ceras**. Subtraem **~6-20 mN/m** conforme o grau de **clarificação**
   (variável mais forte que o Brix). Xarope de usina parcialmente clarificado → **~55-60 mN/m**.

> **σ_efetivo ≈ σ_sacarose_pura(Brix,T) − Δ_impurezas(clarificação)**, com Δ ~ 6-20 mN/m. **Nunca** usar fórmula
> de Brix isolada (superestima). Prova direta: **Schmidt, Christoph & Senge (2000)** — soluções *técnicas* de
> usina têm σ **sistematicamente menor** que sacarose pura de mesmo Brix, com **queda dinâmica** no tempo
> (assinatura de surfactante adsorvendo, ausente na sacarose pura).

## Detalhe fino — σ DINÂMICA vs equilíbrio (importa no ejetor!)
A quebra de bolha no venturi é **rápida (~ms)**, interface recém-criada. Se o surfactante não adsorve a tempo,
a σ **efetiva** é a **dinâmica** (mais alta, ~60-68 mN/m), não a de equilíbrio (~55). Por isso **0,058** é o
compromisso defensável (entre equilíbrio-impuro ~0,055 e dinâmico-quase-puro ~0,065).

## Consequência pro CFD
- Trocar 0,072 → ~0,055-0,058 **sobe We e Ca ~24-30%** (`We=ρU²d/σ`, `Ca=μU/σ`) → **mais quebra, microbolhas ~10% menores**.
  Usar 0,072 gera bolhas **artificialmente grandes/estáveis** (viés otimista contra a flotação).
- **MAS σ é sensibilidade MODERADA** (`d ∝ σ^0,3-0,6`, Hinze/CFD-PBM). O **controlador PRIMÁRIO** da quebra aqui
  é a **viscosidade** (6,5 Pa·s, Ohnesorge alto, Ca~100), não a σ. → σ vale um sweep, não domina o resultado.

## O que confirmar (pra fechar de MÉDIA → alta confiança)
1. **Medição direta** (prioridade): **pendant drop** do xarope da própria planta, na T de operação (60-85 °C) e
   Brix real. *(Não existe na literatura aberta — este número é inferido.)*
2. **σ dinâmica vs equilíbrio** (σ × tempo de idade da interface, ms→s).
3. **Grau de clarificação** do xarope específico (bruto / clarificado / refino) — define o Δ_impurezas (swing >20 mN/m).
4. dσ/dT medido do xarope real (não só extrapolado da água).

## Fontes-chave
- **Schmidt, Christoph & Senge (2000)** — *Surface tension behaviour of pure and technical sucrose solutions*,
  Zuckerindustrie 125(3):175-180. **Primária**: técnicas (impuras) < sacarose pura; queda dinâmica.
- **Docoslis, Giese & van Oss (2000)** — Colloids Surf. B 19(2):147-162. Sacarose até 50% massa eleva σ só ~5% (não é tensoativa).
- **Vázquez, Álvarez & Navaza (1995)** — J. Chem. Eng. Data. σ de sacarose e dσ/dT (25-40 °C).
- **IAPWS (2014) / NIST** — água baseline, dσ/dT ≈ −0,16 mN/m/°C.
- **Saponinas:** MDPI *Sci* (2021) 3(4):44; Colloids Surf. A (2020). Água 72 → ~37-50 mN/m; CMC ~0,025%.
- **Yan et al. (2019)** — CFD-PBM: σ 0,025→0,072 muda d32 de 4,0→5,4 mm (expoente efetivo ~0,3, abaixo do 0,6 de Hinze).
- **Hinze (1955)**; **Physics of Fluids 38, 013353 (2026)** venturi microbolha viscoso; **Rein, Cane Sugar Engineering**.

*(Nota: nesta sessão o egress bloqueou o texto integral de várias fontes; os valores por Brix são consenso
ancorado em snippets/afirmações diretas, não em leitura das tabelas primárias — confirmar ao acessar.)*
