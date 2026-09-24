"""
INPUT: i dati di ingresso del modello.

Corrisponde alla sezione "---- dati di ingresso ----" dello script originale.
La classe ParametriIngresso fa una cosa sola: custodisce i quattro parametri
(lam, mu, K1, K2) e li sa leggere da un file JSON.
"""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParametriIngresso:
    lam: float = 10.0    # tasso di arrivo NOMINALE (pezzi/ora che si presentano all'ingresso)
    mu: float = 12.0     # tasso di servizio (uguale per M1 e M2)
    K1: int = 0          # capacita' del buffer davanti a M1   (0 = nessun buffer)
    K2: int = 0          # capacita' del buffer tra M1 e M2    (0 = nessun buffer)

    def __post_init__(self):
        # controlli minimi: i tassi devono essere positivi, le capacita' non negative
        if self.lam <= 0 or self.mu <= 0:
            raise ValueError("lam e mu devono essere maggiori di zero")
        if self.K1 < 0 or self.K2 < 0:
            raise ValueError("K1 e K2 devono essere maggiori o uguali a zero")
        self.K1 = int(self.K1)
        self.K2 = int(self.K2)

    @property
    def rho(self):
        # fattore di utilizzo lam/mu, usato solo nelle stampe
        return self.lam / self.mu

    @classmethod
    def da_json(cls, percorso):
        """Legge i parametri da un file JSON con le chiavi lam, mu, K1, K2."""
        percorso = Path(percorso)
        with percorso.open("r", encoding="utf-8") as f:
            dati = json.load(f)
        return cls(
            lam=float(dati["lam"]),
            mu=float(dati["mu"]),
            K1=int(dati["K1"]),
            K2=int(dati["K2"]),
        )

    def come_dizionario(self):
        return {"lam": self.lam, "mu": self.mu, "K1": self.K1, "K2": self.K2}
