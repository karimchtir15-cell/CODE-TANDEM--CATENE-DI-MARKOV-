"""
Verifica del modello implementato (tesi, paragrafo 4.2).

Uso:
    python verifica.py                        sezione "verifica" da input/parametri.json
    python verifica.py --input altro.json     legge un altro file JSON

Tre prove, indipendenti dai quattro controlli che il programma esegue a ogni calcolo:
  A. soluzioni in forma chiusa: con K1 = K2 = 0 (modello di riferimento) e con K1 = 1, K2 = 0 la
     distribuzione ottenuta per convergenza deve coincidere con le formule ricavate a mano;
  B. convergenza contro soluzione diretta: su una griglia di configurazioni (K1, K2, lam, mu) la
     distribuzione per convergenza deve coincidere con quella che risolve direttamente pi*Q = 0;
  C. efficacia dei controlli: si introducono di proposito 13 errori nelle regole di transizione e nei
     parametri del calcolo, e per ciascuno si guarda quali dei quattro controlli lo rilevano.
     Ogni errore deve essere rilevato da almeno un controllo.

Ogni esecuzione salva in output/verifica/AAAA-MM-GG_HHMMSS/ il file verifica.txt (lo stesso testo
stampato a video) e i dettagli in forma_chiusa.csv, convergenza_vs_diretta.csv, errori.csv.
"""
import argparse
import csv
import io
import json
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

import numpy as np

from tandem import (ParametriIngresso, SpazioStati, ModelloTandem, ControlliMatrice, RisolutoreConvergenza,
                    CalcolatoreIndicatori, VerificheSoluzione)
from tandem.oggetti import Stato
from tandem.diretto import RisolutoreDiretto

CARTELLA_PROGETTO = Path(__file__).resolve().parent
FILE_PARAMETRI = CARTELLA_PROGETTO / "input" / "parametri.json"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output" / "verifica"


# ---------------------------------------------------------------- A. forma chiusa

def prova_forma_chiusa(lam, mu):
    rho = lam / mu
    righe = []
    # modello di riferimento (par. 1.4): p00 = 2 / (3 rho^2 + 4 rho + 2)
    par = ParametriIngresso(lam, mu, 0, 0); spazio = SpazioStati(par)
    p, _ = RisolutoreConvergenza(ModelloTandem(par, spazio)).converge()
    A = 3 * rho**2 + 4 * rho + 2
    righe.append({"caso": "K1=0, K2=0", "stato": "N(0,0)", "formula": 2 / A, "convergenza": p[spazio.indice(Stato("N", 0, 0))]})
    # K1 = 1, K2 = 0 (par. 3.2): denominatore comune S
    par = ParametriIngresso(lam, mu, 1, 0); spazio = SpazioStati(par)
    p, _ = RisolutoreConvergenza(ModelloTandem(par, spazio)).converge()
    S = 3 * rho**5 + 15 * rho**4 + 24 * rho**3 + 20 * rho**2 + 12 * rho + 4
    righe.append({"caso": "K1=1, K2=0", "stato": "N(0,0)", "formula": (4 * rho + 4) / S, "convergenza": p[spazio.indice(Stato("N", 0, 0))]})
    righe.append({"caso": "K1=1, K2=0", "stato": "B(2,1)", "formula": (rho**5 + 5 * rho**4 + 6 * rho**3) / S,
                  "convergenza": p[spazio.indice(Stato("B", 2, 1))]})
    for r in righe:
        r["differenza"] = abs(r["formula"] - r["convergenza"])
    return righe


# ---------------------------------------------------------------- B. convergenza contro soluzione diretta

def prova_diretta(sezione):
    righe = []
    for mu in sezione["mu"]:
        for lam in sezione["lam"]:
            for K1 in sezione["K1"]:
                for K2 in sezione["K2"]:
                    par = ParametriIngresso(lam, mu, K1, K2)
                    modello = ModelloTandem(par, SpazioStati(par))
                    p_conv, passi = RisolutoreConvergenza(modello).converge()
                    p_dir = RisolutoreDiretto(modello).risolvi()
                    righe.append({"lam": lam, "mu": mu, "K1": K1, "K2": K2, "stati": modello.numero_stati,
                                  "passi": passi, "differenza_massima": float(np.max(np.abs(p_conv - p_dir)))})
    return righe


# ---------------------------------------------------------------- C. errori introdotti di proposito

ERRORI = [
    "regola di sblocco tolta",
    "regola di blocco tolta",
    "M1 passa il pezzo nello stato sbagliato",
    "diagonale di Q dimezzata",
    "passo h trenta volte piu' grande",
    "arrivo con tasso mu",
    "arrivo negli stati bloccati con tasso mu",
    "M2 finisce con tasso lam",
    "solo 3 passi di convergenza",
    "tolleranza di arresto 1e-4",
    "sblocco senza togliere il pezzo dal lato M1",
    "arrivi negli stati bloccati tolti",
    "blocco gia' con j = K2",
]


