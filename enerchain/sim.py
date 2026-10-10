"""Site simulation for the development network.

A site has a generator (solar here), a household load, optionally a battery,
a GEN meter at the generator terminals and a GRID meter at the point of
connection. Optionally a LOAD meter measures what the house (and the
battery behind it) takes from the site bus, so the ledger can check
GEN = GRID + LOAD. ``siphon_w`` models a tap between the GEN and GRID meters
that takes power before the GRID meter sees it: the energy-balance check is
how such a tap shows up (docs/grid-operator.md). Power flows are stepped
minute by minute; each meter turns its own energy into pulses and signs
records through the EC-MINT1 model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .meter import EnergyMeter
from .record import ROLE_GEN, ROLE_GRID, ROLE_LOAD


def solar_w(minute_of_day: int, peak_w: float) -> float:
    h = minute_of_day / 60.0
    if 6.0 <= h <= 18.0:
        return peak_w * math.sin(math.pi * (h - 6.0) / 12.0)
    return 0.0


def house_w(minute_of_day: int, base_w: float = 400.0, evening_w: float = 1500.0) -> float:
    h = minute_of_day / 60.0
    return base_w + (evening_w if 18.0 <= h < 21.0 else 0.0)


@dataclass
class Site:
    gen: EnergyMeter
    grid: EnergyMeter
    load: EnergyMeter | None = None
    peak_w: float = 5000.0
    battery_loop_w: float = 0.0     # grid->battery at night, battery->grid at noon
    standby_w: float = 5.0          # inverter draw at night, seen by the GEN meter
    siphon_w: float = 0.0           # a tap between the GEN and GRID meters
    minute: int = 0
    log: dict = field(default_factory=lambda: {"gen_wh": 0.0, "net_export_wh": 0.0,
                                                "import_wh": 0.0, "load_wh": 0.0,
                                                "siphon_wh": 0.0})

    @classmethod
    def new(cls, gen_id: int, grid_id: int, load_id: int = 0, gen_error: float = 0.003,
            grid_error: float = -0.002, load_error: float = 0.001, **kw) -> "Site":
        load = EnergyMeter(load_id, ROLE_LOAD, load_error) if load_id else None
        return cls(EnergyMeter(gen_id, ROLE_GEN, gen_error),
                   EnergyMeter(grid_id, ROLE_GRID, grid_error), load, **kw)

    @property
    def meters(self) -> list[EnergyMeter]:
        return [m for m in (self.gen, self.grid, self.load) if m is not None]

    def step(self) -> None:
        m = self.minute % 1440
        pv = solar_w(m, self.peak_w)
        load = house_w(m)
        h = m / 60.0
        battery = 0.0                # + charging from the grid, - discharging to it
        if self.battery_loop_w:
            if 1.0 <= h < 3.0:
                battery = self.battery_loop_w
            elif 11.0 <= h < 13.0:
                battery = -self.battery_loop_w
        standby = 0.0 if pv > 0 else self.standby_w
        # GEN meter: generator terminals. It sees the panels, not the battery.
        self.gen.step(pv, standby, 60)
        # LOAD meter: the house and the battery behind it, fed from the bus.
        # Wired so that consumption runs generator stud to grid stud.
        taken = load + battery
        if self.load is not None:
            self.load.step(max(taken, 0.0), max(-taken, 0.0), 60)
        # GRID meter: point of connection. Positive net is export. A siphon
        # upstream of it takes power the GRID meter never sees.
        net = pv - standby - taken - self.siphon_w
        self.grid.step(max(net, 0.0), max(-net, 0.0), 60)
        self.log["gen_wh"] += pv / 60.0
        self.log["net_export_wh"] += net / 60.0
        self.log["import_wh"] += max(-net, 0.0) / 60.0
        self.log["load_wh"] += taken / 60.0
        self.log["siphon_wh"] += self.siphon_w / 60.0
        self.minute += 1

    def take_records(self) -> list:
        """Every meter's new frames in the order they went out, as a radio
        would deliver them. The balance check relies on that order."""
        out = []
        for i, m in enumerate(self.meters):
            out += [(r.t or 0, i, r) for r in m.take_records()]
        return [r for _, _, r in sorted(out, key=lambda x: (x[0], x[1]))]

    def run_days(self, days: float) -> None:
        for _ in range(int(days * 1440)):
            self.step()
