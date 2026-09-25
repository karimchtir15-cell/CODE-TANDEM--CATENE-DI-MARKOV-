"""
Analisi di sensitivita' del modello tandem e grafici.

Uso:
    python sensitivita.py                        scenario base e bound letti da input/parametri.json
    python sensitivita.py --input altro.json     legge un altro file JSON

Ogni parametro (lam, mu, K1, K2) viene fatto variare da solo tra il lower e l'upper bound
della sezione "sensitivita" del JSON, tenendo gli altri tre al valore base (one-at-a-time).

Ogni esecuzione salva in una cartella nuova, output/sensitivita/AAAA-MM-GG_HHMMSS/,
cosi' i risultati precedenti non vengono sovrascritti:
    configurazione.json        scenario base e bound usati (per poter rifare l'esecuzione)
    sensitivita.csv            una riga per esecuzione del modello: parametro variato, valore, indicatori
    sensitivita_<par>.png      gli indicatori al variare di un parametro tra i bound
    macchine_ai_bound.png      M1 e M2 a lower bound / base / upper bound: % del tempo lavora / vuota / bloccata
"""
import argparse
import csv
import io
import json
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # disegna su file, senza aprire finestre
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

from tandem import ParametriIngresso
from main import esegui

CARTELLA_PROGETTO = Path(__file__).resolve().parent
FILE_PARAMETRI = CARTELLA_PROGETTO / "input" / "parametri.json"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output" / "sensitivita"

PARAMETRI = ("lam", "mu", "K1", "K2")
SIMBOLO = {"lam": "λ", "mu": "μ", "K1": "K1", "K2": "K2"}
DESCRIZIONE = {"lam": "pezzi/ora che arrivano", "mu": "pezzi/ora lavorati da ogni macchina",
               "K1": "posti di buffer davanti a M1", "K2": "posti di buffer tra M1 e M2"}

# indicatori nei grafici di sensitivita': (campo di Indicatori, titolo, unita')
INDICATORI_GRAFICO = [
    ("throughput", "Throughput", "pezzi/ora"),
    ("p_perso",    "P(arrivo rifiutato)", ""),
    ("p_bloccata", "P(M1 bloccata)", ""),
    ("Ls",         "WIP  (pezzi nel sistema)", "pezzi"),
    ("Ws",         "Ws  (tempo nel sistema)", "ore"),
]

COLORE = {"lavora": "#2a78d6", "vuota": "#c3c2b7", "bloccata": "#eb6834"}


# ---------------------------------------------------------------- calcolo

def calcola(parametri):
    """Esegue il modello senza stampare e restituisce una riga con parametri e indicatori."""
    with redirect_stdout(io.StringIO()):
        modello, risultati = esegui(parametri)
    riga = parametri.come_dizionario()
    riga.update(rho=parametri.rho, stati=modello.numero_stati, passi=risultati.passi)
    riga.update(risultati.indicatori.come_dizionario())
    return riga


def valori_da_provare(nome, bound):
    b = bound[nome]
    if nome in ("K1", "K2"):
        return list(range(int(b["lower"]), int(b["upper"]) + 1))     # i buffer sono interi
    return list(np.linspace(b["lower"], b["upper"], int(b["punti"])))


def sensitivita(base, bound):
    """Scenario base + un parametro alla volta tra i bound. Restituisce la lista delle righe."""
    righe = [{"parametro": "base", "valore": None, **calcola(base)}]
    for nome in PARAMETRI:
        for valore in valori_da_provare(nome, bound):
            campi = base.come_dizionario()
            campi[nome] = valore
            righe.append({"parametro": nome, "valore": valore, **calcola(ParametriIngresso(**campi))})
    return righe


# ---------------------------------------------------------------- grafici

def barre_macchine(asse, scenari, titolo):
    """Per ogni scenario due barre (M1, M2) divise in % del tempo: lavora / vuota / bloccata."""
    larghezza = 0.38
    posizioni = []
    for s, (etichetta, r) in enumerate(scenari):
        quote = {"M1": {"lavora": r["p_M1_occupata"], "bloccata": r["p_bloccata"],
                        "vuota": 1 - r["p_M1_occupata"] - r["p_bloccata"]},
                 "M2": {"lavora": r["p_M2_occupata"], "bloccata": 0.0, "vuota": 1 - r["p_M2_occupata"]}}
        for m, macchina in enumerate(("M1", "M2")):
            x = s + (m - 0.5) * larghezza
            posizioni.append((x, macchina))
            fondo = 0.0
            for parte in ("lavora", "vuota", "bloccata"):
                h = 100 * quote[macchina][parte]
                if h > 0:
                    asse.bar(x, h, larghezza, bottom=fondo, color=COLORE[parte], edgecolor="white", linewidth=1.5)
                    if h >= 6:
                        asse.text(x, fondo + h / 2, f"{h:.0f}%", ha="center", va="center", fontsize=8,
                                  color="#0b0b0b" if parte == "vuota" else "white")
                    fondo = fondo + h
        asse.text(s, -0.13, etichetta, ha="center", va="top", fontsize=8, transform=asse.get_xaxis_transform())
    asse.set_xticks([x for x, _ in posizioni])
    asse.set_xticklabels([m for _, m in posizioni], fontsize=8)
    asse.set_ylim(0, 100)
    asse.set_title(titolo, fontsize=10)
    asse.spines[["top", "right"]].set_visible(False)


