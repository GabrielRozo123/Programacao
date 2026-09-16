# Base normativa para o dimensionamento e para o CFD

> **Grau de confiança.** O que está marcado **[verificar]** é valor ou referência
> que eu conheço de prática corrente mas que varia entre edições e entre fontes.
> Nada aqui substitui abrir a norma. Os itens sem marca são estruturais e não
> mudam de edição para edição (o que a norma cobre, e o que ela não cobre).

---

## 1. A pergunta certa antes de escolher a norma

Nenhuma norma de separador entrega as duas coisas ao mesmo tempo:

| O que se quer | Quem entrega |
|---|---|
| Uma velocidade máxima de gás | GPSA (fator K), NORSOK, DEPs de licenciadores |
| Um diâmetro de gota a remover | API 521 (tocha), algumas DEPs |
| Um critério de aceitação para CFD | **ninguém** |

Essa terceira linha é a que importa para o estudo. Não existe norma que diga "sua
simulação deve mostrar X". O critério de aceitação do CFD tem que ser **construído
e acordado com o cliente antes de rodar**, e a única forma de ele ser defensável é
ancorá-lo num número que a norma já dá. A seção 5 propõe como.

---

## 2. Dimensionamento de processo

### GPSA Engineering Data Book, Seção 7 — *Separators and Filters*
A referência de facto do fator K. É de onde vem o 0,35 ft/s.

- K = 0,35 ft/s (0,107 m/s) para vaso vertical com tela de malha, P ≲ 100 psig **[verificar]**
- Redução de 0,01 ft/s a cada 100 psi acima de 100 psig **[verificar]** — algumas
  edições trazem tabela ponto a ponto em vez da regra linear
- Sem eliminador de névoa: cerca de metade **[verificar]** (faixa citada 0,15–0,20 ft/s)
- Horizontal: majoração de ~1,25 sobre o K vertical **[verificar]**

**Não é norma.** É livro de referência da Gas Processors Association. Tem peso
enorme na prática, mas se o contrato exigir "conforme norma", GPSA sozinho não
fecha — precisa vir junto com a especificação do cliente.

### API STD 521 — *Pressure-relieving and Depressuring Systems*
A que governa vaso de nocaute de tocha, e a única da lista que prescreve **diâmetro
de gota** em vez de fator K. Faixa típica de remoção: 300 a 600 µm **[verificar a
edição vigente]**. É metodologicamente superior ao K porque o critério é físico e
verificável — e por isso é o melhor gancho para amarrar o CFD (seção 5).

### API SPEC 12J — *Oil and Gas Separators*
Origem em campo de produção, não em petroquímica. Traz K e tempos de retenção.
Útil como fonte cruzada; raramente é a norma contratual numa planta como a Braskem.

### NORSOK P-002 — *Process System Design*
Norueguesa, mas muito usada fora. É a fonte aberta mais citável para os critérios
de **ρv² no bocal de entrada**, que são o parâmetro que o estudo de CFD vai atacar.
Valores usuais **[verificar]**, em lb/(ft·s²):

| Dispositivo de entrada | ρv² |
|---|---|
| Sem dispositivo (bocal nu) | 1000–1500 |
| Chapa defletora | 3000–6000 |
| Meia-cana aberta | 5000–6000 |
| Palhetas (vane) | 6000–10000 |
| Ciclônico | 10000–15000 |

### DEPs de licenciador (Shell DEP 31.22.05.11-Gen e equivalentes)
Proprietárias. Se a unidade tem licenciador, é a DEP dele que manda, e ela
normalmente é mais restritiva que GPSA. **Pergunte ao cliente qual é antes de
fixar qualquer K** — é a pergunta que evita refazer o trabalho.

---

## 3. A máquina a jusante

### API STD 617 — compressores centrífugos
Exige gás isento de líquido na sucção, mas **não prescreve K nem vaso**. É o
documento que justifica rebaixar o K por severidade de consequência, não o que
fornece o número. O número vem da prática ou da DEP.

### API STD 618 — compressores alternativos
Mais severo ainda quanto a líquido: em alternativo, arraste é dano imediato.

Em ambos vale a mesma leitura: a norma da máquina cria a **obrigação**, a norma de
processo fornece o **método**, e nenhuma das duas verifica se o método funcionou.

---

## 4. Mecânico e regulatório — o lado brasileiro

| Documento | Papel |
|---|---|
| **ASME BPVC Seção VIII Divisão 1** | Projeto mecânico: espessura, bocais, reforços |
| **NR-13** (MTE) | **Regulatória e obrigatória no Brasil.** Vasos de pressão: categorização, inspeção, prontuário, profissional habilitado |
| **ABNT NBR 16035** (série) | Adoção brasileira do ASME BPVC **[verificar qual parte se aplica]** |
| Padrão do proprietário | Braskem tem o seu. Pedir. É o documento que realmente vale |

NR-13 não afeta o dimensionamento de processo, mas afeta o **entregável**: o vaso
vai precisar de prontuário e de responsável técnico. Vale saber disso antes de
prometer escopo.

---

## 5. Como amarrar o CFD a uma norma de verdade

A proposta, em três critérios. O primeiro dá legitimidade normativa, o segundo é
o que o cliente quer de fato, o terceiro é o que só o CFD consegue responder.

**Critério 1 — âncora normativa (adaptado da API 521).**
Fixe um diâmetro-alvo `d_alvo` e exija remoção ≥ 99% em massa das gotas com
`d ≥ d_alvo`. Para `d_alvo`, use o **diâmetro implícito no K adotado**, que o
módulo calcula. Isso transforma o K numa afirmação falseável: em vez de "o vaso
atende ao K de 0,25 ft/s", passa a ser "o vaso remove 99% das gotas acima de
366 µm", que uma simulação pode confirmar ou desmentir.

**Critério 2 — arraste absoluto.**
Vazão mássica de líquido que sai pelo bocal de gás, em kg/h, comparada ao limite
do fabricante do compressor. Valor de prática às vezes citado para saída de
eliminador de névoa: 0,1 gal/MMscf **[verificar — peça o limite ao fabricante da
máquina, é ele quem define]**.

**Critério 3 — o que só o CFD entrega, e o assunto do post.**
Fração da área da face do demister (ou da seção a meia altura) onde a velocidade
vertical local ultrapassa o `v_max` de Souders-Brown.

O método clássico dimensiona pela **média**: `v = Q/A ≤ v_max`. Mas a tela do
fabricante tem limite de carga **local**, e o líquido vai embora pelo local. Se
30% da área da seção está acima do `v_max` enquanto a média está a 99% dele, o
vaso está fora de critério num sentido que nenhuma planilha consegue enxergar — e
está formalmente dentro da norma.

É esse número que fecha o post: *o vaso está corretamente dimensionado pela norma
e ainda assim arrasta, porque a norma dimensiona pela média e o líquido vai embora
pelo local.*

---

## 6. O que pedir ao cliente antes de começar

1. Qual a especificação/DEP de separador aplicável (a resposta define o K)
2. Balanço de massa e energia da corrente de entrada: P, T, composição, Z, vazão por fase
3. Propriedades de transporte do simulador de processo (µ do gás, ρ e σ do líquido)
4. Limite de arraste do fabricante do compressor (critério 2)
5. Folha de dados do eliminador de névoa, se houver — inclusive a curva de
   carga/inundação, que é o que torna o critério 3 verificável
6. Casos de operação além do normal: partida, mínimo, máximo, alívio
