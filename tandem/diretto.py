"""
DIRETTO: la distribuzione stazionaria ottenuta risolvendo direttamente pi*Q = 0.

Non sostituisce il metodo della convergenza (sezione 4), che resta quello usato nelle analisi.
Serve per due cose:
  - verificare la convergenza: le due soluzioni devono coincidere (controllo usato nella tesi, par. 4.2);
  - calcolare configurazioni con capacita' molto grandi (valori_limite.py), dove la convergenza
    richiederebbe troppi passi.

Le equazioni di equilibrio pi*Q = 0 sono linearmente dipendenti: una si sostituisce con la
normalizzazione sum(pi) = 1 e si risolve il sistema lineare che ne risulta.
"""
import numpy as np


class RisolutoreDiretto:

    def __init__(self, modello):
        self.modello = modello

    def risolvi(self):
        """Restituisce pi, la distribuzione stazionaria (stesso ordine degli stati della matrice Q)."""
        n = self.modello.numero_stati
        A = self.modello.Q.T.copy()          # pi*Q = 0  <=>  Q^T * pi^T = 0
        A[-1, :] = 1.0                       # l'ultima equazione diventa sum(pi) = 1
        b = np.zeros(n)
        b[-1] = 1.0
        return np.linalg.solve(A, b)


def calcola_diretto(parametri):
    """Come sensitivita.calcola, ma con la soluzione diretta: una riga con parametri e indicatori.
    Si usa per le griglie e le serie piu' estese (capacita' oltre 10 per buffer o oltre 20 posti in tutto),
    dove la convergenza richiederebbe molti passi; il valore di 'passi' e' 0."""
    from . import SpazioStati, ModelloTandem, CalcolatoreIndicatori
    spazio = SpazioStati(parametri)
    modello = ModelloTandem(parametri, spazio)
    p = RisolutoreDiretto(modello).risolvi()
    riga = parametri.come_dizionario()
    riga.update(rho=parametri.rho, stati=modello.numero_stati, passi=0)
    riga.update(CalcolatoreIndicatori(parametri, spazio).calcola(p).come_dizionario())
    return riga
