# FOXTERMO — Cristalização de Óleo de Palma (Tanque com Serpentina + Agitador)

Estudo CFD de um **tanque de cristalização de óleo de palma** com **serpentina de imersão** (resfriamento)
e **agitador**. Cliente **FOXTERMO Refrigeração e Aquecimento LTDA** (via CAEXPERTS). Ferramenta: STAR-CCM+.

> **Status (2026-07-16):** oportunidade recebida (Álvaro Salla). Fase de **proposta**. Nada modelado.
> Marcus a avisar. Ver [`00_proposta_tecnica.md`](00_proposta_tecnica.md) e as pendências de dados.

## Contato
- **Álvaro Salla, BME** — FOXTERMO Refrigeração e Aquecimento LTDA
- CNPJ 20.032.287/0001-49 · alvaro.salla@foxtermo.com.br · (11) 98855-6006

## O pedido (e-mail do Álvaro, 16/07)
- Projeto de **cristalização de óleo de palma**. Tanque com **serpentina interna** (tubos curvados,
  imersão) + **agitador**. **Objetivo declarado: calcular as velocidades internas na serpentina.**
- **Água de torre de resfriamento circula DENTRO da serpentina**; **óleo de palma por FORA** (no tanque).
- **~4 simulações** com **densidade e viscosidade variando com a temperatura** e **possível variação da
  rotação do agitador**.

## Por que é um projeto rico (e onde já temos know-how)
| Ingrediente | Já dominamos em | 
|---|---|
| **Agitador (MRF)** | Ito (impelidor, potência/Np/Nq) |
| **Transferência de calor conjugada (óleo↔parede↔água)** | Condensador (h) + Valgroup (térmica) |
| **Propriedades fortemente dependentes da T (viscosidade)** | Sugar (xarope 6,5 Pa·s) |
| **Mudança de fase (cristalização)** | Condensador (mudança de fase) |

## Índice
| Doc | Conteúdo |
|---|---|
| [`00_proposta_tecnica.md`](00_proposta_tecnica.md) | Proposta: objetivo, escopo, metodologia, 4 cenários, entregáveis, dados a pedir |

## Log
- **2026-07-16** — Repo aberto. Oportunidade do Álvaro (FOXTERMO). Proposta técnica rascunhada; comercial
  (prazo/valor) fica com CAEXPERTS/Marcus. Lista de dados a pedir ao cliente montada.
