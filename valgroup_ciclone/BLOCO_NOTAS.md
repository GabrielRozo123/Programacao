# 📝 Bloco de notas — Valgroup (uso interno)

> Pontos levantados por nós que **ainda não foram passados ao Marcus**. Combinado em 13/10/2026:
> soltar aos poucos, para não sobrecarregar a conversa. Ao passar um item, mover para
> "Já passado" com a data.

---

## ✅ Desenho R01 recebido (06/11/2026) — geometria da rodada gerada

Arquivos do cliente: `Ciclone_DC307_3_vistas_R01.dwg` + PNG, `Criterios_e_observacoes_R01.txt`, memorial
`MC_VP_T-202 Rev.00` (ASME VIII Div.1) e apresentação do memorial. O cliente informou também que o
responsável anterior (Henrique) saiu e o Matheus pode atrasar outras informações.

**O que o desenho define (diâmetros INTERNOS):**
| item | desenho R01 | modelo anterior |
|---|---|---|
| corpo / cone | DI 307, H 460,5 / cone 767,5 | igual |
| entrada | 153,5 × 61,4, **cantos R15**, reto **307 preservado** (= 460,5 a partir do plano do eixo) | igual, cantos vivos |
| transição | **retângulo → círculo centrada, L = 100**, e = 4,75; semiângulo 24,9° em planta | — |
| tubo de entrada | **6" SCH40S, DI 154,08**, ponta de 50 mm (sem flange) | — |
| saída de gás | 6" SCH40S, DI 154,08, e 7,11, L 307 c/ flange | DI 153,5, e 4,75 |
| saída de pó | **4" SCH40S, DI 102,26**, e 6,02, L 153,5 → **muda a base do cone** (semiângulo 7,12° → 7,60°) | DI 115,13 |
| tampo | **12,70 mm** | 4,75 |

**Geometria gerada:** `simulacao/ciclone_Dc307_t4p75_Lr460_D154_Lt100_R01_ASSEMBLY.step` (fluido 87,16 L, sólido
11,0 L ≈ 87 kg de aço, ambos válidos, nenhuma face < 50 mm²). Comando no cabeçalho do `gen_ciclone_cht.py`.

**Decisões / pontos de atenção:**
- A transição **contrai** no sentido do escoamento (área do retângulo = 0,505 × a do tubo; laterais −24,9°, topo/fundo −0,2°):
  não há risco de descolamento por expansão; o jato acelera de ~12 para ~19 m/s antes do duto reto de 307 mm.
- **Cantos R15 não modelados** (cantos vivos, como no estudo anterior) para isolar o efeito da transição. R15 reduz a área
  da entrada em ~2 % → v_i +2 %, ΔP ~+4 %. Pode entrar numa rodada seguinte.
- Tubo de CFD a montante: 5·D = 770 mm (o real é uma ponta de 50 mm + tubulação desconhecida) — só afasta a BC.
- **Vortex finder:** o desenho não cota o mergulho interno; mantido S = 153,5 mm (0,5·Dc). Confirmar.
- Mudaram **três coisas** em relação ao modelo antigo (transição, saída de pó 102,26, bocais/tampo reais): a comparação
  de η e ΔP com o estudo anterior mistura os efeitos. Se precisar separar, rodar também a base com saída de pó 102,26 sem
  transição.
- Medir ΔP **estático e total** nos mesmos planos (fecha a pendência 3 400 × 2 910 Pa).
- Inserção de 8 mm (253,5 × 161,4, R30) é reforço externo da abertura: não entra no fluido.

## Pendentes — transição redondo-retangular na entrada (pedido de 13/10/2026)

**Pedido do Marcus:** a Valgroup quer encurtar o duto retangular de entrada ao mínimo do desenho
deles e colocar uma transição redondo-"quadrado". Adaptar o CAD, rodar de novo o escoamento,
passar ao Simas T e P nesse trecho e ver se a transição afeta a eficiência.

**Estado:** aguardando o desenho. O `simulacao/gen_ciclone_cht.py` já aceita a transição por
parâmetros (`--l-ret --d-tubo --l-trans --l-tubo --dx-tubo --dz-tubo --t-tubo`), testado.

1. **Eficiência — expectativa: sem impacto relevante.** d50 de 2–3 µm contra char a partir de
   ~61 µm: margem de 19× no pior cenário. A transição piora o perfil de entrada, não nessa ordem.

2. **O "mínimo possível" tem dois limites:**
   - **Geométrico:** a parede interna do duto só sai do casco em y ≈ 132 mm (medido do plano do
     eixo do ciclone). A transição não pode começar antes.
   - **Escoamento:** com tubo menor que 153,5 mm, a transição abre na vertical; acima de ~7,5°
     por lado, descola. Transição mínima: 4" Sch40 → ~195 mm · 5" Sch40 → ~95 mm ·
     6" Sch40 → sem restrição (só estreita).
   - Descolamento mexe no ΔP e na pressão local para o Simas, não na eficiência.

3. **"Redondo-quadrado":** a nossa entrada é **153,5 × 61,4 mm (2,5:1)**, não quadrada. Confirmar
   no desenho se a seção se mantém — se mudar, o ciclone muda (velocidade, ΔP, eficiência).

4. **Conferir no desenho:** Ø interno do tubo · comprimento da transição e do duto retangular (e
   de onde é medido) · eixo do tubo centrado ou não · espessura da transição · o que vem antes
   (reto ou curva).

5. **Cuidados na nova rodada:**
   - ΔP nos **mesmos planos** do modelo antigo, em **estática e total** — fecha também a
     pendência 3 400 × 2 910 Pa.
   - Lagrangeano com os mesmos ajustes. Com ~1 200 parcelas, η = 96,25 % tem ruído de
     ±0,55 pp (1σ): diferenças < ~1 pp não são separáveis do ruído. Se precisar, mais parcelas.
   - Conferir MM, µ e T de entrada do gás antes de rodar.
   - **Plano B de malha (só se precisar):** se o sólido de 4,75 mm der problema na transição
     (faces estreitas, cunhas), a parede pode ir como **shell** — espessura como propriedade, uma
     camada de células (tutorial STAR 05, `star_ccm_tutoriais/05_Parts_Based_Shells_Exhaust.md`).
     O Simas receberia T na superfície média. Não trocar se o sólido continuar funcionando.

## Anteriores — confirmar com o Gabriel se já foram passados

6. **Envelope de ΔP em k-ω.** Todo o envelope de 29–74 mbar foi levantado em k-ω; o relatório
   final (§5.1) diz que o k-ω subestima 18–39 %. Ver `simulacao/11_CHT_FEA_espessura_4p75.md` §2.
   Depende de fechar a convenção estática × total (item 5).

7. **Grau do aço:** e-mail diz AISI 304, memorial diz SA-240 304L. O Simas usou 304L
   (conservador). Confirmar com a Valgroup.

8. **Arranjo de apoios do ciclone** — sem ele o caso térmico do FEA não fecha.

9. **Particulado 10 × 80 kg/h** — a erosão escala linearmente; não exige re-rodar.

## Já passado

| data | item |
|---|---|
| — | — |
