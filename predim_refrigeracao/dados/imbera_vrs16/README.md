# Imbera VRS16 (2024): dados para calibração

Produto de referência que a IMBERA passou para calibrar a rotina e o modelo do Amesim.

**Fontes** (a letra entre colchetes aparece em cada dado):

- **[E]** e-mail de Luiz Parigine (IMBERA) para Pedro Costa, em resposta a "[CAEXPERTS] Dados para calibração dos novos desenvolvimentos" (pedido de 10/11/2026, respostas recebidas em 23/11/2026).
- **[D]** datasheet do compressor Embraco VEMT404U, código 513903037, anexo ao mesmo e-mail.
- **[R]** fichas técnicas de revendas, consultadas em 23/11/2026:
  1. [Xiririca](https://xiririca.com.br/produto/refrigerador-imbera-vrs16-branco-bivolt/)
  2. [Acimaq](https://www.acimaq.com.br/refrigerador-vertical-vrs-16-inverter-branco-453l-porta-vidro-bivolt---imbera/p)
  3. [Líder](https://www.liderequipamento.com.br/refrigeradores/expositor-refrigerador-vrs16-454-litros-imbera)
  4. [Bamaq](https://www.bamaqbalancas.com.br/acougues/expositor-refrigerado/refrigerador-expositor-visa-cooler-454l-220v-imbera-vrs16-pt)
- **[C]** calculado por nós a partir dos dados acima.

Quando as fontes divergem, vale o e-mail [E].

## Gabinete

| Item | Valor | Fonte |
|---|---|---|
| Dimensões internas (L × A × P) | 590 × 1555 × 500 mm | [E]; [R] 1–3 iguais, [R] 4 diz 598 × 1559 × 487 |
| Dimensões externas (L × A × P) | 680 × 2048 × 619 mm | [E]; [R] dão profundidade de 603 mm (uma, 612) |
| Volume bruto / líquido | 485 L / 453 L | [E], [R] |
| Volume pelas dimensões internas | 459 L | [C] |
| Paredes | chapa de aço; espuma isolante "eco", sem CFC/HFC | [E], [R] |
| Espessura lateral total (chapas + espuma) | ≈ 45 mm, de (680 − 590)/2 | [C] |
| Porta | uma porta de vidro duplo, com autofechamento | [R] |
| Iluminação | LED superior, potência não informada | [R] |
| Prateleiras | 3 na versão de venda; 5 × 40 garrafas no ensaio | [R], [E] |
| Capacidade comercial | 240 garrafas PET de 600 mL; 530 latas de 350 mL | [R] |
| Peso líquido | 104 kg | [R] (uma revenda diz 95 kg) |

## Sistema de refrigeração

| Item | Valor | Fonte |
|---|---|---|
| Fluido / carga | R290 / **48 g** | [E] |
| Compressor | Embraco VEMT404U, velocidade variável (inversor CF03B01), 1200–4500 rpm | [D] |
| Deslocamento | 4,25 cm³ | [D] |
| Óleo | alquilbenzeno ISO 22, 220 mL | [D] |
| Capacidade nominal | 211 W e 1,44 W/W a 4500 rpm (−31,7 / 40,6 °C) | [D] |
| Mapa de desempenho | 156 pontos: 6 rotações × condensação a 35/45/55 °C × evaporação de −40 a 0 °C. Arquivo `compressor_VEMT404U.csv` | [D] |
| Condição do catálogo | sub-resfriamento 0 K, gás de retorno a 4,4 °C, EN 12900:2013 | [D] |
| Envelope de operação | evaporação de −40 a 0 °C; condensação de 20 a 60 °C (45 °C em −40 °C) | [D] |
| Tubos do compressor (DI) | sucção 6,5 mm; descarga 4,94 mm | [D] |
| Capilar | cobre, 2600 mm, "vazão 4,6 L/min a 5 bar" | [E] |
| Diâmetro interno do capilar | ≈ 0,78–0,80 mm (bitola comercial 0,031" = 0,787 mm), **a confirmar** | [C] |
| Trocador interno | capilar enrolado no tubo de retorno (sucção) | [E] |
| Condensador | aço; geometria não informada | [E] |
| Evaporador | alumínio, aletado; geometria não informada | [E], [R] |
| Ventiladores (evaporador e condensador) | motor de 15 W, 127/220 V, 50/60 Hz, 1500 rpm; desligam com o compressor | [E] |
| Outros componentes | nenhum (sistema básico: sem acumulador nem válvulas) | [E] |
| Tipo de refrigeração / degelo | ar forçado / manual (uma só fonte) | [R] |

**Conferência do mapa do compressor.** Em todos os 156 pontos, a capacidade publicada é igual a ṁ × Δh do R290 (CoolProp), dentro do arredondamento do catálogo. O Δh vai do gás de retorno a 4,4 °C ao líquido saturado na condensação. Isso confirma a condição de ensaio e a transcrição. O COP publicado também bate com capacidade ÷ potência em todos os pontos.

**Diâmetro do capilar.** A estimativa vem de escoamento adiabático de nitrogênio com atrito (Fanno, atrito de Churchill, tubo liso), 5 bar manométrico na entrada, 2,6 m e saída à atmosfera. Conforme a referência do L/min (0 °C ou 20 °C), sai D = 0,797 mm ou 0,777 mm. Falta confirmar o gás, se a pressão é manométrica e a referência da vazão.

## Controle

| Item | Valor | Fonte |
|---|---|---|
| Modo normal | SP1 = 2,8 °C, diferencial rd = 2,0 K | [E] |
| Modo standby (economia) | SPE = 6,5 °C, diferencial rEd = 2,0 K | [E] |
| Temperaturas alvo | 3,3 °C / 7,2 °C | [E] |
| Ventiladores | desligam com o compressor | [E] |
| Faixa de operação | 0 a +7 °C | [R] |

## Ensaio

| Item | Valor | Fonte |
|---|---|---|
| Carga | 200 garrafas de 600 mL (ou 400 latas de 350 mL), 5 prateleiras × 40 | [E] |
| Instrumentação | 26 termopares, nas posições do mapa de prateleiras do e-mail | [E] |
| Umidade relativa | 65 a 75 %, conforme o ensaio | [E] |
| Consumo publicado | 6,665 kWh/24h e 2,9 A a 220 V, com asterisco e sem a condição | [R] 4 |
| Norma citada | "55 % mais econômico que o modelo anterior", segundo a ISO 22044 | [R] 1 |

## O que ainda falta

Os quatro primeiros itens são as perguntas que o Luiz marcou em vermelho por não ter entendido. A [mensagem pronta](#mensagem-para-o-luiz) reescreve todas.

1. **Dados medidos no ensaio de pull-down.** Sem eles não há calibração.
2. **Divisão interna do gabinete:** caixa do evaporador, dutos e saída/retorno do ar.
3. **Curva ou vazão dos ventiladores.**
4. **Banda de histerese:** o rd = 2,0 provavelmente já é ela; falta confirmar o sensor e a lógica de rotação do inversor.
5. **Geometria do condensador e do evaporador:** sem ela a rotina só compara as ordens de grandeza.
6. **Condições do ensaio:** temperatura da sala, norma e classe climática, duração, aberturas de porta.
7. **Diâmetro interno do capilar** e comprimento do trecho soldado ou enrolado na sucção.
8. **Potências de iluminação e de resistência anti-embaçante,** se houver.
9. **Espessura da espuma** nas paredes, no fundo, no topo e na base.

## Mensagem para o Luiz

> Luiz, obrigado pelas respostas, ajudaram muito. Seguem as perguntas que ficaram em aberto, explicadas de outro jeito. Foto com trena, planilha exportada ou desenho servem.
>
> 1. **Ensaio de pull-down (o mais importante).** A planilha exportada do sistema de aquisição: os 26 termopares ao longo do tempo, potência ou corrente do compressor e, se houver, rotação do inversor e pressões. Junto, a temperatura e a umidade da sala, a duração e se a porta foi aberta.
> 2. **Divisão interna.** Onde ficam o evaporador e o ventilador (fundo ou topo), quanto espaço a caixa e os dutos ocupam, e por onde o ar frio sai e volta (grelhas). Uma foto do interior vazio com trena resolve.
> 3. **Ventiladores.** Se não houver curva, basta o modelo da hélice (diâmetro, número de pás) ou a vazão de ar do evaporador e do condensador.
> 4. **Controle.** O rd = 2,0 é o diferencial, ou seja, o compressor desliga a 2,8 °C e religa a 4,8 °C? Em qual sensor (ar de retorno, ar insuflado ou produto)? E como o inversor escolhe a rotação: fixa ou variando com a temperatura?
> 5. **Condensador e evaporador.** Número de fileiras e de tubos, diâmetro do tubo, passo e espessura das aletas, largura e altura da face. Para o condensador de aço: é aletado ou arame-sobre-tubo?
> 6. **Capilar.** Diâmetro interno, se tiverem. Se não, confirmar a vazão de 4,6 L/min: é de nitrogênio, a 5 bar manométrico? E qual o comprimento do trecho enrolado no tubo de retorno?
> 7. **Consumo e cargas internas.** Os 6,665 kWh/24h da ficha comercial: em qual condição e norma (ISO 22044, classe climática)? Potência do LED e de resistência anti-embaçante, se houver.
> 8. **Isolamento.** Espessura da espuma nas laterais, no fundo, no topo e na base (o CAD também serve).
