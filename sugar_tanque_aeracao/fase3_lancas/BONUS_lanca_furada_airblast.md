# Bônus · Lança furada / air-blast — até onde dá para reduzir a bolha

> Bônus aprovado pelo Marcus ("mantém como ele pediu, pode fazer como bônus pra ele
> se quiser essa sua ideia"). Meta declarada do Ito: bolha < 0,2 mm.
>
> Propriedades: σ = 0,058 N/m · ρ_xarope = 1350 kg/m³ · µ = 6,5 Pa·s ·
> ρ_ar ≈ 2,1 kg/m³ (1,85 bar abs no injetor) · Q_ar = 40 m³/h.

## 1. Air-blast clássico (Lefebvre) — atomizar o xarope: não funciona

$$\frac{SMD}{d_o}=0{,}48\left[\frac{\sigma}{\rho_A U^2 d_o}\right]^{0,4}(1+1/ALR)^{0,4}
+0{,}15\left[\frac{\mu_L^2}{\sigma\rho_L d_o}\right]^{0,5}(1+1/ALR)^{0,5}$$

| d_o | U_ar | ALR | termo inercial | termo viscoso | SMD | viscoso |
|---|---|---|---|---|---|---|
| 2 mm | 50 m/s | 1 | 0,158 mm | 7,0 mm | 7,1 mm | 97,8 % |
| 2 mm | 150 m/s | 1 | 0,066 mm | 7,0 mm | 7,0 mm | 99,1 % |
| 1 mm | 50 m/s | 3 | 0,089 mm | 4,0 mm | 4,1 mm | 97,8 % |
| 1 mm | 150 m/s | 3 | 0,037 mm | 4,0 mm | 4,1 mm | 99,1 % |

O termo viscoso domina com 98–99 % e **não contém a velocidade do ar**. Triplicar de
50 para 150 m/s não muda o resultado. A 6,5 Pa·s o xarope não atomiza.

## 2. Por que a bolha nunca diminui depois de formada — argumento inercial

Independente do argumento de Grace (que é de cisalhamento viscoso), a rota inercial
também fecha. Ohnesorge `Oh = µ/√(ρσd)`, Weber crítico corrigido por Brodkey
`We_crit = 12(1 + 1,077·Oh^1,6)`:

| bolha | Oh | We_crit | U_rel necessária | τ (relaxação inercial) | t_cap (deformação) | falta |
|---|---|---|---|---|---|---|
| 0,2 mm | 51,9 | 7 194 | 39,3 m/s | 7,2e−10 s | 4,3e−4 s | 6e5 × |
| 1,0 mm | 23,2 | 1 994 | 9,3 m/s | 1,8e−8 s | 4,8e−3 s | 3e5 × |
| 3,0 mm | 13,4 | 835 | 3,5 m/s | 1,6e−7 s | 2,5e−2 s | 2e5 × |

A velocidade relativa é atingível. O que não existe é **tempo**: o arrasto viscoso
freia a bolha em nanossegundos, e a deformação capilar que a quebraria leva
milissegundos. Faltam cinco a seis ordens de grandeza.

**Conclusão estrutural: o único ponto de controle do diâmetro é a FORMAÇÃO.**
Nem cisalhamento, nem inércia, nem bico nenhum reduzem a bolha depois que ela existe.

## 3. O que funciona: jato de gás em vez de borbulhamento

Na formação há duas regimes. Em baixa velocidade a bolha destaca por empuxo — lei de
Tate, `d_b = (6σd_o/ρg)^(1/3)`, dependência **cúbica** (furo 8× menor para bolha 2×
menor). Acima de `We_g = ρ_g U²d_o/σ ≈ 2` o gás passa a **jato**, que se rompe em
bolhas da ordem do próprio furo — dependência **linear**.

| furo | U de jetting | Q por furo | nº de furos | por lança (16) | Tate | jato | ganho |
|---|---|---|---|---|---|---|---|
| 5,0 mm | 3,3 m/s | 235 L/h | 170 | 11 | 5,08 mm | 5,00 mm | 1,0× |
| 3,0 mm | 4,3 m/s | 109 L/h | 366 | 23 | 4,29 mm | 3,00 mm | 1,4× |
| 2,0 mm | 5,3 m/s | 59 L/h | 673 | 42 | 3,75 mm | 2,00 mm | 1,9× |
| **1,0 mm** | **7,4 m/s** | **21 L/h** | **1 903** | **119** | 2,97 mm | **1,00 mm** | **3,0×** |
| 0,5 mm | 10,5 m/s | 7,4 L/h | 5 384 | 336 | 2,36 mm | 0,50 mm | 4,7× |
| 0,2 mm | 16,6 m/s | 1,9 L/h | 21 282 | 1 330 | 1,74 mm | **0,20 mm** | 8,7× |

A meta de 0,2 mm **é alcançável**, mas exige 21 282 furos de 0,2 mm (1 330 por lança).
Isso não é lança furada — é elemento sinterizado poroso, que existe comercialmente.

**Ponto de projeto recomendado: furo de 1 mm, 119 furos por lança.** Bolha ~1 mm, três
vezes menor que Tate, furo usinável, velocidade de jetting de apenas 7,4 m/s.

## 4. A restrição que decide a viabilidade: entupimento

Pressão capilar que segura o xarope fora de um furo de 1 mm: `4σ/d` = **232 Pa**.
Hidrostática na ponta da lança (submergência 6,67 m): **88 334 Pa**.

**380 vezes maior.** Com o ar desligado o xarope entra nos furos e entope. Qualquer
lança furada aqui exige **válvula de retenção por lança** ou pressurização permanente.
É a diferença entre um projeto que funciona e um que entope na primeira parada — e
vale ir ao Ito junto com o resto.

## 5. Resumo para o cliente

1. Reduzir a bolha **depois de formada** é impossível neste xarope — provado por três
   caminhos independentes (Grace/cisalhamento, Weber-Ohnesorge/inércia, e a medição do
   próprio ejetor: 0,10 mm injetado saiu a 0,705 mm).
2. O único controle é o **diâmetro do furo**, e ele só é eficiente no regime de **jato**
   (`We_g > 2`), onde a dependência vira linear em vez de cúbica.
3. Com furo de 1 mm e 119 furos por lança chega-se a ~1 mm de bolha, 3× melhor que a
   lança de ponta aberta, sem nada exótico.
4. Os 0,2 mm exigem sparger poroso e blindagem contra entupimento.
