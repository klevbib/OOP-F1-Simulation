from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
import random

# Data Classes

@dataclass
class Driver:
    name: str
    quali_pace: float           #Higher is better
    race_pace: float            #Higher is better
    consistency: float          #(0...1) Higher = Fewer mistakes

@dataclass
class Car:
    chassis: float              #Higher is better
    engine: float               #Higher is better
    reliability: float          #(0...1) Higher = Fewer DNFs

@dataclass
class Team:
    name: str
    car: Car
    drivers: List[Driver]
    pit_crew: float             #Higher is better

@dataclass
class Circuit:
    name: str
    laps: int
    downforce_sens: float       # (0..1) How much chassis matters
    engine_sens: float          # (0..1) How much engine matters
    pit_loss_sec: float         # average time lost in pit lane

@dataclass
class Log:                      #simple event log entry
    timestamp: datetime
    message: str

@dataclass
class RaceResult:
    order: List[str]
    dnf: List[str]
    points: Dict[str, int]
    log: List[Log]

POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

#Simulation Engine

class RaceWeekend:
    def __init__(self, circuit: Circuit, weather: str = 'dry'):
        self.circuit = circuit
        self.weather = weather
        self.log: list[Log] = []

    def _log(self, msg: str):
        self.log.append(Log(datetime.now(),msg))

    def quali_time(self, team: Team, driver: Driver) -> float:
        base = 100.0
        aero = team.car.chassis * (1.0 + self.circuit.downforce_sens)
        power = team.car.engine * (1.0 + self.circuit.engine_sens)
        driver_factor = driver.quali_pace * 1.2         #Accounts for lower fuel loads in qualifying compared to race.
        noise = random.gauss(0, 0.8)
        t = base - (aero + power + driver_factor) + noise
        self._log(f"Quali lap estimate for {driver.name}: {t:.3f}s")
        return t

    def race_lap_time(self, team: Team, driver: Driver) -> float:
        weather_pen = 1.5 if self.weather == "wet" else 1.0
        pace = (team.car.chassis + team.car.engine + driver.race_pace)
        consistency_noise =  random.gauss(0, (1 - driver.consistency) * 1.2)
        return (100.0 - pace) * weather_pen + consistency_noise

    def run_race(self, grid: List[Driver], team_of: Dict[str, Team]) -> RaceResult:
        scores = []
        dnfs: List[str] = []

        for d in grid:
            team = team_of [d.name]

            if random.random() > team.car.reliability:          #Reliability (DNF) Check
                dnfs.append(d.name)
                self._log(f"DNF: {d.name} due to reliability.")
                continue

            lap_time = self.race_lap_time(team, d)
            pit_effect = max(self.circuit.pit_loss_sec - team.pit_crew * 0.25, 0)
            total = lap_time * self.circuit.laps + pit_effect
            scores.append((total, d.name))
            self._log(f"Race total for {d.name}: {total:.2f}s (lap {lap_time:.3f} + pit {pit_effect:.2f})")

        scores.sort(key=lambda x: x[0])
        finish_order = [name for _, name in scores] + dnfs
        points = {name: (POINTS[i] if i < len(POINTS) else 0) for i, name in enumerate(finish_order)}

        return RaceResult(order=finish_order, dnfs=dnfs, points=points, log=self.log)
