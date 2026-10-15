import json

import pytest

from predimref import EntradasProjeto, ErroProjeto, ParametrosProjeto, dimensionar
from predimref.ciclo import ParametrosCiclo


@pytest.fixture(scope="module")
def res():
    return dimensionar(EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0))


def test_coerencia_global(res):
    b, c = res.balanco, res.ciclo
    assert abs(b.erro_balanco) < 1e-8
    assert abs(res.exergia["erro_fechamento"]) < 1e-8
    assert res.condensador.Q == pytest.approx(b.Q_cond, rel=3e-3)
    assert res.evaporador.Q == pytest.approx(b.Q_evap, rel=3e-3)
    assert res.ciclo.estados["4"].P == pytest.approx(res.evaporador.P_in, rel=1e-4)
    assert res.capilar.escolhido.m == pytest.approx(b.m)
    assert c.COP == pytest.approx(2.0)


def test_faixas_realistas(res):
    """Ordens de grandeza de um visi-cooler de 200 L a R290 (sanidade, não validação)."""
    assert 150 < res.carga.Q_projeto < 400
    assert 1.0 < res.compressor.deslocamento_cm3 < 5.0
    assert 0.5e-3 < res.capilar.escolhido.D < 1.2e-3
    assert 0.02 < res.carga_refrigerante["total_kg"] < 0.25
    assert 1.0 < res.energia["total_kWh_dia"] < 5.0


def test_json(res):
    d = res.para_dict()
    s = json.dumps(d)
    assert "amesim" in d and "capilar" in d["amesim"]
    assert d["amesim"]["capilar"]["comprimento_m"] == pytest.approx(res.capilar.escolhido.L)
    assert len(s) > 1000
    assert "resumo" not in d
    assert "CAPILAR" in res.resumo()


def test_cop_impossivel_com_sugestao():
    with pytest.raises(ErroProjeto, match="seriam necessários"):
        dimensionar(EntradasProjeto(COP=4.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0))


def test_garrafas_e_fluidos():
    for fluido in ("R600a", "R134a"):
        r = dimensionar(EntradasProjeto(COP=1.7, T_ambiente_C=32.0, T_alvo_C=3.0, n_garrafas=150, fluido=fluido),
                        ParametrosProjeto(analise_sensibilidade=False))
        assert r.capacidade.n_garrafas == 150
        assert r.capilar.escolhido.L > 0


def test_ihx_melhora_capacidade_especifica():
    e = EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0)
    r0 = dimensionar(e, ParametrosProjeto(analise_sensibilidade=False))
    r1 = dimensionar(e, ParametrosProjeto(ciclo=ParametrosCiclo(eficacia_ihx=0.6), analise_sensibilidade=False))
    assert r1.ciclo.q_evap > r0.ciclo.q_evap
    assert r1.balanco.m < r0.balanco.m


def test_eficacia_padrao_065(res):
    assert res.entradas.eficacia_condensador == 0.65 and res.entradas.eficacia_evaporador == 0.65
    for r in (res.condensador, res.evaporador):
        assert r.eficacia == pytest.approx(0.65, abs=1e-3)
    d = res.para_dict()
    assert d["condensador"]["eficacia"]["obtida"] == pytest.approx(0.65, abs=1e-3)
    assert d["amesim"]["evaporador"]["velocidade_face_m_s"] == pytest.approx(res.evaporador.velocidade_face)


def test_eficacia_livre_reproduz_modo_antigo():
    e = EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0,
                        eficacia_condensador=None, eficacia_evaporador=None)
    r = dimensionar(e, ParametrosProjeto(analise_sensibilidade=False))
    assert r.condensador.velocidade_face == 2.0 and r.evaporador.velocidade_face == 1.5
    assert r.condensador.eficacia_alvo is None


