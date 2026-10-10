#!/usr/bin/env python3
"""EC-SEAL1 fabrication artwork, v0.0.1 (doc-1.2, board revision B).

The release is the land pattern, the mains and analog pours, the netlist,
and the centroid. QFN fanout is not maze-routed: a 0.25 mm grid cannot
hold a 0.60 mm via pad on a 0.50 mm pitch without a short, and a short
is not a deliverable. See hardware/fab/ec-seal1/MANUFACTURER.md.
"""
from __future__ import annotations

import collections
import csv
import math
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "hardware", "fab", "ec-seal1")
GER = os.path.join(OUT, "gerber")
os.makedirs(GER, exist_ok=True)

GW, GH = 100.0, 70.0
CELL = 0.25
NX, NY = int(GW / CELL), int(GH / CELL)

# Logic ground is Line on the grid side of the shunt (net GND). The inner
# ground plane is that net, and it starts at x = 46 so it never sits under
# the Neutral-referenced mains copper.
PADS = []
PARTS = []


def add_part(ref, value, mpn, pkg, x, y, rot, pads):
    PARTS.append((ref, value, mpn, pkg, x, y, rot))
    rad = rot * math.pi / 180.0
    c, s = math.cos(rad), math.sin(rad)
    for name, dx, dy, w, h, net, drill in pads:
        rx, ry = c * dx - s * dy, s * dx + c * dy
        ww, hh = (w, h) if rot % 180 == 0 else (h, w)
        PADS.append((x + rx, y + ry, ww, hh, net, drill, ref, name))


def p(name, dx, dy, w, h, net, drill=0):
    return (name, dx, dy, w, h, net, drill)


