"""
OGGETTI: gli stati della catena.

Corrisponde alla sezione "1. LISTA DEGLI STATI" dello script originale.

  Stato        e' la terna (tipo, i, j) con la sua etichetta di stampa
  SpazioStati  costruisce la lista di tutti gli stati e sa dire l'indice di ciascuno
"""
from typing import NamedTuple


class Stato(NamedTuple):
    """
    Ogni stato e' una terna (tipo, i, j):
      ("N", i, j)     stato NORMALE: i = pezzi sul lato M1 (coda + pezzo in macchina), 0..K1+1
                                     j = pezzi sul lato M2 (buffer + pezzo in macchina), 0..K2+1
      ("B", i, K2+1)  stato BLOCCATO: M1 ha finito un pezzo ma il lato M2 e' saturo e non puo' passarlo.
                                     i = pezzo bloccato in M1 + coda, 1..K1+1; il lato M2 vale sempre K2+1
    """
    tipo: str
    i: int
    j: int

    def etichetta(self):
        # es. N(0,1) oppure B(1,1): e' la stessa etichetta dello script originale
        return self.tipo + "(" + str(self.i) + "," + str(self.j) + ")"


class SpazioStati:
    """Costruisce e custodisce la lista ordinata degli stati (l'ordine e' quello dello script)."""

    def __init__(self, parametri):
        K1 = parametri.K1
        K2 = parametri.K2

        self.stati = []
        for i in range(0, K1 + 2):                 # primo ciclo: tutti gli stati normali -> (K1+2)(K2+2) stati
            for j in range(0, K2 + 2):
                self.stati.append(Stato("N", i, j))
        for i in range(1, K1 + 2):                 # secondo ciclo: gli stati bloccati -> K1+1 stati
            self.stati.append(Stato("B", i, K2 + 1))
        self.numero_stati = len(self.stati)

    def indice(self, stato):
        # posizione dello stato nella lista = riga/colonna nella matrice
        return self.stati.index(stato)

    @property
    def vuoto(self):
        # indice dello stato N(0,0): sistema completamente vuoto
        return self.indice(Stato("N", 0, 0))

    def etichette(self):
        return [s.etichetta() for s in self.stati]

    def __len__(self):
        return self.numero_stati

    def __iter__(self):
        return iter(self.stati)

    def __getitem__(self, r):
        return self.stati[r]
