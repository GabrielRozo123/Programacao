"""Linha de comando: XML Pulse -> relatório PDF + Excel + figuras.

Exemplo:
    python scripts/run_analysis.py gravacao.xml --ref pulse_ref.json --out saida/
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pulseva as pv  # noqa: E402
from pulseva.export import to_excel  # noqa: E402
from pulseva.report_latex import build_latex  # noqa: E402
from pulseva.report_pdf import build_report  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xml", help="arquivo XML exportado pelo Pulse DAQ")
    ap.add_argument("--ref", help="JSON com os valores do relatório Pulse (opcional)")
    ap.add_argument("--out", default="saida", help="pasta de saída")
    ap.add_argument("--autor", default=None, help="nome do responsável (capa do PDF)")
    ap.add_argument("--equipamento", default=None, help="identificação do equipamento")
    ap.add_argument("--documento", default="RT-VIB-001", help="número do documento (relatório LaTeX)")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = pv.load_pulse_xml(a.xml)
    print(rec.summary(), "\n")
    an = pv.analyze(rec)
    ref = pv.load_reference(a.ref) if a.ref else None
    print(an.table().round(3).to_string(), "\n")
    for f in an.findings:
        print(f)
    stem = Path(a.xml).stem
    pdf = build_report(an, out / f"Relatorio_Tecnico_{stem}.pdf", ref=ref, figdir=out / "figuras",
                       author=a.autor, equipment=a.equipamento)
    xls = to_excel(an, out / f"Resultados_{stem}.xlsx", ref=ref)
    tex, zp = build_latex(an, out / "relatorio_latex", equipamento=a.equipamento or rec.meta.get("Serial", ""),
                          documento=a.documento)
    print(f"\nPDF  : {pdf}\nExcel: {xls}\nLaTeX: {tex} (Overleaf: {zp})")


if __name__ == "__main__":
    main()
