"""
Punto di ingresso: fa esattamente quello che faceva modello_generale_convergenza3.py,
ma usando le classi del package tandem.

Uso:
    python main.py                              parametri letti da input/parametri.json
    python main.py --input altro_file.json      parametri letti da un altro file JSON
    python main.py --lam 10 --mu 12 --K1 1 --K2 1   sovrascrive singoli valori del JSON
    python main.py --no-salva                   non scrive nulla nella cartella output/

Ingresso:  input/parametri.json     (JSON con lam, mu, K1, K2)
Uscita:    output/risultati.json    (JSON con tutti i risultati)  +  output/report.txt
"""
import argparse
from pathlib import Path

from tandem import (
    ParametriIngresso,
    SpazioStati,
    ModelloTandem,
    ControlliMatrice,
    RisolutoreConvergenza,
    CalcolatoreIndicatori,
    VerificheSoluzione,
    Risultati,
    StampaConsole,
    SalvaRisultati,
)

CARTELLA_PROGETTO = Path(__file__).resolve().parent
CARTELLA_INPUT = CARTELLA_PROGETTO / "input"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output"
FILE_PARAMETRI = CARTELLA_INPUT / "parametri.json"


def leggi_parametri(argomenti):
    # 1) dal file JSON (input/parametri.json, o quello passato con --input);
    # 2) se il file non esiste, i default scritti in ParametriIngresso;
    # 3) in entrambi i casi i valori passati da riga di comando hanno la precedenza
    if argomenti.input.exists():
        parametri = ParametriIngresso.da_json(argomenti.input)
        print("Parametri letti da:", argomenti.input)
    else:
        parametri = ParametriIngresso()
        print("File", argomenti.input, "non trovato: uso i parametri di default",
              "(copia input/parametri.example.json in input/parametri.json per cambiarli)")
    if argomenti.lam is not None: parametri.lam = argomenti.lam
    if argomenti.mu is not None:  parametri.mu = argomenti.mu
    if argomenti.K1 is not None:  parametri.K1 = argomenti.K1
    if argomenti.K2 is not None:  parametri.K2 = argomenti.K2
    return ParametriIngresso(parametri.lam, parametri.mu, parametri.K1, parametri.K2)   # ricontrolla i valori


def esegui(parametri, stampa=None):
    """Esegue l'intero modello e restituisce (modello, risultati). Le stampe seguono l'ordine dello script."""
    if stampa is None:
        stampa = StampaConsole()

    # 1. lista degli stati  +  2. matrici Q, L, P(h)
    spazio = SpazioStati(parametri)
    modello = ModelloTandem(parametri, spazio)
    stampa.intestazione(modello)
    stampa.tabelle(modello)

    # 3. controlli sulla matrice (prima di convergere)
    esiti_controlli = ControlliMatrice(modello).esegui()
    stampa.controlli_matrice(esiti_controlli)
    if not ControlliMatrice.tutti_superati(esiti_controlli):
        raise SystemExit("La matrice non supera i controlli: correggere le regole di transizione prima di procedere.")

    # 4. distribuzione stazionaria per convergenza
    p, passi = RisolutoreConvergenza(modello).converge()

    # 5. indicatori di prestazione
    indicatori = CalcolatoreIndicatori(parametri, spazio).calcola(p)

    # 6. verifiche sulla soluzione
    esiti_verifiche = VerificheSoluzione(modello).esegui(p, indicatori)

    risultati = Risultati(
        parametri=parametri,
        etichette_stati=spazio.etichette(),
        h=modello.h,
        p=p,
        passi=passi,
        indicatori=indicatori,
        controlli_matrice=esiti_controlli,
        verifiche=esiti_verifiche,
    )
    stampa.probabilita_stazionarie(risultati)
    stampa.indicatori(risultati)
    stampa.verifiche(esiti_verifiche)
    return modello, risultati


def main():
    parser = argparse.ArgumentParser(description="Catena di Markov: due macchine in tandem (metodo della convergenza)")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="file JSON con lam, mu, K1, K2 (default: input/parametri.json)")
    parser.add_argument("--lam", type=float, default=None)
    parser.add_argument("--mu", type=float, default=None)
    parser.add_argument("--K1", type=int, default=None)
    parser.add_argument("--K2", type=int, default=None)
    parser.add_argument("--output", type=Path, default=CARTELLA_OUTPUT, help="cartella in cui salvare i risultati")
    parser.add_argument("--no-salva", action="store_true", help="non salvare nulla su file")
    argomenti = parser.parse_args()

    parametri = leggi_parametri(argomenti)
    modello, risultati = esegui(parametri)

    if not argomenti.no_salva:
        percorsi = SalvaRisultati(argomenti.output).tutto(modello, risultati)
        print()
        print("Risultati salvati in:", ", ".join(str(p) for p in percorsi))


if __name__ == "__main__":
    main()
