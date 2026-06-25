# Status dos Projetos — CAExperts

> Atualizado: 2026-06-25

---

## 1. GreyBeer — Chiller Tank (CFD Estratificação Térmica)

**Cliente:** GreyLogix | **Contato:** Pedro Costa  
**Status:** Simulação transiente rodando no Star-CCM+

### Arquivos principais
- `_arquivo/chiller/generate_chiller_tank_v3_dual_lateral.py` — script de geometria (versão ativa)
- `_arquivo/chiller/chiller_tank_fluid_v3.step` — domínio fluido (86 KB, OCCT valid, 13 faces)

### Geometria (v3 — dual lateral)
- Tanque cilíndrico com fundo cônico: D=4210 mm, H_cil=4720 mm, H_cone=780 mm
- Volume: ~69.3 m³ (solução hidroalcóolica 70% água + 30% etanol)
- Inlet (do chiller, −5°C): parede lateral, z=1641 mm, DN150
- Outlet (para o chiller): parede lateral, z=1116 mm, DN150
- BCs: inlet → Mass Flow Inlet (ṁ=3.109 kg/s), outlet → Pressure Outlet, resto → Wall

### Resultados parciais (~t=20h)
- Física: **estratificação filling-box** (Baines & Turner 1969), NÃO curto-circuito
- T_outlet = −4.26°C, T_bulk = −0.49°C, T_topo = +3.5°C, T_fundo = −4°C
- CSTR preveria T_bulk = −4.7°C → real é 9× mais lento
- Q decaiu de 113 kW → 7.57 kW em t=81,330 s
- Recomendação: usar T_topo < −4.5°C como critério de desligamento do chiller

### Pendente
- [ ] Aguardar simulação completar resfriamento total (estimado >40h total)
- [ ] Capturar T(z) final e T_bulk(t) para slides do Pedro
- [ ] Confirmar com Pedro Costa critério de shutdown

---

## 2. Valgroup — Ciclone (Separação Gás-Sólido)

**Cliente:** Valgroup | **Contatos:** Marcus Castro Neves, Daniel  
**Status:** Aguardando dados de processo para dimensionamento

### Arquivos principais
- `valgroup_ciclone/matriz_decisao/gerar_matriz_decisao.py` — matriz de decisão (matplotlib)
- `valgroup_ciclone/literatura/revisao_tecnologias_separacao.md` — revisão tecnológica
- `valgroup_ciclone/literatura/pecanha_ciclone_lapple.md` — equações do modelo Lapple (Peçanha)

### Decisão
- 6 tecnologias × 9 critérios → **Ciclone vence (+9 pontos)**

### Dimensionamento (a fazer)
- Modelo: Lapple (eqs. 3.86–3.113 de Peçanha)
- Equação chave: D_c = f(Q, ρ_g, ρ_p, μ, d_p50) via eq. 3.113
- Precisará de: composição do gás → Peng-Robinson EOS → ρ_g, μ

### Pendente
- [ ] Receber planilha de composição do gás (Marcus/Daniel)
- [ ] Calcular propriedades do gás via Peng-Robinson
- [ ] Rodar dimensionamento Lapple
- [ ] Gerar geometria STEP do ciclone para Star-CCM+

---

## 3. Braskem PE5 — DEM Rosca Transportadora

**Cliente:** Braskem S.A. — Unidade PE5 (RS) | **Contatos:** Marcus Castro Neves, Jeferson Diefenthaler  
**Status:** Proposta enviada ao Marcus

### Arquivos principais
- `braskem_pe5/Proposta_Braskem_PE5_DEM.xlsx` — proposta comercial (ativa)
  - Aba `Proposta`: Objetivo, Escopo, Cronograma, Requisitos, Entregáveis, Quem Somos
  - Aba `Cronograma`: horas por atividade (Marcus=8h, Gabriel=38h)

### Proposta — resumo técnico
- Simulação DEM (Star-CCM+) de rosca transportadora com PEAD + hexano
- Física: Hertz-Mindlin + Liquid Bridge Force (Lian, 1993)
- 2 cenários: rosca padrão (pá helicoidal contínua) e rosca cut-flight
- Prazo: 25 dias | Entregável: relatório .ppt

### Dados necessários (Jeferson)
- Diâmetro externo da pá (D_screw, mm)
- Diâmetro do eixo (D_shaft, mm)
- Passo da hélice (pitch, mm)
- RPM de operação
- Granulometria do PEAD (D10, D50, D90) ou confirmação de semelhança com talco
- Densidade aparente (bulk density, kg/m³)
- Localização do embuchamento (início/meio/fim)
- Desenho técnico ou croqui com cotas

### Pendente
- [ ] Marcus revisar HH e aprovar proposta
- [ ] Receber dados operacionais do Jeferson
- [ ] Confirmar geometria e iniciar setup DEM

---

## Contatos rápidos

| Pessoa | Empresa | Projeto |
|---|---|---|
| Pedro Costa | GreyLogix | Chiller |
| Marcus Castro Neves | CAExperts | Valgroup + Braskem |
| Daniel | Valgroup | Ciclone |
| Jeferson Diefenthaler | Braskem PE5 | DEM rosca |