# --- mains, left of the plane -------------------------------------------
# v0.0.1 (doc-1.2). Logic ground is the LINE conductor on the grid side of
# the shunt, so both STPM32 current inputs sit within millivolts of ground.
# doc-1.1 tied ground to Neutral while the shunt sat in Line, which put the
# current inputs at full mains voltage. The voltage divider now hangs from
# Neutral, and the supply is an LNK304 buck referenced to Line.
#
# Studs. Pad copper is the 6 mm ring flashed from the drill list.
add_part("H1", "M3 grid line", "terminal", "hole-3.2", 16, 60, 0, [
    p("1", 0, 0, 6.0, 6.0, "GND", 3.2),
])
add_part("H2", "M3 generator line", "terminal", "hole-3.2", 16, 46, 0, [
    p("1", 0, 0, 6.0, 6.0, "L_GEN", 3.2),
])
add_part("H3", "M3 neutral", "terminal", "hole-3.2", 12, 32, 0, [
    p("1", 0, 0, 6.0, 6.0, "N", 3.2),
])
# Shunt, rot 90: force pads land on the left, sense pads on the right.
# SG is the generator-side Kelvin pad, SI the grid-side Kelvin pad.
add_part("RS", "100 uohm", "Vishay WSBS5216L1000JT", "shunt-5216", 24, 52, 90, [
    p("FG", -6.0, 1.2, 2.4, 2.0, "L_GEN", 0),
    p("SG", -6.0, -1.2, 1.4, 1.4, "IIN_F", 0),
    p("IG", 6.0, 1.2, 2.4, 2.0, "GND", 0),
    p("SI", 6.0, -1.2, 1.4, 1.4, "IIP_F", 0),
])
# Supply input: fuse in the Neutral leg, MOV across Neutral and Line.
add_part("F1", "250 mA T 5x20", "Littelfuse 0215.250HXP", "fuse-5x20", 28, 38, 0, [
    p("1", -10, 0, 2.2, 2.2, "N", 1.2),
    p("2", 10, 0, 2.2, 2.2, "N_F", 1.2),
])
add_part("RV1", "275 VAC", "Bourns MOV-10D431K", "disc-10", 45, 33, 0, [
    p("1", -2.5, 0, 1.8, 1.8, "N_F", 0.9),
    p("2", 2.5, 0, 1.8, 1.8, "GND", 0.9),
])
add_part("R1", "10 ohm anti-surge", "Panasonic ERJ-P08J100V", "1206", 42.5, 25, 90, [
    p("1", 1.6, 0, 1.0, 1.2, "N_F", 0),
    p("2", -1.6, 0, 1.0, 1.2, "N_R", 0),
])
add_part("D1", "1000 V", "Diodes S1M-13-F", "SMA", 42.5, 19, 90, [
    p("A", 2.0, 0, 1.4, 1.4, "N_R", 0),
    p("K", -2.0, 0, 1.4, 1.4, "VB1", 0),
])
add_part("C1", "4.7 uF 400 V", "Nichicon UVY2G4R7MPD", "rad-10", 31, 13.5, 90, [
    p("+", 2.5, 0, 1.6, 1.6, "VB1", 0.8),
    p("-", -2.5, 0, 1.6, 1.6, "GND", 0.8),
])
add_part("L1", "1 mH", "Bourns RLB0914-102KL", "rad-9.5", 24, 28.5, 0, [
    p("1", -2.5, 0, 1.8, 1.8, "VB1", 0.9),
    p("2", 2.5, 0, 1.8, 1.8, "VBULK", 0.9),
])
add_part("C16", "4.7 uF 400 V", "Nichicon UVY2G4R7MPD", "rad-10", 20.5, 13.5, 90, [
    p("+", 2.5, 0, 1.6, 1.6, "VBULK", 0.8),
    p("-", -2.5, 0, 1.6, 1.6, "GND", 0.8),
])
# LNK304DG, SO-8C (pin 3 removed). BP 1, FB 2, D 4, S 5-8. Source is the
# switch node; the IC and its feedback ride on it.
add_part("U5", "offline buck", "Power Integrations LNK304DG-TL", "SO-8", 33.5, 28.5, 0, [
    p("BP", -2.7, 1.905, 1.5, 0.6, "BP", 0),
    p("FB", -2.7, 0.635, 1.5, 0.6, "FB", 0),
    p("D", -2.7, -1.905, 1.5, 0.6, "VBULK", 0),
    p("S5", 2.7, -1.905, 1.5, 0.6, "SW", 0),
    p("S6", 2.7, -0.635, 1.5, 0.6, "SW", 0),
    p("S7", 2.7, 0.635, 1.5, 0.6, "SW", 0),
    p("S8", 2.7, 1.905, 1.5, 0.6, "SW", 0),
])
add_part("D3", "600 V ultrafast", "onsemi ES1J", "SMA", 36, 21.5, 0, [
    p("K", -2.0, 0, 1.4, 1.4, "SW", 0),
    p("A", 2.0, 0, 1.4, 1.4, "GND", 0),
])
add_part("L2", "1 mH", "Bourns RLB0914-102KL", "rad-9.5", 36, 46, 0, [
    p("1", -2.5, 0, 1.8, 1.8, "SW", 0.9),
    p("2", 2.5, 0, 1.8, 1.8, "VRECT", 0.9),
])
add_part("C17", "100 nF", "Murata GRM188R71H104KA93", "0603", 30.5, 33.5, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "BP", 0),
    p("2", 0.7, 0, 0.6, 0.7, "SW", 0),
])
add_part("R2", "13.0 k", "Yageo RC0603FR-0713KL", "0603", 34, 33.5, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "FBC", 0),
    p("2", 0.7, 0, 0.6, 0.7, "FB", 0),
])
add_part("R3", "2.05 k", "Yageo RC0603FR-072K05L", "0603", 37, 33.5, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "FB", 0),
    p("2", 0.7, 0, 0.6, 0.7, "SW", 0),
])
add_part("D2", "1000 V", "Diodes S1M-13-F", "SMA", 36, 54, 0, [
    p("A", -2.0, 0, 1.4, 1.4, "VRECT", 0),
    p("K", 2.0, 0, 1.4, 1.4, "FBC", 0),
])
add_part("C18", "10 uF 25 V", "Murata GRM31CR71E106KA12L", "1206", 41, 57, 0, [
    p("1", -1.6, 0, 1.0, 1.2, "FBC", 0),
    p("2", 1.6, 0, 1.0, 1.2, "SW", 0),
])
# 12 V rail, logic side of the plane cut.
add_part("Z1", "15 V 500 mW", "Diodes BZT52C15-7-F", "SOD-123", 50, 58, 0, [
    p("A", -1.6, 0, 0.8, 1.0, "GND", 0),
    p("K", 1.6, 0, 0.8, 1.0, "VRECT", 0),
])
add_part("C2", "470 uF 25 V", "Panasonic EEE-FK1E471P", "rad-10", 52, 50, 0, [
    p("+", -2.5, 0, 1.6, 1.6, "VRECT", 0.8),
    p("-", 2.5, 0, 1.6, 1.6, "GND", 0.8),
])
add_part("R27", "3.3 k preload", "Yageo RC0603FR-073K3L", "0603", 56, 56, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "VRECT", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("U1", "3.3 V LDO", "TI LM2936MP-3.3/NOPB", "SOT-223", 62, 58, 0, [
    p("IN", -3.2, 1.5, 1.2, 1.4, "VRECT", 0),
    p("GND", -3.2, -1.5, 1.2, 1.4, "GND", 0),
    p("OUT", 3.2, 1.5, 1.2, 1.4, "VDD", 0),
    p("TAB", 0, -2.2, 3.5, 1.6, "VDD", 0),
])
add_part("C3", "10 uF 10 V", "Murata GRM21BR71A106KE51L", "0805", 74, 62, 0, [
    p("1", -1.0, 0, 0.9, 1.2, "VDD", 0),
    p("2", 1.0, 0, 0.9, 1.2, "GND", 0),
])
add_part("C4", "100 nF", "Murata GRM188R71H104KA93", "0603", 58, 50, 0, [
    p("1", -0.7, 0, 0.7, 0.8, "VRECT", 0),
    p("2", 0.7, 0, 0.7, 0.8, "GND", 0),
])
# Divider from Neutral. Four 499 k, then 1.00 k to ground (Line).
# 240 V rms -> 0.120 V rms on VIP; the pin sees -v_LN, and the current
# inputs are wired so the product is positive for export.
for i, name in enumerate(("R4", "R5", "R6", "R7")):
    n0 = "N" if i == 0 else f"VD{i}"
    n1 = f"VD{i+1}" if i < 3 else "VIP_S"
    add_part(name, "499 k 0.1% 700 V", "Vishay TNPV1206499KBEEN", "1206",
             20 + i * 7, 7, 0, [
                 p("1", -1.6, 0, 1.0, 1.2, n0, 0),
                 p("2", 1.6, 0, 1.0, 1.2, n1, 0),
             ])
add_part("R8", "1.00 k 0.1%", "Vishay TNPW06031K00BEEA", "0603", 50, 7, 0, [
    p("1", -0.8, 0, 0.7, 0.8, "VIP_S", 0),
    p("2", 0.8, 0, 0.7, 0.8, "GND", 0),
])
add_part("C5", "10 nF C0G", "KEMET C0603C103J3GACTU", "0603", 53, 9.5, 90, [
    p("1", -0.8, 0, 0.7, 0.8, "VIP_S", 0),
    p("2", 0.8, 0, 0.7, 0.8, "GND", 0),
])
add_part("R9", "1.00 k", "Vishay TNPW06031K00BEEA", "0603", 56, 7, 0, [
    p("1", -0.8, 0, 0.7, 0.8, "VIP_S", 0),
    p("2", 0.8, 0, 0.7, 0.8, "VIP", 0),
])
add_part("TVS1", "5 V bidirectional", "Bourns CDSOD323-T05C", "SOD-323", 56, 22, 0, [
    p("1", -1.0, 0, 0.6, 0.6, "VIP", 0),
    p("2", 1.0, 0, 0.6, 0.6, "GND", 0),
])
add_part("R10", "100 ohm 0.1%", "Panasonic ERA-3AEB101V", "0603", 60, 24, 0, [
    p("1", -0.8, 0, 0.7, 0.8, "IIP_F", 0),
    p("2", 0.8, 0, 0.7, 0.8, "IIP", 0),
])
add_part("R11", "100 ohm 0.1%", "Panasonic ERA-3AEB101V", "0603", 60, 28, 0, [
    p("1", -0.8, 0, 0.7, 0.8, "IIN_F", 0),
    p("2", 0.8, 0, 0.7, 0.8, "IIN", 0),
])
add_part("C6", "10 nF C0G", "KEMET C0603C103J3GACTU", "0603", 60, 32, 90, [
    p("1", -0.8, 0, 0.7, 0.8, "IIP", 0),
    p("2", 0.8, 0, 0.7, 0.8, "IIN", 0),
])
# One via where ground (Line) enters the inner ground plane, at the end
# of the top-edge strip from the grid stud.
add_part("TV1", "ground tie", "via-0.30", "via", 48, 66.5, 0, [
    p("1", 0, 0, 0.60, 0.60, "GND", 0.30),
])


def qfn_pads(pins_left, pins_bottom, pins_right, pins_top, pitch, body, along, radial):
    """along is the pad size parallel to the side. It must be < pitch."""
    pads = []
    nL = len(pins_left)
    span = (nL - 1) * pitch
    y0 = span / 2
    x_out = body / 2 + radial / 2 - 0.15
    for i, (name, net) in enumerate(pins_left):
        pads.append(p(name, -x_out, y0 - i * pitch, radial, along, net))
    for i, (name, net) in enumerate(pins_bottom):
        pads.append(p(name, -y0 + i * pitch, -x_out, along, radial, net))
    for i, (name, net) in enumerate(pins_right):
        pads.append(p(name, x_out, -y0 + i * pitch, radial, along, net))
    for i, (name, net) in enumerate(pins_top):
        pads.append(p(name, -y0 + i * pitch, x_out, along, radial, net))
    return pads




# STPM32, DocID025358 Figure 4. Pin 1 is the top of the left side.
st_left = [("CLKOUT", "NC"), ("XTAL2", "XTAL2"), ("XTAL1", "XTAL1"),
           ("LED1", "LED1"), ("LED2", "LED2"), ("INT1", "NC")]
st_bot = [("EN", "STP_EN"), ("VIP1", "VIP"), ("VIN1", "GND"),
          ("IIP1", "IIP"), ("IIN1", "IIN"), ("VREF1", "VREF")]
st_right = [("GND_REF", "GND"), ("GNDA", "GND"), ("VDDA", "VDDA"),
            ("GND_REG", "GND"), ("VCC", "VDD"), ("GNDD", "GND")]
st_top = [("MISO", "STP_MISO"), ("MOSI", "STP_MOSI"), ("SCL", "STP_SCK"),
          ("SCS", "STP_CS_N"), ("VDDD", "VDDD"), ("SYN", "GND")]
add_part("U2", "metrology", "ST STPM32TR", "QFN-24-4x4", 70, 28, 0,
         qfn_pads(st_left, st_bot, st_right, st_top, 0.5, 4.0, 0.28, 0.70)
         + [p("EP", 0, 0, 2.4, 2.4, "GND")])
add_part("Y1", "16.000 MHz", "Abracon ABM8-16.000MHZ-B2-T", "3.2x2.5", 70, 16, 0, [
    p("1", -1.1, 0, 0.9, 1.0, "XTAL1", 0),
    p("2", 1.1, 0, 0.9, 1.0, "XTAL2", 0),
])
add_part("C7", "27 pF C0G", "Murata GRM1885C1H270JA01", "0603", 64, 16, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "XTAL1", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("C8", "27 pF C0G", "Murata GRM1885C1H270JA01", "0603", 76, 16, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "XTAL2", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("C9", "1 uF", "Murata GRM188R71C105KA12", "0603", 78, 22, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "VREF", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("C10", "100 nF", "Murata GRM188R71H104KA93", "0603", 78, 34, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "VDDA", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("C11", "100 nF", "Murata GRM188R71H104KA93", "0603", 62, 34, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "VDDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("C12", "100 nF", "Murata GRM188R71H104KA93", "0603", 62, 22, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
# EN is driven by EC-MINT1 (SPI select). R12 holds it low until then.
add_part("R12", "10 k", "Yageo RC0603FR-0710KL", "0603", 62, 16, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "GND", 0),
    p("2", 0.7, 0, 0.6, 0.7, "STP_EN", 0),
])
add_part("R13", "10 k", "Yageo RC0603FR-0710KL", "0603", 78, 12, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "LED1", 0),
    p("2", 0.7, 0, 0.6, 0.7, "VDD", 0),
])
add_part("R14", "100 ohm", "Yageo RC0603FR-07100RL", "0603", 86, 16, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "LED1", 0),
    p("2", 0.7, 0, 0.6, 0.7, "CF_G", 0),
])
add_part("C13", "100 pF", "Murata GRM1885C1H101JA01", "0603", 86, 12, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "CF_G", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("Q1", "2N7002", "onsemi 2N7002", "SOT-23", 92, 16, 0, [
    p("G", -1.0, 0.9, 0.6, 0.6, "CF_G", 0),
    p("S", -1.0, -0.9, 0.6, 0.6, "GND", 0),
    p("D", 1.0, 0, 0.6, 0.6, "CF_EXP", 0),
])
add_part("R15", "10 k", "Yageo RC0603FR-0710KL", "0603", 92, 22, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "CF_EXP", 0),
])
add_part("R16", "100 k", "Yageo RC0603FR-07100KL", "0603", 86, 64, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "MESH", 0),
])
add_part("R17", "10 k", "Yageo RC0603FR-0710KL", "0603", 92, 58, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "MESH", 0),
    p("2", 0.7, 0, 0.6, 0.7, "MESH_SW", 0),
])
add_part("PT1", "phototransistor", "Vishay VEMT3700", "side-looker", 96, 64, 0, [
    p("C", -1.2, 0, 0.8, 0.8, "VDD", 0),
    p("E", 1.2, 0, 0.8, 0.8, "MESH", 0),
])
add_part("R18", "47 k", "Yageo RC0603FR-0747KL", "0603", 86, 52, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "MESH", 0),
    p("2", 0.7, 0, 0.6, 0.7, "Q2B", 0),
])
add_part("R19", "100 k", "Yageo RC0603FR-07100KL", "0603", 80, 52, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "Q2B", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("Q2", "MMBT3904", "onsemi MMBT3904", "SOT-23", 92, 50, 0, [
    p("B", -1.0, 0.9, 0.6, 0.6, "Q2B", 0),
    p("E", -1.0, -0.9, 0.6, 0.6, "GND", 0),
    p("C", 1.0, 0, 0.6, 0.6, "Q2C", 0),
])
add_part("R20", "10 k", "Yageo RC0603FR-0710KL", "0603", 96, 54, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "Q2C", 0),
    p("2", 0.7, 0, 0.6, 0.7, "Q3B", 0),
])
add_part("Q3", "MMBT3906", "onsemi MMBT3906", "SOT-23", 92, 60, 0, [
    p("B", -1.0, -0.9, 0.6, 0.6, "Q3B", 0),
    p("E", -1.0, 0.9, 0.6, 0.6, "VDD", 0),
    p("C", 1.0, 0, 0.6, 0.6, "ZEROIZE", 0),
])
add_part("R21", "10 k", "Yageo RC0603FR-0710KL", "0603", 84, 46, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "ZEROIZE", 0),
    p("2", 0.7, 0, 0.6, 0.7, "Q2B", 0),
])
add_part("R22", "1.5 M", "Yageo RC0603FR-071M5L", "0603", 84, 40, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "ZEROIZE", 0),
    p("2", 0.7, 0, 0.6, 0.7, "CROW_G", 0),
])
add_part("C14", "2.2 uF", "Murata GRM188R71C225KE15", "0603", 90, 40, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "CROW_G", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
# Signer rail: Q5 is a P-channel switch from VDD, on while CROW_G is low.
# When the delayed ZEROIZE raises CROW_G, Q5 opens and Q4 discharges the
# rail through R23. doc-1.1 fed the signer through 47 ohm and crowbarred
# the rail, which dropped about 1 V at sign current and, when fired, pulled
# 70 mA from a 50 mA regulator. Q4 (Vth 1.0-2.5 V) can turn on before Q5
# (|Vth| 0.4-0.9 V) has opened, since they share CROW_G, so R23 is 1 k: the
# overlap draws at most 3.3 mA, and the rail (C15, 100 nF) still discharges in
# well under a millisecond. doc-1.4 lengthens R22*C14 from 0.22 s to 3.3 s so
# that Q5 stays fully on while the QS7001 signs the one tamper record after
# the wipe (1.1 s ready-poll limit plus a 0.21 s frame); the meter key itself
# is still erased within microseconds of ZEROIZE (M-9).
add_part("Q5", "P-FET rail switch", "Diodes DMG2305UX-7", "SOT-23", 82, 35, 0, [
    p("G", -1.0, 0.9, 0.6, 0.6, "CROW_G", 0),
    p("S", -1.0, -0.9, 0.6, 0.6, "VDD", 0),
    p("D", 1.0, 0, 0.6, 0.6, "QS_VDD", 0),
])
add_part("Q4", "2N7002 discharge", "onsemi 2N7002", "SOT-23", 96, 36, 0, [
    p("G", -1.0, 0.9, 0.6, 0.6, "CROW_G", 0),
    p("S", -1.0, -0.9, 0.6, 0.6, "GND", 0),
    p("D", 1.0, 0, 0.6, 0.6, "QS_DIS", 0),
])
add_part("R23", "1 k", "Panasonic ERJ-8ENF1001V", "1206", 88, 32, 0, [
    p("1", -1.4, 0, 0.8, 1.0, "QS_VDD", 0),
    p("2", 1.4, 0, 0.8, 1.0, "QS_DIS", 0),
])

# EC-MINT1. Top row, left to right, is pins 32 down to 25.
ml = [("VDD", "VDD"), ("VSS", "GND"), ("CF_EXP", "CF_EXP"), ("ZEROIZE", "ZEROIZE"),
      ("RST_N", "RST_N"), ("MINT", "MINT"), ("UART_TX", "UART_TX"), ("QS_SCK", "QS_SCK")]
mb = [("QS_MOSI", "QS_MOSI"), ("QS_MISO", "QS_MISO"), ("QS_CS_N", "QS_CS_N"),
      ("QS_RST_N", "QS_RST"), ("STP_SCK", "STP_SCK"), ("STP_MOSI", "STP_MOSI"),
      ("STP_MISO", "STP_MISO"), ("STP_CS_N", "STP_CS_N")]
mr = [("XI", "XI"), ("PROV_CS", "PROV_CS"), ("PROV_SCK", "PROV_SCK"),
      ("PROV_MOSI", "PROV_MOSI"), ("PROV_MISO", "PROV_MISO"), ("CAL_LOCKED", "CAL_LOCKED"),
      ("VDD2", "VDD"), ("VSS2", "GND")]
mt = [("32", "GND"), ("31", "GND"), ("STP_EN", "STP_EN"), ("FR_MISO", "FR_MISO"),
      ("FR_MOSI", "FR_MOSI"), ("FR_SCK", "FR_SCK"), ("FR_CS_N", "FR_CS_N"),
      ("CF_IMP", "CF_IMP")]
add_part("U3", "schedule die", "EC-MINT1", "QFN-32-5x5", 78, 46, 0,
         qfn_pads(ml, mb, mr, mt, 0.5, 5.0, 0.28, 0.70) + [p("EP", 0, 0, 3.1, 3.1, "GND")])
add_part("Y2", "16.000 MHz CMOS", "Abracon ASE-16.000MHZ-LR-T", "3.2x2.5", 90, 46, 0, [
    p("EN", -1.1, 0.6, 0.6, 0.6, "VDD", 0),
    p("GND", -1.1, -0.6, 0.6, 0.6, "GND", 0),
    p("OUT", 1.1, 0, 0.6, 0.6, "XI", 0),
])
add_part("R24", "100 k", "Yageo RC0603FR-07100KL", "0603", 70, 40, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "RST_N", 0),
])

