"""
Package tandem: il modello a catena di Markov di due macchine in tandem,
organizzato in classi, una per sezione del calcolo.

  input.py        ParametriIngresso            (dati di ingresso)
  oggetti.py      Stato, SpazioStati           (sezione 1: lista degli stati)
  modello.py      ModelloTandem                (sezione 2: Q, L, h, P(h))
  controlli.py    ControlliMatrice             (sezione 3: controlli sulla matrice)
  convergenza.py  RisolutoreConvergenza        (sezione 4: distribuzione stazionaria)
  indicatori.py   Indicatori, CalcolatoreIndicatori   (sezione 5)
  verifiche.py    VerificheSoluzione           (sezione 6)
  risultati.py    Risultati                    (contenitore dei risultati)
  output.py       StampaConsole, SalvaRisultati (stampa a video e salvataggio su file)
"""
from .input import ParametriIngresso
from .oggetti import Stato, SpazioStati
from .modello import ModelloTandem
from .controlli import EsitoControllo, ControlliMatrice
from .convergenza import RisolutoreConvergenza
from .indicatori import Indicatori, CalcolatoreIndicatori
from .verifiche import VerificheSoluzione
from .risultati import Risultati
from .output import StampaConsole, SalvaRisultati

__all__ = [
    "ParametriIngresso",
    "Stato", "SpazioStati",
    "ModelloTandem",
    "EsitoControllo", "ControlliMatrice",
    "RisolutoreConvergenza",
    "Indicatori", "CalcolatoreIndicatori",
    "VerificheSoluzione",
    "Risultati",
    "StampaConsole", "SalvaRisultati",
]
