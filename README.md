# CODE-TANDEM — due macchine in tandem con catene di Markov

Modello di due macchine in serie (M1 -> M2) con buffer finiti e blocking, risolto come catena di Markov
a tempo continuo: si costruisce la matrice dei tassi Q, si passa a P(h) = I + Q*h e si fa convergere la
distribuzione di probabilita' fino a quella stazionaria, da cui si calcolano gli indicatori di prestazione.

```
input/parametri.json  ->  main.py          ->  output/risultati_<parametri>.json  (+ report_<parametri>.txt)
input/parametri.json  ->  sensitivita.py   ->  output/sensitivita/<data_ora>/     (tabella + grafici)
input/parametri.json  ->  costi.py         ->  output/costi/<data_ora>/           (tabelle + grafici)
```

## Struttura

```
funziona/
├── main.py                 un'esecuzione del modello con i parametri di input/parametri.json
├── sensitivita.py          analisi di sensitivita' one-at-a-time e grafici
├── costi.py                analisi economica: quanti posti di buffer conviene mettere, e come cambia con rho e con i costi
├── input/parametri.json    scenario base (lam, mu, K1, K2), bound della sensitivita', costi
├── output/                 risultati salvati (non tracciata da git: si ricrea lanciando gli script)
├── requirements.txt        pacchetti del .venv (pip freeze)
└── tandem/                 il package con le classi
    ├── input.py        ParametriIngresso             dati di ingresso (lam, mu, K1, K2), anche da JSON
    ├── oggetti.py      Stato, SpazioStati            sezione 1: lista degli stati
    ├── modello.py      ModelloTandem                 sezione 2: Q, tabella con le lettere L, h, P(h)
    ├── controlli.py    ControlliMatrice              sezione 3: P(h) e' di probabilita', catena irriducibile
    ├── convergenza.py  RisolutoreConvergenza         sezione 4: p(n) = p(n-1) * P(h)
    ├── indicatori.py   Indicatori, CalcolatoreIndicatori   sezione 5: indicatori di prestazione
    ├── verifiche.py    VerificheSoluzione            sezione 6: p*Q = 0, conservazione del flusso
    ├── risultati.py    Risultati                     contenitore di tutti i risultati di un'esecuzione
    └── output.py       StampaConsole, SalvaRisultati stampa a video e salvataggio su file
```

## Uso

```bash
python3 -m venv .venv               # solo la prima volta
source .venv/bin/activate           # su Windows: .venv\Scripts\activate
pip install -r requirements.txt     # numpy e matplotlib (pip freeze di un .venv con Python 3.9.6)

python main.py                                   # legge input/parametri.json
python main.py --K1 1 --K2 1                     # sovrascrive singoli valori del JSON
python main.py --input altro_file.json           # legge un altro file JSON
python main.py --no-salva                        # solo stampa, non scrive in output/
```

Per cambiare i parametri modifica `input/parametri.json`:

```json
{
  "lam": 10.0,
  "mu": 12.0,
  "K1": 0,
  "K2": 0
}
```

Alla fine di ogni esecuzione (salvo `--no-salva`) in `output/` trovi due file con i parametri nel nome,
per esempio con lam=10, mu=12, K1=0, K2=0:

- `risultati_lam10_mu12_K1-0_K2-0.json` — parametri, h, passi, probabilita' stazionarie per stato, indicatori, esiti dei controlli
- `report_lam10_mu12_K1-0_K2-0.txt` — lo stesso testo stampato a video

Esecuzioni con parametri diversi producono file diversi, quindi nulla viene sovrascritto.

## Analisi di sensitivita' e grafici

```bash
python sensitivita.py                  # legge lo scenario base e i bound da input/parametri.json
python sensitivita.py --input altro.json
```

Ogni parametro (lam, mu, K1, K2) viene fatto variare da solo tra un lower bound e un upper bound,
tenendo gli altri tre al valore base (analisi one-at-a-time). I bound stanno nella sezione
`"sensitivita"` di `input/parametri.json`:

