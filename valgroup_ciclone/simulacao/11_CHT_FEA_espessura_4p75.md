# 11 — CHT com espessura de parede · entregável para o FEA (Simas)

> **Estudo:** continuação do projeto Valgroup. O Simas faz a análise estrutural em
> **Simcenter 3D**; a CAExperts entrega os campos de **pressão, temperatura e força em
> função da posição**.
> **Arquivo:** `ciclone_307_100_FEA_Espessura.sim` · **Data:** 27/09/2026
> **Geometria:** `gen_ciclone_cht.py` → Dc = 307 mm, t = **4,75 mm**, aço SA-240 304L

---

## 1. Resultado consolidado — carga 100 %

| grandeza | valor | observação |
|---|---|---|
| **ΔP** (estático, entrada → saída gás) | **3 400 Pa = 34,0 mbar** | limite do cliente: 40 mbar |
| número de Euler ξ = 2ΔP/ρv_i² | **6,6** | literatura Stairmand HE ≈ 6,4 |
| ρ média do gás | 2,846 kg/m³ | teórico a 400 °C: 2,801 |
| velocidade de entrada v_i | 19,15 m/s | |
| **calor pela parede** | **5,15 kW** | balanço fecha em **1,2 %** |
| **T da parede — faixa** | **350,1 a 398,0 °C** | média derivada **373 °C** |
| **η com a PSD real** | **96,25 %** | medida pela fuga (ver §5) |

### Condições
| | |
|---|---|
| Vazão mássica de gás | 0,505556 kg/s (1 820 kg/h) |
| Massa molar do gás | 130,594 kg/kmol (Memorial Rev. 01) |
| Viscosidade | 1,1 × 10⁻⁵ Pa·s |
| Pressão de referência | 120 000 Pa |
| Temperatura de entrada | 400 °C (673,15 K) |
| Convecção externa | h = 10 W/m²·K a 25 °C |
| Vazão de particulado | 0,002778 kg/s (10 kg/h) — **⚠️ ver §6** |

---

## 2. ⭐ O ΔP de 3 400 Pa não é erro — mas o recado é mais sério do que parecia

O primeiro instinto foi tratar 3 400 Pa como erro, porque o relatório final do Dc 307 daria
~2 860 Pa nesta densidade. **Estava errado**, mas a explicação certa não é a primeira que
aparece. Em número de Euler (ξ = 2ΔP/ρv_i², invariante à densidade), a família inteira do
projeto — **toda ela em k-ω**:

| rodada | ξ |
|---|---|
| Dc 290 · R1 · 100 % · ρ const | 6,17 |
| Dc 290 · R2 · 50 % · ρ const | 5,61 |
| Dc 290 · R3 · 100 % · + energia | 6,32 |
| Dc 290 · R4 · 50 % · + energia | 5,70 |
| Dc 290 · R5 · 100 % · BC verificada | 6,09 |
| Dc 307 · relatório final | 5,37 |
| **Dc 307 · este estudo · CHT** | **6,62** |

O ξ do projeto sempre viveu entre **5,4 e 6,3**. O 6,62 está logo acima do topo, e a causa é
**malha** — este arquivo tem malha própria, construída para o CHT. **Não é modelo de
turbulência: este estudo também roda k-ω** (confirmado em 27/09).

### ⚠️ E é aí que está o problema

O `RELATORIO_FINAL_ciclone.md` §5.1 diz:

> O k-ω amortece a precessão do núcleo do vórtice e, por isso, **subestima** a queda de pressão.
> RST estacionário: **×1,18** · assíntota pessimista: **×1,39**

Como este resultado também é k-ω, **esse fator se aplica por cima dele, não em vez dele**:

```
ΔP estimado real = 3 400 × (1,18 a 1,39) = 4 010 a 4 730 Pa = 40,1 a 47,3 mbar
```

**Contra o limite de 40 mbar do cliente.** Neste cenário de gás (ρ = 2,80 kg/m³) a margem
fecha ou é ultrapassada.

> **Levar ao Marcus:** o envelope de 29–74 mbar apresentado foi levantado **todo em k-ω**.
> Corrigido pelo fator RST, ele vai para **34–103 mbar**, e boa parte dele passa dos 40 mbar.
> Isso **não** é achado novo — o §5.1 do relatório final já antecipava — mas agora há uma
> medida independente sustentando, e a pergunta "qual cenário de gás é a carga de projeto"
> deixa de ser acadêmica: ela decide se o ciclone atende ou não a especificação.
>
> Para o FEA isso é indiferente: 3 400 Pa contra 40 000 Pa de pressão de projeto do casco.

---

## 3. Campo térmico — quem controla é a convecção externa

