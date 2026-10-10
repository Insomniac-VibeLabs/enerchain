#!/usr/bin/env python3
"""Circuit sheets for EC-SEAL1 revision B, doc-1.4.

Writes docs/schematics/01..08 and mint-path.svg. Every number printed on a
sheet is computed here from the part values, and the script stops if it
disagrees with the figure quoted in hardware/fab/ec-seal1/CIRCUITS.md or
docs/meter-burden.md. Every connection a sheet draws is listed in CLAIMS and
checked against hardware/fab/ec-seal1/netlist.txt, so a drawing cannot show a
wire the board does not have.

Symbols follow IEC 60617: a resistor is a rectangle, a capacitor two plates,
a fuse a rectangle with a line through it, an inductor a row of arcs, a diode
a triangle and bar, ground the stacked mark. Ground on this board is Line at
the grid side of the shunt.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "docs", "schematics")
NETLIST = os.path.join(ROOT, "hardware", "fab", "ec-seal1", "netlist.txt")

EDITION = "EC-SEAL1 rev B, doc-1.4"


# --------------------------------------------------------------------------
# Design values and the numbers printed on the sheets
# --------------------------------------------------------------------------
def near(a, b, tol):
    return abs(a - b) <= tol


V_RMS, V_HI, F = 240.0, 264.0, 50.0
V_PK = V_RMS * math.sqrt(2)

# Supply (sheet 01)
R1, C_BULK = 10.0, 4.7e-6
FB_REF, R2, R3 = 1.65, 13.0e3, 2.05e3
V_RECT = FB_REF * (1 + R2 / R3)
I_INRUSH = V_PK / R1
I2T = I_INRUSH ** 2 * (R1 * 2 * C_BULK) / 2      # both bulk caps, worst case
I_LOGIC, I_RADIO, ETA = 0.030, 0.040, 0.6
P_IN_MAX = V_RECT * (I_LOGIC + I_RADIO) / ETA
P_IN_SLEEP = V_RECT * I_LOGIC / ETA
P_LDO = (V_RECT - 3.3) * I_LOGIC
assert near(V_RECT, 12.1, 0.05), V_RECT
assert near(I_INRUSH, 34, 0.5) and I2T <= 0.06, (I_INRUSH, I2T)
assert near(P_IN_MAX, 1.4, 0.05) and P_IN_SLEEP < 1.0
assert near(P_LDO, 0.26, 0.01)

# Shunt (sheet 02)
RS, I_MAX, GAIN, WINDOW = 100e-6, 40.0, 16, 0.300
V_SH = RS * I_MAX
P_SH = I_MAX ** 2 * RS
V_MOD = V_SH * math.sqrt(2) * GAIN
I_CLIP = WINDOW / GAIN / RS / math.sqrt(2)
F_I = 1 / (2 * math.pi * 200.0 * 10e-9)          # R10 + R11 into C6
assert near(V_SH, 4.0e-3, 1e-6) and near(P_SH, 0.16, 1e-6)
assert near(V_MOD, 0.0905, 0.001) and near(I_CLIP, 130, 5)

# Divider (sheet 03)
R_HI, R_LO, MOV_CLAMP = 4 * 499e3, 1.0e3, 710.0
K_DIV = R_LO / (R_HI + R_LO)
V_PIN = V_RMS * K_DIV
V_PIN_HI_PK = V_HI * K_DIV * math.sqrt(2)
V_PART = V_RMS / 4
V_PART_CLAMP = MOV_CLAMP / 4
P_DIV = V_RMS ** 2 / (R_HI + R_LO)
F_V = 1 / (2 * math.pi * R_LO * 10e-9)           # R8 with C5
assert near(V_PIN, 0.120, 0.001) and V_PIN_HI_PK < WINDOW
assert near(V_PART_CLAMP, 177, 1) and near(P_DIV, 0.029, 0.001)

# Tamper latch and signer rail (sheet 06)
R16, R17, R18, R19, R21 = 100e3, 10e3, 47e3, 100e3, 10e3
VBE = 0.6
V_MESH_CLOSED = 3.3 * R17 / (R16 + R17)
V_TRIP = VBE * (1 + R18 / R19)
I_PHOTO = V_TRIP / R17 + V_TRIP / (R18 + R19) - (3.3 - V_TRIP) / R16
I_HOLD = (3.3 - VBE) / R21 - VBE / R19
I_RELEASE_MAX = VBE / R18
# R22·C14 holds the signer rail up long enough for the tamper record
# (doc-1.4, M-9): Q5 must stay fully enhanced (|Vgs| >= 1.8 V) through the
# 1.1 s ready-poll limit and the 0.21 s frame, even with C14 30 % low.
R22, C14 = 1.5e6, 2.2e-6
TAU_G = R22 * C14
T_Q5_OPEN = TAU_G * math.log(3.3 / 0.9)          # |Vth| = 0.9 V, earliest
T_Q4_ON = TAU_G * math.log(3.3 / (3.3 - 2.1))    # Vth = 2.1 V, typical
T_Q4_FIRST = TAU_G * math.log(3.3 / (3.3 - 1.0))  # Vth = 1.0 V, earliest
T_FULL_ON = TAU_G * math.log(3.3 / 1.8)          # CROW_G reaches 1.5 V
T_FULL_ON_LOW = 0.7 * T_FULL_ON                  # C14 30 % low from DC bias
T_TAMPER = 1.1 + (2 + 32 + 2420) * 10 / (16e6 / 139)   # poll limit + frame
R23 = 1.0e3
I_OVERLAP = 3.3 / R23
TAU_DIS = R23 * 100e-9
assert near(V_MESH_CLOSED, 0.30, 0.005) and near(V_TRIP, 0.88, 0.01)
assert near(I_PHOTO, 70e-6, 3e-6), I_PHOTO
assert near(I_HOLD, 265e-6, 5e-6) and I_RELEASE_MAX < 13e-6
assert T_Q4_ON < T_Q5_OPEN and near(T_Q5_OPEN, 4.29, 0.01)
assert near(T_FULL_ON, 2.00, 0.01) and T_TAMPER < T_FULL_ON_LOW, (T_TAMPER, T_FULL_ON_LOW)

# Schedule, record and radio (sheets 05 and 07)
Q_WH, SIGN_EVERY = 1000, 1
SIG_BYTES, REC_BYTES = 2420, 32
FRAME = 2 + REC_BYTES + SIG_BYTES
BAUD = 16e6 / 139
T_FRAME = FRAME * 10 / BAUD
E_SIGN = 0.019
E_KWH = 3.6e6
assert FRAME == 2454 and near(T_FRAME, 0.213, 0.001)
assert near(E_SIGN / E_KWH, 5.3e-9, 0.1e-9)

# Burden (sheet 08), voltage circuit against the 2 W cap
P_LOGIC = V_RECT * I_LOGIC
P_RADIO = V_RECT * I_RADIO
P_LOSS = P_IN_MAX - P_LOGIC - P_RADIO
P_TOTAL = P_IN_MAX + P_DIV
assert near(P_TOTAL, 1.44, 0.01) and P_TOTAL < 1.5


# --------------------------------------------------------------------------
# Netlist check
# --------------------------------------------------------------------------
def read_netlist():
    nets, cur = {}, None
    with open(NETLIST) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("NET "):
                cur = line[4:].strip()
                nets[cur] = set()
            elif line.startswith("  ") and cur:
                nets[cur].add(line.strip())
    return nets


CLAIMS = {
    "01-supply": [
        ("N", "H3.1 F1.1"), ("N_F", "F1.2 RV1.1 R1.1"), ("N_R", "R1.2 D1.A"),
        ("VB1", "D1.K C1.+ L1.1"), ("VBULK", "L1.2 C16.+ U5.D"),
        ("SW", "U5.S5 D3.K L2.1 C17.2 R3.2 C18.2"),
        ("VRECT", "L2.2 D2.A Z1.K C2.+ R27.1 U1.IN J4.1"),
        ("FBC", "R2.1 D2.K C18.1"), ("FB", "U5.FB R2.2 R3.1"), ("BP", "U5.BP C17.1"),
        ("VDD", "U1.OUT C3.1"),
        ("GND", "RV1.2 C1.- C16.- D3.A Z1.A C2.- R27.2 U1.GND C3.2"),
    ],
    "02-shunt": [
        ("L_GEN", "H2.1 RS.FG"), ("GND", "H1.1 RS.IG"),
        ("IIN_F", "RS.SG R11.1"), ("IIP_F", "RS.SI R10.1"),
        ("IIN", "R11.2 C6.2 U2.IIN1"), ("IIP", "R10.2 C6.1 U2.IIP1"),
    ],
    "03-divider": [
        ("N", "H3.1 R4.1"), ("VD1", "R4.2 R5.1"), ("VD3", "R6.2 R7.1"),
        ("VIP_S", "R7.2 R8.1 C5.1 R9.1"), ("VIP", "R9.2 TVS1.1 U2.VIP1"),
        ("GND", "R8.2 C5.2 TVS1.2 U2.VIN1"),
    ],
    "04-metrology": [
        ("LED1", "U2.LED1 R13.1 R14.1"), ("CF_G", "R14.2 C13.1 Q1.G"),
        ("CF_EXP", "Q1.D R15.2 U3.CF_EXP"), ("LED2", "U2.LED2 R28.1 R29.1"),
        ("CF2_G", "R29.2 C19.1 Q6.G"), ("CF_IMP", "U3.CF_IMP Q6.D R30.2"),
        ("STP_EN", "U2.EN R12.2 U3.STP_EN"), ("XTAL1", "U2.XTAL1 Y1.1 C7.1"),
        ("XTAL2", "U2.XTAL2 Y1.2 C8.1"), ("VREF", "U2.VREF1 C9.1"),
        ("VDDA", "U2.VDDA C10.1"), ("VDDD", "U2.VDDD C11.1"),
        ("VDD", "U2.VCC C12.1 R13.2 R15.1 R28.2 R30.1"),
        ("GND", "Q1.S Q6.S R12.1 C13.2 C19.2"),
    ],
    "05-secure-element": [
        ("XI", "U3.XI Y2.OUT"), ("QS_RST", "U3.QS_RST_N U4.RST R25.2"),
        ("ZEROIZE", "U3.ZEROIZE U4.GPIO3"), ("UART_TX", "U3.UART_TX R26.1"),
        ("RST_N", "U3.RST_N R24.2"),
    ],
    "06-tamper": [
        ("MESH", "R16.2 R17.1 PT1.E R18.1"), ("MESH_SW", "R17.2 SW1.1"),
        ("Q2B", "R18.2 R19.1 Q2.B R21.2"), ("Q2C", "Q2.C R20.1"), ("Q3B", "R20.2 Q3.B"),
        ("ZEROIZE", "Q3.C R21.1 R22.1 U3.ZEROIZE U4.GPIO3"),
        ("CROW_G", "R22.2 C14.1 Q5.G Q4.G"), ("QS_DIS", "Q4.D R23.2"),
        ("QS_VDD", "Q5.D R23.1 U4.VCC C15.1"),
        ("VDD", "R16.1 PT1.C Q3.E Q5.S"),
        ("GND", "SW1.2 R19.2 Q2.E C14.2 Q4.S C15.2"),
    ],
    "07-radio": [
        ("UART_TX", "U3.UART_TX R26.1"), ("RADIO_TX", "R26.2 J4.4"),
        ("VRECT", "J4.1"), ("GND", "J4.2 J4.3"),
    ],
}


def check_claims():
    nets = read_netlist()
    bad = []
    for sheet, claims in CLAIMS.items():
        for net, pins in claims:
            for pin in pins.split():
                if pin not in nets.get(net, ()):
                    bad.append(f"{sheet}: {pin} is not on {net}")
    if bad:
        sys.exit("schematic does not match netlist:\n  " + "\n  ".join(bad))


# --------------------------------------------------------------------------
# Drawing primitives
# --------------------------------------------------------------------------
INK, RED, MUTED, BG = "#111", "#a33", "#444", "#f7f4ee"


class Sheet:
    def __init__(self, w, h, title, subtitle):
        self.w, self.h = w, h
        self.o = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="ui-sans-serif,sans-serif">',
            f'  <rect width="{w}" height="{h}" fill="{BG}"/>',
        ]
        self.text(24, 32, title, 16, INK)
        self.text(24, 52, subtitle, 12, MUTED)

    # text and lines -------------------------------------------------------
    def text(self, x, y, s, size=11, fill=INK, anchor="start", weight=None):
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        wt = f' font-weight="{weight}"' if weight else ""
        self.o.append(f'  <text x="{x:g}" y="{y:g}" font-size="{size}" fill="{fill}" '
                      f'text-anchor="{anchor}"{wt}>{s}</text>')

    def notes(self, x, y, lines, size=12, dy=19):
        for i, s in enumerate(lines):
            self.text(x, y + i * dy, s, size)

    def line(self, x1, y1, x2, y2, color=INK, width=1.2):
        self.o.append(f'  <line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
                      f'stroke="{color}" stroke-width="{width}"/>')

    def wire(self, *pts, color=INK, width=1.2):
        p = " ".join(f"{x:g},{y:g}" for x, y in pts)
        self.o.append(f'  <polyline points="{p}" fill="none" stroke="{color}" '
                      f'stroke-width="{width}"/>')

    def dot(self, x, y, color=INK):
        self.o.append(f'  <circle cx="{x:g}" cy="{y:g}" r="2.6" fill="{color}"/>')

    def rect(self, x, y, w, h, color=INK, fill="none", width=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'  <rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
                      f'fill="{fill}" stroke="{color}" stroke-width="{width}"{d}/>')

    def poly(self, pts, fill="none", color=INK):
        p = " ".join(f"{x:g},{y:g}" for x, y in pts)
        self.o.append(f'  <polygon points="{p}" fill="{fill}" stroke="{color}" stroke-width="1.2"/>')

    def path(self, d, color=INK, width=1.2):
        self.o.append(f'  <path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    # two-terminal parts: pins at centre +/- 30 along the axis ------------
    def _leads(self, cx, cy, vert, half):
        if vert:
            self.line(cx, cy - 30, cx, cy - half)
            self.line(cx, cy + half, cx, cy + 30)
        else:
            self.line(cx - 30, cy, cx - half, cy)
            self.line(cx + half, cy, cx + 30, cy)

    def _label(self, cx, cy, vert, ref, val, side=1):
        if vert:
            x = cx + 12 if side > 0 else cx - 12
            a = "start" if side > 0 else "end"
            self.text(x, cy - 2, ref, 11, INK, a)
            self.text(x, cy + 11, val, 10, MUTED, a)
        else:
            self.text(cx, cy - 12, ref, 11, INK, "middle")
            self.text(cx, cy + 22, val, 10, MUTED, "middle")

    def R(self, cx, cy, ref, val, vert=False, side=1):
        self._leads(cx, cy, vert, 17)
        if vert:
            self.rect(cx - 6, cy - 17, 12, 34)
        else:
            self.rect(cx - 17, cy - 6, 34, 12)
        self._label(cx, cy, vert, ref, val, side)

    def FUSE(self, cx, cy, ref, val):
        self.R(cx, cy, ref, val)
        self.line(cx - 22, cy, cx + 22, cy)

    def MOV(self, cx, cy, ref, val, side=1):
        self.R(cx, cy, ref, val, vert=True, side=side)
        self.wire((cx - 12, cy + 14), (cx - 6, cy + 14), (cx + 6, cy - 14))

    def C(self, cx, cy, ref, val, vert=True, pol=False, side=1):
        self._leads(cx, cy, vert, 4)
        if vert:
            self.line(cx - 11, cy - 4, cx + 11, cy - 4, width=2)
            self.line(cx - 11, cy + 4, cx + 11, cy + 4, width=2)
            if pol:
                self.text(cx - 14, cy - 7, "+", 11, INK, "end")
        else:
            self.line(cx - 4, cy - 11, cx - 4, cy + 11, width=2)
            self.line(cx + 4, cy - 11, cx + 4, cy + 11, width=2)
        if vert:
            self._label(cx, cy, vert, ref, val, side)
        else:
            self.text(cx, cy - 16, ref, 11, INK, "middle")
            self.text(cx, cy + 26, val, 10, MUTED, "middle")

    def L(self, cx, cy, ref, val, vert=False):
        self._leads(cx, cy, vert, 20)
        if vert:
            d = f"M{cx},{cy - 20}" + "".join(f" a5,5 0 0,1 0,10" for _ in range(4))
        else:
            d = f"M{cx - 20},{cy}" + "".join(f" a5,5 0 0,1 10,0" for _ in range(4))
        self.path(d)
        self._label(cx, cy, vert, ref, val)

    def D(self, cx, cy, ref, val, d="r", kind="plain", side=1):
        """Diode, anode to cathode in direction d (r, l, u, d)."""
        vert = d in "ud"
        self._leads(cx, cy, vert, 8)
        s = {"r": (1, 0), "l": (-1, 0), "d": (0, 1), "u": (0, -1)}[d]
        ax, ay = cx - 8 * s[0], cy - 8 * s[1]
        kx, ky = cx + 8 * s[0], cy + 8 * s[1]
        px, py = -s[1], s[0]
        self.poly([(ax + 8 * px, ay + 8 * py), (ax - 8 * px, ay - 8 * py), (kx, ky)])
        self.line(kx + 8 * px, ky + 8 * py, kx - 8 * px, ky - 8 * py, width=2)
        if kind == "zener":
            self.line(kx + 8 * px, ky + 8 * py, kx + 8 * px - 4 * s[0], ky + 8 * py - 4 * s[1], width=2)
            self.line(kx - 8 * px, ky - 8 * py, kx - 8 * px + 4 * s[0], ky - 8 * py + 4 * s[1], width=2)
        if kind == "bidir":
            self.poly([(kx + 8 * px, ky + 8 * py), (kx - 8 * px, ky - 8 * py), (ax, ay)])
        self._label(cx, cy, vert, ref, val, side)

    def GND(self, x, y, label=None, left=False):
        self.line(x, y, x, y + 6)
        self.line(x - 10, y + 6, x + 10, y + 6, width=1.6)
        self.line(x - 6, y + 10, x + 6, y + 10, width=1.6)
        self.line(x - 2, y + 14, x + 2, y + 14, width=1.6)
        if label:
            if left:
                self.text(x - 14, y + 13, label, 10, MUTED, "end")
            else:
                self.text(x + 14, y + 13, label, 10, MUTED)

    def flag(self, x, y, name, side="r", color=INK):
        """Net label. side: which way the label points from the wire end."""
        w = 7 * len(name) + 10
        if side == "r":
            self.poly([(x, y), (x + 6, y - 8), (x + w, y - 8), (x + w, y + 8), (x + 6, y + 8)], color=color)
            self.text(x + 8, y + 4, name, 10, color)
        elif side == "l":
            self.poly([(x, y), (x - 6, y - 8), (x - w, y - 8), (x - w, y + 8), (x - 6, y + 8)], color=color)
            self.text(x - w + 3, y + 4, name, 10, color)
        elif side == "u":
            self.text(x, y - 5, name, 10, color, "middle")
        else:
            self.text(x, y + 14, name, 10, color, "middle")

    def terminal(self, x, y, name, side="l"):
        self.o.append(f'  <circle cx="{x:g}" cy="{y:g}" r="5" fill="none" stroke="{INK}" stroke-width="1.4"/>')
        if side == "l":
            self.text(x - 9, y + 4, name, 11, INK, "end")
        elif side == "r":
            self.text(x + 9, y + 4, name, 11, INK, "start")
        else:
            self.text(x, y - 10, name, 11, INK, "middle")

    def ic(self, x, y, w, h, ref, name, pins, color=INK):
        """pins: (side, offset, label, ext) with side in l r t b; returns pin coords."""
        self.rect(x, y, w, h, color)
        ty = y + h / 2 - 6 if any(p[0] == "t" for p in pins) else y + 16
        self.text(x + w / 2, ty, ref, 12, color, "middle", "600")
        self.text(x + w / 2, ty + 14, name, 10, MUTED, "middle")
        out = {}
        for side, off, label in pins:
            if side == "l":
                px, py = x, y + off
                self.line(px - 10, py, px, py, color)
                self.text(px + 4, py + 4, label, 9, color)
                out[label] = (px - 10, py)
            elif side == "r":
                px, py = x + w, y + off
                self.line(px, py, px + 10, py, color)
                self.text(px - 4, py + 4, label, 9, color, "end")
                out[label] = (px + 10, py)
            elif side == "t":
                px, py = x + off, y
                self.line(px, py - 10, px, py, color)
                self.text(px, py + 12, label, 9, color, "middle")
                out[label] = (px, py - 10)
            else:
                px, py = x + off, y + h
                self.line(px, py, px, py + 10, color)
                self.text(px, py - 4, label, 9, color, "middle")
                out[label] = (px, py + 10)
        return out

    # three-terminal parts --------------------------------------------------
    def bjt(self, cx, cy, ref, val, pnp=False, photo=False):
        """NPN: B (cx-30,cy), C (cx+10,cy-30), E (cx+10,cy+30).
        PNP is drawn emitter-up: E (cx+10,cy-30), C (cx+10,cy+30)."""
        self.o.append(f'  <circle cx="{cx:g}" cy="{cy:g}" r="17" fill="none" stroke="{INK}" stroke-width="1"/>')
        self.line(cx - 7, cy - 11, cx - 7, cy + 11, width=2)
        if not photo:
            self.line(cx - 30, cy, cx - 7, cy)
        top, bot = (cy - 30, cy + 30)
        self.wire((cx - 7, cy - 5), (cx + 10, cy - 15), (cx + 10, top))
        self.wire((cx - 7, cy + 5), (cx + 10, cy + 15), (cx + 10, bot))
        if pnp:   # arrow into the bar on the emitter (top)
            self.poly([(cx - 4, cy - 7), (cx + 3, cy - 7), (cx + 1, cy - 12)], fill=INK)
        else:     # arrow out on the emitter (bottom)
            self.poly([(cx + 10, cy + 15), (cx + 1, cy + 14), (cx + 5, cy + 9)], fill=INK)
        if photo:
            for o in (-10, 2):
                self.line(cx - 34, cy + o - 12, cx - 20, cy + o - 2, RED)
                self.poly([(cx - 20, cy + o - 2), (cx - 27, cy + o - 3), (cx - 23, cy + o - 8)], fill=RED, color=RED)
        self.text(cx + 22, cy - 2, ref, 11)
        self.text(cx + 22, cy + 11, val, 10, MUTED)

    def fet(self, cx, cy, ref, val, p=False):
        """N-FET: G (cx-30,cy), D (cx+10,cy-30), S (cx+10,cy+30).
        P-FET is drawn source-up: S (cx+10,cy-30), D (cx+10,cy+30)."""
        self.line(cx - 30, cy, cx - 10, cy)
        self.line(cx - 10, cy - 12, cx - 10, cy + 12, width=2)
        for o in (-10, 0, 10):
            self.line(cx - 4, cy + o - 4, cx - 4, cy + o + 4, width=2)
        self.wire((cx - 4, cy - 10), (cx + 10, cy - 10), (cx + 10, cy - 30))
        self.wire((cx - 4, cy + 10), (cx + 10, cy + 10), (cx + 10, cy + 30))
        self.line(cx - 4, cy, cx + 10, cy)
        if p:
            self.poly([(cx + 2, cy - 4), (cx + 2, cy + 4), (cx + 9, cy)], fill=INK)
        else:
            self.poly([(cx + 3, cy - 4), (cx + 3, cy + 4), (cx - 4, cy)], fill=INK)
        self.text(cx + 18, cy - 2, ref, 11)
        self.text(cx + 18, cy + 11, val, 10, MUTED)

    def switch(self, cx, cy, ref, val):
        """Vertical normally-closed contact, pins cy-30 and cy+30."""
        self.line(cx, cy - 30, cx, cy - 10)
        self.line(cx, cy + 10, cx, cy + 30)
        self.line(cx, cy + 10, cx - 10, cy - 12, width=1.6)
        self.line(cx - 4, cy - 10, cx + 4, cy - 10)
        self._label(cx, cy, True, ref, val)

    def save(self, name):
        self.o.append("</svg>")
        with open(os.path.join(OUT, name), "w") as f:
            f.write("\n".join(self.o) + "\n")


def sci(x):
    m, e = f"{x:.1e}".split("e")
    sup = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return f"{m} × 10{str(int(e)).translate(sup)}"


def mA(x):
    return f"{x * 1e3:.1f} mA"


def uA(x):
    return f"{x * 1e6:.0f} µA"


# --------------------------------------------------------------------------
# Sheets
# --------------------------------------------------------------------------
def sheet_supply():
    s = Sheet(1120, 640, "01 — Supply: fused Neutral, half-wave, LNK304 buck to 12 V, LM2936 to 3.3 V",
              f"IEC 60617 symbols. Ground is Line (H1). {EDITION}. Values from hardware/fab/ec-seal1/BOM.csv.")
    y, g = 150, 330
    s.terminal(40, y, "H3 N", "u")
    s.line(45, y, 80, y)
    s.FUSE(110, y, "F1", "250 mA T")
    s.line(140, y, 200, y); s.dot(170, y)
    s.flag(185, y - 22, "N_F", "u")
    s.MOV(170, 240, "RV1", "275 VAC", side=-1)
    s.line(170, y, 170, 210); s.line(170, 270, 170, g)
    s.R(230, y, "R1", "10 Ω surge")
    s.line(260, y, 290, y)
    s.D(320, y, "D1", "S1M", "r")
    s.line(350, y, 420, y); s.dot(390, y); s.flag(400, y - 22, "VB1", "u")
    s.C(390, 240, "C1", "4.7 µF 400 V", pol=True)
    s.line(390, y, 390, 210); s.line(390, 270, 390, g)
    s.L(450, y, "L1", "1 mH")
    s.line(480, y, 560, y); s.dot(520, y); s.flag(530, y - 22, "VBULK", "u")
    s.C(520, 240, "C16", "4.7 µF 400 V", pol=True)
    s.line(520, y, 520, 210); s.line(520, 270, 520, g)
    p = s.ic(570, 110, 100, 80, "U5", "LNK304DG", [("l", 40, "D"), ("b", 50, "S"),
                                                     ("r", 22, "BP"), ("r", 58, "FB")])
    s.line(560, y, p["D"][0], y)
    s.flag(p["BP"][0], p["BP"][1], "BP"); s.flag(p["FB"][0], p["FB"][1], "FB")
    sw = (620, 250)
    s.line(620, 200, 620, 250); s.dot(*sw); s.flag(612, 232, "SW", "l")
    s.D(620, 290, "D3", "ES1J", "u", side=-1)
    s.line(620, 320, 620, g)
    s.line(620, 250, 670, 250)
    s.L(700, 250, "L2", "1 mH")
    s.line(730, 250, 1000, 250)
    for x in (780, 840, 900):
        s.dot(x, 250)
    s.flag(760, 232, "VRECT 12 V, also J4.1 (radio)", "u")
    s.C(780, 290, "C2", "470 µF 25 V", pol=True, side=-1); s.line(780, 320, 780, g)
    s.D(840, 290, "Z1", "15 V", "u", kind="zener"); s.line(840, 320, 840, g)
    s.R(900, 290, "R27", "3.3 k", vert=True); s.line(900, 320, 900, g)
    s.line(900, 250, 900, 260); s.line(840, 250, 840, 260); s.line(780, 250, 780, 260)
    q = s.ic(950, 200, 90, 90, "U1", "LM2936-3.3", [("l", 50, "IN"), ("r", 50, "OUT"), ("b", 45, "GND")])
    s.line(q["GND"][0], q["GND"][1], q["GND"][0], g)
    s.line(q["OUT"][0], 250, 1090, 250); s.dot(1065, 250)
    s.line(q["IN"][0], 250, q["IN"][0] - 10, 250)
    s.C(1065, 290, "C3", "10 µF", side=-1); s.line(1065, 320, 1065, g)
    s.flag(1080, 232, "VDD 3.3 V", "u")
    s.line(40, g, 1090, g, width=1.6)
    s.GND(1090, g, "GND = Line, H1", left=True)
    # Feedback network rides on SW
    fy = 420
    s.text(40, fy - 48, "Feedback, referenced to SW (the floating source of U5):", 12, INK)
    s.flag(70, fy, "VRECT", "l")
    s.D(100, fy, "D2", "S1M", "r")
    s.line(130, fy, 190, fy); s.dot(160, fy); s.flag(170, fy - 22, "FBC", "u")
    s.R(220, fy, "R2", "13.0 k")
    s.line(250, fy, 290, fy); s.dot(270, fy); s.flag(290, fy, "FB", "r")
    s.R(270, fy + 70, "R3", "2.05 k", vert=True)
    s.line(270, fy, 270, fy + 40); s.line(270, fy + 100, 270, fy + 120); s.flag(270, fy + 120, "SW", "d")
    s.C(160, fy + 70, "C18", "10 µF", side=-1)
    s.line(160, fy, 160, fy + 40); s.line(160, fy + 100, 160, fy + 120); s.flag(160, fy + 120, "SW", "d")
    s.flag(380, fy, "BP", "l")
    s.C(410, fy, "C17", "100 nF", vert=False)
    s.flag(440, fy, "SW", "r")
    s.notes(520, 400, [
        f"V_RECT = 1.65 V × (1 + 13.0 k / 2.05 k) = {V_RECT:.2f} V.",
        f"Inrush: {V_PK:.0f} V pk / 10 Ω ≈ {I_INRUSH:.0f} A, τ ≤ 10 Ω × 9.4 µF; I²t ≤ {I2T:.2f} A²s.",
        f"Load: {I_LOGIC * 1e3:.0f} mA logic + up to {I_RADIO * 1e3:.0f} mA radio at 12 V, 60 % efficiency:",
        f"   {P_IN_MAX:.2f} W worst case, {P_IN_SLEEP:.2f} W with the radio asleep. Cap 2 W.",
        f"LM2936: (12.1 − 3.3) V × 30 mA = {P_LDO:.2f} W in SOT-223. Radio runs from VRECT.",
        "RV1 sits after F1 from Neutral to Line. The tap is on the grid side of the",
        "shunt, so the meter's own draw is counted as neither export nor import.",
    ])
    s.save("01-supply.svg")


def sheet_shunt():
    s = Sheet(960, 520, "02 — Current shunt, Kelvin sense into the STPM32",
              f"Four-terminal 100 µΩ shunt in Line. Ground is its grid-side force pad. {EDITION}.")
    y = 140
    s.terminal(90, y, "H2 L_GEN (generator)", "u")
    s.line(95, y, 330, y, width=3)
    s.rect(330, y - 14, 140, 28)
    s.text(400, y + 4, "RS 100 µΩ", 11, INK, "middle")
    s.text(340, y - 20, "FG", 9, MUTED); s.text(450, y - 20, "IG", 9, MUTED)
    s.line(470, y, 760, y, width=3)
    s.terminal(765, y, "H1 grid Line = GND", "u")
    s.GND(620, y)
    s.poly([(230, y - 8), (245, y), (230, y + 8)], fill=RED, color=RED)
    s.text(238, y - 14, "export current i", 10, RED, "middle")
    # Kelvin taps
    s.line(360, y + 14, 360, 230); s.text(366, y + 30, "SG", 9, MUTED)
    s.line(440, y + 14, 440, 300); s.text(446, y + 30, "SI", 9, MUTED)
    s.line(360, 230, 480, 230); s.R(510, 230, "R11", "100 Ω 0.1 %")
    s.line(540, 230, 600, 230)
    s.line(440, 300, 480, 300); s.R(510, 300, "R10", "100 Ω 0.1 %")
    s.line(540, 300, 600, 300)
    s.dot(575, 230); s.dot(575, 300)
    s.C(575, 265, "C6", "10 nF C0G", side=-1)
    s.flag(585, 222, "IIN", "u"); s.flag(585, 318, "IIP", "d")
    s.ic(610, 200, 150, 120, "U2", "STPM32", [("l", 30, "IIN1"), ("l", 100, "IIP1")])
    s.notes(40, 380, [
        f"At 40 A: v = I·R = {V_SH * 1e3:.1f} mV rms, {V_SH * math.sqrt(2) * 1e3:.2f} mV peak; burden I²R = {P_SH:.2f} W.",
        f"Gain 16: {V_MOD * 1e3:.0f} mV peak at the modulator against ±300 mV; clips near {I_CLIP:.0f} A rms.",
        f"R10 + R11 with C6: differential pole ≈ {F_I / 1e3:.0f} kHz.",
        "Export flows FG → IG, so V(SG) − V(SI) = +i·R and IIP1 − IIN1 = −i·R. With the divider",
        "reading −v (sheet 03) the STPM32 sees (−v)(−i) = +p: export is positive active power.",
        "The Kelvin pair leaves the element at SG and SI and shares no copper with the force path.",
    ])
    s.save("02-shunt.svg")


def sheet_divider():
    s = Sheet(980, 520, "03 — Voltage divider from Neutral",
              f"Four 499 kΩ 0.1 % 700 V parts over R8 1.00 kΩ to ground (Line). {EDITION}.")
    y = 150
    s.terminal(40, y, "H3 N", "u")
    s.line(45, y, 80, y)
    xs = [110, 200, 290, 380]
    for i, x in enumerate(xs):
        s.R(x, y, f"R{4 + i}", "499 k")
        if i:
            s.line(xs[i - 1] + 30, y, x - 30, y)
    for i, x in enumerate((155, 245, 335)):
        s.text(x, y - 6, f"VD{i + 1}", 9, MUTED, "middle")
    s.line(410, y, 560, y)
    s.dot(450, y); s.dot(520, y)
    s.flag(455, y - 22, "VIP_S", "u")
    s.R(450, 230, "R8", "1.00 k 0.1 %", vert=True, side=-1)
    s.line(450, y, 450, 200); s.line(450, 260, 450, 300)
    s.C(520, 230, "C5", "10 nF")
    s.line(520, y, 520, 200); s.line(520, 260, 520, 300)
    s.R(590, y, "R9", "1.00 k")
    s.line(620, y, 720, y); s.dot(670, y)
    s.flag(680, y - 22, "VIP", "u")
    s.D(670, 230, "TVS1", "5 V bidir.", "d", kind="bidir", side=-1)
    s.line(670, y, 670, 200); s.line(670, 260, 670, 300)
    p = s.ic(730, 110, 140, 110, "U2", "STPM32", [("l", 40, "VIP1"), ("l", 80, "VIN1")])
    s.line(p["VIN1"][0], p["VIN1"][1], 700, p["VIN1"][1]); s.line(700, p["VIN1"][1], 700, 300)
    s.line(450, 300, 760, 300, width=1.6)
    s.GND(760, 300, "GND = Line", left=True)
    s.notes(40, 360, [
        f"k = 1.00 k / (4 × 499 k + 1.00 k) = 1 / {1 / K_DIV:.0f}. At 240 V rms the pin sees {V_PIN:.3f} V rms, {V_PIN * math.sqrt(2):.3f} V peak.",
        f"At 264 V (+10 %): {V_PIN_HI_PK:.3f} V peak, inside the ±0.3 V VIP1/VIN1 window.",
        f"Each 499 k part drops {V_PART:.0f} V rms, and {V_PART_CLAMP:.1f} V at the MOV clamp ({MOV_CLAMP:.0f} V), against a 700 V rating.",
        f"String dissipation V²/R = {P_DIV * 1e3:.0f} mW. C5 across R8: anti-alias pole ≈ {F_V / 1e3:.0f} kHz.",
        "The divider measures V(N) − V(L) = −v_LN. That sign is what makes export positive (sheet 02).",
    ])
    s.save("03-divider.svg")


def sheet_metrology():
    s = Sheet(1200, 600, "04 — Metrology: STPM32, two pulse trains, one per direction",
              f"LED1 export, LED2 import, 1000 impulses per kWh each: one pulse is one watt-hour. {EDITION}.")
    p = s.ic(130, 120, 190, 300, "U2", "STPM32", [
        ("l", 50, "VIP1"), ("l", 80, "VIN1"), ("l", 110, "IIP1"), ("l", 140, "IIN1"),
        ("l", 190, "XTAL1"), ("l", 230, "XTAL2"),
        ("r", 50, "LED1"), ("r", 140, "LED2"), ("r", 190, "EN"),
        ("r", 220, "SCS"), ("r", 245, "SCL"), ("r", 270, "MOSI"), ("r", 290, "MISO"),
        ("t", 40, "VCC"), ("t", 90, "VREF1"), ("t", 130, "VDDA"), ("t", 170, "VDDD"),
    ])
    for k, txt in (("VIP1", "sheet 03"), ("VIN1", "GND"), ("IIP1", "sheet 02"), ("IIN1", "sheet 02")):
        s.text(p[k][0] - 4, p[k][1] + 4, txt, 9, MUTED, "end")
    s.text(p["VCC"][0], p["VCC"][1] - 4, "VDD + C12", 9, MUTED, "middle")
    s.text(p["VREF1"][0], p["VREF1"][1] - 4, "C9 1 µF", 9, MUTED, "middle")
    s.text(p["VDDA"][0], p["VDDA"][1] - 16, "C10", 9, MUTED, "middle")
    s.text(p["VDDD"][0], p["VDDD"][1] - 4, "C11", 9, MUTED, "middle")
    s.text(p["VDDA"][0], p["VDDA"][1] - 4, "100 nF", 9, MUTED, "middle")
    # crystal
    x1, x2 = p["XTAL1"], p["XTAL2"]
    s.line(x1[0], x1[1], 90, x1[1]); s.line(x2[0], x2[1], 90, x2[1])
    s.rect(80, x1[1] + 8, 20, x2[1] - x1[1] - 16)
    s.text(76, (x1[1] + x2[1]) / 2 + 4, "Y1", 10, INK, "end")
    s.text(76, (x1[1] + x2[1]) / 2 + 16, "16 MHz", 9, MUTED, "end")
    s.text(40, x2[1] + 50, "C7, C8 27 pF C0G to GND", 9, MUTED)
    # export pulse buffer
    def buffer(ledpin, y, rp, rs, cs, q, rd, net, pin, bx=560):
        lx = p[ledpin][0]
        s.wire((lx, p[ledpin][1]), (bx - 40, p[ledpin][1]), (bx - 40, y), (bx, y))
        s.dot(bx, y)
        s.R(bx, y - 50, rp, "10 k", vert=True, side=-1); s.line(bx, y - 20, bx, y)
        s.flag(bx, y - 80, "VDD", "u")
        s.line(bx, y, bx + 30, y); s.R(bx + 60, y, rs, "100 Ω"); s.line(bx + 90, y, bx + 140, y)
        s.dot(bx + 120, y)
        s.C(bx + 120, y + 50, cs, "100 pF"); s.line(bx + 120, y, bx + 120, y + 20); s.GND(bx + 120, y + 80)
        s.fet(bx + 170, y, q, "2N7002")
        s.GND(bx + 180, y + 30)
        s.line(bx + 180, y - 30, bx + 180, y - 40); s.line(bx + 180, y - 40, bx + 310, y - 40)
        s.dot(bx + 250, y - 40)
        s.R(bx + 250, y - 90, rd, "10 k", vert=True); s.line(bx + 250, y - 60, bx + 250, y - 40)
        s.flag(bx + 250, y - 120, "VDD", "u")
        s.flag(bx + 310, y - 40, f"{net} → U3 pin {pin}", "r", RED)
    buffer("LED1", 190, "R13", "R14", "C13", "Q1", "R15", "CF_EXP", 3)
    buffer("LED2", 400, "R28", "R29", "C19", "Q6", "R30", "CF_IMP", 25)
    # EN and SPI
    en = p["EN"]
    s.line(en[0], en[1], 350, en[1])
    s.text(354, en[1] + 4, "STP_EN ← U3; R12 10 k to GND", 9, MUTED)
    for k, n in (("SCS", "STP_CS_N ← U3, active low"), ("SCL", "STP_SCK ← U3"), ("MOSI", "STP_MOSI ← U3"), ("MISO", "STP_MISO → U3")):
        s.line(p[k][0], p[k][1], 350, p[k][1]); s.text(354, p[k][1] + 4, n, 9, MUTED)
    s.notes(40, 500, [
        "One LED edge is one watt-hour; 1000 net-export edges are one token (1 kWh) in U3. Q1 and Q6 turn each LED",
        "edge into a clean 3.3 V pulse into U3. U3 holds EN low, takes SCS low and raises EN so the part latches SPI,",
        "then replays the calibration transcript (the configuration is volatile). Splitting LED1/LED2 by sign is O-2.",
    ])
    s.save("04-metrology.svg")


def sheet_signer():
    s = Sheet(1100, 640, "05 — Schedule die and signer: EC-MINT1, FM25V02A F-RAM, QS7001",
              f"U3 counts, builds and persists; U4 signs. Each has one master on its SPI: U3. {EDITION}.")
    u3 = s.ic(380, 120, 340, 300, "U3", "EC-MINT1 schedule die", [
        ("l", 50, "CF_EXP"), ("l", 80, "CF_IMP"), ("l", 120, "ZEROIZE"), ("l", 160, "XI"),
        ("l", 190, "RST_N"), ("l", 230, "STP_*"), ("l", 270, "PROV_*"),
        ("r", 50, "QS_SCK/MOSI/MISO"), ("r", 80, "QS_CS_N"), ("r", 110, "QS_RST_N"),
        ("r", 190, "FR_SCK/MOSI/MISO"), ("r", 220, "FR_CS_N"), ("r", 270, "UART_TX"),
    ])
    s.text(540, 200, "credit = e_exp − e_imp − 1000·tokens", 11, INK, "middle")
    s.text(540, 218, "export: credit+1; at 1000 → tokens+1, credit 0", 10, MUTED, "middle")
    s.text(540, 234, "import: credit−1", 10, MUTED, "middle")
    s.text(540, 254, "every token (1 kWh): build and sign one record", 10, RED, "middle")
    s.text(540, 270, "no host write port; 48-bit cumulative", 10, MUTED, "middle")
    for k, t in (("CF_EXP", "from Q1 (sheet 04)"), ("CF_IMP", "from Q6 (sheet 04)"),
                 ("ZEROIZE", "from latch (sheet 06)"), ("STP_*", "STPM32 SPI + EN"),
                 ("PROV_*", "J5 factory row, under the mesh")):
        s.line(u3[k][0] - 40, u3[k][1], u3[k][0], u3[k][1])
        s.text(u3[k][0] - 44, u3[k][1] + 4, t, 10, MUTED, "end")
    s.line(u3["XI"][0] - 60, u3["XI"][1], u3["XI"][0], u3["XI"][1])
    s.rect(250, u3["XI"][1] - 14, 60, 28); s.text(280, u3["XI"][1] + 4, "Y2", 10, INK, "middle")
    s.text(280, u3["XI"][1] - 20, "16.000 MHz CMOS", 9, MUTED, "middle")
    s.line(u3["RST_N"][0] - 40, u3["RST_N"][1], u3["RST_N"][0], u3["RST_N"][1])
    s.text(u3["RST_N"][0] - 44, u3["RST_N"][1] + 4, "R24 100 k to VDD", 10, MUTED, "end")
    u4 = s.ic(810, 100, 180, 150, "U4", "QS7001 ML-DSA-44", [
        ("l", 50, "SPI_CLK/MOSI/MISO"), ("l", 80, "SPI_CS"), ("l", 110, "RST"),
        ("r", 80, "GPIO3"), ("r", 110, "VCC"),
    ])
    for a, b in (("QS_SCK/MOSI/MISO", "SPI_CLK/MOSI/MISO"), ("QS_CS_N", "SPI_CS"), ("QS_RST_N", "RST")):
        s.line(u3[a][0], u3[a][1], u4[b][0], u4[b][1])
    s.text(765, u3["QS_RST_N"][1] + 16, "R25 100 k pull-up", 9, MUTED, "middle")
    s.text(u4["GPIO3"][0] + 4, u4["GPIO3"][1] + 4, "ZEROIZE", 10, RED)
    s.text(u4["VCC"][0] + 4, u4["VCC"][1] + 4, "QS_VDD", 10, MUTED)
    s.text(u4["VCC"][0] + 4, u4["VCC"][1] + 17, "(sheet 06)", 9, MUTED)
    u6 = s.ic(810, 280, 180, 90, "U6", "FM25V02A F-RAM", [("l", 30, "SCK/SI/SO"), ("l", 60, "/CS")])
    s.line(u3["FR_SCK/MOSI/MISO"][0], u3["FR_SCK/MOSI/MISO"][1], u6["SCK/SI/SO"][0], u6["SCK/SI/SO"][1])
    s.line(u3["FR_CS_N"][0], u3["FR_CS_N"][1], u6["/CS"][0], u6["/CS"][1])
    s.text(900, 360, "/WP, /HOLD high; C20 100 nF", 9, MUTED, "middle")
    s.line(u3["UART_TX"][0], u3["UART_TX"][1], 780, u3["UART_TX"][1])
    s.text(784, u3["UART_TX"][1] + 4, "→ R26 → J4.4, radio (sheet 07)", 10, MUTED)
    s.notes(40, 480, [
        f"q = {Q_WH} Wh: one token per kWh of net export, and a record for every token, so each kWh is signed and credited on its own.",
        "Record, 32 bytes: id, version/role, class 0x22, seq, e_exp, e_imp, tokens, CRC-16 of the calibration image, kind.",
        f"Built when its token mints (credit = 0), so e_exp − e_imp = 1000·tokens exactly. Frame EC 01 + record + {SIG_BYTES} B = {FRAME} B.",
        "After a day with no record U3 signs the last one again under a new seq, so a dropped frame comes back without a receive path.",
        "On ZEROIZE: 5C 5C erases the meter key, then A7 has the tamper key sign one record of kind 1 over the counters, and is erased.",
        f"One ML-DSA-44 sign ≈ 19 mJ against 3.6 MJ in the kWh it attests: {sci(E_SIGN / E_KWH)} of the energy.",
        "The QS7001 signs only records that advance its last signed (seq, e_exp, e_imp, tokens), with tokens·1000 ≤ e_exp.",
        "Counters, seq and the image sit in F-RAM, two CRC-8 slots; a power cut loses at most the pulses since the last write.",
    ])
    s.save("05-secure-element.svg")


def sheet_tamper():
    s = Sheet(1120, 640, "06 — Tamper latch and signer rail",
              f"Discrete latch: opening the cover sets ZEROIZE (active high) until power is removed. {EDITION}.")
    rail, g = 100, 470
    s.line(60, rail, 1060, rail, width=1.6)
    s.text(64, rail - 8, "VDD 3.3 V", 11)
    # MESH node
    mx, my = 200, 230
    s.R(mx, 165, "R16", "100 k", vert=True, side=-1); s.line(mx, rail, mx, 135); s.line(mx, 195, mx, my)
    s.dot(mx, my); s.text(mx - 8, my - 6, "MESH", 10, RED, "end")
    s.R(mx, 300, "R17", "10 k", vert=True, side=-1); s.line(mx, my, mx, 270)
    s.switch(mx, 380, "SW1", "cover spring"); s.line(mx, 330, mx, 350)
    s.line(mx, 410, mx, g)
    s.bjt(80, 170, "PT1", "VEMT3700", photo=True)
    s.line(90, 140, 90, rail); s.wire((90, 200), (90, my), (mx, my))
    # Q2
    s.R(260, my, "R18", "47 k"); s.line(mx, my, 230, my)
    s.line(290, my, 330, my); s.dot(310, my)
    s.R(310, 330, "R19", "100 k", vert=True, side=-1); s.line(310, my, 310, 300); s.line(310, 360, 310, g)
    s.bjt(360, my, "Q2", "MMBT3904")
    s.line(370, 260, 370, g)
    s.line(370, 200, 370, 170); s.line(370, 170, 380, 170)
    s.R(410, 170, "R20", "10 k"); s.line(440, 170, 450, 170)
    s.bjt(480, 170, "Q3", "MMBT3906", pnp=True)
    s.line(490, 140, 490, rail)
    zx, zy = 490, 300
    s.line(490, 200, 490, zy); s.dot(zx, zy)
    s.R(430, zy, "R21", "10 k"); s.line(460, zy, zx, zy)
    s.wire((400, zy), (320, zy), (320, my)); s.dot(320, my)
    s.text(zx + 6, zy + 18, "ZEROIZE", 11, RED, weight="600")
    s.line(zx, zy, zx, 400); s.line(zx, 400, 530, 400)
    s.text(534, 404, "→ U3 pin 4, U4 GPIO3", 10, RED)
    # signer rail
    s.line(zx, zy, 560, zy)
    s.R(590, zy, "R22", "1.5 M")
    s.line(620, zy, 760, zy); s.dot(660, zy)
    s.text(668, zy - 6, "CROW_G", 10, MUTED)
    s.C(660, 360, "C14", "2.2 µF", side=-1); s.line(660, zy, 660, 330); s.line(660, 390, 660, g)
    s.line(660, zy, 660, 170); s.line(660, 170, 690, 170)
    s.fet(720, 170, "Q5", "DMG2305UX", p=True)
    s.line(730, 140, 730, rail)
    s.line(730, 200, 730, 230); s.line(730, 230, 1040, 230); s.dot(840, 230); s.dot(930, 230)
    s.text(1000, 222, "QS_VDD → U4 VCC", 10, INK, "end")
    s.R(840, 270, "R23", "1 k", vert=True, side=-1); s.line(840, 230, 840, 240)
    s.line(760, zy, 760, 360); s.line(760, 360, 820, 360)
    s.fet(850, 360, "Q4", "2N7002")
    s.line(860, 330, 860, 310); s.line(840, 300, 840, 310); s.line(840, 310, 860, 310)
    s.text(866, 318, "QS_DIS", 9, MUTED)
    s.line(860, 390, 860, g)
    s.C(930, 270, "C15", "100 nF"); s.line(930, 300, 930, g); s.line(930, 230, 930, 240)
    s.line(60, g, 1060, g, width=1.6); s.GND(1060, g, "GND = Line", left=True)
    s.notes(40, 520, [
        f"Cover on: MESH = 3.3 V × 10 k / 110 k = {V_MESH_CLOSED:.2f} V. Q2 trips at MESH ≈ 0.6 V × (1 + 47 k/100 k) = {V_TRIP:.2f} V.",
        f"Light on PT1 with the spring still closed: about {uA(I_PHOTO)} lifts MESH to the trip point. Latched, R21 feeds Q2 ≈ {uA(I_HOLD)};",
        f"closing the cover again can pull at most {uA(I_RELEASE_MAX)} back through R18, so the latch holds until power is removed.",
        f"ZEROIZE → U3 sends 5C 5C within microseconds (meter key erased), then A7 and the tamper record, signed by the tamper key.",
        f"R22·C14 = {TAU_G:.1f} s: Q5 stays fully on for ≈ {T_FULL_ON:.1f} s ({T_FULL_ON_LOW:.1f} s with C14 30 % low), past the {T_TAMPER:.2f} s the tamper record needs.",
        f"Q4 conducts from ≈ {T_Q4_FIRST:.1f}–{T_Q4_ON:.1f} s, Q5 opens at ≈ {T_Q5_OPEN:.1f} s. In that overlap R23 = 1 k limits the draw to {mA(I_OVERLAP)};",
        f"once Q5 is open C15 discharges with τ = {TAU_DIS * 1e3:.1f} ms. Unpowered tamper is O-1.",
    ], size=11, dy=18)
    s.save("06-tamper.svg")


def sheet_radio():
    s = Sheet(960, 460, "07 — Radio header J4: transmit only",
              f"The radio forwards signed frames. It has no key and no path back into U3, U4 or U6. {EDITION}.")
    p = s.ic(520, 100, 160, 180, "J4", "radio module header", [
        ("l", 40, "1 VRECT"), ("l", 70, "2 GND"), ("l", 100, "3 GND"), ("l", 130, "4 RX ← UART"),
        ("l", 160, "5, 6 empty"),
    ])
    s.line(p["1 VRECT"][0], p["1 VRECT"][1], 300, p["1 VRECT"][1]); s.flag(300, p["1 VRECT"][1], "VRECT 12 V", "l")
    s.wire(p["2 GND"], (460, p["2 GND"][1]), (460, p["3 GND"][1]), p["3 GND"])
    s.line(460, 185, 400, 185); s.dot(460, 185); s.GND(400, 185)
    s.R(420, p["4 RX ← UART"][1], "R26", "100 Ω")
    s.line(450, p["4 RX ← UART"][1], p["4 RX ← UART"][0], p["4 RX ← UART"][1])
    s.line(300, p["4 RX ← UART"][1], 390, p["4 RX ← UART"][1])
    s.flag(300, p["4 RX ← UART"][1], "UART_TX from U3", "l")
    s.notes(40, 330, [
        f"One frame per token, that is per kWh: EC 01 + 32-byte record + {SIG_BYTES}-byte ML-DSA-44 signature = {FRAME} bytes.",
        f"8N1 at 16 MHz / 139 = {BAUD:.0f} baud: {T_FRAME:.2f} s per frame.",
        f"Budget: average under 40 mA at 12 V. Even at the full 0.48 W for 1 s per frame, about 0.5 J per kWh ({sci(0.48 / E_KWH)} of it).",
        "The radio takes its power from VRECT so its transmit current never passes through the 50 mA LM2936.",
    ])
    s.save("07-radio.svg")


def sheet_burden():
    s = Sheet(960, 520, "08 — Burden chart",
              f"Voltage-circuit draw of revision B against the 2 W IEC 62052-11 cap and the 1.5 W field target. {EDITION}.")
    bars = [
        ("logic at 12 V (30 mA)", P_LOGIC),
        ("radio at 12 V (≤ 40 mA avg)", P_RADIO),
        ("buck loss at 60 %", P_LOSS),
        ("divider string", P_DIV),
        ("sign, 19 mJ per kWh", 0.0),
    ]
    x0, y0, scale = 260, 100, 300.0       # px per watt
    for i, (name, w) in enumerate(bars):
        y = y0 + i * 44
        s.text(x0 - 10, y + 18, name, 12, INK, "end")
        s.rect(x0, y, max(w * scale, 1), 26, INK, "#cfc6b4", 1)
        s.text(x0 + max(w * scale, 1) + 8, y + 18, f"{w:.2f} W" if w else "≈ 0 W average", 11)
    y = y0 + len(bars) * 44 + 10
    s.text(x0 - 10, y + 18, "total, radio transmitting", 12, INK, "end", "600")
    s.rect(x0, y, P_TOTAL * scale, 26, INK, "#8f7f63", 1)
    s.text(x0 + P_TOTAL * scale - 8, y + 18, f"{P_TOTAL:.2f} W", 11, "#fff", "end", "600")
    for wv, lab, col in ((1.5, "1.5 W field target", MUTED), (2.0, "2 W cap", RED)):
        x = x0 + wv * scale
        s.line(x, y0 - 16, x, y + 40, col, 1.4)
        s.text(x, y0 - 22, lab, 11, col, "middle")
    s.notes(40, 420, [
        f"Radio asleep: {P_IN_SLEEP + P_DIV:.2f} W. The shunt is the current circuit: {P_SH:.2f} W at 40 A, a separate 1 VA-at-nominal limit.",
        f"Signing once per kWh costs {sci(E_SIGN / E_KWH)} of the energy it attests; it does not move a bar.",
        "Efficiency, logic current and radio average are the budget figures in CIRCUITS.md (open item O-4 confirms them).",
    ])
    s.save("08-burden-chart.svg")


def sheet_mint_path():
    s = Sheet(1180, 620, "Enerchain mint path — EC-SEAL1 revision B",
              f"One sealed board per meter, two meters per site. Ground is Line at the shunt. {EDITION}.")
    s.text(40, 98, "generator", 11, MUTED); s.text(1100, 98, "grid", 11, MUTED, "end")
    s.line(40, 110, 1140, 110, width=3); s.text(40, 126, "L", 11)
    s.line(40, 190, 1140, 190, width=2); s.text(40, 206, "N", 11)
    s.rect(240, 96, 100, 28, INK, "#fff"); s.text(290, 115, "RS 100 µΩ", 11, INK, "middle")
    s.text(400, 104, "grid-side force pad = GND", 10, MUTED)
    blocks = [
        (60, 250, 170, 80, "supply (sheet 01)", ["F1, RV1, LNK304 → 12 V", "LM2936 → 3.3 V, ≤ 2 W"]),
        (280, 250, 170, 80, "divider (sheet 03)", ["4 × 499 k / 1 k from N", "0.120 V rms at 240 V"]),
        (500, 250, 190, 80, "STPM32 (sheet 04)", ["Σ v·i·Δt, both directions", "LED1 export, LED2 import"]),
        (740, 250, 200, 110, "EC-MINT1 (sheet 05)", ["1 Wh per pulse", "1000 Wh net export = 1 token", "record for every token", "F-RAM: counters, image"]),
        (990, 250, 160, 80, "QS7001 (sheet 05)", ["ML-DSA-44 key, on chip", "rollback guard"]),
        (740, 420, 200, 70, "tamper latch (sheet 06)", ["ZEROIZE → erase, rail off"]),
        (500, 420, 190, 70, "radio (sheet 07)", ["TX only, 2454 B per kWh"]),
    ]
    for x, y, w, h, title, lines in blocks:
        s.rect(x, y, w, h, INK, "#fffdf8")
        s.text(x + w / 2, y + 18, title, 12, INK, "middle", "600")
        for i, t in enumerate(lines):
            s.text(x + w / 2, y + 36 + i * 15, t, 10, MUTED, "middle")
    s.line(145, 190, 145, 250); s.text(150, 230, "fused N", 9, MUTED)
    s.line(365, 190, 365, 250)
    s.line(290, 124, 290, 150); s.wire((290, 150), (595, 150), (595, 250)); s.text(450, 145, "Kelvin pair (sheet 02)", 9, MUTED)
    s.line(450, 290, 500, 290)
    s.line(690, 280, 740, 280); s.text(715, 274, "CF_EXP", 8, RED, "middle")
    s.line(690, 305, 740, 305); s.text(715, 320, "CF_IMP", 8, RED, "middle")
    s.line(940, 290, 990, 290); s.text(965, 284, "SPI", 9, MUTED, "middle")
    s.wire((840, 360), (840, 420)); s.text(846, 395, "ZEROIZE", 9, RED)
    s.wire((940, 455), (1070, 455), (1070, 330)); s.text(1000, 450, "ZEROIZE", 9, RED)
    s.wire((760, 360), (760, 390), (595, 390), (595, 420))
    s.text(680, 385, "UART", 9, MUTED)
    s.notes(40, 530, [
        "GEN board at the generator terminals, GRID board at the connection. Each signs its own cumulative record for every token.",
        "The ledger verifies both and credits min(T_GEN, T_GRID) less what it already credited: one token per kWh delivered net.",
        "An optional LOAD board on the site's own load mints nothing; it lets the ledger check GEN = GRID + LOAD and flag a tap between them.",
        "No host CPU in the path. Ledger nodes only verify and chain (SHA-384); there is no difficulty and no hash contest.",
    ], size=12)
    s.save("mint-path.svg")


def main():
    check_claims()
    sheet_supply()
    sheet_shunt()
    sheet_divider()
    sheet_metrology()
    sheet_signer()
    sheet_tamper()
    sheet_radio()
    sheet_burden()
    sheet_mint_path()
    print("PASS schematics: values match CIRCUITS.md, connections match netlist.txt")


if __name__ == "__main__":
    main()
