# Roteiro do estudo no Simcenter STAR-CCM+

O cartão de configuração com todos os números sai de
`python3 scripts/relatorio_caso.py`. Este documento é a ordem em que fazer as
coisas e, principalmente, **onde parar e conferir**.

---

## Fase 0 — Teste de verificação (antes de qualquer geometria)

Caixa fechada, gás parado, gravidade ligada, uma classe de gota, acoplamento de
uma via. Solte a gota e leia a velocidade assintótica.

Compare com a tabela da seção 7 do cartão. **Tolerância: 1%.** Se não bater, pare
o estudo e conserte a configuração. As três causas, em ordem de frequência:

1. `Gravity` ligado no continuum e **ausente** na lista de forças da fase
   lagrangiana. A gota flutua, o caso "converge", o resultado não significa nada.
2. Lei de arrasto no solver diferente da que gerou a tabela. Regere a tabela com
   a mesma lei — `tabela_de_velocidades_terminais(..., lei="...")`.
3. Passo de tempo do tracking grande demais para a menor classe. O tempo de
   relaxação da gota é `τ = ρ_L d² / (18 µ_G)`; para 10 µm no caso do propeno isso
   dá ~5 ms. O passo tem que ser uma fração disso.

Este teste custa 20 minutos e é o único motivo pelo qual alguém deveria acreditar
no resultado final.

---

## Fase 1 — Campo de gás

Geometria pelas cotas do cartão. Nível de líquido (HLL) como parede — não é
VOF, não é euleriano multifásico. Só a fase gasosa.

RANS estacionário, k-ω SST. Resolva até convergir **antes** de pensar em gotas.

Estudo de malha: três níveis, fator ~1,5 entre eles. A grandeza a monitorar não é
a perda de carga — é o **perfil de velocidade vertical na seção a meia altura**,
porque é dele que sai o resultado do estudo. Se o perfil ainda muda entre o nível
médio e o fino, a malha não está pronta, mesmo que os resíduos estejam ótimos.

**Se os resíduos estagnarem e os monitores oscilarem com amplitude estável, isso é
física.** O jato de entrada num vaso grande tende a bater e oscilar; a solução
estacionária pode simplesmente não existir. Use o campo estacionário como condição
inicial e passe para URANS. Não aumente relaxação para "forçar convergência" — isso
só esconde o fenômeno que você está tentando medir.

---

## Fase 2 — Rastreamento lagrangiano

Com acoplamento de uma via as gotas não alteram o gás, então o tracking roda sobre
o campo congelado: **um campo de gás, dez rodadas de tracking**. A varredura de
classes fica barata.

Para cada classe da varredura (10 a 500 µm), extraia:

```
η(d) = massa capturada (parede + superfície de líquido)
       ──────────────────────────────────────────────────
                    massa injetada
```

Rode **com e sem dispersão turbulenta**. A diferença entre as duas curvas é, por
si só, metade do conteúdo do post: sem dispersão as gotas seguem a linha de
corrente média e a eficiência sai otimista.

Com dispersão ligada o resultado é estocástico. Parta as parcelas em duas metades
e compare η. Diferença acima de ~1 ponto percentual significa que faltam parcelas,
não que o resultado é esse.

---

## Fase 3 — Os dois resultados que viram post

**Resultado 1 — curva de eficiência por tamanho de gota.**
`graficos.figura_eficiencia(dim, caminho, cfd=(diametros_um, eficiencias))`
já aceita os dados do CFD e sobrepõe à previsão clássica. O contraste entre o
degrau e a curva real é o argumento.

**Resultado 2 — contorno de velocidade vertical numa seção a meia altura, com a
linha do `v_max` de Souders-Brown marcada.**

Este é o mais visual e o mais difícil de contestar. Reporte junto o número:
**fração da área da seção onde a velocidade local excede o `v_max`**, com a
velocidade média abaixo dele. É o critério 3 da base normativa, e é o que
transforma uma imagem bonita em resultado de engenharia.

---

## Sobre o demister

Não modele a tela como geometria resolvida. Duas opções honestas:

1. Meio poroso com resistência inercial calibrada pela perda de carga do fabricante.
2. Terminar o domínio na base da tela e reportar a distribuição de velocidade e de
   gota **que chega nela**.

A opção 2 é mais defensável e é a que responde à pergunta certa: a tela do
fabricante tem limite de carga local, e a média não diz se ele foi violado.

---

## Sobre os tutoriais

Sim, mande. O que mais ajuda, na ordem:

1. Qualquer tutorial da seção **Multiphase Flow** que use **Lagrangian Multiphase**
   com injetor e condições de contorno de partícula (`Escape` / `Trap`) — é o
   esqueleto exato do nosso caso.
2. Um que configure **Turbulent Dispersion** na fase lagrangiana, se houver.
3. Um de **injetor com distribuição de tamanho** (Rosin-Rammler), para a sintaxe
   do painel — mesmo que a gente vá usar monodisperso na varredura.

O que **não** precisa: tutoriais de VOF, de euleriano multifásico e de spray com
evaporação. São o caminho errado para este problema e só vão custar tempo.

Se você tiver um `.sim` de vaso separador já montado de algum trabalho anterior,
mesmo de outro serviço, vale mais que os três tutoriais juntos.
