"""
OUTPUT: la stampa a video e il salvataggio su file.

  StampaConsole   riproduce esattamente le stampe dello script originale, sezione per sezione
  SalvaRisultati  scrive i risultati nella cartella di output (JSON + report di testo)
"""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path


class StampaConsole:

    LARGHEZZA = 11   # un modo per dare a ogni casella la stessa larghezza: rjust(11) e ljust(11)
    MAX_STATI_TABELLA = 40   # con piu' di 40 stati la tabella sarebbe larga piu' di 440 caratteri e illeggibile

    # ---- sezione 2: intestazione e tabelle ----
    def intestazione(self, modello):
        print("Numero di stati:", modello.numero_stati, "  [(K1+2)(K2+2)+(K1+1)]",
              "   passo h = 0.1/max|Q[r][r]| =", round(modello.h, 6), "ore")

    def tabella(self, modello, T, titolo):
        w = self.LARGHEZZA
        stati = modello.spazio
        print()
        print(titolo)
        print("".ljust(w), end="")
        for c in range(modello.numero_stati):
            print(stati[c].etichetta().rjust(w), end="")
        print()
        for r in range(modello.numero_stati):
            print(stati[r].etichetta().ljust(w), end="")     # bordi tabella
            for c in range(modello.numero_stati):
                print(str(T[r][c]).rjust(w), end="")
            print()

    def tabelle(self, modello):
        # le due tabelle vengono stampate solo se il numero di stati e' ragionevole
        if modello.numero_stati <= self.MAX_STATI_TABELLA:
            self.tabella(modello, modello.L,
                         "=== TABELLA DEGLI STATI con le lettere (probabilita' di passare da riga a colonna in un intervallo h) ===")
            self.tabella(modello, modello.tabella_P_h(),
                         "=== MATRICE P(h) = I + Q*h che viene fatta convergere (lam = " + str(modello.parametri.lam)
                         + ", mu = " + str(modello.parametri.mu) + ") ===")

    # ---- sezione 3: controlli sulla matrice ----
    def controlli_matrice(self, esiti):
        print()
        print("=== CONTROLLI SULLA MATRICE ===")
        for e in esiti:
            print(e.riga())

    # ---- sezione 4: probabilita' stazionarie ----
    def probabilita_stazionarie(self, risultati):
        print()
        print("=== PROBABILITA' STAZIONARIE (rho =", round(risultati.parametri.rho, 4), ")   raggiunte dopo",
              risultati.passi, "passi, tempo simulato", round(risultati.tempo_simulato, 2), "ore ===")
        for r, etichetta in enumerate(risultati.etichette_stati):
            print(etichetta.ljust(9), " p =", round(risultati.p[r], 4))

    # ---- sezione 5: indicatori ----
    def indicatori(self, risultati):
        ind = risultati.indicatori
        lam = risultati.parametri.lam
        print()
        print("=== INDICATORI ===")
        print("P(M1 bloccata)      =", round(ind.p_bloccata, 4))
        print("P(sistema vuoto)    =", round(ind.p_vuoto, 4))
        print("P(arrivo rifiutato) =", round(ind.p_perso, 4), "   -> su", lam,
              "pezzi/ora che si presentano ne vengono rifiutati", round(lam - ind.lam_eff, 4))
        print("Throughput          =", round(ind.throughput, 4), "pezzi/ora  (= lambda effettivo, cio' che entra e' cio' che esce)")
        print("Ls (= WIP)          =", round(ind.Ls, 4), "pezzi     (numero medio di pezzi nel sistema)")
        print("Ws                  =", round(ind.Ws, 4), "ore =", round(ind.Ws * 60, 2),
              "minuti   (tempo medio nel sistema, Ws = Ls / lambda_eff)")

    # ---- sezione 6: verifiche sulla soluzione ----
    def verifiche(self, esiti):
        print()
        print("=== VERIFICHE SULLA SOLUZIONE ===")
        for e in esiti:
            print(e.riga())

    # ---- tutto insieme (usato per il report su file) ----
    def rapporto_completo(self, modello, risultati):
        self.intestazione(modello)
        self.tabelle(modello)
        self.controlli_matrice(risultati.controlli_matrice)
        self.probabilita_stazionarie(risultati)
        self.indicatori(risultati)
        self.verifiche(risultati.verifiche)

    def testo_rapporto(self, modello, risultati):
        # stesso testo di rapporto_completo, ma restituito come stringa invece che stampato
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.rapporto_completo(modello, risultati)
        return buffer.getvalue()


class SalvaRisultati:

    def __init__(self, cartella):
        self.cartella = Path(cartella)

    def json(self, risultati, nome="risultati.json"):
        self.cartella.mkdir(parents=True, exist_ok=True)
        percorso = self.cartella / nome
        with percorso.open("w", encoding="utf-8") as f:
            json.dump(risultati.come_dizionario(), f, indent=2, ensure_ascii=False)
        return percorso

    def report(self, modello, risultati, nome="report.txt"):
        self.cartella.mkdir(parents=True, exist_ok=True)
        percorso = self.cartella / nome
        testo = StampaConsole().testo_rapporto(modello, risultati)
        with percorso.open("w", encoding="utf-8") as f:
            f.write(testo)
        return percorso

    def tutto(self, modello, risultati):
        # un file per combinazione di parametri: rilanciare con parametri diversi non sovrascrive i risultati precedenti
        p = risultati.parametri
        suffisso = f"_lam{p.lam:g}_mu{p.mu:g}_K1-{p.K1}_K2-{p.K2}"
        return [self.json(risultati, "risultati" + suffisso + ".json"),
                self.report(modello, risultati, "report" + suffisso + ".txt")]
