# Criando os casos no AI4Tech Suite

Guia para levar o splitter C3 para a plataforma. Dois casos, nesta ordem:
**primeiro o Python**, depois o DWSIM.

## Por que o Python Case vem primeiro

| | Python Case | DWSIM Case |
|---|---|---|
| Tempo por run | 22 ms | 2,5 a 8 s |
| DOE de 500 pontos | ~11 segundos | 20 min a 1 h |
| Consome quota | não significativa | sim |
| Erro conhecido | 0,006 ponto na pureza de topo | referência |

O gêmeo está validado contra a coluna rigorosa em cinco configurações. Isso
permite **aprender a plataforma inteira** — DOE, Analysis, Surrogate,
Optimization, MCDM — sem gastar quota nem esperar. Quando o DWSIM Case entrar,
ele entra com as faixas já escolhidas e um DOE pequeno e bem posicionado.

---

## ⚠️ A pegadinha do campo Cell

A documentação da suite dá o formato do Cell para DWSIM como
**`Mixer-001.Temperature`** — ou seja, **tag do objeto + propriedade**.

Isso é o **oposto** do que o DWSIM usa internamente. O `GETPROPVAL` do
Spreadsheet referencia por GUID:

```
=GETPROPVAL("MAT-9c4e4e77-638c-40c3-8607-0cd1fbd38802";"PROP_MS_0";"C")
```

As duas convenções têm comportamentos opostos ao renomear:

| | Sobrevive a renomear? | Sobrevive a recriar o objeto? |
|---|---|---|
| GUID (`MAT-9c4e…`) | ✅ sim | ❌ não |
| Tag (`DCOL-1.…`) | ❌ **não** | ✅ sim |

**Consequência: renomeie as correntes ANTES de criar o DWSIM Case.** Se você
configurar as variáveis e depois renomear, todos os caminhos quebram.

### Renomeie primeiro

As correntes estão com os nomes automáticos `1`, `3` e `4`. Além de quebradiço,
`3.MolarFlow` é ilegível. Antes de exportar o `.dwxmz`:

| Tag atual | Renomear para | O que é |
|---|---|---|
| `1` | `ALIM` | alimentação, 1000 kmol/h, 75/25, líquido saturado |
| `3` | `DEST` | destilado, propeno grau polímero |
| `4` | `FUNDO` | produto de fundo, propano |
| `DCOL-1` | manter | a coluna |

---

## Caso 1 — Python Case

1. Baixe [`casos-python/02-splitter-c3/simulate.py`](../casos-python/02-splitter-c3/simulate.py).
2. **＋ New ▾ → 🐍 New Python Case**.
3. Preencha:
   - **Case Name**: `splitter-c3-python`
   - **Description**: `Splitter propeno/propano, gemeo calibrado contra DWSIM 10.2.3.0`
   - **Python Script**: suba o `simulate.py`
4. Aguarde o status verde: *"Script valid — simulate() function found"*.

   > ⚠️ **O script não pode escrever no `stdout`.** A plataforma executa o
   > arquivo como subprocesso e lê o `stdout` para parsear o resultado como
   > JSON. Um `print()` no nível do módulo, ou num bloco
   > `if __name__ == "__main__"`, produz
   > `Dry run failed: Invalid JSON output from script` no Test Run. Os casos
   > deste repositório não têm bloco `__main__` por esse motivo, e o
   > `validar_caso.py` reprova o script se encontrar qualquer saída.
5. **Timeout**: deixe o padrão de 30 s. O caso roda em 22 ms, sobra folga de
   três ordens de grandeza.
6. Cadastre as entradas (tabela abaixo).
7. Clique **🧪 Test Run** — ele chama `simulate()` com os defaults e descobre as
   23 saídas sozinho.
8. **🐍 Create Python Case**.

### Entradas

| Name (dict key) | Unit | Type | Default | Min | Max | Step |
|---|---|---|---|---|---|---|
| `N_estagios` | - | Discrete | 200 | 100 | 260 | 10 |
| `pos_alimentacao` | - | Continuous | 0.5 | 0.3 | 0.7 | — |
| `razao_refluxo` | - | Continuous | 15 | 8 | 24 | — |
| `corte_pct` | % | Continuous | 99.5 | 97.0 | 99.9 | — |
| `pressao` | bar | Continuous | 18 | 14 | 22 | — |
| `z_propeno` | - | Continuous | 0.75 | 0.6 | 0.9 | — |
| `F_alimentacao` | kmol/h | Fixed | 1000 | — | — | — |

