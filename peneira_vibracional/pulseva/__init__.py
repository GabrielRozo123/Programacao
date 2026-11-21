"""pulseva — análise vibracional de peneiras a partir de gravações Pulse VA (XML).

Uso rápido::

    import pulseva as pv
    rec = pv.load_pulse_xml("gravacao.xml")
    an = pv.analyze(rec)
    print(an.table().round(2))
"""
from .io import SENSOR_ORDER, Record, load_pulse_xml, load_reference
from .metrics import (CORNERS, G0, PULSE_LIMITS, Analysis, SensorResult, analyze,
                      compare_with_reference, ellipse_from_amplitudes,
                      ellipse_from_phasors, reference_consistency, stroke_mm,
                      throw_index)

__version__ = "1.0.0"
__all__ = [
    "SENSOR_ORDER", "Record", "load_pulse_xml", "load_reference", "CORNERS", "G0",
    "PULSE_LIMITS", "Analysis", "SensorResult", "analyze", "compare_with_reference",
    "ellipse_from_amplitudes", "ellipse_from_phasors", "reference_consistency",
    "stroke_mm", "throw_index",
]
