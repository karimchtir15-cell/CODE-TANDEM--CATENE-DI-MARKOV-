"""
Analisi di sensitivita' del modello tandem e grafici.

Uso:
    python sensitivita.py                        parametri letti da input/parametri.json
    python sensitivita.py --input altro.json     legge un altro file JSON
    python sensitivita.py --output cartella      salva in un'altra cartella (default: output/sensitivita)

Ingresso: input/parametri.json con lo scenario base (lam, mu, K1, K2) e la sezione "sensitivita":
per ogni parametro il lower bound, l'upper bound e (per lam e mu) il numero di punti.
Ogni parametro viene fatto variare da solo tra i due bound, tenendo gli altri tre al valore base
(analisi "one-at-a-time").

Uscita (tutto in output/sensitivita/, cartella esclusa da git):
    scenario_base.json           risultati completi dello scenario base
    sensitivita.csv              una riga per esecuzione: parametro variato, valore, parametri, indicatori
    fig1_macchine_base.png       barre impilate M1 e M2: % del tempo in cui lavora / e' vuota / e' bloccata
    fig2_distribuzione_base.png  probabilita' stazionarie di ogni stato (scenario base)
    fig3_sensitivita_<par>.png   per ogni parametro: gli indicatori al variare del parametro tra i bound
    fig4_macchine_bounds.png     barre M1 e M2 a lower bound / base / upper bound, per ogni parametro
"""
import argparse
import csv
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # disegna su file, senza aprire finestre
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

from tandem import ParametriIngresso, SalvaRisultati
from main import esegui

CARTELLA_PROGETTO = Path(__file__).resolve().parent
FILE_PARAMETRI = CARTELLA_PROGETTO / "input" / "parametri.json"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output" / "sensitivita"

# bound usati se il JSON non ha la sezione "sensitivita"
BOUND_DEFAULT = {
    "lam": {"lower": 4.0, "upper": 20.0, "punti": 9},
    "mu":  {"lower": 6.0, "upper": 24.0, "punti": 9},
    "K1":  {"lower": 0, "upper": 10},
    "K2":  {"lower": 0, "upper": 10},
}

ETICHETTA = {
    "lam": "λ  (pezzi/ora che arrivano)",
    "mu":  "μ  (pezzi/ora lavorati da ogni macchina)",
    "K1":  "K1  (posti di buffer davanti a M1)",
    "K2":  "K2  (posti di buffer tra M1 e M2)",
}

# gli indicatori mostrati nei grafici di sensitivita': (campo in Indicatori, titolo, unita')
INDICATORI_GRAFICO = [
    ("throughput", "Throughput", "pezzi/ora"),
    ("p_perso",    "P(arrivo rifiutato)", ""),
    ("p_bloccata", "P(M1 bloccata)", ""),
    ("Ls",         "WIP  (pezzi nel sistema)", "pezzi"),
    ("Ws",         "Ws  (tempo nel sistema)", "ore"),
]

# colori: blu = lavora, grigio = vuota, arancione = bloccata
COLORE = {"lavora": "#2a78d6", "vuota": "#c3c2b7", "bloccata": "#eb6834", "linea": "#2a78d6", "base": "#eb6834"}


# ---------------------------------------------------------------- calcolo

def leggi_configurazione(percorso):
    """Restituisce (parametri base, bound per parametro)."""
    with Path(percorso).open("r", encoding="utf-8") as f:
        dati = json.load(f)
    base = ParametriIngresso.da_json(percorso)
    bound = dict(BOUND_DEFAULT)
    bound.update(dati.get("sensitivita", {}))
    return base, bound


def calcola(parametri):
    """Esegue il modello senza stampare nulla e restituisce (modello, risultati)."""
    with redirect_stdout(io.StringIO()):
        return esegui(parametri)


def valori_da_provare(nome, bound):
    b = bound[nome]
    if nome in ("K1", "K2"):
        return list(range(int(b["lower"]), int(b["upper"]) + 1))          # i buffer sono interi
    return list(np.linspace(b["lower"], b["upper"], int(b.get("punti", 9))))


def riga(parametro, valore, parametri, modello, risultati):
    """Una riga della tabella: cosa si e' variato + parametri + indicatori."""
    r = {"parametro": parametro, "valore": valore}
    r.update(parametri.come_dizionario())
    r["rho"] = parametri.rho
    r["stati"] = modello.numero_stati
    r["passi"] = risultati.passi
    r.update(risultati.indicatori.come_dizionario())
    return r


