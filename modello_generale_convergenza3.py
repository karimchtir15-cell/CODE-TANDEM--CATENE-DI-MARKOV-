import numpy as np

# ---- dati di ingresso ----
lam = 10.0    # tasso di arrivo NOMINALE (pezzi/ora che si presentano all'ingresso)
mu = 12.0     # tasso di servizio (uguale per M1 e M2)
K1 = 0        # capacita' del buffer davanti a M1   (0 = nessun buffer)
K2 = 0        # capacita' del buffer tra M1 e M2    (0 = nessun buffer)
# La distribuzione stazionaria si ottiene "facendo convergere" la matrice P(h) = I + Q*h: si parte da una
# distribuzione iniziale e si moltiplica per P(h) un passo alla volta finche' non cambia piu'.
# Il passo h lo sceglie il codice: il piu' grande possibile, h = 1/max|Q[r][r]|, cosi' servono meno passi.


# ============================================================
# 1. LISTA DEGLI STATI
# ============================================================
# Ogni stato e' una terna (tipo, i, j):
#   ("N", i, j)     stato NORMALE: i = pezzi sul lato M1 (coda + pezzo in macchina), 0..K1+1
#                                  j = pezzi sul lato M2 (buffer + pezzo in macchina), 0..K2+1
#   ("B", i, K2+1)  stato BLOCCATO: M1 ha finito un pezzo ma il lato M2 e' saturo e non puo' passarlo.
#                                  i = pezzo bloccato in M1 + coda, 1..K1+1; il lato M2 vale sempre K2+1

stati = []
for i in range(0, K1 + 2):                 # primo ciclo: tutti gli stati normali -> (K1+2)(K2+2) stati
    for j in range(0, K2 + 2):
        stati.append(("N", i, j))
for i in range(1, K1 + 2):                 # secondo ciclo: gli stati bloccati -> K1+1 stati
    stati.append(("B", i, K2 + 1))
numero_stati = len(stati)


# ============================================================
# 2. MATRICE GENERATRICE Q E TABELLA CON LE LETTERE
# ============================================================
# Q[r][c] = tasso con cui si passa dallo stato r (riga) allo stato c (colonna).
# Gli arrivi si presentano sempre con tasso lam: se il lato M1 e' pieno la transizione non esiste
# (il pezzo e' rifiutato e il sistema resta dov'e'): i rifiuti restano "dentro" la diagonale.
# L e' la stessa tabella scritta con le lettere (λh, μh, 1-λh-μh, ...), per il confronto con la versione a mano.

Q = np.zeros((numero_stati, numero_stati))
L = [["" for c in range(numero_stati)] for r in range(numero_stati)]

def aggiungi(r, arrivo, tasso, lettera):
    # scrive UNA transizione: dallo stato in riga r allo stato "arrivo", con il tasso dato
    c = stati.index(arrivo)                  # colonna dello stato di arrivo
    Q[r][c] = Q[r][c] + tasso                # il numero nella matrice dei tassi
    L[r][c] = L[r][c] + lettera              # la lettera nella casella
    L[r][r] = L[r][r] + "-" + lettera        # ogni uscita toglie il suo pezzo alla probabilita' di restare

# Le regole di transizione: una riga per ogni riga della tabella delle transizioni.
for r in range(numero_stati):
    tipo, i, j = stati[r]
    if tipo == "N":
        if i < K1 + 1:              aggiungi(r, ("N", i + 1, j),      lam, "λh")   # arrivo: c'e' posto sul lato M1
        if i >= 1 and j < K2 + 1:   aggiungi(r, ("N", i - 1, j + 1),  mu,  "μh")   # M1 finisce e il pezzo passa al lato M2
        if i >= 1 and j == K2 + 1:  aggiungi(r, ("B", i, K2 + 1),     mu,  "μh")   # M1 finisce ma il lato M2 e' saturo: si blocca
        if j >= 1:                  aggiungi(r, ("N", i, j - 1),      mu,  "μh")   # M2 finisce: il pezzo esce dal sistema
    else:
        if i < K1 + 1:              aggiungi(r, ("B", i + 1, K2 + 1), lam, "λh")   # arrivo: si mette in coda dietro al blocco
        aggiungi(r, ("N", i - 1, K2 + 1), mu, "μh")                                # M2 finisce: il pezzo bloccato passa, M1 riparte

