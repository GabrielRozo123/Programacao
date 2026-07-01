# O que pedir sobre a geometria (Sugar) + estratégia CFD

> O CAD recebido é modelo Plant 3D detalhado (centenas de peças: parafusos, flanges,
> niples...). Para CFD isso NÃO serve direto. Este doc lista o que pedir e a estratégia.
> Atualizado: 2026-07-01.

## Princípio: CFD precisa do DOMÍNIO FLUIDO, não do hardware
Ignora-se parafuso/flange/estrutura. Só importa o **volume interno oco** por onde o
fluido passa. Estratégia: **construir domínio fluido limpo** a partir de cotas-chave
(geometria paramétrica, como no chiller) — não malhar o assembly cru.

## Peças do ejetor que definem o CAMINHO DO FLUIDO (as únicas que importam)
- **01 - BICO** (×4) = bocais / **venturi** ⭐
- **FECHAMENTO DA CAMARA** (+ INFERIOR) = câmara de mistura
- **REDUCAO CONCENTRICA** = mudanças de área
- **TUBO AC** = lanças (canal interno)
- **TAMPA HEADER** = manifold
Ignorar: Flange Solto, Parafuso, bos-us (weld boss), Hexagon Nipples = ferragem.

## LISTA DO QUE PEDIR (Jadir / Marcus Ito)
1. **Desenho de conjunto / GA cotado** (2D com cotas internas) — ejetor E tanque ⭐
2. **Perfil do BICO (venturi):** Ø garganta, Ø entrada, Ø saída, ângulos conv./div.
3. **Bicos de ar (1 mm):** quantidade e posição de injeção do ar comprimido
4. **Câmara de mistura:** Ø e comprimento
5. **Lança:** Ø INTERNO e comprimento
6. **Tanque aerador:** Ø interno, altura do cilindro, altura/ângulo do cone, nível de
   líquido (transbordo), **profundidade de penetração das lanças**, quebra-ondas, transbordo
7. (Ideal) modelo do **domínio fluido** já simplificado, se existir
+ Curva **vazão × pressão do ar** (já pedida no kick-off) — parâmetro do ejetor

## Plano B (se não vier GA cotado)
Medir no visualizador/Star (como o flange já medido, ×10):
- Isolar BICO → medir garganta, entrada, saída
- Isolar CAMARA → Ø, comprimento
- Isolar TUBO → Ø interno, comprimento
Com essas medidas, construímos o domínio fluido paramétrico (CadQuery/3D-CAD).

## Próximo passo
Reunir cotas → construir domínio fluido limpo (venturi + câmara + lança + tanque) →
malha → CFD multifásico (geração de bolha + flotação no meio viscoso).