# QS7001, summary 6658GS page 5. Pin 1 top of the left side.
ql = [("VCC", "QS_VDD"), ("GND", "GND"), ("GPIO6", "NC"), ("GPIO5", "NC"),
      ("NC5", "NC"), ("NC6", "NC"), ("GPIO4", "NC"), ("VCC2", "QS_VDD")]
qb = [("GND9", "GND"), ("JTAG10", "NC"), ("JTAG11", "NC"), ("JTAG12", "NC"),
      ("JTAG13", "NC"), ("VCC14", "QS_VDD"), ("JTAG15", "NC"), ("GND16", "GND")]
qr = [("RST", "QS_RST"), ("GPIO3", "ZEROIZE"), ("SPI_CLK", "QS_SCK"),
      ("SPI_CS", "QS_CS_N"), ("SPI_MOSI", "QS_MOSI"), ("VCC22", "QS_VDD"),
      ("GND23", "GND"), ("SPI_MISO", "QS_MISO")]
qt = [("GND32", "GND"), ("NC31", "NC"), ("SCL", "NC"), ("SDA", "NC"),
      ("GPIO7A", "NC"), ("GPIO7B", "NC"), ("NC26", "NC"), ("NC25", "NC")]
add_part("U4", "ML-DSA element", "SEALSQ QS7001", "QFN-32-5x5", 62, 46, 0,
         qfn_pads(ql, qb, qr, qt, 0.5, 5.0, 0.28, 0.70) + [p("EP", 0, 0, 3.1, 3.1, "GND")])
