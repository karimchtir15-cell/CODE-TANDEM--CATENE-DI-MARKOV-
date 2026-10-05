"""
Ripartizione dei posti di buffer tra K1 (a monte di M1) e K2 (tra M1 e M2), posti necessari per un
throughput obiettivo, dipendenza dal carico e tempo di permanenza al variare di K2 per piu' valori di K1.

Uso:
    python allocazione.py                        scenario base e sezione "allocazione" da input/parametri.json
    python allocazione.py --input altro.json     legge un altro file JSON

Ogni configurazione e' risolta per convergenza come in main.py (stessa funzione calcola di sensitivita.py).
Ogni esecuzione salva in una cartella nuova output/allocazione/AAAA-MM-GG_HHMMSS/:
    configurazione.json        scenario base e sezione usata
    ripartizioni.csv           tutte le coppie con K1 + K2 = N, per N da 0 a N_max, con lo scarto % dal massimo di N
    migliori_per_N.csv         per ogni N la ripartizione con throughput massimo, N da 0 a N_max_curva
                               (tesi, Tabella 5.6 per N <= N_max e Figura 5.11)
    obiettivi.csv              per ogni throughput obiettivo il minimo N e la ripartizione  (tesi, Tabella 5.7)
    carico.csv                 ripartizione migliore per ogni lam (rho < 1) e ogni N della lista (soluzione diretta)
    W_K2.csv                   tempo di permanenza al variare di K2 per i K1 scelti
    W_K2.png                   W in funzione di K2 per i K1 scelti, con il minimo cerchiato (tesi, Figura 5.9b)
    W_3d.png                   superficie 3D di W su (K1, K2) con i punti calcolati e i minimi (tesi, Figura 5.9a)
    ripartizione_3d.png        (a) throughput 3D su K1 + K2 <= N_max_3d con linee a N costante e ripartizioni
                               migliori; (b) scarto % dal massimo con lo stesso N nel piano (K1, K2) (tesi, Figura 5.10)
    migliori_per_N.png         throughput, P(rifiuto) e W della ripartizione migliore, N da 0 a N_max_curva,
                               con i valori a buffer molto grandi come riferimento         (tesi, Figura 5.11)

Per N da 0 a N_max si confrontano tutte le ripartizioni risolte per convergenza. Per N oltre N_max, fino a
N_max_curva, le ripartizioni si confrontano risolvendo direttamente pi*Q = 0 (stessa funzione di valori_limite.py):
le due soluzioni coincidono (verifica.py), ma con molti stati la convergenza richiederebbe troppo tempo.
    carico.png                 mappa (rho, N): K1 della ripartizione migliore e quota a monte (tesi, Figura 5.12)
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.colors import BoundaryNorm, ListedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registra la proiezione 3d)
import numpy as np

from tandem import ParametriIngresso
from sensitivita import calcola
from valori_limite import risolvi as risolvi_diretto
from tandem.diretto import calcola_diretto

CARTELLA_PROGETTO = Path(__file__).resolve().parent
FILE_PARAMETRI = CARTELLA_PROGETTO / "input" / "parametri.json"
CARTELLA_OUTPUT = CARTELLA_PROGETTO / "output" / "allocazione"
COLORI = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#7b61c9"]

_cache = {}


LIMITE_CONVERGENZA = 20      # fino a K1 + K2 = 20 convergenza, oltre soluzione diretta (stessi valori, vedi verifica.py)


def risolvi(lam, mu, K1, K2):
    """Una configurazione (memorizzata: la stessa coppia serve in piu' analisi). Per convergenza come in main.py
    se K1 + K2 <= LIMITE_CONVERGENZA, altrimenti con la soluzione diretta di pi*Q = 0."""
    chiave = (float(lam), float(mu), int(K1), int(K2))
    if chiave not in _cache:
        par = ParametriIngresso(*chiave)
        _cache[chiave] = calcola(par) if K1 + K2 <= LIMITE_CONVERGENZA else calcola_diretto(par)
    return _cache[chiave]


def ripartizioni(lam, mu, N):
    """Tutte le ripartizioni di N posti: K1 da 0 a N, K2 = N - K1."""
    return [risolvi(lam, mu, K1, N - K1) for K1 in range(N + 1)]


def migliore(righe):
    return max(righe, key=lambda r: r["throughput"])


def scrivi_csv(percorso, righe, campi=None):
    campi = campi or list(righe[0].keys())
    with percorso.open("w", newline="", encoding="utf-8") as f:
        scrittore = csv.DictWriter(f, fieldnames=campi, extrasaction="ignore")
        scrittore.writeheader()
        scrittore.writerows(righe)


def stile(asse):
    asse.grid(color="#e1e0d9", linewidth=0.8)
    asse.spines[["top", "right"]].set_visible(False)


def main():
    parser = argparse.ArgumentParser(description="Ripartizione dei posti di buffer, obiettivi e dipendenza dal carico")
    parser.add_argument("--input", type=Path, default=FILE_PARAMETRI, help="JSON con scenario base e sezione allocazione")
    argomenti = parser.parse_args()

    base = ParametriIngresso.da_json(argomenti.input)
    sezione = json.loads(argomenti.input.read_text(encoding="utf-8"))["allocazione"]
    lam, mu = base.lam, base.mu
    N_max = int(sezione["N_max"])

    cartella = CARTELLA_OUTPUT / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "configurazione.json").write_text(
        json.dumps({"scenario_base": base.come_dizionario(), "allocazione": sezione}, indent=2), encoding="utf-8")

    # 1. ripartizione di N posti, N = 0..N_max
    tutte = {N: ripartizioni(lam, mu, N) for N in range(N_max + 1)}
    migliori = [{"N": N, **migliore(righe)} for N, righe in tutte.items()]
    X_max = {m["N"]: m["throughput"] for m in migliori}
    scrivi_csv(cartella / "ripartizioni.csv",
               [{"N": N, **r, "scarto_dal_massimo_perc": 100 * (1 - r["throughput"] / X_max[N])} for N, righe in tutte.items() for r in righe])
    # estensione della serie dei migliori fino a N_max_curva, con la soluzione diretta
    for m in migliori:
        m["metodo"] = "convergenza"
    for N in range(N_max + 1, int(sezione.get("N_max_curva", N_max)) + 1):
        m = max((risolvi_diretto(lam, mu, K1, N - K1) for K1 in range(N + 1)), key=lambda r: r["throughput"])
        migliori.append({"N": N, **m, "metodo": "diretta"})
    scrivi_csv(cartella / "migliori_per_N.csv", migliori,
               ["N", "K1", "K2", "metodo", "throughput", "p_perso", "p_bloccata", "Ls", "Ws"])

    # 2. posti minimi per un throughput obiettivo (ricavati dalla serie precedente)
    obiettivi = []
    for X_obj in sezione["obiettivi"]:
        trovato = next((m for m in migliori if m["throughput"] >= X_obj), None)
        if trovato is None:
            obiettivi.append({"throughput_obiettivo": X_obj, "N": f"oltre {migliori[-1]['N']}"})
        else:
            obiettivi.append({"throughput_obiettivo": X_obj, "N": trovato["N"], "K1": trovato["K1"], "K2": trovato["K2"],
                              "throughput": trovato["throughput"], "p_perso": trovato["p_perso"], "Ws": trovato["Ws"]})
    scrivi_csv(cartella / "obiettivi.csv", obiettivi,
               ["throughput_obiettivo", "N", "K1", "K2", "throughput", "p_perso", "Ws"])

    # 3. dipendenza dal carico: lam variabile (rho < 1), mu al valore base, ogni N della lista.
    #    Sono migliaia di configurazioni: si confrontano con la soluzione diretta di pi*Q = 0, come per N > N_max.
    carico = []
    for N in sezione["carico"]["N"]:
        for lam_c in sezione["carico"]["lam"]:
            m = migliore([risolvi_diretto(lam_c, mu, K1, N - K1) for K1 in range(N + 1)])
            carico.append({"N": N, "lam": lam_c, "rho": lam_c / mu, "K1": m["K1"], "K2": m["K2"],
                           "quota_monte": m["K1"] / N, "throughput": m["throughput"], "p_perso": m["p_perso"],
                           "p_bloccata": m["p_bloccata"], "Ws": m["Ws"]})
    scrivi_csv(cartella / "carico.csv", carico)

    # 4. tempo di permanenza al variare di K2 per alcuni K1
    W_K2 = [{"K1": K1, "K2": K2, "Ws": risolvi(lam, mu, K1, K2)["Ws"]}
            for K1 in sezione["W_K1"] for K2 in range(int(sezione["W_K2_max"]) + 1)]
    scrivi_csv(cartella / "W_K2.csv", W_K2)
    K3 = int(sezione.get("W_3d_K_max", 10))
    Z = np.array([[risolvi(lam, mu, K1, K2)["Ws"] for K2 in range(K3 + 1)] for K1 in range(K3 + 1)])

    # ---- grafici
    fig, asse = plt.subplots(figsize=(9, 4.8))
    for colore, K1 in zip(COLORI, sezione["W_K1"]):
        punti = [r for r in W_K2 if r["K1"] == K1]
        x = [r["K2"] for r in punti]; y = [r["Ws"] for r in punti]
        asse.plot(x, y, color=colore, marker="o", markersize=3.5, linewidth=1.8, label=f"K1 = {K1}")
        i = int(np.argmin(y))
        asse.plot(x[i], y[i], "o", markersize=9, markerfacecolor="none", markeredgecolor="#0b0b0b")
    asse.set_xlabel("K2"); asse.set_ylabel("Ws [ore]")
    asse.set_title(f"Tempo di permanenza al variare di K2 (λ={lam:g}, μ={mu:g}); cerchio = minimo di ogni curva", fontsize=10)
    asse.legend(frameon=False, ncol=len(sezione["W_K1"])); stile(asse)
    fig.tight_layout(); fig.savefig(cartella / "W_K2.png", dpi=150); plt.close(fig)

    # superficie 3D di W: il reticolo dei punti calcolati, con gli spazi colorati
    K = np.arange(K3 + 1)
    K1g, K2g = np.meshgrid(K, K, indexing="ij")
    jmin = Z.argmin(axis=1)
    fig = plt.figure(figsize=(9, 6.5))
    asse = fig.add_subplot(projection="3d")
    sup = asse.plot_surface(K1g, K2g, Z, cmap="viridis", edgecolor=(1, 1, 1, 0.55), linewidth=0.3)
    asse.scatter(K1g.ravel(), K2g.ravel(), Z.ravel(), color="#0b0b0b", s=4, depthshade=False)
    asse.scatter(K, jmin, Z[K, jmin], s=40, facecolor="white", edgecolor="#0b0b0b", depthshade=False)
    asse.set_xlabel("K1"); asse.set_ylabel("K2"); asse.set_zlabel("Ws [ore]")
    asse.view_init(elev=24, azim=-122)
    fig.colorbar(sup, ax=asse, shrink=0.6, pad=0.08, label="Ws [ore]")
    asse.set_title(f"Tempo di permanenza su (K1, K2) (λ={lam:g}, μ={mu:g}); cerchi bianchi = minimo per ogni K1", fontsize=10)
    fig.tight_layout(); fig.savefig(cartella / "W_3d.png", dpi=150); plt.close(fig)

    # ripartizione di N posti: (a) superficie 3D del throughput su tutte le coppie con K1 + K2 <= N_max,
    # (b) scarto percentuale dal massimo con lo stesso N, nel piano (K1, K2)
    N_3d = int(sezione.get("N_max_3d", N_max))
    tutte_3d = {N: (tutte[N] if N <= N_max else ripartizioni(lam, mu, N)) for N in range(N_3d + 1)}
    X_max_3d = {N: migliore(r)["throughput"] for N, r in tutte_3d.items()}
    cresta = [{"N": N, **migliore(r)} for N, r in tutte_3d.items()]
    punti = [r for N in range(N_3d + 1) for r in tutte_3d[N]]
    K1p = np.array([r["K1"] for r in punti], float); K2p = np.array([r["K2"] for r in punti], float)
    Xp = np.array([r["throughput"] for r in punti])
    scarto = np.array([100 * (1 - r["throughput"] / X_max_3d[r["K1"] + r["K2"]]) for r in punti])
    fig = plt.figure(figsize=(9, 11))
    asse = fig.add_axes([0.0, 0.44, 0.92, 0.52], projection="3d"); asse.computed_zorder = False
    sup = asse.plot_trisurf(mtri.Triangulation(K1p, K2p), Xp, cmap="viridis", edgecolor=(1, 1, 1, 0.25), linewidth=0.2, zorder=1)
    for N in range(4, N_3d + 1, 4):                                   # linee a N costante
        asse.plot([r["K1"] for r in tutte_3d[N]], [r["K2"] for r in tutte_3d[N]], [r["throughput"] + 0.03 for r in tutte_3d[N]],
                  color="white", linewidth=0.8, zorder=2)
    xb, yb, zb = [m["K1"] for m in cresta], [m["K2"] for m in cresta], [m["throughput"] + 0.05 for m in cresta]
    asse.plot(xb, yb, zb, color="#eb6834", linewidth=1.6, zorder=3)
    asse.scatter(xb, yb, zb, s=20, color="#eb6834", edgecolor="white", depthshade=False, zorder=4)
    asse.set_xlabel("K1"); asse.set_ylabel("K2"); asse.set_zlabel("throughput [pezzi/ora]")
    asse.view_init(elev=26, azim=-128)
    fig.colorbar(sup, ax=asse, shrink=0.55, pad=0.06, label="throughput [pezzi/ora]")
    asse.set_xticks(range(0, N_3d + 1, 8)); asse.set_yticks(range(0, N_3d + 1, 8))
    fig.text(0.5, 0.99, f"(a) Throughput su K1 + K2 <= {N_3d} (λ={lam:g}, μ={mu:g})\n"
                   "linee bianche = N costante, punti arancioni = ripartizione migliore", fontsize=10, ha="center", va="top")
    asse2 = fig.add_axes([0.08, 0.05, 0.72, 0.34])
    classi = [0, 1, 2, 5, 10, 20, max(50, float(np.ceil(scarto.max())))]
    cmap = ListedColormap(plt.get_cmap("Blues_r")(np.linspace(0.05, 0.9, len(classi) - 1)))
    norma = BoundaryNorm(classi, cmap.N)
    for k1, k2, sc in zip(K1p, K2p, scarto):
        asse2.add_patch(plt.Rectangle((k1 - 0.5, k2 - 0.5), 1, 1, facecolor=cmap(norma(min(sc, classi[-1] - 0.1))),
                                      edgecolor="white", linewidth=0.3))
    asse2.plot(xb, yb, color="#eb6834", linewidth=1.2)
    asse2.scatter(xb, yb, s=8, color="#eb6834", edgecolor="white", linewidth=0.4, zorder=3)
    asse2.set_xlim(-0.5, N_3d + 0.5); asse2.set_ylim(-0.5, N_3d + 0.5); asse2.set_aspect("equal")
    asse2.set_xticks(range(0, N_3d + 1, 4)); asse2.set_yticks(range(0, N_3d + 1, 4))
    asse2.set_xlabel("K1"); asse2.set_ylabel("K2")
    asse2.set_title("(b) Throughput inferiore al massimo con lo stesso N = K1 + K2 (ogni diagonale e' un N)", fontsize=10)
    fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norma), ax=asse2, fraction=0.05, pad=0.03, ticks=classi,
                 label="scarto dal massimo [%]")
    fig.savefig(cartella / "ripartizione_3d.png", dpi=150); plt.close(fig)

    # riferimento: indici con entrambi i buffer molto grandi (K1 = K2 = massimo di "K_entrambi" in valori_limite)
    K_rif = max(json.loads(argomenti.input.read_text(encoding="utf-8"))["valori_limite"]["K_entrambi"])
    rif = risolvi_diretto(lam, mu, K_rif, K_rif)
    fig, assi = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    Ns = [m["N"] for m in migliori]
    for asse, (campo, titolo) in zip(assi, [("throughput", "Throughput [pezzi/ora]"), ("p_perso", "P(rifiuto)"), ("Ws", "Ws [ore]")]):
        asse.axhline(rif[campo], color="#898781", linewidth=1, linestyle="--", label=f"valore con K1 = K2 = {K_rif}")
        asse.plot(Ns, [m[campo] for m in migliori], color=COLORI[0], marker="o", markersize=3.5, linewidth=1.8)
        asse.set_title(titolo, fontsize=10, loc="left"); stile(asse)
    assi[0].legend(frameon=False, loc="lower right")
    assi[-1].set_xlabel(f"N posti totali, ripartiti al meglio (fino a N = {N_max} convergenza, oltre soluzione diretta)")
    fig.tight_layout(); fig.savefig(cartella / "migliori_per_N.png", dpi=150); plt.close(fig)

    # dipendenza dal carico: una casella per (rho, N), colore = quota dei posti a monte, numero = K1
    lams_c = sorted(set(sezione["carico"]["lam"])); Ns_c = sorted(set(sezione["carico"]["N"]))
    trova = {(r["lam"], r["N"]): r for r in carico}
    Q = np.array([[trova[(l, N)]["quota_monte"] for l in lams_c] for N in Ns_c])
    fig, asse = plt.subplots(figsize=(10, 8))
    im = asse.imshow(Q, origin="lower", cmap="Blues", vmin=0.4, vmax=1.0, aspect="auto")
    for a, N in enumerate(Ns_c):
        for b, l in enumerate(lams_c):
            asse.text(b, a, str(trova[(l, N)]["K1"]), ha="center", va="center", fontsize=7,
                      color="white" if Q[a, b] > 0.72 else "#0b0b0b")
    asse.set_xticks(range(len(lams_c))); asse.set_xticklabels([f"{l / mu:.2f}" for l in lams_c], rotation=90)
    asse.set_yticks(range(len(Ns_c))); asse.set_yticklabels(Ns_c)
    asse.set_xlabel(f"ρ = λ/μ (μ = {mu:g})"); asse.set_ylabel("N posti totali")
    asse.set_title("Ripartizione con throughput massimo: numero = K1 (K2 = N - K1), colore = quota a monte", fontsize=10)
    fig.colorbar(im, ax=asse, label="quota dei posti a monte di M1")
    fig.tight_layout(); fig.savefig(cartella / "carico.png", dpi=150); plt.close(fig)

    print(len(_cache), "configurazioni risolte. Risultati e grafici in:", cartella)
    for o in obiettivi:
        print("  throughput >=", o["throughput_obiettivo"], "->", o["N"], "posti", (o.get("K1"), o.get("K2")))


if __name__ == "__main__":
    main()