def grafico_sensitivita(righe, nome, percorso):
    """Un pannello per indicatore: il suo valore al variare di `nome` tra lower e upper bound."""
    base = righe[0]
    punti = [r for r in righe if r["parametro"] == nome]
    x = [r["valore"] for r in punti]
    fig, assi = plt.subplots(1, len(INDICATORI_GRAFICO), figsize=(3.1 * len(INDICATORI_GRAFICO), 3.2))
    for asse, (campo, titolo, unita) in zip(assi, INDICATORI_GRAFICO):
        asse.plot(x, [r[campo] for r in punti], color=COLORE["lavora"], linewidth=2, marker="o", markersize=4)
        asse.axvline(base[nome], color="#898781", linewidth=1, linestyle="--")
        asse.plot([base[nome]], [base[campo]], color=COLORE["bloccata"], marker="o", markersize=7,
                  linestyle="none", label="scenario base")
        asse.set_title(titolo, fontsize=9)
        asse.set_xlabel(f"{SIMBOLO[nome]}  ({DESCRIZIONE[nome]})", fontsize=8)
        asse.set_ylabel(unita, fontsize=8)
        asse.grid(color="#e1e0d9", linewidth=0.8)
        asse.spines[["top", "right"]].set_visible(False)
        asse.tick_params(labelsize=8)
        if nome in ("K1", "K2"):
            asse.set_xticks(x)
    fig.suptitle(f"Sensitivita' a {SIMBOLO[nome]}: gli altri parametri restano al valore base "
                 f"(λ={base['lam']:g}, μ={base['mu']:g}, K1={base['K1']}, K2={base['K2']})", fontsize=10)
    # legenda sotto il titolo, fuori dai pannelli: dentro un pannello sembrava un punto del grafico
    fig.legend(*assi[0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, 0.93),
               fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


def punto_centrale(punti, base, nome):
    """Punto da mostrare come riferimento centrale tra lower e upper bound.

    Di norma e' lo scenario base. Ma se il base di questo parametro coincide col
    lower bound (es. K1=K2=0 nello scenario base), usarlo duplicherebbe la barra
    del lower bound: si sceglie invece, tra i punti intermedi, quello dove la
    probabilita' di blocco ha gia' coperto meta' della variazione totale tra i
    due bound, cosi' il pannello mostra un cambiamento vero e non un doppione.
    """
    if base[nome] != punti[0]["valore"] or len(punti) <= 2:
        return f"base\n{SIMBOLO[nome]}={base[nome]:g}", base
    obiettivo = (punti[0]["p_bloccata"] + punti[-1]["p_bloccata"]) / 2
    centro = min(punti[1:-1], key=lambda r: abs(r["p_bloccata"] - obiettivo))
    return f"{SIMBOLO[nome]}={centro['valore']:g}\n(punto intermedio)", centro


def grafico_macchine_ai_bound(righe, percorso):
    """Un pannello per parametro: barre M1/M2 a lower bound, un riferimento centrale e upper bound."""
    base = righe[0]
    fig, assi = plt.subplots(1, len(PARAMETRI), figsize=(15, 4), sharey=True)
    for asse, nome in zip(assi, PARAMETRI):
        punti = [r for r in righe if r["parametro"] == nome]
        s = SIMBOLO[nome]
        etichetta_centro, centro = punto_centrale(punti, base, nome)
        scenari = [(f"lower bound\n{s}={punti[0]['valore']:g}", punti[0]),
                   (etichetta_centro, centro),
                   (f"upper bound\n{s}={punti[-1]['valore']:g}", punti[-1])]
        barre_macchine(asse, scenari, f"al variare di {s}")
    assi[0].set_ylabel("% del tempo")
    assi[0].legend(handles=[Patch(color=COLORE[p], label=p) for p in ("lavora", "vuota", "bloccata")],
                   loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, fontsize=8, frameon=False)
    fig.suptitle("Stato delle macchine ai bound della sensitivita' (% del tempo: lavora / vuota / bloccata)", fontsize=10)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="Analisi di sensitivita' del modello tandem (one-at-a-time)")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="JSON con scenario base e sezione sensitivita")
    argomenti = parser.parse_args()

    base = ParametriIngresso.da_json(argomenti.input)
    bound = json.loads(argomenti.input.read_text(encoding="utf-8"))["sensitivita"]

    cartella = CARTELLA_OUTPUT / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "configurazione.json").write_text(
        json.dumps({"scenario_base": base.come_dizionario(), "sensitivita": bound}, indent=2), encoding="utf-8")

    righe = sensitivita(base, bound)
    with (cartella / "sensitivita.csv").open("w", newline="", encoding="utf-8") as f:
        scrittore = csv.DictWriter(f, fieldnames=list(righe[0].keys()))
        scrittore.writeheader()
        scrittore.writerows(righe)

    for nome in PARAMETRI:
        grafico_sensitivita(righe, nome, cartella / f"sensitivita_{nome}.png")
    grafico_macchine_ai_bound(righe, cartella / "macchine_ai_bound.png")
    print(len(righe), "esecuzioni del modello. Risultati e grafici in:", cartella)


if __name__ == "__main__":
    main()