add_part("C15", "100 nF", "Murata GRM188R71H104KA93", "0603", 70, 64, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "QS_VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("R25", "100 k", "Yageo RC0603FR-07100KL", "0603", 54, 64, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "QS_VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "QS_RST", 0),
])
add_part("R26", "100 ohm", "Yageo RC0603FR-07100RL", "0603", 92, 28, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "UART_TX", 0),
    p("2", 0.7, 0, 0.6, 0.7, "RADIO_TX", 0),
])
add_part("J4", "radio header", "Samtec TSM-106-01-L-SV", "1x6-2.54", 96, 22, 0, [
    p("1", 0, 6.35, 1.6, 1.6, "VRECT", 1.0),
    p("2", 0, 3.81, 1.6, 1.6, "GND", 1.0),
    p("3", 0, 1.27, 1.6, 1.6, "GND", 1.0),
    p("4", 0, -1.27, 1.6, 1.6, "RADIO_TX", 1.0),
    p("5", 0, -3.81, 1.6, 1.6, "NC", 1.0),
    p("6", 0, -6.35, 1.6, 1.6, "NC", 1.0),
])
add_part("J5", "provision, seal over", "pad-1.0", "1x8-1.27", 70, 6, 0, [
    p("1", 0, 0, 0.8, 0.8, "PROV_CS", 0),
    p("2", 1.27, 0, 0.8, 0.8, "PROV_SCK", 0),
    p("3", 2.54, 0, 0.8, 0.8, "PROV_MOSI", 0),
    p("4", 3.81, 0, 0.8, 0.8, "PROV_MISO", 0),
    p("5", 5.08, 0, 0.8, 0.8, "CAL_LOCKED", 0),
    p("6", 6.35, 0, 0.8, 0.8, "GND", 0),
    p("7", 7.62, 0, 0.8, 0.8, "VDD", 0),
    p("8", 8.89, 0, 0.8, 0.8, "MINT", 0),
])
add_part("SW1", "mesh contact", "spring", "pad", 96, 6, 0, [
    p("1", 0, 0, 1.5, 1.5, "MESH_SW", 0),
    p("2", 0, 3.0, 1.5, 1.5, "GND", 0),
])