for r in range(numero_stati):
    Q[r][r] = -sum(Q[r])                     # diagonale di Q: ogni riga somma a zero
    L[r][r] = "1" + L[r][r]                  # diagonale con le lettere: 1 meno tutte le uscite

# P(h) = I + Q*h e' la matrice che verra' fatta convergere. 1/max|Q[r][r]| e' il passo piu' grande per cui
# ogni riga di P(h) resta una probabilita'; ne prendo un decimo, cosi' h e' "piccolo" (termini in h^2 trascurabili)
h = 0.1 / max(-Q[r][r] for r in range(numero_stati))
P_h = np.eye(numero_stati) + Q * h #È la formula che collega i due modi di descrivere lo stesso sistema: i tassi (tempo continuo) e le probabilità (tempo discreto)


# ---- stampa delle due tabelle ---- #un modo per dare a ogni casella la stessa larghezza: rjust(11) e ljust(11)
def etichetta(s):
    return s[0] + "(" + str(s[1]) + "," + str(s[2]) + ")"

def stampa_tabella(T, titolo):
    print()
    print(titolo)
    print("".ljust(11), end="")
    for c in range(numero_stati):
        print(etichetta(stati[c]).rjust(11), end="")
    print()
    for r in range(numero_stati): 
        print(etichetta(stati[r]).ljust(11), end="") #bordi tabellaa
        for c in range(numero_stati):
            print(str(T[r][c]).rjust(11), end="")
        print()

print("Numero di stati:", numero_stati, "  [(K1+2)(K2+2)+(K1+1)]", "   passo h = 0.1/max|Q[r][r]| =", round(h, 6), "ore")
if numero_stati <= 40: #Con più di 40 stati la tabella sarebbe larga più di 440 caratteri e illeggibile a video, quindi si salta tutto.
    stampa_tabella(L, "=== TABELLA DEGLI STATI con le lettere (probabilita' di passare da riga a colonna in un intervallo h) ===")
    V = [["" if (r != c and P_h[r][c] == 0) else round(P_h[r][c], 4) #lasciamo 0?
          for c in range(numero_stati)] 
          for r in range(numero_stati)]
    stampa_tabella(V, "=== MATRICE P(h) = I + Q*h che viene fatta convergere (lam = " + str(lam) + ", mu = " + str(mu) + ") ===")


# ============================================================
# 3. CONTROLLI SULLA MATRICE (prima di convergere)
# ============================================================
toll = 1e-9

def controllo(descrizione, superato, valore):
    print("OK     " if superato else "ERRORE ", descrizione.ljust(60), valore)
    return superato

# quali stati si raggiungono partendo da uno stato, seguendo le transizioni in avanti o all'indietro
def raggiungibili(partenza, all_indietro): #riga per riga 
    trovati = [partenza]
    for r in trovati:                        # la lista si allunga mentre la scorro
        for c in range(numero_stati): #per ogni r vedo i singoli c
            tasso = Q[c][r] if all_indietro else Q[r][c]
            if c != r and tasso > 0 and c not in trovati: #terza condizione: la "stanza" non devo averla gia' trovata, altrimenti entrerei in un ciclo infinito
                trovati.append(c)
    return len(trovati)

print()
print("=== CONTROLLI SULLA MATRICE ===")
# 1) P(h) e' una matrice di probabilita': righe a somma 1 (equivale a righe di Q a somma 0) ed elementi in [0,1]
ok1 = controllo("1. P(h) e' una matrice di probabilita' (righe a 1, elementi in [0,1])",
                max(abs(sum(P_h[r]) - 1) for r in range(numero_stati)) < toll and P_h.min() >= -toll and P_h.max() <= 1 + toll,
                "min = " + str(round(float(P_h.min()), 4)) + ", max = " + str(round(float(P_h.max()), 4)))
