from dataclasses import dataclass


@dataclass
class Config:
    # Data connector
    instrument: str = "SBER"
    period: int = 60
