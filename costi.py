"""
Analisi economica dei buffer: quanti posti conviene mettere davanti a M1 e tra M1 e M2.

Uso:
    python costi.py                        parametri e costi letti da input/parametri.json
    python costi.py --input altro.json     legge un altro file JSON

Per ogni coppia (K1, K2) da 0 a K_max il modello da' il throughput e i pezzi in attesa nei
due buffer; il profitto orario e'

    profitto = ricavo_pezzo * throughput
             - costo_posto_ora * (K1 + K2)
             - costo_attesa_ora * (L_buffer1 + L_buffer2)

e la coppia migliore e' quella col profitto piu' alto. La griglia viene rifatta per ogni rho
della lista (lam = rho * mu, con mu al valore base) per vedere con quali carichi convengono
buffer grandi o piccoli; la sensitivita' ai costi (un costo alla volta, moltiplicato per i
fattori) usa la griglia dello scenario base. Costi, K_max, rho e fattori stanno nella
sezione "costi" del JSON.

Ogni esecuzione salva in una cartella nuova, output/costi/AAAA-MM-GG_HHMMSS/:
    configurazione.json     scenario base, costi, rho e fattori usati
    griglia.csv             una riga per (rho, K1, K2): indicatori, ricavo, costi, profitto
    ottimo_vs_rho.csv       per ogni rho la coppia migliore, il suo profitto e quello senza buffer
    ottimo_vs_costi.csv     per ogni costo e fattore la coppia migliore
    profitto_griglia.png    mappa del profitto su (K1, K2), un pannello per rho, ottimo cerchiato
    ottimo_vs_rho.png       K1*, K2* e profitto al variare di rho
    ottimo_vs_costi.png     K1*, K2* al variare di ciascun costo
"""
import argparse
import csv
import io
import json
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker                      # disegna su file, senza aprire finestre
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from tandem import ParametriIngresso
from main import esegui

CARTELLA_PROGETTO = Path(__file__).resolve().parent
FILE_PARAMETRI = CARTELLA_PROGETTO / "input" / "parametri.json"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output" / "costi"

# i tre costi: (chiave nel JSON, descrizione, unita')
COSTI = [
    ("ricavo_pezzo",     "ricavo per pezzo prodotto",   "€/pezzo"),
    ("costo_posto_ora",  "costo di un posto di buffer", "€/(posto·ora)"),
    ("costo_attesa_ora", "costo di un pezzo in attesa", "€/(pezzo·ora)"),
]
COLORE = {"K1": "#2a78d6", "K2": "#eb6834", "senza": "#898781", "riferimento": "#898781"}
MAPPA_BLU = LinearSegmentedColormap.from_list("blu", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])


# ---------------------------------------------------------------- calcolo

def calcola_griglia(base, lam, K_max):
    """Esegue il modello per ogni (K1, K2) da 0 a K_max, con lam dato e mu al valore base."""
    righe = []
    for K1 in range(K_max + 1):
        for K2 in range(K_max + 1):
            with redirect_stdout(io.StringIO()):
                modello, risultati = esegui(ParametriIngresso(lam=lam, mu=base.mu, K1=K1, K2=K2))
            i = risultati.indicatori
            righe.append({"rho": lam / base.mu, "lam": lam, "mu": base.mu, "K1": K1, "K2": K2,
                          "stati": modello.numero_stati, "throughput": i.throughput,
                          "p_perso": i.p_perso, "p_bloccata": i.p_bloccata, "Ls": i.Ls,
                          "L_buffer1": i.L_buffer1, "L_buffer2": i.L_buffer2})
    return righe


def con_profitto(righe, costi):
    """Aggiunge a ogni riga ricavo, costi e profitto orario. Lavora su copie: la stessa griglia
    si riusa con costi diversi senza rieseguire il modello."""
    risultato = []
    for r in righe:
        r = dict(r)
        r["ricavo"] = costi["ricavo_pezzo"] * r["throughput"]
        r["costo_posti"] = costi["costo_posto_ora"] * (r["K1"] + r["K2"])
        r["costo_attesa"] = costi["costo_attesa_ora"] * (r["L_buffer1"] + r["L_buffer2"])
        r["profitto"] = r["ricavo"] - r["costo_posti"] - r["costo_attesa"]
        risultato.append(r)
    return risultato


def ottimo(righe):
    return max(righe, key=lambda r: r["profitto"])


def senza_buffer(righe):
    return next(r for r in righe if r["K1"] == 0 and r["K2"] == 0)


def scrivi_csv(percorso, righe):
    with percorso.open("w", newline="", encoding="utf-8") as f:
        scrittore = csv.DictWriter(f, fieldnames=list(righe[0].keys()))
        scrittore.writeheader()
        scrittore.writerows(righe)


# ---------------------------------------------------------------- grafici

def stile(asse):
    asse.grid(color="#e1e0d9", linewidth=0.8)
    asse.spines[["top", "right"]].set_visible(False)
    asse.tick_params(labelsize=8)


