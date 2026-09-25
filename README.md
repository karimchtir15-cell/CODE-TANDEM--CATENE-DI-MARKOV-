# funziona — modello a classi

Versione a classi di `modello_generale_convergenza3.py` (che resta qui intatto come riferimento).
I calcoli, i commenti e le stampe sono gli stessi dello script originale: l'output di
`python main.py` e' identico riga per riga a quello di `python modello_generale_convergenza3.py`
(a parte la prima riga, che dice da quale file sono stati letti i parametri).

Ingresso e uscita sono JSON:

```
input/parametri.json     ->  main.py  ->  output/risultati.json  (+ output/report.txt)
```

## Struttura

```
funziona/
├── modello_generale_convergenza3.py   copia dello script originale (non usato da main.py)
├── main.py                            punto di ingresso: usa le classi nell'ordine dello script
├── input/parametri.json               parametri di ingresso letti da main.py
├── output/                            risultati salvati da main.py (risultati.json, report.txt)
└── tandem/                            il package con le classi
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

Ogni classe fa poche cose: `ModelloTandem` costruisce solo le matrici, `RisolutoreConvergenza`
fa solo convergere, `StampaConsole` stampa soltanto, `Risultati` contiene soltanto.

## Uso

```bash
source .venv/bin/activate           # il venv del progetto
pip install -r requirements.txt     # solo la prima volta (serve solo numpy)

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

Alla fine di ogni esecuzione (salvo `--no-salva`) in `output/` trovi:

- `risultati.json` — parametri, h, passi, probabilita' stazionarie per stato, indicatori, esiti dei controlli
- `report.txt` — lo stesso testo stampato a video

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

Tutto finisce in `output/sensitivita/` (non tracciata da git):

- `sensitivita.csv` — una riga per esecuzione: parametro variato, valore, parametri, indicatori
- `scenario_base.json` — risultati completi dello scenario base
- `fig1_macchine_base.png` — barre impilate M1 e M2: % del tempo in cui la macchina lavora / e' vuota / e' bloccata
- `fig2_distribuzione_base.png` — probabilita' stazionarie di ogni stato
- `fig3_sensitivita_<par>.png` — per ogni parametro, gli indicatori (throughput, P(rifiuto), P(M1 bloccata), WIP, Ws) al variare del parametro tra i bound
- `fig4_macchine_bounds.png` — barre M1/M2 a lower bound, base e upper bound, per ogni parametro

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
