"""Interface de linha de comando.

    python -m biokin demo                    varredura completa em dados sintéticos
    python -m biokin screen dados.csv        varredura sobre dados reais
    python -m biokin mechanisms              catálogo e leis derivadas
    python -m biokin design dados.csv        próximos experimentos
    python -m biokin transport               calculadora de transporte do monolito
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--keq",
        nargs=3,
        type=float,
        metavar=("KEQ1", "KEQ2", "KEQ3"),
        help="fixa as constantes de equilíbrio das três etapas "
        "(recomendado: longe do equilíbrio elas não são identificáveis)",
    )
    p.add_argument("--refine", type=int, default=5, help="modelos refinados por regressão integral")
    p.add_argument(
        "--mode",
        default="ideal",
        choices=("ideal", "film", "full"),
        help="tratamento do transporte nas corridas em monolito",
    )
    p.add_argument("--starts", type=int, default=10, help="partidas por modelo na triagem")
    p.add_argument("--no-ml", action="store_true", help="pula a referência de rede neural")
    p.add_argument("--no-design", action="store_true", help="pula o planejamento de experimentos")
    p.add_argument("--figures", metavar="DIR", help="diretório para gravar as figuras")
    p.add_argument("--out", metavar="ARQ", help="grava o relatório em arquivo de texto")
    p.add_argument("--seed", type=int, default=0)


def _config(args):
    from .screening import ScreeningConfig

    fixed = None
    if args.keq:
        fixed = {f"Keq_{i + 1}": v for i, v in enumerate(args.keq)}
    return ScreeningConfig(
        fixed=fixed,
        mode=args.mode,
        n_refine=args.refine,
        n_starts_differential=args.starts,
        run_ml_baseline=not args.no_ml,
        run_design=not args.no_design,
        seed=args.seed,
    )


def _finish(result, args) -> None:
    text = result.report()
    print()
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"\nrelatório gravado em {args.out}")
    if args.figures:
        from .report import write_all_figures

        paths = write_all_figures(result, args.figures, mode=args.mode)
        print(f"figuras gravadas em {args.figures}:")
        for p in paths:
            print(f"  {p.name}")


# ----------------------------------------------------------------------
def cmd_demo(args) -> int:
    from .screening import run_screening
    from .synthetic import TRUE_MODEL_ID, generate_dataset

    print("Gerando dados sintéticos a partir de um mecanismo conhecido.")
    print(f"Mecanismo verdadeiro (oculto da varredura): {TRUE_MODEL_ID}\n")
    dataset = generate_dataset(
        relative_noise=args.noise, seed=args.seed, monolith_mode=args.mode
    )
    result = run_screening(dataset, _config(args))
    _finish(result, args)

    best = result.best
    print("\n" + "=" * 78)
    if best and best.model_id == TRUE_MODEL_ID:
        print(f"VALIDAÇÃO: mecanismo verdadeiro recuperado ({TRUE_MODEL_ID}).")
    elif best:
        print(
            f"VALIDAÇÃO: melhor = {best.model_id}, verdadeiro = {TRUE_MODEL_ID}.\n"
            "Confira a tabela: modelos equivalentes ao verdadeiro empatam por "
            "construção, e a posição do verdadeiro no ranking é o que importa."
        )
    return 0


def cmd_screen(args) -> int:
    from .data import read_csv
    from .screening import run_screening

    dataset = read_csv(args.csv)
    print(dataset.summary())
    result = run_screening(dataset, _config(args))
    _finish(result, args)
    return 0


def cmd_mechanisms(args) -> int:
    from .library import build_catalog, enumerate_rate_laws
    from .network import build_network

    catalog = build_catalog()
    laws = enumerate_rate_laws(catalog, include_empirical=True)
    print(f"{len(catalog)} mecanismos, {len(laws)} leis de velocidade distintas\n")
    if args.detail:
        for mech in catalog:
            print(mech.pretty())
            print()
    for law in laws:
        net = build_network(law)
        print(f"{law.model_id}")
        print(f"   família {law.family} | denominador de ordem {law.denominator_exponent}")
        print(f"   {law.pretty()}")
        print(f"   rede: {net.n_params} parâmetros — {', '.join(net.param_names)}")
        print()
    return 0


def cmd_design(args) -> int:
    from .data import read_csv
    from .screening import ScreeningConfig, run_screening

    dataset = read_csv(args.csv)
    cfg = _config(args)
    cfg.run_design = True
    result = run_screening(dataset, cfg)
    if result.design is None:
        print("Não há dois modelos admissíveis em disputa — nada a discriminar.")
        return 1
    print(result.design.table(top=15))
    return 0


def cmd_transport(args) -> int:
    from .transport import FluidProperties, MonolithGeometry, diagnose

    geom = MonolithGeometry(
        cell_density_cpsi=args.cpsi,
        washcoat_thickness_m=args.washcoat * 1e-6,
        length_m=args.length,
    )
    fluid = FluidProperties(diffusivity_m2_s=args.diffusivity)
    print(f"passo da célula      {geom.cell_pitch_m * 1e3:8.3f} mm")
    print(f"lado do canal        {geom.channel_side_m * 1e3:8.3f} mm")
    print(f"área frontal aberta  {geom.open_frontal_area:8.3f}")
    print(f"área específica a_v  {geom.specific_surface_m2_m3:8.0f} m²/m³")
    print(f"washcoat / reator    {geom.washcoat_volume_fraction:8.4f}")
    print(f"massa de catalisador {geom.catalyst_density_g_L:8.2f} g/L de reator")
    print(f"Re                   {fluid.reynolds(args.velocity, geom.hydraulic_diameter_m):8.2f}")
    print(f"Sc                   {fluid.schmidt():8.3g}")
    print()
    print(f"para r_obs = {args.rate:g} mol/(g·min) e C = {args.conc:g} mol/L:")
    print(diagnose(lambda c: args.rate * c / args.conc, args.conc, geom, fluid, args.velocity).report())
    return 0


# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="biokin",
        description="Discriminação de mecanismos cinéticos para produção de "
        "biodiesel em reatores monolíticos.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("demo", help="varredura sobre dados sintéticos de mecanismo conhecido")
    _add_common(d)
    d.add_argument("--noise", type=float, default=0.03, help="ruído relativo das medidas")
    d.set_defaults(func=cmd_demo)

    s = sub.add_parser("screen", help="varredura sobre dados experimentais em CSV")
    s.add_argument("csv", help="arquivo no formato de biokin.data.write_csv")
    _add_common(s)
    s.set_defaults(func=cmd_screen)

    m = sub.add_parser("mechanisms", help="lista o catálogo e as leis derivadas")
    m.add_argument("--detail", action="store_true", help="mostra as etapas elementares")
    m.set_defaults(func=cmd_mechanisms)

    g = sub.add_parser("design", help="condições de máximo poder discriminatório")
    g.add_argument("csv")
    _add_common(g)
    g.set_defaults(func=cmd_design)

    t = sub.add_parser("transport", help="calculadora de transporte do monolito")
    t.add_argument("--cpsi", type=float, default=400.0, help="densidade de células [cpsi]")
    t.add_argument("--washcoat", type=float, default=30.0, help="espessura do washcoat [µm]")
    t.add_argument("--length", type=float, default=0.10, help="comprimento [m]")
    t.add_argument("--velocity", type=float, default=0.01, help="velocidade superficial [m/s]")
    t.add_argument("--diffusivity", type=float, default=7.5e-10, help="difusividade [m²/s]")
    t.add_argument("--rate", type=float, default=2e-3, help="velocidade observada [mol/(g·min)]")
    t.add_argument("--conc", type=float, default=0.9, help="concentração do reagente-chave [mol/L]")
    t.set_defaults(func=cmd_transport)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
