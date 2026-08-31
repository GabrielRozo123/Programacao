# Python Cases

Cada subpasta é um caso pronto para subir na plataforma em
`Projects → ＋ New ▾ → 🐍 New Python Case`.

| Caso | Tema | Estado |
|---|---|---|
| [`_template/`](_template/simulate.py) | Esqueleto comentado para casos novos | — |
| [`01-cstr-nao-isotermico/`](01-cstr-nao-isotermico/CONFIG.md) | CSTR exotérmico com multiplicidade de estados estacionários | pronto |
| [`02-splitter-c3/`](02-splitter-c3/CONFIG.md) | Splitter propeno/propano, com dimensionamento e economia anual | pronto |

## O contrato da plataforma

O AI4Tech Suite exige uma única coisa do arquivo `.py`:

```python
def simulate(inputs: dict) -> dict
```

As chaves do dicionário de entrada e de saída são o campo **Cell** no cadastro
de variáveis. Nome no wizard e chave no código precisam bater exatamente.

## Cinco regras que evitam retrabalho

1. **Zero dependências externas.** O worker pode não ter numpy ou scipy.
2. **Nunca levante exceção dentro de `simulate()`.** Em um lote de DOE, uma
   exceção pode derrubar centenas de pontos. Devolva `convergiu = 0`.
3. **Sempre as mesmas chaves de saída**, em qualquer cenário — inclusive no
   caminho de falha. Chave ausente vira erro de leitura na plataforma.
4. **Só números finitos.** Nada de `None`, string, lista ou `NaN`.
5. **Aceite entradas ausentes** usando o valor padrão, para que variáveis
   marcadas como `Fixed` no wizard continuem funcionando.
6. **Nunca escreva no `stdout`.** A plataforma executa o script como
   subprocesso e lê o `stdout` para parsear o resultado como JSON. Um `print()`
   no nível do módulo — ou num bloco `if __name__ == "__main__"` — corrompe
   essa saída e produz `Dry run failed: Invalid JSON output from script`.
   Por isso nenhum caso aqui tem bloco `__main__`: para rodar localmente,
   use `ferramentas/validar_caso.py`, que já faz um run com os padrões.

O validador local checa as regras 1, 2, 4 e 6 automaticamente.

## Criando um caso novo

```bash
cp -r casos-python/_template casos-python/02-meu-caso
# edite simulate.py: ajuste VARIAVEIS e substitua o modelo
python3 ferramentas/validar_caso.py casos-python/02-meu-caso/simulate.py --n 200
```

O bloco `VARIAVEIS` é a fonte única da verdade: o validador tira dele o DOE
local e a tabela de variáveis para o wizard.