def sensitivita(base, bound):
    """Varia un parametro alla volta tra lower e upper bound. Restituisce la lista delle righe."""
    righe = []
    for nome in ("lam", "mu", "K1", "K2"):
        for valore in valori_da_provare(nome, bound):
            campi = base.come_dizionario()
            campi[nome] = valore
            parametri = ParametriIngresso(**campi)
            modello, risultati = calcola(parametri)
            righe.append(riga(nome, valore, parametri, modello, risultati))
    return righe


def salva_csv(righe, percorso):
    with Path(percorso).open("w", newline="", encoding="utf-8") as f:
        scrittore = csv.DictWriter(f, fieldnames=list(righe[0].keys()))
        scrittore.writeheader()
        scrittore.writerows(righe)
    return percorso


# ---------------------------------------------------------------- grafici

def quote_macchine(ind):
    """Frazione di tempo di ogni macchina: lavora / vuota (senza pezzi) / bloccata. Le tre sommano a 1."""
    return {
        "M1": {"lavora": ind["p_M1_occupata"], "bloccata": ind["p_bloccata"],
               "vuota": 1 - ind["p_M1_occupata"] - ind["p_bloccata"]},
        "M2": {"lavora": ind["p_M2_occupata"], "bloccata": 0.0,
               "vuota": 1 - ind["p_M2_occupata"]},
    }


def barre_macchine(asse, scenari, titolo):
    """Barre impilate: per ogni scenario due barre (M1, M2) divise in lavora / vuota / bloccata (in %)."""
    larghezza = 0.38
    posizioni = []
    for s, (etichetta, ind) in enumerate(scenari):
        quote = quote_macchine(ind)
        for m, macchina in enumerate(("M1", "M2")):
            x = s * 1.0 + (m - 0.5) * larghezza
            posizioni.append((x, macchina))
            fondo = 0.0
            for parte in ("lavora", "vuota", "bloccata"):
                h = 100 * quote[macchina][parte]
                if h > 0:
                    asse.bar(x, h, larghezza, bottom=fondo, color=COLORE[parte], edgecolor="white", linewidth=1.5)
                    if h >= 6:
                        asse.text(x, fondo + h / 2, f"{h:.0f}%", ha="center", va="center", fontsize=8,
                                  color="white" if parte != "vuota" else "#0b0b0b")
                    fondo = fondo + h
    asse.set_xticks([x for x, _ in posizioni])
    asse.set_xticklabels([m for _, m in posizioni], fontsize=8)
    for s, (etichetta, _) in enumerate(scenari):
        asse.text(s * 1.0, -0.13, etichetta, ha="center", va="top", fontsize=8,
                  transform=asse.get_xaxis_transform(), clip_on=False)
    asse.set_ylim(0, 100)
    asse.set_ylabel("% del tempo")
    asse.set_title(titolo, fontsize=10)
    asse.spines[["top", "right"]].set_visible(False)
    asse.legend(handles=[Patch(color=COLORE[p], label=p) for p in ("lavora", "vuota", "bloccata")],
                loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=8, frameon=False)


def grafico_macchine_base(risultati, percorso):
    fig, asse = plt.subplots(figsize=(4.5, 4))
    p = risultati.parametri
    barre_macchine(asse, [("scenario base", risultati.indicatori.come_dizionario())],
                   f"Stato delle macchine  (λ={p.lam:g}, μ={p.mu:g}, K1={p.K1}, K2={p.K2})")
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return percorso


def grafico_distribuzione_base(risultati, percorso):
    etichette = risultati.etichette_stati
    n = len(etichette)
    fig, asse = plt.subplots(figsize=(max(4.5, 0.35 * n + 2), 3.8))
    colori = [COLORE["bloccata"] if e.startswith("B") else COLORE["lavora"] for e in etichette]
    asse.bar(range(n), risultati.p, color=colori, edgecolor="white", linewidth=1)
    for r in range(n):
        if n <= 30:
            asse.text(r, risultati.p[r], f"{risultati.p[r]:.3f}", ha="center", va="bottom", fontsize=7)
    asse.set_xticks(range(n))
    asse.set_xticklabels(etichette, rotation=90 if n > 12 else 0, fontsize=8)
    asse.set_ylabel("probabilita' stazionaria")
    p = risultati.parametri
    asse.set_title(f"Distribuzione stazionaria  (λ={p.lam:g}, μ={p.mu:g}, K1={p.K1}, K2={p.K2})   "
                   f"blu = stati normali, arancione = M1 bloccata", fontsize=9)
    asse.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return percorso


