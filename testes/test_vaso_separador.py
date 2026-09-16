"""Testes do pacote. Rode com:  python3 -m unittest discover -s testes -v

A primeira classe e a que importa de verdade: ela verifica a fisica contra
solucoes fechadas conhecidas. Se ela passar, a tabela de velocidade terminal que
vai servir de caso de verificacao do STAR-CCM+ esta correta.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vaso_separador.arraste import (
    G,
    cd_schiller_naumann,
    diametro_maximo_estavel,
    diametro_para_velocidade_terminal,
    numero_de_weber,
    velocidade_terminal,
    velocidade_terminal_stokes,
)
from vaso_separador.casos import CASOS, CRITERIOS_POR_CASO
from vaso_separador.dimensionamento import dimensionar_vaso_vertical
from vaso_separador.propriedades import massa_especifica_gas, rho_v2_em_pa, seleciona_bocal
from vaso_separador.souders_brown import (
    ATM_BARA,
    FATORES_K,
    FT_S,
    K_para_remover_gota,
    correcao_gpsa_pressao,
    diametro_de_gota_implicito,
    souders_brown,
    velocidade_maxima,
)

# Condicoes do caso principal, para nao repetir em cada teste.
RHO_G, RHO_L, MU_G, SIGMA = 3.1657, 613.0, 6.5e-6, 0.019


class TestFisicaContraSolucaoFechada(unittest.TestCase):
    """Se estes testes falharem, nada mais no pacote significa coisa alguma."""

    def test_gota_pequena_converge_para_stokes(self):
        # Em Re << 1 a solucao iterativa tem que reproduzir g d^2 drho / (18 mu).
        for d_um in (1.0, 2.0, 5.0):
            d = d_um * 1e-6
            v = velocidade_terminal(d, RHO_G, RHO_L, MU_G).v_t
            v_stokes = velocidade_terminal_stokes(d, RHO_G, RHO_L, MU_G)
            self.assertLess(velocidade_terminal(d, RHO_G, RHO_L, MU_G).Re, 1.0)
            self.assertAlmostEqual(v / v_stokes, 1.0, delta=0.08,
                                   msg=f"d = {d_um} um deveria estar no regime de Stokes")

    def test_gota_grande_converge_para_newton(self):
        # Em Re > 1000, Cd -> 0.44 e v_t tem forma fechada.
        d = 5e-3
        t = velocidade_terminal(d, RHO_G, RHO_L, MU_G)
        self.assertGreater(t.Re, 1000.0)
        v_newton = math.sqrt(4.0 * G * d * (RHO_L - RHO_G) / (3.0 * 0.44 * RHO_G))
        self.assertAlmostEqual(t.v_t / v_newton, 1.0, delta=1e-6)

    def test_balanco_de_forcas_fecha(self):
        # Peso - empuxo = arrasto, na velocidade terminal, para toda a faixa.
        for d_um in (10.0, 50.0, 100.0, 300.0, 800.0):
            d = d_um * 1e-6
            t = velocidade_terminal(d, RHO_G, RHO_L, MU_G)
            peso_liquido = (math.pi / 6.0) * d**3 * (RHO_L - RHO_G) * G
            arrasto = t.Cd * (math.pi / 8.0) * d**2 * RHO_G * t.v_t**2
            self.assertAlmostEqual(arrasto / peso_liquido, 1.0, delta=1e-8,
                                   msg=f"balanco nao fecha em d = {d_um} um")

    def test_reynolds_consistente_com_a_solucao(self):
        for d_um in (10.0, 100.0, 500.0):
            t = velocidade_terminal(d_um * 1e-6, RHO_G, RHO_L, MU_G)
            self.assertAlmostEqual(t.Re, RHO_G * t.v_t * t.d / MU_G, delta=1e-9)
            self.assertAlmostEqual(t.Cd, cd_schiller_naumann(t.Re), delta=1e-12)

    def test_inversao_diametro_velocidade_e_exata(self):
        for d_um in (8.0, 40.0, 150.0, 600.0, 2000.0):
            d = d_um * 1e-6
            v = velocidade_terminal(d, RHO_G, RHO_L, MU_G).v_t
            d_volta = diametro_para_velocidade_terminal(v, RHO_G, RHO_L, MU_G)
            self.assertAlmostEqual(d_volta / d, 1.0, delta=1e-6)

    def test_velocidade_terminal_cresce_com_o_diametro(self):
        ds = [10e-6, 50e-6, 100e-6, 500e-6, 1000e-6]
        vs = [velocidade_terminal(d, RHO_G, RHO_L, MU_G).v_t for d in ds]
        self.assertEqual(vs, sorted(vs))

    def test_gota_mais_leve_que_o_gas_e_rejeitada(self):
        with self.assertRaises(ValueError):
            velocidade_terminal(100e-6, 700.0, 613.0, MU_G)


class TestWeber(unittest.TestCase):
    def test_diametro_maximo_estavel_devolve_we_critico(self):
        v, we_c = 25.0, 12.0
        d = diametro_maximo_estavel(v, RHO_G, SIGMA, we_c)
        self.assertAlmostEqual(numero_de_weber(d, v, RHO_G, SIGMA), we_c, delta=1e-9)

    def test_gas_parado_nao_quebra_gota(self):
        self.assertEqual(diametro_maximo_estavel(0.0, RHO_G, SIGMA), math.inf)


class TestSoudersBrown(unittest.TestCase):
    def test_identidade_K_igual_raiz_de_4gd_sobre_3Cd(self):
        # K = sqrt(4 g d / (3 Cd)) e a origem algebrica do fator empirico.
        v_max = souders_brown("succao_de_compressor", RHO_G, RHO_L, 1.4).v_max
        d = diametro_de_gota_implicito(v_max, RHO_G, RHO_L, MU_G)
        t = velocidade_terminal(d, RHO_G, RHO_L, MU_G)
        K_reconstruido = math.sqrt(4.0 * G * d / (3.0 * t.Cd))
        K_usado = v_max / math.sqrt((RHO_L - RHO_G) / RHO_G)
        self.assertAlmostEqual(K_reconstruido / K_usado, 1.0, delta=1e-6)

    def test_ida_e_volta_entre_K_e_diametro_alvo(self):
        for d_alvo_um in (150.0, 300.0, 600.0):
            d_alvo = d_alvo_um * 1e-6
            K_ft_s, v_max = K_para_remover_gota(d_alvo, RHO_G, RHO_L, MU_G)
            self.assertAlmostEqual(
                velocidade_maxima(K_ft_s * FT_S, RHO_G, RHO_L) / v_max, 1.0, delta=1e-9)
            d_volta = diametro_de_gota_implicito(v_max, RHO_G, RHO_L, MU_G)
            self.assertAlmostEqual(d_volta / d_alvo, 1.0, delta=1e-6)

    def test_criterio_300um_da_api521_cai_perto_do_K_gpsa_sem_demister(self):
        # Cruzamento entre as duas rotas normativas: a API 521 prescreve o
        # diametro de gota, o GPSA prescreve o K. Nas mesmas condicoes eles
        # tem que dar aproximadamente a mesma coisa - e dao.
        K_api, _ = K_para_remover_gota(300e-6, RHO_G, RHO_L, MU_G)
        K_gpsa = FATORES_K["gpsa_vertical_sem_demister"].K_ft_s
        self.assertAlmostEqual(K_api / K_gpsa, 1.0, delta=0.30)

    def test_correcao_de_pressao_gpsa(self):
        P_100psig = ATM_BARA + 100 * 6894.757 / 1e5
        self.assertAlmostEqual(correcao_gpsa_pressao(0.35, P_100psig), 0.35, delta=1e-6)
        self.assertAlmostEqual(correcao_gpsa_pressao(0.35, 1.0), 0.35, delta=1e-9)
        P_600psig = ATM_BARA + 600 * 6894.757 / 1e5
        self.assertAlmostEqual(correcao_gpsa_pressao(0.35, P_600psig), 0.35 - 0.05, delta=1e-6)
        self.assertGreaterEqual(correcao_gpsa_pressao(0.35, 400.0), 0.12)  # piso

    def test_K_cai_monotonicamente_com_a_pressao(self):
        Ks = [FATORES_K["succao_de_compressor"].K_efetivo_ft_s(p)
              for p in (1.5, 10.0, 20.0, 40.0, 80.0)]
        self.assertEqual(Ks, sorted(Ks, reverse=True))

    def test_fator_de_projeto_reduz_v_max_proporcionalmente(self):
        a = souders_brown("succao_de_compressor", RHO_G, RHO_L, 1.4, 1.0).v_max
        b = souders_brown("succao_de_compressor", RHO_G, RHO_L, 1.4, 0.8).v_max
        self.assertAlmostEqual(b / a, 0.8, delta=1e-9)

    def test_todo_fator_K_declara_fonte(self):
        for chave, f in FATORES_K.items():
            self.assertTrue(f.fonte.strip(), f"{chave} sem fonte declarada")
            self.assertTrue(f.confirmar.strip(), f"{chave} sem aviso de conferencia")


class TestPropriedades(unittest.TestCase):
    def test_gas_ideal(self):
        # 1 kmol de gas ideal a 0 degC e 1,01325 bara ocupa 22,414 m3.
        rho = massa_especifica_gas(1.01325, 0.0, 28.0, 1.0)
        self.assertAlmostEqual(rho, 28.0 / 22.414, delta=1e-3)

    def test_bocal_atende_o_criterio(self):
        for Q in (0.5, 2.0, 5.0, 12.0, 30.0):
            limite = rho_v2_em_pa(1500.0)
            b = seleciona_bocal(Q, 3.3, limite)
            self.assertLessEqual(b.rho_v2, limite * (1 + 1e-9))
            self.assertAlmostEqual(b.velocidade, Q / b.area, delta=1e-9)
            self.assertGreaterEqual(b.di, b.di_minimo)

    def test_bocal_excessivo_levanta_erro_em_vez_de_inventar_bitola(self):
        with self.assertRaises(ValueError):
            seleciona_bocal(5000.0, 3.3, rho_v2_em_pa(1500.0))


class TestDimensionamento(unittest.TestCase):
    def setUp(self):
        self.dim = dimensionar_vaso_vertical(
            CASOS["propeno_refrigeracao"], CRITERIOS_POR_CASO["propeno_refrigeracao"])

    def test_continuidade(self):
        self.assertAlmostEqual(
            self.dim.v_gas, self.dim.corrente.Q_gas / self.dim.area, delta=1e-9)
        self.assertAlmostEqual(
            self.dim.area, math.pi * self.dim.D**2 / 4.0, delta=1e-9)

    def test_velocidade_real_nao_ultrapassa_v_max(self):
        for chave in CASOS:
            d = dimensionar_vaso_vertical(CASOS[chave], CRITERIOS_POR_CASO[chave])
            self.assertLessEqual(d.v_gas, d.sb.v_max, f"{chave} acima do v_max")
            self.assertGreaterEqual(d.D, d.D_minimo)

    def test_alturas_somam_o_total(self):
        soma = sum(h for _, h in self.dim.alturas.como_lista())
        self.assertAlmostEqual(soma, self.dim.alturas.total, delta=1e-9)

    def test_LD_minimo_e_atendido(self):
        for chave in CASOS:
            crit = CRITERIOS_POR_CASO[chave]
            d = dimensionar_vaso_vertical(CASOS[chave], crit)
            if crit.forcar_LD_minimo is not None:
                self.assertGreaterEqual(d.LD, crit.forcar_LD_minimo - 1e-9, chave)

    def test_volume_de_retencao_corresponde_ao_tempo_declarado(self):
        crit = CRITERIOS_POR_CASO["propeno_refrigeracao"]
        Q_liq = CASOS["propeno_refrigeracao"].Q_liq
        self.assertAlmostEqual(
            self.dim.volume_holdup, Q_liq * crit.tempo_holdup_min * 60.0, delta=1e-9)
        self.assertAlmostEqual(
            self.dim.alturas.holdup_LLL_a_NLL * self.dim.area,
            self.dim.volume_holdup, delta=1e-9)

    def test_todo_caso_gera_avisos_rastreaveis(self):
        for chave in CASOS:
            d = dimensionar_vaso_vertical(CASOS[chave], CRITERIOS_POR_CASO[chave])
            self.assertTrue(any("CONFIRMAR" in a for a in d.avisos), chave)

    def test_bocal_de_entrada_atomiza_abaixo_do_que_o_vaso_promete(self):
        # Esta e a tese do estudo. Se algum dia um caso NAO satisfizer isso,
        # o teste falha e a tese precisa ser revista - que e o que um teste
        # de regressao de engenharia deve fazer.
        for chave in CASOS:
            d = dimensionar_vaso_vertical(CASOS[chave], CRITERIOS_POR_CASO[chave])
            self.assertGreater(d.razao_de_atomizacao, 1.0, chave)


class TestRegressaoDosNumerosPublicados(unittest.TestCase):
    """Trava os numeros do caso principal. Se mudarem, foi de proposito?"""

    def test_caso_principal(self):
        d = dimensionar_vaso_vertical(
            CASOS["propeno_refrigeracao"], CRITERIOS_POR_CASO["propeno_refrigeracao"])
        self.assertAlmostEqual(d.corrente.rho_g, 3.1657, delta=1e-3)
        self.assertAlmostEqual(d.sb.v_max, 1.0576, delta=1e-3)
        self.assertAlmostEqual(d.D, 2.40, delta=1e-9)
        self.assertAlmostEqual(d.alturas.total, 4.80, delta=1e-3)
        self.assertAlmostEqual(d.LD, 2.00, delta=1e-3)
        self.assertAlmostEqual(d.d_implicito * 1e6, 366.0, delta=2.0)
        self.assertAlmostEqual(d.d_max_estavel_bocal * 1e6, 113.0, delta=2.0)
        self.assertEqual(d.bocal_entrada.nps, '20"')


if __name__ == "__main__":
    unittest.main(verbosity=2)