def test_alternativas_fileiras(res):
    from predimref.projeto import alternativas_fileiras
    tab = alternativas_fileiras(res, "condensador", range(2, 7))
    viaveis = [t for t in tab if t["viavel"]]
    assert viaveis, tab
    assert all(t["motivo"] in ("ok", "alvo acima do maximo", "alvo abaixo do minimo", "sem ponto valido") for t in tab)
    Vs = [t["velocidade_face_m_s"] for t in viaveis]
    assert Vs == sorted(Vs)   # mais fileiras -> mais velocidade para a mesma ε
    escolhido = next(t for t in viaveis if t["fileiras"] == res.condensador.n_fileiras)
    assert escolhido["velocidade_face_m_s"] == pytest.approx(res.condensador.velocidade_face, rel=2e-3)


def test_amesim_bloco_coerente(res):
    """ε × ρ c_p V̇_projeto × ΔT = Q_sens com a serpentina de projeto; a construtiva tem a margem."""
    import CoolProp.CoolProp as CP
    d = res.para_dict()["amesim"]
    for tipo, r in (("condensador", res.condensador), ("evaporador", res.evaporador)):
        a = d[tipo]
        T = a["ar_entrada"]["T_K"]
        rho, cp = CP.PropsSI("D", "T", T, "P", 101325, "Air"), CP.PropsSI("C", "T", T, "P", 101325, "Air")
        Tsat = d["alvo_validacao"]["T_cond_K" if tipo == "condensador" else "T_evap_K"]
        Q_sens = r.Q / r.fator_umidade
        Q_exp = a["eficacia_saturacao"] * rho * cp * a["projeto_sem_margem"]["vazao_ar_m3_s"] * abs(Tsat - T)
        assert Q_exp == pytest.approx(Q_sens, rel=2e-3)
        razao = a["construtiva_com_margem"]["comprimento_total_tubo_m"] / a["projeto_sem_margem"]["comprimento_total_tubo_m"]
        assert razao == pytest.approx(1.0 + a["margem_area"], rel=1e-9)
        assert 0 < a["ar_entrada"]["umidade_relativa"] <= 1.0
    ci = d["condicoes_iniciais"]
    assert ci["carga_circuito_kg"] + ci["carga_gas_carcaca_kg"] + ci["carga_dissolvida_oleo_kg"] == pytest.approx(
        ci["carga_refrigerante_total_kg"], rel=1e-12)
    assert "linhas" in d and d["compressor"]["massa_oleo_kg"] > 0


@pytest.mark.parametrize("kw", [
    dict(volume_interno_L=1500.0, T_ambiente_C=38.0),
    dict(volume_interno_L=200.0, T_ambiente_C=32.0, eficacia_condensador=0.85, eficacia_evaporador=0.3),
    dict(volume_interno_L=120.0, T_ambiente_C=20.0, eficacia_condensador=0.3, eficacia_evaporador=0.75),
])
def test_sem_excecao_crua(kw):
    """Casos que antes quebravam com exceção do CoolProp: agora resolvem ou dão ErroProjeto claro."""
    base = dict(COP=2.0, T_alvo_C=2.5)
    base.update(kw)
    try:
        r = dimensionar(EntradasProjeto(**base), ParametrosProjeto(analise_sensibilidade=False))
        assert r.condensador.L_requerido > 0 and r.evaporador.L_requerido > 0
    except ErroProjeto as err:
        assert str(err)


def test_ihx_forte_nao_quebra():
    e = EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0)
    r = dimensionar(e, ParametrosProjeto(ciclo=ParametrosCiclo(eficacia_ihx=0.8)))
    assert r.ciclo.estados["4"].x < 0.25 and r.evaporador.eficacia == pytest.approx(0.65, abs=1e-3)


def test_superaquecimento_zero_sem_ihx():
    p = ParametrosProjeto(ciclo=ParametrosCiclo(superaquecimento=0.0), analise_sensibilidade=False)
    r = dimensionar(EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0), p)
    assert r.ciclo.estados["1"].x == 1.0 and r.compressor.eta_v > 0