class ModelloConErrore(ModelloTandem):
    """ModelloTandem con un errore introdotto di proposito nelle regole o nella diagonale."""

    def __init__(self, parametri, spazio, errore):
        self.errore = errore
        super().__init__(parametri, spazio)
        if errore == "passo h trenta volte piu' grande":
            self.h = 30 * self.h
            self.P_h = np.eye(self.numero_stati) + self.Q * self.h

    def _costruisci_transizioni(self):
        e = self.errore
        lam, mu, K1, K2 = self.parametri.lam, self.parametri.mu, self.parametri.K1, self.parametri.K2
        for r in range(self.numero_stati):
            tipo, i, j = self.spazio[r]
            if tipo == "N":
                if i < K1 + 1:
                    self._aggiungi(r, Stato("N", i + 1, j), mu if e == "arrivo con tasso mu" else lam, "λh")
                if i >= 1 and j < K2 + 1:
                    arrivo = Stato("N", i - 1, j) if e == "M1 passa il pezzo nello stato sbagliato" else Stato("N", i - 1, j + 1)
                    self._aggiungi(r, arrivo, mu, "μh")
                blocca = (i >= 1 and j >= K2) if e == "blocco gia' con j = K2" else (i >= 1 and j == K2 + 1)
                if blocca and e != "regola di blocco tolta":
                    self._aggiungi(r, Stato("B", i, K2 + 1), mu, "μh")
                if j >= 1:
                    self._aggiungi(r, Stato("N", i, j - 1), lam if e == "M2 finisce con tasso lam" else mu, "μh")
            else:
                if i < K1 + 1 and e != "arrivi negli stati bloccati tolti":
                    self._aggiungi(r, Stato("B", i + 1, K2 + 1), mu if e == "arrivo negli stati bloccati con tasso mu" else lam, "λh")
                if e == "sblocco senza togliere il pezzo dal lato M1":
                    self._aggiungi(r, Stato("N", i, K2 + 1), mu, "μh")
                elif e != "regola di sblocco tolta":
                    self._aggiungi(r, Stato("N", i - 1, K2 + 1), mu, "μh")

    def _completa_diagonale(self):
        super()._completa_diagonale()
        if self.errore == "diagonale di Q dimezzata":
            for r in range(self.numero_stati):
                self.Q[r][r] = 0.5 * self.Q[r][r]


def prova_errori(lam, mu, K1, K2):
    righe = []
    for errore in ERRORI:
        par = ParametriIngresso(lam, mu, K1, K2)
        spazio = SpazioStati(par)
        modello = ModelloConErrore(par, spazio, errore)
        esiti = ControlliMatrice(modello).esegui()          # controlli 1 e 2 (qui non si ferma: si vuole vedere anche 3 e 4)
        risolutore = RisolutoreConvergenza(modello)
        if errore == "solo 3 passi di convergenza":
            risolutore.passi_massimi = 3
        if errore == "tolleranza di arresto 1e-4":
            risolutore.tolleranza = 1e-4
        with np.errstate(all="ignore"):
            p, _ = risolutore.converge()
            try:
                indicatori = CalcolatoreIndicatori(par, spazio).calcola(p)
                esiti += VerificheSoluzione(modello).esegui(p, indicatori)
            except (ZeroDivisionError, FloatingPointError):
                esiti += [None, None]
        rilevato = [not (e is not None and bool(e.superato)) for e in esiti]   # un calcolo impossibile conta come rilevato
        righe.append({"errore": errore, **{f"controllo_{k + 1}": "X" if rilevato[k] else "." for k in range(4)},
                      "rilevato": any(rilevato)})
    return righe


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="Verifica del modello implementato")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="JSON con scenario base e sezione verifica")
    argomenti = parser.parse_args()

    base = ParametriIngresso.da_json(argomenti.input)
    sezione = json.loads(argomenti.input.read_text(encoding="utf-8"))["verifica"]
    cartella = CARTELLA_OUTPUT / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    cartella.mkdir(parents=True, exist_ok=True)

    testo = io.StringIO()
    with redirect_stdout(testo):
        print(f"VERIFICA DEL MODELLO IMPLEMENTATO   (lam = {base.lam:g}, mu = {base.mu:g})")
        print("\nA. Confronto con le soluzioni in forma chiusa")
        A = prova_forma_chiusa(base.lam, base.mu)
        for r in A:
            print(f"   {r['caso']:<12} pi_{r['stato']:<7} formula = {r['formula']:.10f}   convergenza = {r['convergenza']:.10f}   diff = {r['differenza']:.1e}")
        print("\nB. Convergenza contro soluzione diretta di pi*Q = 0")
        B = prova_diretta(sezione)
        print(f"   {len(B)} configurazioni, differenza massima tra le due distribuzioni: {max(r['differenza_massima'] for r in B):.1e}")
        print(f"\nC. Errori introdotti di proposito (K1 = {sezione['errori_K1']}, K2 = {sezione['errori_K2']})")
        C = prova_errori(base.lam, base.mu, sezione["errori_K1"], sezione["errori_K2"])
        print(f"   {'errore':<46} 1  2  3  4")
        for r in C:
            print(f"   {r['errore']:<46} {r['controllo_1']}  {r['controllo_2']}  {r['controllo_3']}  {r['controllo_4']}")
        print("   X = il controllo rileva l'errore, . = il controllo passa")
        print(f"   errori rilevati da almeno un controllo: {sum(r['rilevato'] for r in C)} su {len(C)}")
    print(testo.getvalue())
    (cartella / "verifica.txt").write_text(testo.getvalue(), encoding="utf-8")
    for nome, righe in [("forma_chiusa.csv", A), ("convergenza_vs_diretta.csv", B), ("errori.csv", C)]:
        with (cartella / nome).open("w", newline="", encoding="utf-8") as f:
            scrittore = csv.DictWriter(f, fieldnames=list(righe[0].keys()))
            scrittore.writeheader()
            scrittore.writerows(righe)
    print("Risultati in:", cartella)


if __name__ == "__main__":
    main()
