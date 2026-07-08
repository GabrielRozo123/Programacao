# 04 — Método CFD

## Modelos físicos (herdados do as-built — slide 3)
- **Implicit Unsteady** (transiente). No as-built: Δt = 1 s. *(Reavaliar o Δt para o tanque
  menor — as escalas de tempo mudam com o tamanho; ver "verificações" abaixo.)*
- **Turbulência:** k-ε Realizable.
- **Densidade polinomial em T:** ρ = 1082,88 − 0,55·T [kg/m³, T em K] → acopla temperatura e
  empuxo (motor da estratificação).
- **Gravidade:** g = −9,81 m/s² (eixo Z).
- **Energia:** ativa (é um problema térmico).
- Sem impelidor/rotação → **não precisa de MRF**. A mistura é por jato dos bocais e pela bomba.

## Condições de contorno — circuito do chiller (já validado no as-built)
- **Entrada (retorno do chiller):** T = −5 °C, Q = 12 m³/h.
- **Saída (sucção ao chiller):** pressão = 0 Pa rel (ou vazão prescrita).
- **Paredes:** adiabáticas, sem deslizamento.
- **T inicial:** +5 °C uniforme.

## Como modelar a BOMBA DE RECIRCULAÇÃO sem malhá-la
**Princípio:** a bomba **não é geometria** e **não gera nenhuma célula**. Ela é um transporte de
massa entre dois bocais → representada por **duas condições de contorno acopladas**. (É a mesma
lógica do loop do chiller, que também são só BCs.)

### Receita no STAR-CCM+
1. **Geometria:** apenas dois *stubs* de bocal (tubos curtos) na parede, nas alturas de
   **captação** e **retorno** da recirc. Malha: refino local + prism layer nos stubs.
2. **Bocal de RETORNO (recalque):** *Velocity/Mass Flow Inlet*
   - Vazão mássica: **ṁ = ρ·Q = 932,65 × (12/3600) = 3,11 kg/s**
   - ou velocidade **v = Q/A** conforme o DN:

   | DN | v de entrada |
   |---|---|
   | DN40 | 2,65 m/s |
   | DN50 | 1,70 m/s |
   | DN65 | 1,00 m/s |
   | DN80 | 0,66 m/s |

3. **Bocal de CAPTAÇÃO (sucção):** *Velocity Inlet* com **velocidade apontando para FORA** do
   domínio, mesma vazão. Isso força a extração fixa e fecha o balanço de massa do loop (entra
   3,11 kg/s no retorno, sai 3,11 kg/s na captação). Como o fluxo sai, o STAR usa a T de montante.
4. **Fechamento de energia (o passo-chave):** a água recirculada volta com a **mesma temperatura**
   (a bomba não troca calor). Implementar:
   - **Report** = *Mass-Flow-Averaged Temperature* na superfície de **captação**;
   - transformar em **Field Function**;
   - usar essa field function como a **Static Temperature** do bocal de **retorno**.

   Assim o fluido recirculado carrega a própria temperatura → loop **adiabático**, energia
   conservada. Sem esse acoplamento, injetar-se-ia uma T arbitrária e o balanço térmico furaria.
5. **Calor da bomba:** desprezível — mesmo com 2 bar de recalque, ΔT = P/(ṁ·cp) ≈ **0,06 °C**.
   Pode ignorar (bomba adiabática).

### Diferença entre os dois loops
- **Chiller:** par de BCs que **remove calor** (retorna a −5 °C).
- **Recirc:** par de BCs **adiabático** (T carregada da captação para o retorno).
- Se os 12 m³/h da recirc **somam** aos 12 m³/h do chiller, é só ter **os dois pares de BCs
  operando juntos** — nada especial na malha. *(Confirmar — pergunta 4.)*

### Alternativa (não recomendada aqui)
Representar a bomba como *Momentum Source* num volume. Dá empuxo de jato, mas para um loop de dois
bocais o par de BCs conserva massa e energia corretamente — fica com o par de BCs.

## Verificações a fazer (rigor)
- **Δt:** revisar o passo de tempo para o tanque de 3.500 L (as escalas convectivas/difusivas
  mudam com o tamanho); fazer um mínimo de sensibilidade.
- **Malha near-injector:** resolução nos bocais e prism layers adequados aos jatos.
- **Convergência estatística:** rodar até o campo de estratificação estabilizar (ou até o critério
  de controle −5 °C, se for o objetivo).
- **Baseline consistente:** os três casos com malha/física idênticas — só muda a posição do bocal
  e a presença da recirc.
