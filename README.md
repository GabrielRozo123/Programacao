# Projeto Industrial de Trocador de Calor Casco e Tubo

Este projeto foi evoluído para um formato **mais próximo da prática industrial de anteprojeto**, removendo simplificações grosseiras e incorporando correlações clássicas de projeto térmico e hidráulico.

## O que foi melhorado

- Banco de dados de fluidos em arquivo dedicado (`fluids_db.json`) com propriedades em função da temperatura.
- Interpolação de propriedades (`ρ`, `cp`, `μ`, `k`) por temperatura de bulk e parede.
- Lado tubo com:
  - **Gnielinski** para turbulento.
  - **Sieder-Tate** para laminar em desenvolvimento térmico.
  - Fator de atrito **Churchill** para queda de pressão.
- Lado casco com estrutura **Bell-Delaware**:
  - `h_ideal` por fator `j` em banco de tubos.
  - fatores de correção (`Jc`, `Jl`, `Jb`, `Jr`, `Js`).
- `Uo` limpo/sujo com resistência da parede do tubo e incrustações.
- Queda de pressão no casco com abordagem Bell-Delaware (ideal + correções).
- Otimização automática de múltiplas geometrias.
- Geração de **dashboard gráfico** (estilo executivo) com score, `U`, perda de carga e razão de área.

## Estrutura

- `heat_exchanger.py`: motor de cálculo e CLI.
- `fluids_db.json`: banco de dados de propriedades dos fluidos.
- `artifacts/heat_exchanger_dashboard.png`: dashboard gerado (quando `--plot` é usado).

## Como executar

```bash
python3 heat_exchanger.py
```

Com dashboard gráfico:

```bash
python3 heat_exchanger.py --plot
```

Com banco de dados customizado:

```bash
python3 heat_exchanger.py --db meu_banco.json --plot
```

## Observações importantes

- O software já está em nível robusto de **engenharia preliminar**.
- Para projeto de fabricação final, ainda é recomendado complementar com:
  - validação por TEMA/ASME aplicável,
  - checagem mecânica (espessura, vibração, expansão térmica),
  - propriedades termofísicas acopladas ao perfil local de temperatura por segmento.