def test_sugestao_cop_r404a_respeita_ponto_critico():
    """COP acima do ciclo ideal (inviável com os ΔT padrão), mas atingível com trocadores maiores: a
    sugestão deve trazer os ΔT necessários, e não 'mesmo com trocadores muito grandes...' (o limite
    superior da busca respeita T_cond < T_c − 5 K do R404A)."""
    from predimref.ciclo import resolver_ciclo
    from predimref.propriedades import Fluido
    fl = Fluido("R404A")
    pc = ParametrosCiclo()
    c = resolver_ciclo(fl, 276.15 - pc.dT_evap, 305.15 + pc.dT_cond, pc, None)
    with pytest.raises(ErroProjeto) as exc:
        dimensionar(EntradasProjeto(COP=1.05 * c.COP_ciclo_ideal, T_ambiente_C=32.0, T_alvo_C=3.0,
                                    volume_interno_L=300.0, fluido="R404A"))
    assert "seriam necessários" in str(exc.value) and "muito grandes" not in str(exc.value)


def test_limites_carga_a2l():
    r = dimensionar(EntradasProjeto(COP=1.6, T_ambiente_C=32.0, T_alvo_C=3.0, volume_interno_L=300.0,
                                    fluido="R1234yf"), ParametrosProjeto(analise_sensibilidade=False))
    cr = r.carga_refrigerante
    assert cr["classe"] == "A2L" and cr["limites_kg"]
    assert max(cr["limites_kg"].values()) <= 1.2
    if cr["total_kg"] > 0.150:
        assert any("A2L" in a.mensagem for a in r.avisos)


def test_balanco_umidade_lewis(res):
    """No equilíbrio, a água removida pela serpentina (superfície efetiva, Lewis = 1) em média diária
    é a que entra por infiltração, e o ξ de projeto é o latente dessa remoção com o compressor ligado."""
    import math as m
    from predimref.propriedades import ar_seco, calor_latente_agua
    u = res.carga.infiltracao["umidade"]
    ev = res.evaporador
    m_ar = ev.C_ar / ar_seco(ev.T_ar_in).cp
    remov_lig = m_ar * (1 - m.exp(-u["NTU_ar"])) * (u["W_interno"] - u["W_superficie"])   # kg/s, ligado
    agua_inf = res.carga.infiltracao["agua_kg_dia"] / 86400.0
    assert remov_lig * u["fracao_ligado"] == pytest.approx(agua_inf, rel=2e-2)
    Q_lat_lig = remov_lig * calor_latente_agua(ev.T_ar_in)
    assert Q_lat_lig == pytest.approx(res.carga.Q_latente_projeto, rel=3e-2)
    assert u["W_interno"] > u["W_superficie"] and 0.3 < res.parametros.uso.UR_interna < 0.95


def test_umidade_fixa_avisa_incoerencia():
    from predimref.gabinete import Uso
    p = ParametrosProjeto(uso=Uso(UR_interna=0.95, umidade_interna="fixa"), analise_sensibilidade=False)
    r = dimensionar(EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0), p)
    assert any("incompatível" in a.mensagem for a in r.avisos)


def test_circuitos_automaticos_por_perda_de_carga():
    e = EntradasProjeto(COP=2.0, T_ambiente_C=38.0, T_alvo_C=2.5, volume_interno_L=1500.0)
    r = dimensionar(e, ParametrosProjeto(analise_sensibilidade=False))
    assert r.evaporador.n_circuitos >= 1
    if r.evaporador.n_circuitos > 1:
        assert any("n_circuitos aumentado" in a.mensagem for a in r.avisos)
    p = ParametrosProjeto(analise_sensibilidade=False)
    p.evaporador.circuitos_automaticos = False
    try:
        dimensionar(e, p)
    except ErroProjeto as err:
        assert "n_circuitos" in str(err)
