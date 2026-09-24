"""
CONVERGENZA: la distribuzione stazionaria ottenuta iterando p(n) = p(n-1) * P(h).

Corrisponde alla sezione "4. DISTRIBUZIONE STAZIONARIA PER CONVERGENZA" dello script originale.
La classe RisolutoreConvergenza parte da una distribuzione iniziale e moltiplica per P(h)
un passo alla volta finche' non cambia piu'.
"""
import numpy as np


class RisolutoreConvergenza:

    def __init__(self, modello, tolleranza=1e-13, passi_massimi=1000000):
        self.modello = modello
        self.tolleranza = tolleranza
        self.passi_massimi = passi_massimi

    def distribuzione_iniziale(self):
        # p(0): all'inizio il sistema e' vuoto con certezza
        p0 = np.zeros(self.modello.numero_stati)
        p0[self.modello.spazio.vuoto] = 1.0
        return p0

    def converge(self, p_iniziale=None):
        """Restituisce (p, passi): la distribuzione stazionaria e il numero di passi fatti."""
        if p_iniziale is None:
            p_iniziale = self.distribuzione_iniziale()
        P_h = self.modello.P_h
        h = self.modello.h

        p_n = p_iniziale.copy()
        n = 0
        while True:
            p_prec = p_n
            p_n = p_n @ P_h                      # un passo di durata h, chiocciola vettore x matrice
            n = n + 1
            if max(abs(p_n - p_prec)) / h < self.tolleranza or n >= self.passi_massimi:   # variazione per unita' di tempo
                return p_n, n
