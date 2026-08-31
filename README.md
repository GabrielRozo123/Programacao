# Programação — DWSIM + AI4Tech Suite

Repositório de estudos e projetos integrando **DWSIM** (simulação de processos)
com o **AI4Tech Suite** (plataforma web de PSE do Prof. Dr. Nicolas Spogis):
DOE, análise estatística, modelos surrogate, otimização mono e multiobjetivo,
MCDM e análise de operabilidade.

## Estrutura

```
casos-python/        Python Cases prontos para upload na plataforma
  _template/         Esqueleto comentado para criar um caso novo
  01-cstr-nao-isotermico/
                     CSTR com multiplicidade de estados estacionários
docs/
  roadmap-ai4tech.md Seis projetos propostos, em ordem de ambição
ferramentas/
  validar_caso.py    Validador e DOE local — rode antes de gastar quota
```

## Começando

```bash
# 1. Confira que o caso roda e produz saídas sadias
python3 ferramentas/validar_caso.py casos-python/01-cstr-nao-isotermico/simulate.py --n 200

# 2. Gere a tabela de variáveis para colar no wizard da plataforma
python3 ferramentas/validar_caso.py casos-python/01-cstr-nao-isotermico/simulate.py --tabela

# 3. Exporte um DOE local em CSV, se quiser comparar com o da nuvem
python3 ferramentas/validar_caso.py casos-python/01-cstr-nao-isotermico/simulate.py --n 500 --csv doe_local.csv
```

Nenhuma dependência externa: só Python 3.8+ e a biblioteca padrão.

## Princípios adotados aqui

**Zero dependências nos casos.** O worker que executa o Python Case pode não ter
numpy ou scipy. Um caso que só importa `math` nunca falha por ambiente.

**Validar local antes de subir.** Erro de unidade descoberto depois de 500 runs
na nuvem custa quota e paciência. O validador local roda o mesmo caso em
milissegundos por ponto.

**Metadados como fonte única da verdade.** Cada caso declara `VARIAVEIS` com
nomes, unidades, tipos e faixas. O validador gera o DOE e a tabela do wizard a
partir daí — a documentação não sai do lugar em relação ao código.

**Simulate nunca levanta exceção.** Em um lote de centenas de pontos, uma
exceção pode derrubar o lote inteiro. Entrada inválida devolve valores finitos
com `convergiu = 0`.

## Próximos passos

Ver [`docs/roadmap-ai4tech.md`](docs/roadmap-ai4tech.md).

## Referências

- [AI4Tech Suite — documentação](https://app.ai4tech.ai/help/)
- [DWSIM](https://dwsim.org)