# Import pulses: LED2 through a second buffer into EC-MINT1 CF_IMP.
add_part("R28", "10 k", "Yageo RC0603FR-0710KL", "0603", 82, 12, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "LED2", 0),
    p("2", 0.7, 0, 0.6, 0.7, "VDD", 0),
])
add_part("R29", "100 ohm", "Yageo RC0603FR-07100RL", "0603", 82, 8, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "LED2", 0),
    p("2", 0.7, 0, 0.6, 0.7, "CF2_G", 0),
])
add_part("C19", "100 pF", "Murata GRM1885C1H101JA01", "0603", 84.5, 4.5, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "CF2_G", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])
add_part("Q6", "2N7002", "onsemi 2N7002", "SOT-23", 88, 8, 0, [
    p("G", -1.0, 0.9, 0.6, 0.6, "CF2_G", 0),
    p("S", -1.0, -0.9, 0.6, 0.6, "GND", 0),
    p("D", 1.0, 0, 0.6, 0.6, "CF_IMP", 0),
])
add_part("R30", "10 k", "Yageo RC0603FR-0710KL", "0603", 92, 10, 90, [
    p("1", -0.7, 0, 0.6, 0.7, "VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "CF_IMP", 0),
])
# FRAM for counters, sequence and the calibration image. SOIC-8:
# 1 /CS, 2 SO, 3 /WP, 4 VSS, 5 SI, 6 SCK, 7 /HOLD, 8 VDD.
add_part("U6", "256 Kbit SPI F-RAM", "Infineon FM25V02A-G", "SOIC-8", 84, 25, 0, [
    p("1", -2.7, 1.905, 1.5, 0.6, "FR_CS_N", 0),
    p("2", -2.7, 0.635, 1.5, 0.6, "FR_MISO", 0),
    p("3", -2.7, -0.635, 1.5, 0.6, "VDD", 0),
    p("4", -2.7, -1.905, 1.5, 0.6, "GND", 0),
    p("5", 2.7, -1.905, 1.5, 0.6, "FR_MOSI", 0),
    p("6", 2.7, -0.635, 1.5, 0.6, "FR_SCK", 0),
    p("7", 2.7, 0.635, 1.5, 0.6, "VDD", 0),
    p("8", 2.7, 1.905, 1.5, 0.6, "VDD", 0),
])
add_part("C20", "100 nF", "Murata GRM188R71H104KA93", "0603", 84, 30, 0, [
    p("1", -0.7, 0, 0.6, 0.7, "VDD", 0),
    p("2", 0.7, 0, 0.6, 0.7, "GND", 0),
])



PKG_BODY = {
    "1206": (3.2, 1.6),
    "0603": (1.6, 0.8),
    "0805": (2.0, 1.25),
    "SMA": (4.5, 2.6),
    "SOD-123": (2.8, 1.6),
    "SOD-323": (1.8, 1.3),
    "SOT-23": (2.9, 1.3),
    "SOT-223": (6.5, 3.5),
    "QFN-24-4x4": (4.0, 4.0),
    "QFN-32-5x5": (5.0, 5.0),
    "3.2x2.5": (3.2, 2.5),
    "shunt-5216": (16.2, 5.2),
    "rad-8": (8.0, 8.0),
    "rad-10": (10.0, 10.0),
    "rad-9.5": (9.5, 9.5),
    "SO-8": (6.0, 5.0),
    "SOIC-8": (6.0, 5.0),
    "disc-10": (10.0, 10.0),
    "box-22.5": (26.5, 11.0),
    "fuse-5x20": (20.0, 5.2),
    "hole-3.2": (6.5, 6.5),
    "1x6-2.54": (2.54, 15.24),
    "1x8-1.27": (11.5, 2.0),
    "side-looker": (4.0, 2.5),
    "pad": (1.6, 4.0),
    "via": (0.6, 0.6),
}


def bodies():
    out = []
    for ref, value, mpn, pkg, x, y, rot in PARTS:
        wh = PKG_BODY.get(pkg)
        if wh is None:
            continue
        w, h = wh if rot % 180 == 0 else (wh[1], wh[0])
        # Header and shunt already store the long axis in the unrotated size
        # when the pad offsets carry the axis. Shunt package is long in X
        # at rot 0; rot 90 swaps it, which is what we want.
        out.append((ref, x - w / 2, y - h / 2, x + w / 2, y + h / 2))
    return out


hits = []
B = bodies()
for i in range(len(B)):
    a, ax0, ay0, ax1, ay1 = B[i]
    for j in range(i + 1, len(B)):
        b, bx0, by0, bx1, by1 = B[j]
        gap_x = max(0, max(ax0, bx0) - min(ax1, bx1)) if False else None
        ox = min(ax1, bx1) - max(ax0, bx0)
        oy = min(ay1, by1) - max(ay0, by0)
        if ox > 0.05 and oy > 0.05:
            hits.append((a, b, round(ox, 2), round(oy, 2)))
if hits:
    print("BODY OVERLAPS")
    for row in hits:
        print(" ", row)
else:
    print("bodies clear", len(B))


occ = [[None for _ in range(NX)] for _ in range(NY)]
REGION_CELLS = set()
PAD_CELLS = set()
REGIONS = []


def mark_rect(x, y, w, h, net):
    x0, y0 = x - w / 2, y - h / 2
    x1, y1 = x + w / 2, y + h / 2
    for iy in range(max(0, int(y0 / CELL)), min(NY, int((y1 - 1e-9) / CELL) + 1)):
        for ix in range(max(0, int(x0 / CELL)), min(NX, int((x1 - 1e-9) / CELL) + 1)):
            cx, cy = (ix + 0.5) * CELL, (iy + 0.5) * CELL
            if not (x0 <= cx <= x1 and y0 <= cy <= y1):
                continue
            prev = occ[iy][ix]
            if prev not in (None, net) and net != "NC" and prev != "NC":
                raise SystemExit(f"pad short {prev} vs {net} at {cx:.2f},{cy:.2f}")
            if net != "NC":
                occ[iy][ix] = net
                PAD_CELLS.add((ix, iy))


for x, y, w, h, net, drill, ref, name in PADS:
    mark_rect(x, y, w, h, net)


def pour(net, x0, y0, x1, y1):
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    REGIONS.append((net, x0, y0, x1, y1))
    ix0 = max(0, int(x0 / CELL))
    iy0 = max(0, int(y0 / CELL))
    ix1 = min(NX - 1, int((x1 - 1e-6) / CELL))
    iy1 = min(NY - 1, int((y1 - 1e-6) / CELL))
    for iy in range(iy0, iy1 + 1):
        for ix in range(ix0, ix1 + 1):
            cx, cy = (ix + 0.5) * CELL, (iy + 0.5) * CELL
            if not (x0 <= cx <= x1 and y0 <= cy <= y1):
                continue
            owner = occ[iy][ix]
            if owner not in (None, net):
                raise SystemExit(f"pour {net} hits {owner} at {cx:.2f},{cy:.2f}")
            occ[iy][ix] = net
            REGION_CELLS.add((ix, iy))


def paint(net, x0, y0, x1, y1, width=0.50):
    """Centerline copper. width is the finished trace width in mm."""
    ix0, iy0 = int(x0 / CELL), int(y0 / CELL)
    ix1, iy1 = int(x1 / CELL), int(y1 / CELL)
    n = max(abs(ix1 - ix0), abs(iy1 - iy0), 1)
    half = max(0, int(round((width / 2) / CELL)))
    for i in range(n + 1):
        ix = ix0 + (ix1 - ix0) * i // n
        iy = iy0 + (iy1 - iy0) * i // n
        for dy in range(-half, half + 1):
            for dx in range(-half, half + 1):
                if max(abs(dx), abs(dy)) > half:
                    continue
                x, y = ix + dx, iy + dy
                if not (0 <= x < NX and 0 <= y < NY):
                    continue
                owner = occ[y][x]
                if owner not in (None, net):
                    raise SystemExit(
                        f"trace {net} hits {owner} at {x * CELL:.2f},{y * CELL:.2f}"
                    )
                occ[y][x] = net


# 40 A force pours. They cover the stud and the force pad, not the Kelvin pad.
# Ground is Line: the grid stud, the grid-side force pad, and a strip along
# the top edge to via TV1, where the inner ground plane begins.
pour("L_GEN", 13.0, 43.0, 24.0, 49.0)
pour("GND", 13.0, 55.0, 24.2, 67.0)
pour("GND", 24.0, 66.0, 48.8, 67.0)
# Neutral: the stud, a strip to the fuse, and a left gutter to the divider.
pour("N", 9.0, 29.0, 15.0, 35.0)
pour("N", 12.0, 35.0, 19.1, 39.1)
pour("N", 9.6, 6.4, 10.4, 29.0)
pour("N", 9.6, 6.4, 19.0, 7.6)

# Fused Neutral: fuse, MOV, surge resistor.
paint("N_F", 38.0, 38.0, 42.5, 38.0, 0.80)
paint("N_F", 42.5, 38.0, 42.5, 26.6, 0.80)
# Low-voltage end of the divider, on the logic side of the plane cut.
paint("VIP_S", 42.6, 7.0, 49.2, 7.0, 0.40)


def covers(ref, pad, net):
    for x, y, w, h, n, drill, r, name in PADS:
        if r == ref and name == pad:
            hit = False
            x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
            for iy in range(max(0, int(y0 / CELL)), min(NY, int(y1 / CELL) + 1)):
                for ix in range(max(0, int(x0 / CELL)), min(NX, int(x1 / CELL) + 1)):
                    if occ[iy][ix] == net:
                        hit = True
            if not hit:
                print("UNCONNECTED", ref, pad, net, "at", round(x, 2), round(y, 2))
                FAILED.append(("unconnected", ref, pad))
            return
    print("NO PAD", ref, pad)
    FAILED.append(("no pad", ref, pad))


FAILED = []
for ref, pad, net in (
    ("H1", "1", "GND"), ("RS", "IG", "GND"), ("TV1", "1", "GND"),
    ("H2", "1", "L_GEN"), ("RS", "FG", "L_GEN"),
    ("H3", "1", "N"), ("F1", "1", "N"), ("R4", "1", "N"),
    ("F1", "2", "N_F"), ("RV1", "1", "N_F"), ("R1", "1", "N_F"),
    ("R7", "2", "VIP_S"), ("R8", "1", "VIP_S"),
):
    covers(ref, pad, net)

# Nets that swing with the mains relative to logic ground (Line).
HV = {"N", "N_F", "N_R", "VD1", "VD2", "VD3", "VB1", "VBULK", "SW", "BP", "FB", "FBC"}
# Nets within a few volts of logic ground, including the shunt itself.
LV = {"GND", "L_GEN", "IIN_F", "IIP_F", "VRECT", "VDD", "VIP_S", "VIP", "QS_VDD"}
NEED = 2.5
# VD3 is the last tap of the divider string: it sits about a quarter of the
# line voltage above VIP_S, across R7 itself (a 700 V TNPV1206). The full
# 2.5 mm line rule does not apply across that one resistor.
NEED_PAIR = {("VD3", "VIP_S"): 1.5}


def cells_of(net):
    return [(x, y) for y in range(NY) for x in range(NX) if occ[y][x] == net]


def min_gap(net, others, need):
    """Cell-centre distance from net to the nearest cell of any net in
    others, searched out to `need`. Returns (gap, where)."""
    r = int(math.ceil(need / CELL)) + 1
    best, where = 999.0, None
    for x, y in cells_of(net):
        for dy in range(-r, r + 1):
            yy = y + dy
            if not 0 <= yy < NY:
                continue
            row = occ[yy]
            for dx in range(-r, r + 1):
                xx = x + dx
                if 0 <= xx < NX and row[xx] in others:
                    d = math.hypot(dx * CELL, dy * CELL)
                    if d < best:
                        best, where = d, (x * CELL, y * CELL, xx * CELL, yy * CELL, row[xx])
    return best, where


worst = []
for net in sorted(HV):
    gap, where = min_gap(net, LV, NEED)
    worst.append((net, round(min(gap, 999), 2)))
    if where and (net, where[4]) in NEED_PAIR:
        if gap < NEED_PAIR[(net, where[4])]:
            print("CLEARANCE", net, "to", where[4], round(gap, 2), where[:4])
            FAILED.append(("clearance", net, where[4]))
        # The rest of the logic nets still get the full rule.
        gap, where = min_gap(net, LV - {where[4]}, NEED)
    if gap < NEED:
        print("CLEARANCE", net, "to", where[4], round(gap, 2), where[:4])
        FAILED.append(("clearance", net, where[4]))
# The inner planes start at x = 46. Mains copper stays 2.5 mm short of them,
# and 3 mm from the board edge.
for net in sorted(HV):
    for x, y in cells_of(net):
        cx, cy = (x + 0.5) * CELL, (y + 0.5) * CELL
        if cx > 46.0 - NEED:
            FAILED.append(("plane", net, cx, cy))
            print("PLANE", net, "copper at", cx, cy, "is within 2.5 mm of the plane cut")
            break
        if min(cx, cy, GW - cx, GH - cy) < 3.0:
            FAILED.append(("edge", net, cx, cy))
            print("EDGE", net, "copper at", cx, cy)
            break
print("clearance (mains net, gap to logic ground nets in mm; 999 = none within 2.5)", worst)
if FAILED:
    raise SystemExit(f"{len(FAILED)} layout rule failures")


def gerber_header(name):
    return (
        f"G04 EC-SEAL1 rev B {name} v0.0.1 doc-1.2*\n"
        "%FSLAX46Y46*%\n%MOMM*%\n%LPD*%\n"
        "%ADD10C,0.250*%\n%ADD11C,0.600*%\n%ADD12C,0.150*%\n"
    )


def flash(x, y, d):
    return f"D{d}*\nX{int(round(x * 1e6)):07d}Y{int(round(y * 1e6)):07d}D03*\n"


def draw_seg(x0, y0, x1, y1, d=10):
    return (
        f"D{d}*\n"
        f"X{int(round(x0 * 1e6)):07d}Y{int(round(y0 * 1e6)):07d}D02*\n"
        f"X{int(round(x1 * 1e6)):07d}Y{int(round(y1 * 1e6)):07d}D01*\n"
    )


def region(x0, y0, x1, y1):
    def c(v):
        return f"X{int(round(v * 1e6)):07d}"
    return (
        "G36*\n"
        f"{c(x0)}Y{int(round(y0 * 1e6)):07d}D02*\n"
        f"{c(x1)}Y{int(round(y0 * 1e6)):07d}D01*\n"
        f"{c(x1)}Y{int(round(y1 * 1e6)):07d}D01*\n"
        f"{c(x0)}Y{int(round(y1 * 1e6)):07d}D01*\n"
        f"{c(x0)}Y{int(round(y0 * 1e6)):07d}D01*\n"
        "G37*\n"
    )


top = [gerber_header("F.Cu")]
for net, x0, y0, x1, y1 in REGIONS:
    top.append(f"G04 pour {net}*\n")
    top.append(region(x0, y0, x1, y1))
for y in range(NY):
    for x in range(NX):
        if (x, y) in REGION_CELLS or (x, y) in PAD_CELLS:
            continue
        n = occ[y][x]
        if not n:
            continue
        cx, cy = (x + 0.5) * CELL, (y + 0.5) * CELL
        if x + 1 < NX and (x + 1, y) not in REGION_CELLS and occ[y][x + 1] == n:
            top.append(draw_seg(cx, cy, cx + CELL, cy, 10))
        if y + 1 < NY and (x, y + 1) not in REGION_CELLS and occ[y + 1][x] == n:
            top.append(draw_seg(cx, cy, cx, cy + CELL, 10))
ap = 20
for x, y, w, h, net, drill, ref, name in PADS:
    if drill:
        dia = max(w, h)
        top.append(f"%ADD{ap}C,{dia:.3f}*%\n" + flash(x, y, ap))
    else:
        top.append(f"%ADD{ap}R,{w:.3f}X{h:.3f}*%\n" + flash(x, y, ap))
    ap += 1
top.append("M02*\n")

# Bottom is the fanout layer. No pour: a pour here would short the escape.
bot = [gerber_header("B.Cu"), "G04 fanout layer, no copper released*\n", "M02*\n"]

# Inner planes. The house punches antipads when it adds fanout vias.
in1 = [gerber_header("In1.Cu GND"), region(46.0, 2.0, 98.0, 68.0), "M02*\n"]
in2 = [gerber_header("In2.Cu VDD"), region(46.0, 2.0, 98.0, 68.0), "M02*\n"]

edge = (
    gerber_header("Edge.Cuts")
    + draw_seg(0, 0, GW, 0, 11)
    + draw_seg(GW, 0, GW, GH, 11)
    + draw_seg(GW, GH, 0, GH, 11)
    + draw_seg(0, GH, 0, 0, 11)
    + "M02*\n"
)

mask = [gerber_header("F.Mask")]
ap = 40
for x, y, w, h, net, drill, ref, name in PADS:
    if drill:
        dia = max(w, h) + 0.10
        mask.append(f"%ADD{ap}C,{dia:.3f}*%\n" + flash(x, y, ap))
    else:
        mask.append(f"%ADD{ap}R,{w + 0.10:.3f}X{h + 0.10:.3f}*%\n" + flash(x, y, ap))
    ap += 1
mask.append("M02*\n")

silk = [gerber_header("F.Silk")]
silk.append(draw_seg(46, 2, 46, 68, 12))
silk.append("M02*\n")

drill_lines = ["M48\nMETRIC,TZ\n"]
tools = collections.defaultdict(list)
for x, y, w, h, net, drill_d, ref, name in PADS:
    if drill_d:
        tools[f"{drill_d:.2f}"].append((x, y))
body = []
for n, (key, pts) in enumerate(tools.items(), start=1):
    drill_lines.append(f"T{n:02d}C{key}\n")
    body.append(f"T{n:02d}\n")
    for x, y in pts:
        body.append(f"X{x * 1000:.3f}Y{y * 1000:.3f}\n")
drill_lines.append("%\n")
drill_lines.extend(body)
drill_lines.append("M30\n")

open(os.path.join(GER, "ec-seal1-F_Cu.gbr"), "w").write("".join(top))
open(os.path.join(GER, "ec-seal1-B_Cu.gbr"), "w").write("".join(bot))
open(os.path.join(GER, "ec-seal1-In1_Cu.gbr"), "w").write("".join(in1))
open(os.path.join(GER, "ec-seal1-In2_Cu.gbr"), "w").write("".join(in2))
open(os.path.join(GER, "ec-seal1-Edge_Cuts.gbr"), "w").write(edge)
open(os.path.join(GER, "ec-seal1-F_Mask.gbr"), "w").write("".join(mask))
open(os.path.join(GER, "ec-seal1-F_Silk.gbr"), "w").write("".join(silk))
open(os.path.join(GER, "ec-seal1-PTH.drl"), "w").write("".join(drill_lines))

with open(os.path.join(OUT, "centroid.csv"), "w") as f:
    f.write("ref,x_mm,y_mm,rot,value,mpn,package\n")
    for ref, value, mpn, pkg, x, y, rot in PARTS:
        f.write(f"{ref},{x:.3f},{y:.3f},{rot},\"{value}\",{mpn},{pkg}\n")

nets = collections.defaultdict(list)
for x, y, w, h, net, drill, ref, name in PADS:
    if net != "NC":
        nets[net].append(f"{ref}.{name}")
with open(os.path.join(OUT, "netlist.txt"), "w") as f:
    f.write("# EC-SEAL1 rev B netlist, v0.0.1 (doc-1.2).\n")
    f.write("# Finished copper is the pours and the traces in the Gerber.\n")
    f.write("# Every other connection is this list, fanned out by the board house.\n")
    f.write("# GND is Line on the grid side of the shunt: H1, RS.IG and the logic ground.\n")
    f.write("# N is Neutral (H3). The whole board is at mains potential.\n")
    for net in sorted(nets):
        f.write(f"\nNET {net}\n")
        for pin in nets[net]:
            f.write(f"  {pin}\n")

with open(os.path.join(OUT, "BOM.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["ref", "qty", "value", "mpn", "package"])
    grouped = collections.OrderedDict()
    for ref, value, mpn, pkg, x, y, rot in PARTS:
        grouped.setdefault((value, mpn, pkg), []).append(ref)
    for (value, mpn, pkg), refs in grouped.items():
        w.writerow([" ".join(refs), len(refs), value, mpn, pkg])

# Placement drawing. Origin lower left, y up. Not fabrication artwork.
svg = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    f"<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='760' viewBox='-5 -5 110 80'>",
    "<rect x='0' y='0' width='100' height='70' fill='#1a1e22' stroke='#888' stroke-width='0.3'/>",
    "<g transform='translate(0,70) scale(1,-1)'>",
    "<rect x='46' y='2' width='52' height='66' fill='#243040'/>",
]
colors = {
    "N": "#e85d4c", "L_GEN": "#4aa3df", "N_F": "#e39b3b",
    "VB1": "#e39b3b", "VBULK": "#e39b3b", "SW": "#e39b3b", "GND": "#4aa3df",
    "VDD": "#d6c15a", "QS_VDD": "#c084fc", "VRECT": "#f0a060",
}
for net, x0, y0, x1, y1 in REGIONS:
    svg.append(
        f"<rect x='{x0:.2f}' y='{y0:.2f}' width='{x1 - x0:.2f}' height='{y1 - y0:.2f}' "
        f"fill='{colors.get(net, '#8a8f86')}' fill-opacity='0.9'/>"
    )
for x, y, w, h, net, drill, ref, name in PADS:
    svg.append(
        f"<rect x='{x - w / 2:.2f}' y='{y - h / 2:.2f}' width='{w:.2f}' height='{h:.2f}' "
        f"fill='{colors.get(net, '#666')}' stroke='#111' stroke-width='0.04'/>"
    )
for ref, x0, y0, x1, y1 in B:
    svg.append(
        f"<rect x='{x0:.2f}' y='{y0:.2f}' width='{x1 - x0:.2f}' height='{y1 - y0:.2f}' "
        f"fill='none' stroke='#ddd' stroke-width='0.15'/>"
    )
svg.append("</g>")
for ref, value, mpn, pkg, x, y, rot in PARTS:
    svg.append(
        f"<text x='{x:.2f}' y='{70 - y:.2f}' fill='#eee' font-size='1.6' "
        f"text-anchor='middle' font-family='sans-serif'>{ref}</text>"
    )
svg.append("</svg>")
open(os.path.join(OUT, "placement.svg"), "w").write("\n".join(svg))
img = Image.new("RGB", (NX * 3, NY * 3), (18, 22, 26))
px = img.load()
col = {
    "N": (232, 93, 76), "L_GEN": (74, 163, 223), "N_F": (227, 155, 59),
    "GND": (74, 163, 223), "VIP_S": (120, 180, 120),
}
for y in range(NY):
    for x in range(NX):
        n = occ[y][x]
        if not n:
            continue
        c = col.get(n, (150, 150, 140))
        for dy in range(3):
            for dx in range(3):
                px[x * 3 + dx, (NY - 1 - y) * 3 + dy] = c
img.save(os.path.join(OUT, "placement.png"))
print("wrote", GER, "regions", len(REGIONS), "pads", len(PADS))