# 2) catena irriducibile: da N(0,0) si raggiunge ogni stato e da ogni stato si torna a N(0,0)
#    (ipotesi del teorema che garantisce una sola distribuzione stazionaria)
vuoto = stati.index(("N", 0, 0))
ok2 = controllo("2. catena irriducibile (tutti gli stati comunicano)",
                raggiungibili(vuoto, False) == numero_stati and raggiungibili(vuoto, True) == numero_stati,
                "raggiunti " + str(raggiungibili(vuoto, False)) + " e " + str(raggiungibili(vuoto, True)) + " su " + str(numero_stati))
if not (ok1 and ok2):
    raise SystemExit("La matrice non supera i controlli: correggere le regole di transizione prima di procedere.")


# ============================================================
# 4. DISTRIBUZIONE STAZIONARIA PER CONVERGENZA:  p(n) = p(n-1) * P(h)
# ============================================================
def converge(p_iniziale, tolleranza=1e-13, passi_massimi=1000000):
    p_n = p_iniziale.copy()
    n = 0
    while True:
        p_prec = p_n
        p_n = p_n @ P_h                      # un passo di durata h, chiocciola vettore x matrice
        n = n + 1
        if max(abs(p_n - p_prec)) / h < tolleranza or n >= passi_massimi:   # variazione per unita' di tempo, se supero passi massimi esco comunque
            return p_n, n

p0 = np.zeros(numero_stati)
p0[vuoto] = 1.0                              # p(0): all'inizio il sistema e' vuoto con certezza
p, passi = converge(p0)

print()
print("=== PROBABILITA' STAZIONARIE (rho =", round(lam / mu, 4), ")   raggiunte dopo", passi, "passi, tempo simulato", round(passi * h, 2), "ore ===")
for r in range(numero_stati):
    print(etichetta(stati[r]).ljust(9), " p =", round(p[r], 4))


# ============================================================
# 5. INDICATORI DI PRESTAZIONE
# ============================================================
# Ogni indicatore e' una somma sugli stati che soddisfano una condizione, pesata con p.
p_bloccata = p_vuoto = p_perso = p_M1_occupata = p_M2_occupata = Ls = 0.0

for r in range(numero_stati):
    tipo, i, j = stati[r]
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

print()
print("=== INDICATORI ===")
print("P(M1 bloccata)      =", round(p_bloccata, 4))
print("P(sistema vuoto)    =", round(p_vuoto, 4))
print("P(arrivo rifiutato) =", round(p_perso, 4), "   -> su", lam, "pezzi/ora che si presentano ne vengono rifiutati", round(lam - lam_eff, 4))
print("Throughput          =", round(throughput, 4), "pezzi/ora  (= lambda effettivo, cio' che entra e' cio' che esce)")
print("Ls (= WIP)          =", round(Ls, 4), "pezzi     (numero medio di pezzi nel sistema)")
print("Ws                  =", round(Ws, 4), "ore =", round(Ws * 60, 2), "minuti   (tempo medio nel sistema, Ws = Ls / lambda_eff)")


# ============================================================
# 6. VERIFICHE SULLA SOLUZIONE
# ============================================================
print()
print("=== VERIFICHE SULLA SOLUZIONE ===")
# 3) il punto di convergenza soddisfa le equazioni di equilibrio p*Q = 0: e' davvero la soluzione,
#    non un punto in cui la convergenza e' solo diventata lenta
controllo("3. il punto di convergenza soddisfa p*Q = 0", max(abs(p @ Q)) < toll, "max|p*Q| = " + str(float(max(abs(p @ Q)))))

# 4) conservazione del flusso: cio' che entra = cio' che lavora M1 = cio' che esce da M2
controllo("4. conservazione del flusso: lambda_eff = mu*P(M1) = mu*P(M2)",
          abs(lam_eff - throughput_M1) < toll and abs(lam_eff - throughput) < toll,
          "valori: " + str(round(lam_eff, 6)) + ", " + str(round(throughput_M1, 6)) + ", " + str(round(throughput, 6)))
