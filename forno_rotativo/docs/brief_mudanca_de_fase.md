# Mudança de fase da carga: base do DEM com fusão, poça e carvão

Complemento do `brief_tambor_batelada.md` para o `tamborkit/phasedem.py`. Resume o que a literatura aberta diz sobre o que acontece com cada pedaço de lixo plástico aquecido devagar (1–5 K/min) num tambor rotativo. Marcas: **[TC]** valor do texto completo da fonte; **[D]** derivado aqui a partir da fonte; **[H]** hipótese de ordem de grandeza.

## 1. Do pedaço solto ao fundido

| Material (forma no lixo marinho) | Amolece / encolhe | Funde (pico DSC) | Gruda | Fonte principal |
|---|---|---|---|---|
| PEBD/PELBD (filmes, sacolas) | Filme orientado encolhe até 80 % linear a 135 °C [TC] | 106–116 °C [TC] | ~101–103 °C (início da fusão + 5–7 K) [D] | Equistar US 8,637,607; Voelp et al. 2025; Univation US 7,774,178 |
| PEAD (frascos, tampas, redes) | Redes: amolecimento Kofler 140–145 °C [TC] | 126–132 °C [TC] | ~128–130 °C [D] | Rigaku B-TA1006; Waschke et al. 2026 |
| PP (tampas, redes) | Redes: 175 °C [TC] | 160–165 °C [TC] | ~160–165 °C [H] | Waschke et al. 2026; Voelp et al. 2025 |
| PS expandido (isopor) | Encolhe a partir de 80 °C; acima de 100 °C amolece, contrai e vira um filme de PS fundido [TC] | Tg ~100 °C; flui acima de ~160 °C [TC] | ~110–115 °C (Tg + 10–15 K) [D] | EUMEPS White Book; EUMEPS fire; Gonzalez-Aguilar et al. 2022 |
| PET (garrafas) | Parede biorientada encolhe acima de 60 °C, rápido acima de 85 °C [TC]; cristaliza a frio ~110–120 °C e endurece [TC] | ~255 °C, quase independente da taxa [TC] | ~80–90 °C até cristalizar [D] | Rabello e Wellen 2008; US 8,333,055 |
| PVC rígido | Tg 95 °C; sem fusão cristalina; perde HCl a partir de ~250 °C (10 K/min) [TC] | — | ~150 °C [H] | Tomaszewska et al. 2022 |

**Volume.** O isopor é ~98 % ar. Densificadores de ar quente reduzem o volume 60–80× em minutos a 150–180 °C [TC]. O plástico coletado solto tem 20–25 kg/m³ (filme, garrafas, potes) [TC], contra ~740–760 kg/m³ do fundido. A razão solto → denso fica entre 17 e 38 para filmes e frascos [D].

**Tempo de fusão numa batelada.** Um forno rotativo comercial em batelada usa estas etapas [TC]:

1. Rampa de 1,5 K/min até 100 °C e 50 min de patamar (fusão e secagem).
2. Rampa até 150 °C e 200 min de patamar, até todo o plástico fundir por igual.
3. Rampa até 250 °C (liberação do cloro).
4. Pirólise do fundido.

Fonte: SK Innovation, US 12,296,504.

**O que o modelo usa:**

- fração fundida f_m(T) da faixa de fusão de cada polímero (`feed.py`), com ±8 K de dispersão entre pedaços (graus e formas diferentes) [H];
- colapso do volume aparente para o denso proporcional a f_m;
- pegajosidade crescente com f_m.

A pesquisa sugere três refinamentos para uma versão futura: rampas assimétricas (início → fim da fusão, do tipo DSC), um estágio separado de colapso geométrico do isopor, e o PET encolhendo e depois endurecendo ao cristalizar.

## 2. Por que o pedaço gruda (e o que não adianta modelar)

- **Capilaridade:** é desprezível para pedaços de 40–90 mm. A força de capilaridade 2πR\*γ cos θ, com γ ≈ 25 mN/m (PE, PP a 150–200 °C [TC]) e θ ≈ 70–85° sobre aço [TC], dá ~2 mN, isto é, 10⁻³–10⁻² do peso de um pedaço [D].
- **Ponte viscosa:** é o que prende de fato. A lubrificação 6πηR\*²u/h com η ~ 10³ Pa·s passa de centenas de newtons para u ~ 0,1 m/s e h ~ 1 mm [D]. Os pedaços fundidos andam juntos.
- **Pescoço (sinterização de Frenkel):** a/R = (t/τ)^½ com τ = ηR/γ. Para pedaços de centímetros e η ~ 10³ Pa·s, τ fica em dezenas de minutos [D]. Por isso eles se unem ao longo da batelada, não num choque.