```json
"sensitivita": {
  "lam": {"lower": 4.0, "upper": 20.0, "punti": 9},
  "mu":  {"lower": 6.0, "upper": 24.0, "punti": 9},
  "K1":  {"lower": 0, "upper": 10},
  "K2":  {"lower": 0, "upper": 10}
}
```

Ogni esecuzione salva in una cartella nuova `output/sensitivita/AAAA-MM-GG_HHMMSS/` (non tracciata da git),
cosi' le esecuzioni precedenti restano:

- `configurazione.json` — scenario base e bound usati
- `sensitivita.csv` — una riga per esecuzione del modello: parametro variato, valore, parametri, indicatori
- `sensitivita_<par>.png` — per ogni parametro, throughput, P(rifiuto), P(M1 bloccata), WIP e Ws al variare del parametro tra i bound
- `macchine_ai_bound.png` — M1 e M2 a lower bound, scenario base e upper bound: % del tempo in cui la macchina lavora / e' vuota / e' bloccata

## Analisi economica dei buffer

```bash
python costi.py                        # legge scenario base e sezione "costi" da input/parametri.json
python costi.py --input altro.json
```

Per ogni coppia (K1, K2) da 0 a `K_max` il modello da' il throughput e i pezzi medi in attesa nei due
buffer, e il profitto orario e'

```
profitto = ricavo_pezzo * throughput
         - costo_posto_ora * (K1 + K2)
         - costo_attesa_ora * (L_buffer1 + L_buffer2)
```

La coppia migliore e' quella col profitto piu' alto. La griglia viene rifatta per ogni valore di `rho`
della lista (lam = rho * mu, con mu al valore base) per vedere con quali carichi convengono buffer grandi
o piccoli; la sensitivita' ai costi moltiplica un costo alla volta per i `fattori`, sulla griglia dello
scenario base. Tutto sta nella sezione `"costi"` di `input/parametri.json`; i valori dei costi sono
di esempio, da sostituire con quelli reali:

```json
"costi": {
  "ricavo_pezzo": 10.0,
  "costo_posto_ora": 1.0,
  "costo_attesa_ora": 0.5,
  "K_max": 10,
  "rho": [0.25, 0.5, 0.75, 1.0, 1.25, 1.5],
  "fattori": [0.25, 0.5, 1, 2, 4]
}
```

Ogni esecuzione salva in una cartella nuova `output/costi/AAAA-MM-GG_HHMMSS/` (non tracciata da git):

- `configurazione.json` — scenario base, costi, rho e fattori usati
- `griglia.csv` — una riga per (rho, K1, K2): indicatori, ricavo, costi, profitto
- `ottimo_vs_rho.csv` — per ogni rho la coppia migliore, il suo profitto e quello senza buffer
- `ottimo_vs_costi.csv` — per ogni costo e fattore la coppia migliore
- `profitto_griglia.png` — mappa del profitto su (K1, K2), un pannello per rho, con la coppia migliore cerchiata
- `ottimo_vs_rho.png` — K1*, K2* e profitto orario (con i buffer migliori e senza buffer) al variare di rho
- `ottimo_vs_costi.png` — K1*, K2* al variare di ciascun costo

Se una coppia migliore tocca `K_max`, lo script lo segnala: alza `K_max` nel JSON (il tempo cresce con
il quadrato di K_max: con 10 sono 121 esecuzioni per ogni rho, meno di un minuto in tutto).

## Usare le classi da un altro script

```python
from tandem import ParametriIngresso, SpazioStati, ModelloTandem, RisolutoreConvergenza, CalcolatoreIndicatori

parametri = ParametriIngresso(lam=10.0, mu=12.0, K1=1, K2=1)
spazio = SpazioStati(parametri)
modello = ModelloTandem(parametri, spazio)
p, passi = RisolutoreConvergenza(modello).converge()
indicatori = CalcolatoreIndicatori(parametri, spazio).calcola(p)
print(indicatori.throughput, indicatori.Ws)
```
