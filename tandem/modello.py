"""
MODELLO: la matrice generatrice Q, la tabella con le lettere L e la matrice P(h).

Corrisponde alla sezione "2. MATRICE GENERATRICE Q E TABELLA CON LE LETTERE" dello script originale.
La classe ModelloTandem costruisce le matrici a partire dai parametri e dallo spazio degli stati
e non fa altro: niente stampe, niente convergenza.
"""
import numpy as np

from .oggetti import Stato


class ModelloTandem:

    def __init__(self, parametri, spazio):
        self.parametri = parametri
        self.spazio = spazio
        n = spazio.numero_stati

        # Q[r][c] = tasso con cui si passa dallo stato r (riga) allo stato c (colonna).
        # Gli arrivi si presentano sempre con tasso lam: se il lato M1 e' pieno la transizione non esiste
        # (il pezzo e' rifiutato e il sistema resta dov'e'): i rifiuti restano "dentro" la diagonale.
        # L e' la stessa tabella scritta con le lettere (λh, μh, 1-λh-μh, ...), per il confronto con la versione a mano.
        self.Q = np.zeros((n, n))
        self.L = [["" for c in range(n)] for r in range(n)]

        self._costruisci_transizioni()
        self._completa_diagonale()

        # P(h) = I + Q*h e' la matrice che verra' fatta convergere. 1/max|Q[r][r]| e' il passo piu' grande per cui
        # ogni riga di P(h) resta una probabilita'; ne prendo un decimo, cosi' h e' "piccolo" (termini in h^2 trascurabili)
        self.h = 0.1 / max(-self.Q[r][r] for r in range(n))
        # E' la formula che collega i due modi di descrivere lo stesso sistema:
        # i tassi (tempo continuo) e le probabilita' (tempo discreto)
        self.P_h = np.eye(n) + self.Q * self.h

    @property
    def numero_stati(self):
        return self.spazio.numero_stati

    def _aggiungi(self, r, arrivo, tasso, lettera):
        # scrive UNA transizione: dallo stato in riga r allo stato "arrivo", con il tasso dato
        c = self.spazio.indice(arrivo)               # colonna dello stato di arrivo
        self.Q[r][c] = self.Q[r][c] + tasso          # il numero nella matrice dei tassi
        self.L[r][c] = self.L[r][c] + lettera        # la lettera nella casella
        self.L[r][r] = self.L[r][r] + "-" + lettera  # ogni uscita toglie il suo pezzo alla probabilita' di restare

    def _costruisci_transizioni(self):
        # Le regole di transizione: una riga per ogni riga della tabella delle transizioni.
        lam = self.parametri.lam
        mu = self.parametri.mu
        K1 = self.parametri.K1
        K2 = self.parametri.K2

        for r in range(self.numero_stati):
            tipo, i, j = self.spazio[r]
            if tipo == "N":
                if i < K1 + 1:              self._aggiungi(r, Stato("N", i + 1, j),      lam, "λh")   # arrivo: c'e' posto sul lato M1
                if i >= 1 and j < K2 + 1:   self._aggiungi(r, Stato("N", i - 1, j + 1),  mu,  "μh")   # M1 finisce e il pezzo passa al lato M2
                if i >= 1 and j == K2 + 1:  self._aggiungi(r, Stato("B", i, K2 + 1),     mu,  "μh")   # M1 finisce ma il lato M2 e' saturo: si blocca
                if j >= 1:                  self._aggiungi(r, Stato("N", i, j - 1),      mu,  "μh")   # M2 finisce: il pezzo esce dal sistema
            else:
                if i < K1 + 1:              self._aggiungi(r, Stato("B", i + 1, K2 + 1), lam, "λh")   # arrivo: si mette in coda dietro al blocco
                self._aggiungi(r, Stato("N", i - 1, K2 + 1), mu, "μh")                                # M2 finisce: il pezzo bloccato passa, M1 riparte

    def _completa_diagonale(self):
        for r in range(self.numero_stati):
            self.Q[r][r] = -sum(self.Q[r])           # diagonale di Q: ogni riga somma a zero
            self.L[r][r] = "1" + self.L[r][r]        # diagonale con le lettere: 1 meno tutte le uscite

    def tabella_P_h(self):
        # P(h) arrotondata a 4 cifre, con le caselle a zero fuori diagonale lasciate vuote (come nello script)
        n = self.numero_stati
        return [["" if (r != c and self.P_h[r][c] == 0) else round(self.P_h[r][c], 4)
                 for c in range(n)]
                for r in range(n)]