**O que o modelo usa:** uma coesão efetiva de até 1,5× o peso do pedaço, crescendo com f_m [H]. Representa a ponte viscosa sem resolver o filme.

O critério de agregação de colisões molhadas, St = m v/(6πμa²) < St_c (Ennis; Donahue et al.), e as leis de ponte líquida de Grohn et al. (2020) ficam como referência para uma versão com contatos viscosos explícitos.

**Fusão na poça.** Com f_m ≥ 0,85 o pedaço sai do DEM e soma a massa ao inventário da poça [H]. O MFiX-DEM do NETL faz o mesmo com plástico fundido batendo em areia: a gota sai e passa massa e espécies para a partícula (Banerjee 2024).

## 3. A poça: viscosidade e forma

**Viscosidade.** Ela cai de 10²–10⁴ Pa·s para ~10⁻² Pa·s entre 360 e 410 °C, antes de haver perda de massa significativa. Fontes:

- Radhakrishnan et al.: PE numa rampa de 10 K/min.
- NIST TN 1493: fundidos de PP e PS degradados.
- D'Amato 2012: Mn do PEAD cai de 18,7 mil para ~500 g/mol em 3,5 h a 415 °C.

Valores [TC]:

| Fundido | Viscosidade |
|---|---|
| Poliolefina residual, 340–350 °C, 1–3 h (Eastman US 12,668,677) | 28–206 Pa·s |
| PP degradado a 373 °C | 1 Pa·s |
| PP degradado a 415 °C | 0,15 Pa·s |
| Ceras de PE a 149 °C | 7–130 mPa·s |
| Fundido já craqueado, 410–430 °C (valor central de ordem de grandeza) | ~3 mPa·s (0,4–9) |

**O que o modelo usa (`melt_viscosity`):**

- η₀ = 10³ Pa·s a 200 °C, com energia de ativação de fluxo de 30 kJ/mol. A literatura dá ~500 Pa·s para PEAD e 320–1440 Pa·s para PP a 200 °C [TC]; para PEAD, PEBD e PP, 25–50 kJ/mol [TC].
- Cisão aleatória: Mn/Mn₀ = 1/(1 + DPn₀·0,068·√α), com η ∝ Mn^3,4.
- Piso de cera: 18 mPa·s a 200 °C, com 22 kJ/mol, o que dá ~3 mPa·s a 420 °C [D].

**Forma da poça.** O regime do fundido num cilindro parcialmente cheio girando sai de λ = F²ρgR/(μΩ) (Ashmore, Hosoi e Stone 2003) [TC]:

| λ | Regime |
|---|---|
| < 2 | O fundido gira com a parede (filme) |
| 2–5 | Acumula no lado que sobe |
| > 5 | Poça plana no fundo, com um filme fino nas paredes |

A inclinação da superfície é ~atan(μU/(ρgH²)), com U = ΩR e H a profundidade [D]. No modelo ela é calculada a cada instante com Ω do tambor real e limitada a 30°. Na batelada de referência isso dá:

| Batelada | Viscosidade | λ | Inclinação |
|---|---|---|---|
| 2,3 h, logo após a fusão | ~3·10³ Pa·s | ≪ 1 | 30° |
| 2,6 h | ~660 Pa·s | ~1 | ~6° |
| ≥ 3 h, depois do craqueamento | ~1 → 0,003 Pa·s | — | Poça plana |

Sobre os pedaços imersos atuam o empuxo e o arrasto de Stokes. Areia de 2 mm decanta a 0,004 mm/s em 10³ Pa·s e a 43 mm/s em 0,1 Pa·s [D]. O carvão de madeira e papel tem densidade de envelope < 1 g/cm³ e boia no fundido (Masiello et al. 2012) [TC].

## 4. Carvão

