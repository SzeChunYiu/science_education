"""
circuit_diagrams.py — Programmatic circuit schematic renderer.

Uses Schemdraw to generate clean circuit diagrams that can be exported as PNG
assets for the video pipeline.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import schemdraw
import schemdraw.elements as elm


class CircuitDiagramRenderer:
    """
    Generate simple canonical circuit diagrams as PNG assets.
    """

    def __init__(
        self,
        *,
        unit: float = 5.5,
        fontsize: int = 24,
        dpi: int = 300,
    ) -> None:
        self.unit = unit
        self.fontsize = fontsize
        self.dpi = dpi

    def _new_drawing(self) -> schemdraw.Drawing:
        drawing = schemdraw.Drawing(show=False)
        drawing.config(unit=self.unit, fontsize=self.fontsize)
        return drawing

    def _save(self, drawing: schemdraw.Drawing, out_path: str | Path) -> str:
        out_path = str(Path(out_path).resolve())
        drawing.save(out_path, dpi=self.dpi)
        return out_path

    def simple_series_rc(
        self,
        out_path: str | Path,
        *,
        source_label: str = "V",
        resistor_label: str = "R",
        capacitor_label: str = "C",
    ) -> str:
        """
        Draw a simple series RC loop and save it to ``out_path``.
        """
        d = self._new_drawing()
        d += elm.SourceV().up().label(source_label)
        d += elm.Resistor().right().label(resistor_label)
        d += elm.Capacitor().down().label(capacitor_label)
        d += elm.Line().left()
        d += elm.Line().up()
        return self._save(d, out_path)

    def simple_battery_lamp(
        self,
        out_path: str | Path,
        *,
        source_label: str = "Battery",
        lamp_label: str = "Lamp",
    ) -> str:
        """
        Draw a simple closed-loop battery and lamp schematic.
        """
        d = self._new_drawing()
        d += elm.BatteryCell().up().label(source_label)
        d += elm.Line().right()
        d += elm.Lamp().down().label(lamp_label)
        d += elm.Line().left()
        d += elm.Line().up()
        return self._save(d, out_path)