Resistências em série, com o h interno **medido** pelo CFD (≈ 300–360 W/m²·K):

| | resistência | fração |
|---|---|---|
| convecção interna | 0,0028 m²K/W | 2,7 % |
| aço 304L, 4,75 mm | 0,0003 m²K/W | **0,3 %** |
| convecção externa (h = 10) | 0,1000 m²K/W | **97,0 %** |

**O h externo de 10 W/m²·K domina tudo.** Por isso a parede fica praticamente na temperatura
do gás — o aço e o filme interno quase não oferecem resistência, e o gradiente através dos
4,75 mm é de ~1 °C.

O h interno alto se justifica: o vórtice raspa a parede a ~38 m/s.
```
Re = ρ·v_tang·Dc/µ = 2,85 × 38 × 0,307 / 1,1e-5 = 3,0 × 10⁶
Nu = 0,023 · Re⁰˙⁸ · Pr⁰˙⁴ ≈ 2 770   →   h ≈ 360 W/m²·K
```

### Validação cruzada
| | T parede média |
|---|---|
| Estudo anterior (sem casca, parede fina) | **378,6 °C** |
| Este estudo (CHT completo, casca de 4,75 mm) | **373 °C** |

Dois modelos independentes, **1,5 % de diferença**. Dá confiança no campo que vai para o FEA.

### Critério de orvalho
Parede a 350–398 °C contra ponto de orvalho ácido de ~250 °C. **Folga grande, sem risco de
condensação** — confirma o que o estudo anterior já indicava.

---

## 4. ⚠️ A PSD não cabe em nenhuma função do STAR — usar a tabela

O Marcus pediu para ajustar a granulometria a uma das funções nativas. **Não é possível**, e
`fit_PSD_distribuicoes.py` documenta a justificativa. Resumo:

| ajuste | parâmetros | RMS | erro máx |
|---|---|---|---|
| Rosin-Rammler | d_ref = 127 µm, n = 1,81 | 0,109 | 0,161 |
| Log-normal | d_g = 103 µm, σ_g = 2,09 | 0,101 | 0,147 |

O problema é a forma da distribuição medida:

```
 40 –  61 µm :  9,1 %
 61 –  75 µm : 36,9 %   ← 37 % da massa num intervalo de 23 % em diâmetro
 75 – 150 µm : 25,8 %
150 – 425 µm : 12,1 %
425 µm – 1 mm:  9,5 %
  1 – 12,5 mm:  6,6 %   ← cauda longa
```

Um modo estreitíssimo em ~70 µm (cara de corte de peneira) **mais** uma cauda de 312× em
faixa. Função de dois parâmetros não faz as duas coisas.

E o erro cai exatamente onde este estudo dói:

| fração acima de | medido | Rosin-Rammler | log-normal |
|---|---|---|---|
| 425 µm | **16,1 %** | 0,01 % | 2,7 % |
| 1 mm | **6,6 %** | 0,00 % | 0,1 % |

**Mesmo o melhor ajuste joga fora 6× da massa grossa.** A energia de impacto escala com d³ —
perder a cauda é perder o fenômeno que estamos tentando medir.

> **Decisão:** usar `Table (particle size CDF)` com `char_PSD_CDF.csv`. É o recurso nativo do
> STAR para este caso e reproduz a medida sem erro. O ajuste fica registrado como tentado e
> descartado, com a tabela acima como justificativa ao cliente.

---

## 5. η = 96,25 % com a granulometria real

```
1 − |ṁ_gas| / ṁ_inj  =  0,9625
```

**Por que medir a fuga e não a coleta:** 1 050 das ~1 194 parcelas entram em regime de quiques
sucessivos junto à parede e são encerradas por tempo limite aos 60 s, sem nunca serem
contabilizadas como coletadas. É o mesmo mecanismo descrito no `RELATORIO_FINAL_ciclone.md` §4.

Fisicamente essas parcelas **estão** coletadas — uma partícula que passou 60 s raspando a
parede sob 830 g está na camada limite sendo arrastada para o fundo, não voltando. Contá-las
como não-escapadas é correto, e a fuga é observável sem ambiguidade.

Os 3,75 % que escapam são a cauda fina em torno de 40–61 µm.

> Este número **substitui** a extrapolação classe a classe da curva de grade: é a
> granulometria medida, injetada inteira, sobre o campo CHT convergido.

### ⚠️ Cuidado: truncar a residência INFLA a eficiência

A rodada de verificação com `Maximum Residence Time = 2 s` deu **η = 99,75 %**. Esse número
é **viesado e não deve ser usado**:

```
  2 s  →  escapou 0,25 %
 60 s  →  escapou 3,75 %
```

