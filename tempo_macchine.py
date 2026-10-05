"""
Ripartizione del tempo delle macchine (lavora / vuota / bloccata) su tutta la griglia (K1, K2).

Uso:
    python tempo_macchine.py                        scenario base e sezione "tempo_macchine" da input/parametri.json
    python tempo_macchine.py --input altro.json     legge un altro file JSON

Per ogni coppia (K1, K2) da 0 a K_max il modello viene risolto con lam e mu al valore base: per convergenza
(come in main.py) se K1 + K2 <= 20, con la soluzione diretta di pi*Q = 0 oltre (tandem/diretto.py). Ogni esecuzione salva in una cartella nuova
output/tempo_macchine/AAAA-MM-GG_HHMMSS/:
    configurazione.json                  scenario base e sezione usata
    griglia.csv                          una riga per (K1, K2): frazioni di tempo di M1 e M2 e indicatori
    tempo_macchine_3d.png                superfici su (K1, K2): lavoro (M1 e M2), M1 bloccata, M1 vuota  (tesi, Figura 5.7)
    tempo_macchine_configurazioni.png    colonne impilate per le configurazioni scelte nel JSON         (tesi, Figura 7.1)
    indicatori_3d.png                    superfici 3D di throughput, P(rifiuto), P(M1 bloccata), Ls, Ws  (tesi, Figura 5.8)

M1 e M2 lavorano per la stessa frazione di tempo (conservazione del flusso), per questo il 3D ha un solo
pannello per il lavoro; M2 e' vuota per il tempo restante.
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from tandem import ParametriIngresso
from sensitivita import calcola, COLORE
from tandem.diretto import calcola_diretto

CARTELLA_PROGETTO = Path(__file__).resolve().parent
FILE_PARAMETRI = CARTELLA_PROGETTO / "input" / "parametri.json"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output" / "tempo_macchine"


def frazioni(riga):
    """Frazioni di tempo delle due macchine a partire dagli indicatori di un'esecuzione."""
    return {"M1_lavora": riga["p_M1_occupata"], "M1_bloccata": riga["p_bloccata"],
            "M1_vuota": 1 - riga["p_M1_occupata"] - riga["p_bloccata"],
            "M2_lavora": riga["p_M2_occupata"], "M2_vuota": 1 - riga["p_M2_occupata"]}


def griglia(base, K_max):
    righe = []
    for K1 in range(K_max + 1):
        for K2 in range(K_max + 1):
            par = ParametriIngresso(base.lam, base.mu, K1, K2)
            r = calcola(par) if K1 + K2 <= 20 else calcola_diretto(par)
            r.update(frazioni(r))
            righe.append(r)
    return righe


