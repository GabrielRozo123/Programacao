# -*- coding: utf-8 -*-
"""
Inventario de objetos e propriedades do flowsheet ativo do DWSIM.

COMO USAR
  1. Abra o flowsheet no DWSIM.
  2. Va na aba Script Manager e crie um script novo.
  3. Cole este arquivo inteiro e execute.
  4. A saida aparece no painel de mensagens. Copie e me mande.

PARA QUE SERVE
  O campo "Cell" do AI4Tech Suite precisa de uma referencia ao objeto do
  flowsheet. Este script lista, para cada objeto, o nome interno, a tag visivel
  e todos os identificadores de propriedade (no formato PROP_MS_0, PROP_CO_3
  etc.), com valor e unidade. Sao esses os textos que qualquer camada de
  automacao — inclusive a suite — usa para ler e escrever no flowsheet.

ATENCAO
  Escrito de forma defensiva: nao foi testado contra o DWSIM 10.2.3.0 daqui,
  porque este ambiente nao tem DWSIM instalado. Se algum trecho falhar, ele
  informa o que falhou em vez de interromper — me mande a mensagem de erro que
  eu corrijo.

  Usa print() com uma unica string em todas as chamadas, para funcionar tanto
  em IronPython 2.7 quanto em IronPython 3.
"""

LARGURA = 78


def escrever(texto):
    print(texto)


def titulo(texto):
    escrever("")
    escrever("=" * LARGURA)
    escrever(texto)
    escrever("=" * LARGURA)


def obter_lista_propriedades(obj):
    """
    Devolve a lista de identificadores de propriedade do objeto.

    GetProperties espera um valor do enum PropertyType. O caminho de importacao
    do enum ja mudou entre versoes, entao tentamos as formas conhecidas e, em
    ultimo caso, varremos os inteiros e ficamos com a lista mais longa.
    """
    try:
        from DWSIM.Interfaces.Enums import PropertyType
        return list(obj.GetProperties(PropertyType.ALL)), "PropertyType.ALL"
    except Exception:
        pass

    try:
        import DWSIM.Interfaces.Enums as Enums
        return list(obj.GetProperties(Enums.PropertyType.ALL)), "Enums.PropertyType.ALL"
    except Exception:
        pass

    melhor, origem = [], "nenhuma"
    for valor in range(0, 6):
        try:
            candidato = list(obj.GetProperties(valor))
            if len(candidato) > len(melhor):
                melhor, origem = candidato, "GetProperties(%d)" % valor
        except Exception:
            continue
    return melhor, origem


def descrever_objeto(chave, obj):
    try:
        tag = obj.GraphicObject.Tag
    except Exception:
        tag = "(sem tag)"
    try:
        tipo = obj.GraphicObject.ObjectType.ToString()
    except Exception:
        tipo = "(tipo desconhecido)"

    escrever("")
    escrever("-" * LARGURA)
    escrever("TAG: %s" % tag)
    escrever("  nome interno : %s" % chave)
    escrever("  tipo         : %s" % tipo)

    propriedades, origem = obter_lista_propriedades(obj)
    if not propriedades:
        escrever("  >> nao consegui listar as propriedades deste objeto")
        return

    escrever("  propriedades : %d (via %s)" % (len(propriedades), origem))
    escrever("")
    escrever("    %-22s %18s  %s" % ("identificador", "valor", "unidade"))
    escrever("    %s" % ("-" * 60))
    for prop in propriedades:
        try:
            valor = obj.GetPropertyValue(prop)
        except Exception:
            valor = "(erro na leitura)"
        try:
            unidade = obj.GetPropertyUnit(prop)
        except Exception:
            unidade = ""
        escrever("    %-22s %18s  %s" % (prop, valor, unidade))


def principal():
    titulo("INVENTARIO DO FLOWSHEET — objetos e identificadores de propriedade")

    try:
        chaves = list(Flowsheet.SimulationObjects.Keys)          # noqa: F821
    except Exception as erro:
        escrever("FALHA ao iterar Flowsheet.SimulationObjects: %s" % erro)
        escrever("Me mande esta mensagem que eu ajusto o script.")
        return

    escrever("Objetos encontrados: %d" % len(chaves))

    for chave in chaves:
        try:
            obj = Flowsheet.SimulationObjects[chave]              # noqa: F821
        except Exception as erro:
            escrever("  falha ao obter '%s': %s" % (chave, erro))
            continue
        descrever_objeto(chave, obj)

    titulo("FIM DO INVENTARIO")
    escrever("Copie a saida inteira e mande — dela sai a tabela de variaveis")
    escrever("com o campo Cell no formato que a sua versao usa.")


principal()