Em t = 1,0 s ainda há **1 159 de 1 194 parcelas ativas** — só 3 % saíram no primeiro segundo.
Os 3,5 % extras que escapam entre 2 e 60 s são finos circulando no vórtice interno antes de
achar o vortex finder, e isso é físico. **Truncar em 2 s não aumenta a eficiência: apaga a
fuga.** A rodada de 2 s serve só para a verificação do mapa de erosão (§6.2).

**η = 96,25 % pode ainda ser limite superior.** Aos 60 s as parcelas restantes foram
encerradas por tempo, não por terem parado de escapar. Para saber se a fuga saturou, basta
uma rodada a 120–150 s e ver se os 3,75 % crescem. É barato (campo congelado, uma iteração).

### Execução
| | |
|---|---|
| Sub-steps até terminar | 632 770 (orçamento: 2 000 000) |
| Maximum Residence Time | 60 s |
| Restituição na parede | Normal 0,8 · Tangencial 0,9 |
| Acoplamento | one-way (carga mássica 0,55 %) |

---

## 6. ⚠️ Pendências

### 6.1 Vazão de particulado: 10 ou 80 kg/h
O e-mail do cliente traz os dois números. A rodada usou **10 kg/h**.

**Não bloqueia:** com one-way coupling a taxa de erosão é **linear** na vazão de partículas.
Se o Marcus confirmar 80 kg/h, multiplica-se o resultado por 8 na pós-análise, sem re-rodar.
O que muda 8× é a **vida útil em anos**, não o padrão espacial.

### 6.2 O mapa de erosão precisa de uma verificação
As 1 050 parcelas presas geram impactos rasantes repetidos. Para material **dúctil** como o
304L, o desgaste por corte tem máximo em ângulos de 20–30° — ou seja, **impactos rasantes não
são desprezíveis** e podem inflar o mapa.

**Verificação:** a rodada com `Maximum Residence Time = 2 s` já foi executada (22 040 sub-steps).
Falta **comparar as duas cenas de erosão**:
- padrão igual, magnitude diferente → hot spots reais, usar o de 2 s como conservador
- padrão diferente → o de 60 s está contaminado, vale o de 2 s

> ⚠️ A rodada de 2 s vale **só** para isso. A eficiência dela (99,75 %) é viesada — ver §5.

### 6.3 Modelo de turbulência
Confirmado **k-ω** (27/09). Isso significa que o fator de correção RST **ainda não foi
aplicado** a nenhum resultado deste projeto, e é o que abre a questão do ΔP em §2.

---

## 7. O que entregar ao Simas

| campo | onde | formato |
|---|---|---|
| `Absolute Pressure` (= `Pressure` + 120 kPa) | face interna molhada `Solido_int` | CSV com `Position[X,Y,Z]` + escalar |
| `Temperature` | sólido inteiro | idem |
| Temperatura de projeto | **400 °C** (arredondando 397,8) | é com ela que sai a tensão admissível do SA-240 304L |

### ⭐ A carga de partículas é estruturalmente irrelevante
```
pressão de impacto = ṁ_p · v / A = 0,002778 × 20 / 0,44 ≈ 0,13 Pa
```
Mesmo a 80 kg/h e concentrada em 10 % da área: **~10 Pa**, contra **40 000 Pa** de pressão de
projeto do casco. **Três a quatro ordens de grandeza abaixo.**

> O que o Simas precisa saber sobre o char não é força — é **onde a parede vai desgastar**.
> Vale adiantar isso a ele, porque muda o que ele espera receber.

---

## 8. Erros cometidos no caminho (para não repetir)

| erro | sintoma | causa real |
|---|---|---|
| Solver FE com URF = 1,0 | T oscilando de −20 000 a +120 000 °C | sem sub-relaxação; corrigido para 0,2 |
| `MW_gas` = 184, `mu_gas` = 9,5E-5, T_inlet = 300 K | ρ = 4,398 e ΔP = 1 524 Pa | valores herdados do arquivo antigo e da planilha Lapple (errada) |
| Reports de ΔP em `Total Pressure` | 380 Pa a mais que a convenção | a convenção do estudo é **estática** (ver `literatura/pecanha_ciclone_lapple.md:118`) |
| Perseguir ΔP = 2 862 Pa como "alvo" | caça a um erro inexistente | 2 862 é o **piso k-ω**, não a verdade; ver §2 |
| Polyhedral Mesher no sólido | mesher rejeitado | região com modelo Finite Element exige **Tetrahedral** |

> A lição transversal: **o invariante de Euler (ξ) é o juiz, não o valor absoluto de ΔP.**
> Ele separa erro de entrada (ρ errado) de diferença de modelagem (turbulência/malha) —
> algo que o ΔP sozinho não distingue.
