# 04 — Pendências e perguntas ao cliente

> Log datado. Cada resposta que chegar entra aqui e é propagada para o doc temático.

## Perguntas técnicas abertas

### 1. ⭐ A que altura do fundo se mede a "velocidade próxima ao fundo"?
O critério é **≥ 0,3 m/s**, mas a cota de medição não foi informada. Muda o resultado:
a 5 cm ainda se está dentro da camada limite; a 20 cm já é escoamento livre.
Sem isso, o critério 2 não é verificável de forma objetiva.
**Propor:** adotar um plano a 10 cm do fundo e reportar também o perfil vertical, para o cliente
poder ler no critério dele. → afeta `02_dados_e_criterios.md` §4

### 2. Posição angular (em planta) da entrada e da saída
Entrada (cota 6,3 m) e saída (cota 6,0 m) estão **ambas no topo**. Se estiverem também
próximas em planta, o risco de curto-circuito é alto e independe do misturador.
→ afeta o ensaio de DTR (Etapa 4) e `03_metodo_cfd_e_analise_previa.md` §5

### 3. ⚠️ A entrada descarrega acima do nível do líquido — é intencional?
Cota da entrada 6,3 m contra nível útil de 6,0 m: são **30 cm de queda livre**.
Isso arrasta ar para dentro do reator, o que vai na direção contrária do critério 3
(evitar oxigênio na massa líquida). **Pode ser a fonte dominante de aeração, e não o misturador.**
Confirmar se a entrada é submersa na operação real ou se a cota é de flange.
→ afeta `03_metodo_cfd_e_analise_previa.md` §5

### 4. IVL de projeto e dado de sedimentação
A faixa informada (50 a 170 mL/g) vai de lodo bem sedimentável a lodo com tendência a bulking.
A velocidade de deriva do modelo de sólidos sai dessa correlação — qual valor adotar como projeto?
Existe velocidade de sedimentação medida?
→ afeta `03_metodo_cfd_e_analise_previa.md` §4

### 5. Reologia do lodo
Na ausência de dado, será adotado **comportamento newtoniano** (adequado à faixa de SST informada,
2,5 a 4,6 kg/m³). Confirmar se existe caracterização reológica.

### 6. Interferências internas e restrições de montagem
Tubulações, sensores, suportes dentro do tanque; acesso pelo topo, altura livre para montagem.
Afeta o espaço de projeto do DOE (altura de instalação do hiperboloide).

## Específicas da Opção B (se for a escolhida)
### 7. CAD 3D do misturador
Formato .step, .iges ou parasolid, **com a posição de instalação no reator**.
### 8. Rotação de operação (ou faixa) e potência nominal do acionamento

## Pendências internas (CAEXPERTS)
- [ ] **Revisão das propostas pelo Marcus** — enviadas em 21/09
- [ ] Decidir se este projeto fica em repositório **público** (ver nota no `README.md`)
- [ ] Levantar `Np` de misturador hiperbólico na literatura antes da Etapa 1

## Log de respostas
*(vazio — preencher conforme chegarem)*

| Data | Pergunta | Resposta | Propagado para |
|---|---|---|---|