def grafico_sensitivita(righe, nome, base, percorso):
    """Cinque pannelli: ogni indicatore al variare del parametro `nome` tra lower e upper bound."""
    punti = [r for r in righe if r["parametro"] == nome]
    x = [r["valore"] for r in punti]
    valore_base = base.come_dizionario()[nome]
    fig, assi = plt.subplots(1, len(INDICATORI_GRAFICO), figsize=(3.1 * len(INDICATORI_GRAFICO), 3.2))
    for asse, (campo, titolo, unita) in zip(assi, INDICATORI_GRAFICO):
        y = [r[campo] for r in punti]
        asse.plot(x, y, color=COLORE["linea"], linewidth=2, marker="o", markersize=4)
        asse.axvline(valore_base, color="#898781", linewidth=1, linestyle="--")
        y_base = np.interp(valore_base, x, y)
        asse.plot([valore_base], [y_base], color=COLORE["base"], marker="o", markersize=7, linestyle="none", label="scenario base")
        asse.set_title(titolo, fontsize=9)
        asse.set_xlabel(ETICHETTA[nome], fontsize=8)
        asse.set_ylabel(unita, fontsize=8)
        asse.grid(color="#e1e0d9", linewidth=0.8)
        asse.spines[["top", "right"]].set_visible(False)
        asse.tick_params(labelsize=8)
        if nome in ("K1", "K2"):
            asse.set_xticks(x)
    assi[0].legend(fontsize=8, frameon=False)
    fig.suptitle(f"Sensitivita' a {nome}: gli altri parametri restano al valore base "
                 f"(λ={base.lam:g}, μ={base.mu:g}, K1={base.K1}, K2={base.K2})", fontsize=10)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return percorso


def grafico_macchine_bound(righe, base, percorso):
    """Quattro pannelli (uno per parametro): barre M1/M2 a lower bound, base e upper bound."""
    fig, assi = plt.subplots(1, 4, figsize=(15, 4), sharey=True)
    for asse, nome in zip(assi, ("lam", "mu", "K1", "K2")):
        punti = [r for r in righe if r["parametro"] == nome]
        basso, alto = punti[0], punti[-1]
        base_riga = next(r for r in righe if r["parametro"] == "base")
        scenari = [(f"lower\n{nome}={basso['valore']:g}", basso),
                   (f"base\n{nome}={base_riga[nome]:g}", base_riga),
                   (f"upper\n{nome}={alto['valore']:g}", alto)]
        barre_macchine(asse, scenari, f"al variare di {nome}")
        if asse is not assi[0]:
            asse.set_ylabel("")
            asse.get_legend().remove()
    fig.suptitle("Stato delle macchine ai bound della sensitivita' (% del tempo: lavora / vuota / bloccata)", fontsize=10)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return percorso


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="Analisi di sensitivita' del modello tandem (one-at-a-time)")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="JSON con lo scenario base e i bound")
    parser.add_argument("--output", type=Path, default=CARTELLA_OUTPUT, help="cartella in cui salvare tabella e grafici")
    argomenti = parser.parse_args()

    base, bound = leggi_configurazione(argomenti.input)
    argomenti.output.mkdir(parents=True, exist_ok=True)
    print("Scenario base:", base.come_dizionario())
    print("Bound:", json.dumps(bound))

    # scenario base
    modello, risultati = calcola(base)
    SalvaRisultati(argomenti.output).json(risultati, "scenario_base.json")
    righe = [riga("base", None, base, modello, risultati)]

    # sensitivita' one-at-a-time
    righe.extend(sensitivita(base, bound))
    salva_csv(righe, argomenti.output / "sensitivita.csv")
    print("Esecuzioni:", len(righe), " -> ", argomenti.output / "sensitivita.csv")

    # grafici
    grafico_macchine_base(risultati, argomenti.output / "fig1_macchine_base.png")
    grafico_distribuzione_base(risultati, argomenti.output / "fig2_distribuzione_base.png")
    for nome in ("lam", "mu", "K1", "K2"):
        grafico_sensitivita(righe, nome, base, argomenti.output / f"fig3_sensitivita_{nome}.png")
    grafico_macchine_bound(righe, base, argomenti.output / "fig4_macchine_bounds.png")
    print("Grafici salvati in:", argomenti.output)


if __name__ == "__main__":
    main()
