"""
Template de Python Case para o AI4Tech Suite.

Copie esta pasta, renomeie e substitua o modelo. A plataforma exige apenas uma
coisa: uma funcao de modulo chamada simulate que recebe um dict e devolve um
dict. Todo o resto deste arquivo e convencao nossa, para que a ferramenta
ferramentas/validar_caso.py consiga gerar DOE e tabelas automaticamente.

    def simulate(inputs: dict) -> dict

Regras que evitam dor de cabeca na plataforma
---------------------------------------------
1. ZERO DEPENDENCIAS externas sempre que possivel (so a biblioteca padrao).
   O worker que executa o caso pode nao ter numpy/scipy instalados.
2. NUNCA levante excecao dentro de simulate(). Em um lote de DOE com centenas
   de pontos, uma excecao pode derrubar o lote inteiro. Devolva valores finitos
   com uma flag de convergencia igual a zero.
3. SEMPRE devolva as mesmas chaves, em qualquer cenario. A plataforma le as
   saidas pelo nome (o campo Cell); uma chave ausente vira falha de leitura.
4. So devolva numeros (int/float). Nada de None, string, lista ou NaN.
5. Aceite entradas ausentes usando os valores padrao — assim variaveis marcadas
   como Fixed no wizard continuam funcionando.
"""

import math  # noqa: F401 — disponivel para o seu modelo


# --------------------------------------------------------------------------
# Constantes do modelo (nao entram no DOE)
# --------------------------------------------------------------------------
CONSTANTE_EXEMPLO = 1.0


# --------------------------------------------------------------------------
# Metadados — fonte unica da verdade para o wizard e para o validador local.
# Os campos "nome" viram a coluna Cell no cadastro de variaveis da plataforma.
# --------------------------------------------------------------------------
VARIAVEIS = {
    "descricao": "Descreva aqui o que este caso simula",
    "entradas": [
        {"nome": "x1", "unidade": "-", "tipo": "Continuous",
         "padrao": 1.0, "min": 0.0, "max": 10.0,
         "descricao": "Primeira variavel manipulada"},
        {"nome": "x2", "unidade": "-", "tipo": "Discrete",
         "padrao": 4.0, "min": 2.0, "max": 10.0, "passo": 2.0,
         "descricao": "Variavel inteira, por exemplo numero de estagios"},
        {"nome": "x3", "unidade": "-", "tipo": "Fixed",
         "padrao": 2.5,
         "descricao": "Mantida constante — nao entra no DOE"},
    ],
    "saidas": [
        {"nome": "y1",        "unidade": "-", "descricao": "Resposta principal"},
        {"nome": "y2",        "unidade": "-", "descricao": "Resposta secundaria"},
        {"nome": "convergiu", "unidade": "-", "descricao": "1 = sucesso, 0 = falha"},
    ],
}


def simulate(inputs):
    """Recebe as entradas da plataforma e devolve as saidas do modelo."""
    padroes = {v["nome"]: v["padrao"] for v in VARIAVEIS["entradas"]}
    val = {nome: float(inputs.get(nome, padrao)) for nome, padrao in padroes.items()}

    # Resposta padronizada em caso de entrada invalida — nunca levantar excecao.
    falha = {saida["nome"]: 0.0 for saida in VARIAVEIS["saidas"]}

    if val["x1"] < 0.0:
        return falha

    # ------------------------------------------------------------------
    # Substitua daqui para baixo pelo seu modelo.
    # ------------------------------------------------------------------
    y1 = CONSTANTE_EXEMPLO * val["x1"] ** 2 + val["x2"] * val["x3"]
    y2 = math.sin(val["x1"]) * val["x2"]

    return {"y1": y1, "y2": y2, "convergiu": 1.0}


if __name__ == "__main__":
    for chave, valor in simulate({}).items():
        print("{:<12} = {:.6g}".format(chave, valor))
