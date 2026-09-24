"""
CONTROLLI: le verifiche sulla matrice PRIMA di far convergere.

Corrisponde alla sezione "3. CONTROLLI SULLA MATRICE" dello script originale.

  EsitoControllo    il risultato di un singolo controllo (descrizione, superato, valore)
  ControlliMatrice  esegue i due controlli: P(h) e' una matrice di probabilita', la catena e' irriducibile
"""
from typing import NamedTuple


class EsitoControllo(NamedTuple):
    descrizione: str
    superato: bool
    valore: str

    def riga(self):
        # stessa riga di testo che lo script stampa con controllo(...)
        return ("OK     " if self.superato else "ERRORE ") + " " + self.descrizione.ljust(60) + " " + self.valore

    def come_dizionario(self):
        # bool() serve per il salvataggio su JSON (superato puo' essere un numpy.bool_)
        return {"descrizione": self.descrizione, "superato": bool(self.superato), "valore": self.valore}


class ControlliMatrice:

    def __init__(self, modello, toll=1e-9):
        self.modello = modello
        self.toll = toll

    def raggiungibili(self, partenza, all_indietro):
        # quali stati si raggiungono partendo da uno stato, seguendo le transizioni in avanti o all'indietro
        Q = self.modello.Q
        n = self.modello.numero_stati
        trovati = [partenza]
        for r in trovati:                        # la lista si allunga mentre la scorro
            for c in range(n):                   # per ogni r vedo i singoli c
                tasso = Q[c][r] if all_indietro else Q[r][c]
                if c != r and tasso > 0 and c not in trovati:   # la "stanza" non devo averla gia' trovata, altrimenti ciclo infinito
                    trovati.append(c)
        return len(trovati)

    def matrice_di_probabilita(self):
        # 1) P(h) e' una matrice di probabilita': righe a somma 1 (equivale a righe di Q a somma 0) ed elementi in [0,1]
        P_h = self.modello.P_h
        n = self.modello.numero_stati
        toll = self.toll
        superato = (max(abs(sum(P_h[r]) - 1) for r in range(n)) < toll
                    and P_h.min() >= -toll and P_h.max() <= 1 + toll)
        return EsitoControllo(
            "1. P(h) e' una matrice di probabilita' (righe a 1, elementi in [0,1])",
            superato,
            "min = " + str(round(float(P_h.min()), 4)) + ", max = " + str(round(float(P_h.max()), 4)),
        )

    def catena_irriducibile(self):
        # 2) catena irriducibile: da N(0,0) si raggiunge ogni stato e da ogni stato si torna a N(0,0)
        #    (ipotesi del teorema che garantisce una sola distribuzione stazionaria)
        vuoto = self.modello.spazio.vuoto
        n = self.modello.numero_stati
        avanti = self.raggiungibili(vuoto, False)
        indietro = self.raggiungibili(vuoto, True)
        return EsitoControllo(
            "2. catena irriducibile (tutti gli stati comunicano)",
            avanti == n and indietro == n,
            "raggiunti " + str(avanti) + " e " + str(indietro) + " su " + str(n),
        )

    def esegui(self):
        return [self.matrice_di_probabilita(), self.catena_irriducibile()]

    @staticmethod
    def tutti_superati(esiti):
        return all(e.superato for e in esiti)
