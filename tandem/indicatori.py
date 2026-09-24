"""
INDICATORI: le prestazioni del sistema a regime.

Corrisponde alla sezione "5. INDICATORI DI PRESTAZIONE" dello script originale.

  Indicatori             il contenitore dei valori calcolati
  CalcolatoreIndicatori  li calcola come somme sugli stati, pesate con p
"""
from dataclasses import dataclass, asdict


@dataclass
class Indicatori:
    p_bloccata: float       # M1 ferma con il pezzo finito dentro
    p_vuoto: float          # sistema completamente vuoto
    p_perso: float          # lato M1 pieno: un arrivo viene rifiutato
    p_M1_occupata: float    # M1 sta lavorando
    p_M2_occupata: float    # M2 sta lavorando
    Ls: float               # numero medio di pezzi nel sistema (WIP)
    lam_eff: float          # pezzi/ora che entrano davvero
    throughput_M1: float    # pezzi/ora lavorati da M1 (usato solo nel controllo del flusso)
    throughput: float       # pezzi/ora che escono da M2 = throughput del sistema
    Ws: float               # tempo medio nel sistema (legge di Little)

    def come_dizionario(self):
        # float() serve solo per il salvataggio su JSON (i valori sono numpy.float64)
        return {nome: float(valore) for nome, valore in asdict(self).items()}


class CalcolatoreIndicatori:

    def __init__(self, parametri, spazio):
        self.parametri = parametri
        self.spazio = spazio

    def calcola(self, p):
        # Ogni indicatore e' una somma sugli stati che soddisfano una condizione, pesata con p.
        lam = self.parametri.lam
        mu = self.parametri.mu
        K1 = self.parametri.K1

        p_bloccata = p_vuoto = p_perso = p_M1_occupata = p_M2_occupata = Ls = 0.0

        for r in range(self.spazio.numero_stati):
            tipo, i, j = self.spazio[r]
            if tipo == "B":            p_bloccata = p_bloccata + p[r]            # M1 ferma con il pezzo finito dentro
            if i == 0 and j == 0:      p_vuoto = p_vuoto + p[r]
            if i == K1 + 1:            p_perso = p_perso + p[r]                  # lato M1 pieno: un arrivo viene rifiutato (vale per N e B)
            if tipo == "N" and i >= 1: p_M1_occupata = p_M1_occupata + p[r]      # M1 sta lavorando
            if j >= 1:                 p_M2_occupata = p_M2_occupata + p[r]      # M2 sta lavorando
            Ls = Ls + (i + j) * p[r]                                             # pezzi presenti nello stato, pesati con p

        lam_eff = lam * (1 - p_perso)                # entra davvero solo la frazione di arrivi che trova posto
        throughput_M1 = mu * p_M1_occupata           # pezzi/ora lavorati da M1 (usato solo nel controllo del flusso)
        throughput = mu * p_M2_occupata              # pezzi/ora che escono da M2 = throughput del sistema (a regime = lam_eff)
        Ws = Ls / lam_eff                            # legge di Little: tempo medio nel sistema di un pezzo accettato

        return Indicatori(
            p_bloccata=p_bloccata,
            p_vuoto=p_vuoto,
            p_perso=p_perso,
            p_M1_occupata=p_M1_occupata,
            p_M2_occupata=p_M2_occupata,
            Ls=Ls,
            lam_eff=lam_eff,
            throughput_M1=throughput_M1,
            throughput=throughput,
            Ws=Ws,
        )
