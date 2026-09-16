"""Relatorio de dimensionamento em texto, pronto para colar em memorial."""

from __future__ import annotations

from .dimensionamento import Dimensionamento
from .souders_brown import FT_S

LARG = 78


def _cab(titulo: str) -> list[str]:
    return ["", titulo, "-" * LARG]


def relatorio(dim: Dimensionamento) -> str:
    c, crit, sb = dim.corrente, dim.criterios, dim.sb
    L: list[str] = []

    L += ["=" * LARG, c.nome.center(LARG), "=" * LARG]

    L += _cab("1. CONDICOES DE PROCESSO")
    L += [
        f"  Servico                              {c.servico}",
        f"  Pressao                              {c.P_bara:.2f} bara",
        f"  Temperatura                          {c.T_C:.1f} degC",
        f"  Massa molar do gas                   {c.MM:.2f} kg/kmol   (Z = {c.Z:.3f})",
        f"  Massa especifica do gas              {c.rho_g:.4f} kg/m3",
        f"  Massa especifica do liquido          {c.rho_l:.1f} kg/m3",
        f"  Viscosidade do gas                   {c.mu_g:.3e} Pa.s",
        f"  Tensao interfacial                   {c.sigma * 1000:.1f} mN/m",
        f"  Vazao de gas                         {c.W_gas:,.0f} kg/h = {c.Q_gas:.3f} m3/s",
        f"  Vazao de liquido                     {c.W_liq:,.0f} kg/h = {c.Q_liq * 3600:.2f} m3/h",
        f"  Fracao massica de liquido            {c.fracao_massica_liquido * 100:.1f} %",
        f"  Origem dos dados                     {c.fonte_dados}",
    ]

    L += _cab("2. CRITERIOS DE PROJETO ADOTADOS")
    L += [
        f"  Fator K                              {crit.fator_K}",
        f"  Fator de projeto sobre K             {crit.fator_de_projeto:.2f}",
        f"  Eliminador de nevoa                  {'sim, ' + f'{crit.espessura_demister * 1000:.0f} mm de tela' if crit.com_demister else 'nao'}",
        f"  Dispositivo de entrada               {crit.dispositivo_de_entrada}",
        f"  Tempo de retencao (LLL->NLL)         {crit.tempo_holdup_min:.1f} min",
        f"  Tempo de pulmao (NLL->HLL)           {crit.tempo_surge_min:.1f} min",
    ]

    L += _cab("3. SOUDERS-BROWN")
    L += [
        f"  K nominal                            {sb.fator.K_ft_s:.4f} ft/s" if sb.fator else "",
        f"  K efetivo                            {sb.K_ft_s:.4f} ft/s = {sb.K_m_s:.5f} m/s",
        f"  v_max = K sqrt((rho_L-rho_G)/rho_G)  {sb.v_max:.4f} m/s",
        f"  Area minima requerida                {c.Q_gas / sb.v_max:.4f} m2",
        f"  Diametro minimo teorico              {dim.D_minimo:.4f} m",
    ]
    L = [x for x in L if x != ""] if False else L

    L += _cab("4. VASO ADOTADO")
    L += [
        f"  Diametro interno                     {dim.D:.3f} m  (arredondado de {dim.D_minimo:.3f} m)",
        f"  Area da secao transversal            {dim.area:.4f} m2",
        f"  Velocidade superficial do gas        {dim.v_gas:.4f} m/s",
        f"  Uso do limite de Souders-Brown       {dim.uso_do_limite * 100:.1f} %",
        f"  Altura tangente-tangente             {dim.alturas.total:.3f} m",
        f"  Esbeltez L/D                         {dim.LD:.2f}",
        f"  Volume de retencao (LLL->NLL)        {dim.volume_holdup:.3f} m3",
        f"  Volume de pulmao (NLL->HLL)          {dim.volume_surge:.3f} m3",
        "",
        "  Composicao da altura (de baixo para cima):",
    ]
    for rotulo, h in dim.alturas.como_lista():
        if h > 0:
            L.append(f"      {rotulo:<44} {h:6.3f} m")
    L.append(f"      {'TOTAL':<44} {dim.alturas.total:6.3f} m")

    L += _cab("5. BOCAIS")
    L += [
        f"  Entrada bifasica      {dim.bocal_entrada}",
        f"      massa especifica da mistura      {c.rho_mistura:.3f} kg/m3",
        f"  Saida de gas          {dim.bocal_saida_gas}",
        f"  Saida de liquido      {dim.bocal_saida_liquido}",
        "      quebra-vortice obrigatorio na saida de liquido",
    ]

    L += _cab("6. O QUE O FATOR K ESCONDE")
    L += [
        "  K = sqrt(4 g d / (3 Cd)): o fator empirico embute um diametro de gota e",
        "  um coeficiente de arrasto. Desfazendo a conta nas condicoes reais deste vaso:",
        "",
        f"  Gota implicita no K (a v_max)        {dim.d_implicito * 1e6:.0f} um",
        f"  Gota implicita na velocidade real    {dim.d_implicito_operacao * 1e6:.0f} um",
        f"  Maior gota estavel no bocal (We=12)  {dim.d_max_estavel_bocal * 1e6:.0f} um",
        f"  Razao de atomizacao                  {dim.razao_de_atomizacao:.1f}x",
        "",
        "  Leitura: por sedimentacao pura, este vaso so garante a remocao de gotas",
        f"  acima de {dim.d_implicito * 1e6:.0f} um. O bocal de entrada, a {dim.bocal_entrada.velocidade:.1f} m/s, quebra qualquer",
        f"  gota acima de {dim.d_max_estavel_bocal * 1e6:.0f} um. A populacao que chega ao corpo do vaso e,",
        "  portanto, inteiramente menor que a gota para a qual ele foi dimensionado.",
    ]

    L += _cab("7. AVISOS E RASTREABILIDADE")
    for i, a in enumerate(dim.avisos, 1):
        L.append(f"  {i}. {a}")

    L += [
        "",
        "=" * LARG,
        "  TODOS os fatores K, criterios de rho.v2 e folgas geometricas usados aqui",
        "  sao valores de pratica corrente. ANTES de emitir documento de engenharia,",
        "  confira cada um na edicao da norma efetivamente adotada pelo cliente",
        "  (GPSA Sec. 7, API 521, API 12J, NORSOK P-002 ou DEP equivalente).",
        "=" * LARG,
    ]
    return "\n".join(L)
