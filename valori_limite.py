"""
Valori limite degli indicatori al crescere delle capacita' dei buffer (tesi, Tabella 5.5).

Uso:
    python valori_limite.py                        scenario base e sezione "valori_limite" da input/parametri.json
    python valori_limite.py --input altro.json     legge un altro file JSON

Si fa crescere una capacita' alla volta (limiti univariati) oppure entrambe (limite multivariato) e si
guarda verso quali valori tendono throughput, P(rifiuto), P(M1 bloccata), Ls e Ws:
    K1 = 0,    K2 crescente
    K2 = c,    K1 crescente        per ogni c della lista "K2_fissi"
    K1 = K2,   entrambe crescenti

Con capacita' di qualche centinaio di posti la convergenza richiederebbe troppi passi, quindi qui la
distribuzione stazionaria si ottiene risolvendo direttamente pi*Q = 0 (tandem/diretto.py), con la stessa
matrice Q costruita da ModelloTandem. Le due soluzioni coincidono: la tabella riporta anche, per le capacita'
piu' piccole, la differenza massima con la soluzione per convergenza.

Ogni esecuzione salva in una cartella nuova output/valori_limite/AAAA-MM-GG_HHMMSS/:
    configurazione.json    scenario base e sezione usata
    valori_limite.csv      una riga per configurazione calcolata
    valori_limite.txt      la stessa tabella in forma leggibile
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from tandem import ParametriIngresso, SpazioStati, ModelloTandem, RisolutoreConvergenza, CalcolatoreIndicatori
from tandem.diretto import RisolutoreDiretto

CARTELLA_PROGETTO = Path(__file__).resolve().parent
FILE_PARAMETRI = CARTELLA_PROGETTO / "input" / "parametri.json"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output" / "valori_limite"
CAMPI = ("throughput", "p_perso", "p_bloccata", "Ls", "Ws")


def risolvi(lam, mu, K1, K2, confronta_convergenza=False):
    parametri = ParametriIngresso(lam, mu, K1, K2)
    spazio = SpazioStati(parametri)
    modello = ModelloTandem(parametri, spazio)
    p = RisolutoreDiretto(modello).risolvi()
    riga = {"K1": K1, "K2": K2, "stati": modello.numero_stati}
    riga.update({c: float(getattr(CalcolatoreIndicatori(parametri, spazio).calcola(p), c)) for c in CAMPI})
    if confronta_convergenza:
        p_conv, _ = RisolutoreConvergenza(modello).converge()
        riga["diff_convergenza"] = float(np.max(np.abs(p - p_conv)))
    return riga


def main():
    parser = argparse.ArgumentParser(description="Valori limite degli indicatori al crescere dei buffer")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="JSON con scenario base e sezione valori_limite")
    argomenti = parser.parse_args()

    base = ParametriIngresso.da_json(argomenti.input)
    sezione = json.loads(argomenti.input.read_text(encoding="utf-8"))["valori_limite"]
    K_crescenti = [int(k) for k in sezione["K_crescenti"]]
    K_entrambi = [int(k) for k in sezione["K_entrambi"]]
    K2_fissi = [int(k) for k in sezione["K2_fissi"]]
    K_confronto = int(sezione.get("K_max_confronto_convergenza", 10))

    righe = []
    def aggiungi(serie, K1, K2):
        r = risolvi(base.lam, base.mu, K1, K2, confronta_convergenza=max(K1, K2) <= K_confronto)
        righe.append({"serie": serie, **r})
        print(f"{serie:<22} K1={K1:<4} K2={K2:<4} X={r['throughput']:.4f}")

    for K in K_crescenti:
        aggiungi("K1=0, K2 crescente", 0, K)
    for c in K2_fissi:
        for K in K_crescenti:
            aggiungi(f"K2={c}, K1 crescente", K, c)
    for K in K_entrambi:
        aggiungi("K1=K2 crescenti", K, K)

    cartella = CARTELLA_OUTPUT / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "configurazione.json").write_text(
        json.dumps({"scenario_base": base.come_dizionario(), "valori_limite": sezione}, indent=2), encoding="utf-8")
    campi = ["serie", "K1", "K2", "stati", *CAMPI, "diff_convergenza"]
    with (cartella / "valori_limite.csv").open("w", newline="", encoding="utf-8") as f:
        scrittore = csv.DictWriter(f, fieldnames=campi)
        scrittore.writeheader()
        scrittore.writerows(righe)
    with (cartella / "valori_limite.txt").open("w", encoding="utf-8") as f:
        f.write(f"lam = {base.lam:g}, mu = {base.mu:g}\n\n")
        f.write(f"{'serie':<22}{'K1':>6}{'K2':>6}{'X':>10}{'P_rif':>9}{'P_bloc':>9}{'Ls':>10}{'Ws':>9}{'diff conv.':>12}\n")
        for r in righe:
            d = f"{r['diff_convergenza']:.1e}" if "diff_convergenza" in r else ""
            f.write(f"{r['serie']:<22}{r['K1']:>6}{r['K2']:>6}{r['throughput']:>10.4f}{r['p_perso']:>9.4f}"
                    f"{r['p_bloccata']:>9.4f}{r['Ls']:>10.3f}{r['Ws']:>9.3f}{d:>12}\n")
    print(len(righe), "configurazioni. Risultati in:", cartella)


if __name__ == "__main__":
    main()
