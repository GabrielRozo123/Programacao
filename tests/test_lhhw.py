"""O derivador simbólico reproduz as leis de livro-texto?

Estes testes são a fundação: se a derivação estiver errada, todo o resto do
pacote produz números convincentes e falsos.
"""

import sympy as sp

from biokin.lhhw import KEQ, RATE_CONSTANT, conc_symbol, derive_all, derive_rate_law
from biokin.library import er_methoxide, lh_dual_site, lh_single_site
from biokin.mechanism import Mechanism, Step


def _rds(mech, label):
    return [i for i, s in enumerate(mech.steps) if s.label == label][0]


def test_eley_rideal_reproduz_lei_classica():
    """ER com metóxido: r = k·K_M(C_A C_M - C_B C_E/Keq)/(1 + K_M C_M + K_G C_G)."""
    mech = er_methoxide(("G",))
    law = derive_rate_law(mech, _rds(mech, "sr"))

    C_A, C_B, C_M, C_E, C_G = (conc_symbol(x) for x in ("A", "B", "M", "E", "G"))
    K_M = sp.Symbol("K_ads_M", positive=True)
    K_G = sp.Symbol("K_ads_G", positive=True)
    esperado = (
        RATE_CONSTANT * K_M * (C_A * C_M - C_B * C_E / KEQ)
        / (1 + K_M * C_M + K_G * C_G)
    )
    assert sp.simplify(law.expr - esperado) == 0


def test_langmuir_hinshelwood_tem_denominador_quadratico():
    """LH mono-sítio com reação superficial determinante: denominador ao quadrado."""
    mech = lh_single_site(("G",))
    law = derive_rate_law(mech, _rds(mech, "sr"))
    assert law.denominator_exponent == 2

    _, den = law.numerator_denominator()
    # o termo de adsorção aparece elevado ao quadrado
    assert any(
        isinstance(f, sp.Pow) and f.exp == 2 and isinstance(f.base, sp.Add)
        for f in (den.args if isinstance(den, sp.Mul) else (den,))
    )


def test_dual_sitio_fatora_em_dois_termos():
    """LH dual-sítio: o denominador é produto de dois balanços de sítio."""
    mech = lh_dual_site(("G",))
    law = derive_rate_law(mech, _rds(mech, "sr"))
    _, den = law.numerator_denominator()
    somas = [
        f
        for f in (den.args if isinstance(den, sp.Mul) else (den,))
        if isinstance(f, sp.Add)
    ]
    assert len(somas) == 2, f"esperado produto de dois balanços, obtido {den}"


def test_velocidade_anula_no_equilibrio():
    """Consistência termodinâmica: r = 0 quando Q = Keq, em toda família.

    É a propriedade que separa uma lei mecanística de um ajuste empírico
    com aparência de mecanismo.
    """
    for fabrica in (er_methoxide, lh_single_site, lh_dual_site):
        mech = fabrica(("G",))
        for law in derive_all(mech):
            f = law.lambdify()
            nomes = law.species_names
            # composição de equilíbrio: C_B·C_E = Keq·C_A·C_M
            Keq_val = 2.5
            C = {"A": 0.4, "M": 3.0, "E": 1.5, "G": 0.2}
            C["B"] = Keq_val * C["A"] * C["M"] / C["E"]
            params = {p: 1.3 for p in law.param_names}
            params["Keq"] = Keq_val
            r = f(*[C[s] for s in nomes], *[params[p] for p in law.param_names])
            assert abs(float(r)) < 1e-12, f"{law.model_id} não anula no equilíbrio: {r}"


def test_ciclo_que_nao_fecha_e_rejeitado():
    """Um mecanismo cujas etapas não somam a reação global deve falhar."""
    mech = Mechanism(
        name="quebrado",
        family="X",
        steps=(
            Step("ads_M", {"M": 1, "*": 1}, {"M*": 1}),
            Step("sr", {"M*": 1, "A": 1}, {"B": 1, "*": 1}),  # falta o éster
        ),
        overall={"A": -1, "M": -1, "B": 1, "E": 1},
    )
    try:
        mech.validate()
    except ValueError as exc:
        assert "soma do ciclo" in str(exc) or "não fecha" in str(exc)
    else:
        raise AssertionError("validate() deveria ter rejeitado o mecanismo")


def test_dessorcao_determinante_elimina_parametro():
    """Com dessorção determinante, K_ads do produto é fixado pelo vínculo Keq."""
    mech = lh_single_site(())
    law = derive_rate_law(mech, _rds(mech, "des_B"))
    assert "K_ads_B" not in law.param_names, (
        "K_ads_B deveria ter sido eliminado pela consistência termodinâmica"
    )


def test_constantes_de_adsorcao_seguem_a_especie():
    """Ao instanciar para TG->DG, K_ads_A deve virar K_ads_TG."""
    mech = er_methoxide(("G",))
    law = derive_rate_law(mech, _rds(mech, "sr"))
    inst = law.substitute_species({"A": "TG", "B": "DG"})
    assert "K_ads_M" in inst.param_names
    assert "K_ads_A" not in inst.param_names
