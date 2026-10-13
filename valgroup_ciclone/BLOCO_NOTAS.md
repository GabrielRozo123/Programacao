# 📝 Bloco de notas — Valgroup (uso interno)

> Pontos levantados por nós que **ainda não foram passados ao Marcus**. Combinado em 13/10/2026:
> soltar aos poucos, para não sobrecarregar a conversa. Ao passar um item, mover para
> "Já passado" com a data.

---

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