- **Plásticos fundidos:** o carvão nasce na poça conforme o rendimento de carvão de cada polímero (`feed.py`). Aparece como grânulos de 3 cm, com densidade aparente de 420 kg/m³ [H].
- **Papel, madeira e borracha:** encolhem e escurecem até o carvão. O pinho a 900 °C guarda 19 % da massa e 30 % do volume (Ronewicz et al. 2017) [TC]. O modelo usa retração volumétrica de 0,45 (celulósicos), 0,55 (borracha) e 0,70 (PVC) [H].
- **Incrustação no casco:** é um problema conhecido (crosta de coque e carvão na parede quente; fornecedores citam "anticoqueamento"). Não há dados abertos de taxa. Uma crosta de ~1 mm por batelada, com k ≈ 0,15 W/m·K, somaria uma resistência da ordem de 10⁻² m²K/W [D/H]. Não está no modelo.

## 5. Lacunas

- Não há medida aberta de como o volume de um leito de plástico solto evolui ao ser aquecido, nem do enchimento antes e depois da fusão em reatores de batelada.
- Não há DSC a 1–5 K/min de filme de PEBD pós-consumo. O início da fusão vem de correlações para pós de PE.
- Não há viscosidade medida de fundido de PE/PP em degradação dentro de um reator de batelada ou rotativo a 380–450 °C. A curva do modelo junta fundidos capturados, liquefação a 340 °C e a cinética de cisão.
- As faixas de fusão, a retração, a coesão e o tamanho dos grânulos de carvão são hipóteses de ordem de grandeza. A validação do DEM confere massa, volume ocupado, ordem dos picos de taxa e a viscosidade antes e depois do craqueamento, não a forma dos pedaços.

## Fontes

Todas abertas ou com texto completo acessível.

- EUMEPS (2014). *EPS White Book*; *Behaviour of EPS in case of fire*.
- Fuss, US 5,286,321 (1994); Goehner, US 5,667,746 (1997): densificação de isopor e filme de PEBD por ar quente.
- Gonzalez-Aguilar et al. (2022). *Polymers* 14:4957.
- Rabello, Wellen (2008). *Rev. Eletr. Mater. Processos* 3.2:01–09: DSC do PET.
- Thomasset, US 8,333,055; Bouffand, EP 3 291 962: encolhimento do PET orientado.
- Rigaku, nota de aplicação B-TA1006: TG-DSC de microplásticos.
- Waschke et al. (2026). *Polymers* 18:1809: fusão de redes de pesca de PE e PP.
- Voelp, Bumajdad, Al-Salem (2025). *ACS Omega*: fusão de PEBD e PP.
- Hagerty et al., US 7,774,178 (Univation): temperatura de início de fusão e pegajosidade do PE.
- Equistar, US 8,637,607: encolhimento de filme de PE.
- Tomaszewska et al. (2022). *Materials* 15:8102: PVC rígido.
- Defra (2026). EPR para embalagens, Anexo C: densidade do material coletado solto.
- SK Innovation, US 12,296,504 (2025): rampa de um forno rotativo em batelada.
- Moreira et al. (2003). *Polímeros* 13(1):45–53: tensão superficial de fundidos.
- Zitzenbacher et al. (2018). *Polymers* 10:38: ângulo de contato de PP fundido sobre aço.
- Grohn et al. (2020). *Processes* 8:1090: pontes líquidas em DEM.
- Alvarez et al. (2021). *EPJ Web Conf.* 249:05001: sinterização em DEM.
- Banerjee (2024). NETL Multiphase Flow Workshop, OSTI 2569375.
- Ohlemiller, Shields (2008). NIST TN 1493: fundidos de PP e PS degradados.
- D'Amato (2012). Tese: degradação térmica de PEAD (Mn × tempo a 380 e 415 °C).
- Eastman, US 12,668,677: viscosidade de poliolefina residual em liquefação.
- Radhakrishnan et al. (Iowa State): viscosidade complexa do PE numa rampa de aquecimento.
- Ficha POLYWAX (Baker Hughes): viscosidade de ceras de PE.
- Ferrándiz et al. (2011). *J. Optoelectron. Adv. Mater.* 13(7):902: Cross-WLF do PP.
- Ashmore, Hosoi, Stone (2003). *J. Fluid Mech.* 479:65–98: escoamento num cilindro girando.
- Masiello et al. (2012). EGU2012-830; Ronewicz et al. (2017). *Drvna Industrija* 68(1):29–36: densidade do carvão vegetal.