def grafico_3d(righe, K_max, percorso):
    K = np.arange(K_max + 1)
    K1g, K2g = np.meshgrid(K, K, indexing="ij")
    def matrice(campo):
        Z = np.zeros((K_max + 1, K_max + 1))
        for r in righe:
            Z[r["K1"], r["K2"]] = r[campo]
        return Z
    pannelli = [("M1_lavora", "lavoro (M1 e M2)", COLORE["lavora"]),
                ("M1_bloccata", "M1 bloccata", COLORE["bloccata"]),
                ("M1_vuota", "M1 vuota", COLORE["vuota"])]
    fig = plt.figure(figsize=(14, 5))
    for k, (campo, titolo, colore) in enumerate(pannelli):
        Z = matrice(campo)
        asse = fig.add_subplot(1, 3, k + 1, projection="3d")
        asse.plot_surface(K1g, K2g, Z, color=colore, alpha=0.9, edgecolor="white", linewidth=0.3, shade=False)
        asse.set_xlabel("K1"); asse.set_ylabel("K2")
        asse.set_zlim(0, 1 if k == 0 else max(0.4, float(Z.max()) * 1.1))
        asse.set_title(titolo, fontsize=10)
        asse.view_init(elev=24, azim=-130)
    fig.suptitle("Frazione del tempo al variare di K1 e K2", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafico_indicatori_3d(righe, K_max, percorso):
    """Superfici 3D degli indicatori su (K1, K2), colorate con una scala di colore.
    Sulla superficie di Ws i punti neri indicano, per ogni K1, il K2 con il tempo di permanenza minimo."""
    K = np.arange(K_max + 1)
    K1g, K2g = np.meshgrid(K, K, indexing="ij")
    pannelli = [("throughput", "Throughput [pezzi/ora]"), ("p_perso", "P(rifiuto)"), ("p_bloccata", "P(M1 bloccata)"),
                ("Ls", "WIP Ls [pezzi]"), ("Ws", "Ws [ore]")]
    fig = plt.figure(figsize=(15, 10))
    for k, (campo, titolo) in enumerate(pannelli):
        Z = np.zeros((K_max + 1, K_max + 1))
        for r in righe:
            Z[r["K1"], r["K2"]] = r[campo]
        asse = fig.add_subplot(2, 3, k + 1, projection="3d")
        asse.plot_surface(K1g, K2g, Z, cmap="Blues", edgecolor="white", linewidth=0.3,
                          vmin=Z.min() - 0.25 * (Z.max() - Z.min()), vmax=Z.max())
        if campo == "Ws":
            jmin = Z.argmin(axis=1)
            asse.scatter(K, jmin, Z[K, jmin], color="#0b0b0b", s=12, depthshade=False)
        asse.set_title(titolo, fontsize=10)
        asse.set_xlabel("K1"); asse.set_ylabel("K2")
        asse.view_init(elev=26, azim=-125)
    fig.suptitle("Indicatori di prestazione al variare di K1 e K2", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafico_configurazioni(righe, configurazioni, percorso):
    """Colonne impilate (lavora / vuota / bloccata) di M1 e M2 per le configurazioni (K1, K2) scelte."""
    per_coppia = {(r["K1"], r["K2"]): r for r in righe}
    dati = [per_coppia[tuple(c)] for c in configurazioni]
    x = np.arange(len(dati))
    fig, assi = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for asse, m in zip(assi, ("M1", "M2")):
        fondo = np.zeros(len(dati))
        parti = [("lavora", f"{m}_lavora"), ("vuota", f"{m}_vuota")] + ([("bloccata", "M1_bloccata")] if m == "M1" else [])
        for parte, campo in parti:
            v = np.array([100 * d[campo] for d in dati])
            asse.bar(x, v, bottom=fondo, color=COLORE[parte], width=0.7, edgecolor="white", linewidth=1.2, label=parte)
            for xi, (f0, vi) in enumerate(zip(fondo, v)):
                if vi >= 8:
                    asse.text(xi, f0 + vi / 2, f"{vi:.0f}%", ha="center", va="center", fontsize=8,
                              color="#0b0b0b" if parte == "vuota" else "white")
            fondo = fondo + v
        asse.set_xticks(x)
        asse.set_xticklabels([f"({c[0]}, {c[1]})" for c in configurazioni])
        asse.set_xlabel("(K1, K2)")
        asse.set_ylim(0, 100)
        asse.set_title(m)
        asse.spines[["top", "right"]].set_visible(False)
    assi[0].set_ylabel("% del tempo")
    fig.legend(*assi[0].get_legend_handles_labels(), loc="upper center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Ripartizione del tempo delle macchine sulla griglia (K1, K2)")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="JSON con scenario base e sezione tempo_macchine")
    argomenti = parser.parse_args()

    base = ParametriIngresso.da_json(argomenti.input)
    sezione = json.loads(argomenti.input.read_text(encoding="utf-8"))["tempo_macchine"]
    K_max = int(sezione["K_max"])
    configurazioni = [tuple(c) for c in sezione["configurazioni"]]
    fuori = [c for c in configurazioni if max(c) > K_max]
    if fuori:
        raise SystemExit(f"Configurazioni fuori dalla griglia (K_max = {K_max}): {fuori}")

    cartella = CARTELLA_OUTPUT / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "configurazione.json").write_text(
        json.dumps({"scenario_base": base.come_dizionario(), "tempo_macchine": sezione}, indent=2), encoding="utf-8")

    righe = griglia(base, K_max)
    with (cartella / "griglia.csv").open("w", newline="", encoding="utf-8") as f:
        scrittore = csv.DictWriter(f, fieldnames=list(righe[0].keys()))
        scrittore.writeheader()
        scrittore.writerows(righe)

    grafico_3d(righe, K_max, cartella / "tempo_macchine_3d.png")
    grafico_configurazioni(righe, configurazioni, cartella / "tempo_macchine_configurazioni.png")
    grafico_indicatori_3d(righe, K_max, cartella / "indicatori_3d.png")
    print(len(righe), "esecuzioni del modello. Risultati e grafici in:", cartella)


if __name__ == "__main__":
    main()
