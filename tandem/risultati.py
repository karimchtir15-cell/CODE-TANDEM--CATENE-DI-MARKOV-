"""
RISULTATI: il contenitore in cui vengono salvati tutti i risultati di una esecuzione.

Non calcola nulla: raccoglie parametri, passo h, distribuzione stazionaria, indicatori
ed esiti dei controlli, e sa trasformarsi in un dizionario (per il salvataggio su file).
"""
from dataclasses import dataclass, field


@dataclass
class Risultati:
    parametri: object                      # ParametriIngresso
    etichette_stati: list                  # ["N(0,0)", "N(0,1)", ...]
    h: float                               # passo temporale usato per P(h)
    p: object                              # distribuzione stazionaria (array numpy)
    passi: int                             # passi fatti per convergere
    indicatori: object                     # Indicatori
    controlli_matrice: list = field(default_factory=list)   # [EsitoControllo, ...]
    verifiche: list = field(default_factory=list)           # [EsitoControllo, ...]

    @property
    def tempo_simulato(self):
        return self.passi * self.h

    def probabilita_per_stato(self):
        # {"N(0,0)": 0.1234, ...} nello stesso ordine degli stati
        return {etichetta: float(self.p[r]) for r, etichetta in enumerate(self.etichette_stati)}

    def come_dizionario(self):
        return {
            "parametri": self.parametri.come_dizionario(),
            "rho": self.parametri.rho,
            "h": float(self.h),
            "passi": int(self.passi),
            "tempo_simulato_ore": float(self.tempo_simulato),
            "probabilita_stazionarie": self.probabilita_per_stato(),
            "indicatori": self.indicatori.come_dizionario(),
            "controlli_matrice": [e.come_dizionario() for e in self.controlli_matrice],
            "verifiche": [e.come_dizionario() for e in self.verifiche],
        }