def grafico_griglia(griglie, K_max, percorso):
    """Un pannello per rho: profitto orario su (K1, K2), piu' scuro = piu' alto; l'ottimo e' cerchiato."""
    n = len(griglie)
    colonne = min(n, 4)
    righe_fig = -(-n // colonne)
    fig, assi = plt.subplots(righe_fig, colonne, figsize=(3.9 * colonne, 3.6 * righe_fig), squeeze=False)
    for asse in assi.flat[n:]:
        asse.set_visible(False)
    for asse, (rho, righe) in zip(assi.flat, griglie):
        M = np.full((K_max + 1, K_max + 1), np.nan)
        for r in righe:
            M[r["K2"], r["K1"]] = r["profitto"]
        immagine = asse.imshow(M, origin="lower", cmap=MAPPA_BLU)
        o = ottimo(righe)
        asse.plot(o["K1"], o["K2"], marker="o", markersize=12, markerfacecolor="none",
                  markeredgecolor=COLORE["K2"], markeredgewidth=2.5)
        asse.set_title(f"ρ = {rho:.3g}  (λ = {righe[0]['lam']:g}, μ = {righe[0]['mu']:g})\n"
                       f"ottimo K1 = {o['K1']}, K2 = {o['K2']}:  {o['profitto']:.1f} €/ora", fontsize=9)
        asse.set_xlabel("K1  (posti davanti a M1)", fontsize=8)
        asse.set_ylabel("K2  (posti tra M1 e M2)", fontsize=8)
        asse.set_xticks(range(0, K_max + 1, 2))
        asse.set_yticks(range(0, K_max + 1, 2))
        asse.tick_params(labelsize=8)
        barra = fig.colorbar(immagine, ax=asse, shrink=0.85)
        barra.ax.tick_params(labelsize=7)
        barra.set_label("€/ora", fontsize=8)
    fig.suptitle("Profitto orario per ogni coppia (K1, K2): piu' scuro = piu' alto, il cerchio e' la coppia migliore",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafico_ottimo_vs_rho(tabella, rho_base, K_max, percorso):
    """Sinistra: K1* e K2* al variare di rho. Destra: profitto orario con i buffer migliori e senza buffer."""
    x = [t["rho"] for t in tabella]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
    a1.plot(x, [t["K1_ottimo"] for t in tabella], color=COLORE["K1"], linewidth=2, marker="o", markersize=5,
            label="K1*  (davanti a M1)")
    a1.plot(x, [t["K2_ottimo"] for t in tabella], color=COLORE["K2"], linewidth=2, marker="o", markersize=5,
            label="K2*  (tra M1 e M2)")
    a1.set_ylabel("posti di buffer", fontsize=8)
    a1.set_title("Coppia migliore (K1*, K2*)", fontsize=10)
    a1.set_ylim(-0.3, K_max + 0.5)
    a1.yaxis.get_major_locator().set_params(integer=True)
    a2.plot(x, [t["profitto_ottimo"] for t in tabella], color=COLORE["K1"], linewidth=2, marker="o", markersize=5,
            label="con i buffer migliori")
    a2.plot(x, [t["profitto_senza_buffer"] for t in tabella], color=COLORE["senza"], linewidth=2, marker="o",
            markersize=5, label="senza buffer (K1 = K2 = 0)")
    a2.set_ylabel("€/ora", fontsize=8)
    a2.set_title("Profitto orario", fontsize=10)
    for asse in (a1, a2):
        asse.axvline(rho_base, color=COLORE["riferimento"], linewidth=1, linestyle="--")
        asse.text(rho_base, 0.98, f" scenario base\n ρ = {rho_base:.3g}", transform=asse.get_xaxis_transform(),
                  fontsize=7, color=COLORE["riferimento"], va="top")
        asse.set_xlabel("ρ = λ/μ  (carico: arrivi rispetto alla capacita' di una macchina)", fontsize=8)
        asse.set_xticks([v for v in x if v != rho_base])       # il base e' gia' segnato dal tratteggio
        asse.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
        asse.legend(fontsize=8, frameon=False)
        stile(asse)
    fig.suptitle("Come cambia la coppia migliore di buffer al variare del carico ρ", fontsize=10)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafico_ottimo_vs_costi(tabella, costi, K_max, percorso):
    """Un pannello per costo: K1* e K2* quando quel costo viene moltiplicato per i fattori (gli altri fermi)."""
    fig, assi = plt.subplots(1, len(COSTI), figsize=(4 * len(COSTI), 3.8), sharey=True)
    for asse, (chiave, descrizione, unita) in zip(assi, COSTI):
        punti = [t for t in tabella if t["costo"] == chiave]
        posizioni = range(len(punti))
        asse.plot(posizioni, [t["K1_ottimo"] for t in punti], color=COLORE["K1"], linewidth=2, marker="o",
                  markersize=5, label="K1*  (davanti a M1)")
        asse.plot(posizioni, [t["K2_ottimo"] for t in punti], color=COLORE["K2"], linewidth=2, marker="o",
                  markersize=5, label="K2*  (tra M1 e M2)")
        asse.set_xticks(list(posizioni))
        asse.set_xticklabels([f"{t['valore']:g}\n(×{t['fattore']:g})" for t in punti], fontsize=8)
        base = next(i for i, t in enumerate(punti) if t["fattore"] == 1)
        asse.axvline(base, color=COLORE["riferimento"], linewidth=1, linestyle="--")
        asse.set_title(descrizione, fontsize=10)
        asse.set_xlabel(unita, fontsize=8)
        stile(asse)
    assi[0].set_ylabel("posti di buffer", fontsize=8)
    assi[0].set_ylim(-0.3, K_max + 0.5)
    assi[0].yaxis.get_major_locator().set_params(integer=True)
    assi[0].legend(fontsize=8, frameon=False)
    fig.suptitle(f"Come cambia la coppia migliore al variare di un costo alla volta "
                 f"(scenario base: ricavo {costi['ricavo_pezzo']:g} €/pezzo, posto {costi['costo_posto_ora']:g} €/ora, "
                 f"attesa {costi['costo_attesa_ora']:g} €/ora; tratteggio = valore base)", fontsize=10)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="Analisi economica dei buffer: profitto orario su (K1, K2)")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="JSON con scenario base e sezione costi")
    argomenti = parser.parse_args()

    base = ParametriIngresso.da_json(argomenti.input)
    dati = json.loads(argomenti.input.read_text(encoding="utf-8"))["costi"]
    costi = {chiave: float(dati[chiave]) for chiave, _, _ in COSTI}
    K_max = int(dati["K_max"])
    fattori = [float(f) for f in dati["fattori"]]
    lista_rho = sorted({float(r) for r in dati["rho"]} | {base.rho})     # il rho dello scenario base c'e' sempre

    cartella = CARTELLA_OUTPUT / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "configurazione.json").write_text(json.dumps(
        {"scenario_base": base.come_dizionario(), "costi": costi, "K_max": K_max, "rho": lista_rho, "fattori": fattori},
        indent=2), encoding="utf-8")

    # 1. griglia (K1, K2) per ogni rho
    griglie = []
    for rho in lista_rho:
        righe = con_profitto(calcola_griglia(base, rho * base.mu, K_max), costi)
        griglie.append((rho, righe))
        o = ottimo(righe)
        avviso = "   ATTENZIONE: l'ottimo tocca K_max, alza K_max nel JSON" if K_max in (o["K1"], o["K2"]) else ""
        print(f"rho = {rho:.3g}:  ottimo K1 = {o['K1']}, K2 = {o['K2']},  profitto {o['profitto']:.2f} €/ora{avviso}")
    scrivi_csv(cartella / "griglia.csv", [r for _, righe in griglie for r in righe])

    # 2. coppia migliore al variare di rho
    tabella_rho = []
    for rho, righe in griglie:
        o, s = ottimo(righe), senza_buffer(righe)
        tabella_rho.append({"rho": rho, "lam": righe[0]["lam"], "K1_ottimo": o["K1"], "K2_ottimo": o["K2"],
                            "profitto_ottimo": o["profitto"], "throughput_ottimo": o["throughput"],
                            "profitto_senza_buffer": s["profitto"], "throughput_senza_buffer": s["throughput"]})
    scrivi_csv(cartella / "ottimo_vs_rho.csv", tabella_rho)

    # 3. sensitivita' ai costi, un costo alla volta, sulla griglia dello scenario base
    griglia_base = next(righe for rho, righe in griglie if rho == base.rho)
    tabella_costi = []
    for chiave, _, _ in COSTI:
        for fattore in fattori:
            c = dict(costi)
            c[chiave] = costi[chiave] * fattore
            o = ottimo(con_profitto(griglia_base, c))
            tabella_costi.append({"costo": chiave, "fattore": fattore, "valore": c[chiave],
                                  "K1_ottimo": o["K1"], "K2_ottimo": o["K2"], "profitto_ottimo": o["profitto"]})
            if K_max in (o["K1"], o["K2"]):
                print(f"{chiave} x{fattore:g}: l'ottimo (K1 = {o['K1']}, K2 = {o['K2']}) tocca K_max")
    scrivi_csv(cartella / "ottimo_vs_costi.csv", tabella_costi)

    grafico_griglia(griglie, K_max, cartella / "profitto_griglia.png")
    grafico_ottimo_vs_rho(tabella_rho, base.rho, K_max, cartella / "ottimo_vs_rho.png")
    grafico_ottimo_vs_costi(tabella_costi, costi, K_max, cartella / "ottimo_vs_costi.png")
    print(len(lista_rho) * (K_max + 1) ** 2, "esecuzioni del modello. Risultati e grafici in:", cartella)


if __name__ == "__main__":
    main()