O nome **é** a chave do dicionário. Um typo aqui não dá erro: como o
`simulate()` usa o valor padrão para chave ausente, a variável simplesmente
não teria efeito nenhum no DOE. Falha silenciosa. Confira.

> ⚠️ **O campo numérico do wizard trunca em duas casas decimais.** Foi por isso
> que `corte_pct` está em porcento e não como fração: a faixa original de 0,970
> a 0,999 virava 0,97 a 0,99 sem nenhum aviso, cortando fora a região de maior
> recuperação — e o otimizador reportaria o teto artificial como ótimo.
> **Ao definir qualquer faixa, digite o valor, clique fora e confira se ele
> ficou.**

### Conferência do Test Run

O Test Run roda nos defaults. Confira estes valores antes de criar:

| Saída | Valor esperado |
|---|---|
| `pureza_topo` | 98,514 |
| `pureza_fundo` | 94,152 |
| `Q_refervedor` | 40,969 |
| `T_condensador` | 43,631 |
| `alfa_topo` | 1,076 |
| `convergiu` | 1 |

Se bater, o upload está íntegro.

---

## Caso 2 — DWSIM Case

Só depois de renomear as correntes.

1. No DWSIM, salve o flowsheet convergido (N = 301, alimentação no Stage150,
   R = 17,80) como `.dwxmz`.
2. **＋ New ▾ → 🔧 New DWSIM Case**.
3. **Case Name**: `splitter-c3-dwsim`, e suba o arquivo.
4. Configure as variáveis no Edit modal.
5. **Post-Solve Delay**: deixe em **0**. Nosso flowsheet não tem script interno
   rodando depois da convergência.

### O que dá e o que não dá para expor

| Variável | Objeto | Exponível? |
|---|---|---|
| Razão de refluxo | especificação do condensador | ✅ operacional |
| Vazão de fundo | especificação do refervedor | ✅ operacional |
| Pressão do condensador | parâmetro da coluna | ✅ operacional |
| Vazão de alimentação | corrente `ALIM` | ✅ propriedade de corrente |
| Composição da alimentação | corrente `ALIM` | ⚠️ verificar |
| **Número de estágios** | estrutura da coluna | ⚠️ provavelmente não |
| **Estágio de alimentação** | estrutura da coluna | ⚠️ provavelmente não |

Os dois últimos são **estruturais**, não propriedades operacionais. Se o
seletor não os oferecer, não é problema — é o recorte industrial correto:
**a coluna já existe, otimize a operação dela.** Mantenha N = 300 e alimentação
no meio fixos, e varie as cinco operacionais.

Nesse caso, no Python Case marque `N_estagios` e `pos_alimentacao` como
**Fixed** (300 e 0.5) para que os dois DOEs fiquem comparáveis variável a
variável.

### Não adivinhe os caminhos — verifique

O formato é `Objeto.Propriedade`, mas os nomes exatos das propriedades variam.
Duas fontes, nesta ordem:

1. **O seletor do Edit modal**, se houver. É a fonte autoritativa.
2. **O inventário** ([`ferramentas/dwsim_inventario.py`](../ferramentas/dwsim_inventario.py))
   no Script Manager, que lista objeto por objeto o que existe.

### A verificação que fecha tudo

Depois de configurar, faça um **Single Run com os defaults** no Simulator e
compare com o que já sabemos do flowsheet convergido:

| Saída | Valor conhecido |
|---|---|
| Propeno em `DEST` | 0,99700127 |
| Propano em `FUNDO` | 0,97502712 |
| Carga do condensador | 48 134,39 kW |
| Vazão de `DEST` | ~745 kmol/h |

**Se um valor voltar zero, vazio ou diferente, aquele caminho está errado.** É
o teste mais barato que existe — um run — e evita descobrir o erro depois de
300 simulações.

---

## Depois dos dois casos

| Etapa | Onde | Custo |
|---|---|---|
| DOE grande (1000 pontos, LHS) | Python Case | ~25 s |
| Analysis, Surrogate, Optimization, MCDM | sobre o Python | grátis |
| DOE pequeno (100–200 pontos) | DWSIM Case, worker local | horas |
| Comparação dos dois DOEs | Analysis | — |
| Validação do Pareto | DWSIM, poucos pontos | minutos |

E na hora de fechar o relatório: o Edit modal tem **📝 Download Report
Template**, que gera um `.docx` já preenchido com o nome do caso e as
definições de variáveis.
