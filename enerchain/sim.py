"""Site simulation for the development network.

A site has a generator (solar here), a household load, optionally a battery,
a GEN meter at the generator terminals and a GRID meter at the point of
connection. Power flows are stepped minute by minute; each meter turns its
own energy into pulses and signs records through the EC-MINT1 model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .meter import EnergyMeter
from .record import ROLE_GEN, ROLE_GRID


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
    peak_w: float = 5000.0
    battery_loop_w: float = 0.0     # grid->battery at night, battery->grid at noon
    standby_w: float = 5.0          # inverter draw at night, seen by the GEN meter
    minute: int = 0
    log: dict = field(default_factory=lambda: {"gen_wh": 0.0, "net_export_wh": 0.0,
                                                "import_wh": 0.0})

    @classmethod
    def new(cls, gen_id: int, grid_id: int, gen_error: float = 0.003,
            grid_error: float = -0.002, **kw) -> "Site":
        return cls(EnergyMeter(gen_id, ROLE_GEN, gen_error),
                   EnergyMeter(grid_id, ROLE_GRID, grid_error), **kw)

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
        # GEN meter: generator terminals. It sees the panels, not the battery.
        self.gen.step(pv, 0.0 if pv > 0 else self.standby_w, 60)
        # GRID meter: point of connection. Positive net is export.
        net = pv - load - battery
        self.grid.step(max(net, 0.0), max(-net, 0.0), 60)
        self.log["gen_wh"] += pv / 60.0
        self.log["net_export_wh"] += net / 60.0
        self.log["import_wh"] += max(-net, 0.0) / 60.0
        self.minute += 1

    def run_days(self, days: float) -> None:
        for _ in range(int(days * 1440)):
            self.step()
