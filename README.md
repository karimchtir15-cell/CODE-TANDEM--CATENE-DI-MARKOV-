# CODE-TANDEM — due macchine in tandem con catene di Markov

Modello di due macchine in serie (M1 -> M2) con buffer finiti e blocking, risolto come catena di Markov
a tempo continuo: si costruisce la matrice dei tassi Q, si passa a P(h) = I + Q*h e si fa convergere la
distribuzione di probabilita' fino a quella stazionaria, da cui si calcolano gli indicatori di prestazione.

```
input/parametri.json  ->  main.py          ->  output/risultati_<parametri>.json  (+ report_<parametri>.txt)
input/parametri.json  ->  sensitivita.py   ->  output/sensitivita/<data_ora>/     (tabella + grafici)
input/parametri.json  ->  costi.py         ->  output/costi/<data_ora>/           (tabelle + grafici)
input/parametri.json  ->  tempo_macchine.py ->  output/tempo_macchine/<data_ora>/ (griglia + grafici 3D e a colonne)
input/parametri.json  ->  valori_limite.py ->  output/valori_limite/<data_ora>/   (tabella dei valori limite)
input/parametri.json  ->  allocazione.py   ->  output/allocazione/<data_ora>/     (ripartizione di N posti, obiettivi, carico)
input/parametri.json  ->  verifica.py      ->  output/verifica/<data_ora>/        (verifica del modello implementato)
```

## Da dove vengono figure e tabelle della tesi

| Tesi | Script | File prodotto |
|---|---|---|
| Fig. 1.2, 3.2, 3.4, 3.6, 4.2 (diagrammi delle transizioni) | `schemi/genera_diagrammi_K01.py`, `schemi/genera_diagrammi_K2.py` | `schemi/diagrammi_stati*.drawio`, `schemi/K1_*_K2_*.svg` |
| Fig. 2.1 (metodo), Fig. 4.1 (programma), legenda dei diagrammi | `schemi/genera_schema_metodo.py`, `schemi/genera_schema_programma.py`, `schemi/genera_legenda.py` | `schemi/*.drawio`, `schemi/*.svg` |
| Tab. 4.1 (numero di stati), passi e tempi del par. 4.3 | `main.py` | stampa a video, `report_*.txt` |
| Par. 4.2 (forma chiusa, 48 configurazioni, 13 errori) | `verifica.py` | `verifica.txt` |
| Fig. 5.1, 5.2 (caso base al variare di λ e μ) | `sensitivita.py` | `sensitivita_lam.png`, `sensitivita_mu.png` |
| Fig. 5.3, 5.5 (sensitivita' a K1 e K2) | `sensitivita.py` | `sensitivita_K1.png`, `sensitivita_K2.png` |
| Fig. 5.4, 5.6 (tempo delle macchine al variare di K1 e K2) | `sensitivita.py` | `tempo_macchine_K1.png`, `tempo_macchine_K2.png` |
| Tab. 5.1-5.4 (caso base e configurazioni con un posto per buffer) | `main.py --K1 .. --K2 ..` | `risultati_*.json` |
| Fig. 5.7 (tempo delle macchine in 3D), Fig. 5.8 (indici in 3D), Fig. 7.1 | `tempo_macchine.py` | `tempo_macchine_3d.png`, `indicatori_3d.png`, `tempo_macchine_configurazioni.png` |
| Tab. 5.5 (valori limite) | `valori_limite.py` | `valori_limite.txt` |
| Fig. 5.9 (W in 3D su (K1, K2) e al variare di K2 per K1 da 1 a 5) | `allocazione.py` | `W_3d.png`, `W_K2.png` |
| Fig. 5.10, Tab. 5.6 (ripartizione di N posti: throughput 3D e scarto dal massimo) | `allocazione.py` | `ripartizione_3d.png`, `migliori_per_N.csv`, `ripartizioni.csv` |
| Fig. 5.11, Tab. 5.7 (dimensionamento: ripartizione migliore per N da 0 a 40, posti per un throughput obiettivo) | `allocazione.py` | `migliori_per_N.png`, `migliori_per_N.csv`, `obiettivi.csv` |
| Fig. 5.12 (dipendenza dal carico, ogni N da 1 a 20 e ρ < 1) | `allocazione.py` | `carico.png`, `carico.csv` |
| Capitolo 6 (valutazione economica; Tab. 6.2 e Fig. 6.2 con ρ < 1) | `costi.py` | `costo_griglia.png`, `ottimo_vs_rho.png`, `ottimo_vs_costi.png`, csv |

I grafici della tesi hanno un'impaginazione ritoccata per il Word, ma i numeri sono quelli prodotti da
questi script.

## Struttura

```
funziona/
├── main.py                 un'esecuzione del modello con i parametri di input/parametri.json
├── sensitivita.py          analisi di sensitivita' one-at-a-time e grafici
├── costi.py                analisi economica: quanti posti di buffer conviene mettere, e come cambia con rho e con i costi
├── tempo_macchine.py       griglia (K1, K2): tempo delle macchine (lavora / vuota / bloccata) e superfici 3D degli indicatori
├── valori_limite.py        valori limite degli indicatori al crescere delle capacita' dei buffer
├── allocazione.py          ripartizione di N posti tra K1 e K2, posti per un obiettivo, dipendenza dal carico, W al variare di K2
├── verifica.py             verifica del modello implementato: forma chiusa, convergenza vs soluzione diretta, 13 errori
├── schemi/                 diagrammi e schemi della tesi in draw.io (+ svg/png) e gli script genera_*.py che li producono
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
    ├── diretto.py      RisolutoreDiretto             soluzione diretta di pi*Q = 0 (verifica e capacita' molto grandi)
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

Come nella tesi (par. 3.1), il carico rho = lam/mu deve essere minore di 1: con lam >= mu il programma
si ferma con un errore. Tutte le sezioni del JSON (sensitivita', costi, allocazione, verifica) usano solo
valori di lam e mu che rispettano questa condizione.

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
  "lam": {"lower": 0.5, "upper": 11.5, "punti": 23},
  "mu":  {"lower": 11.0, "upper": 10000.0, "punti": 80, "scala": "log"},
  "K1":  {"lower": 0, "upper": 40},
  "K2":  {"lower": 0, "upper": 20},
  "tempo_macchine_valori": {"K1": [0, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 40], "K2": [0, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20]}
}
```

Ogni esecuzione salva in una cartella nuova `output/sensitivita/AAAA-MM-GG_HHMMSS/` (non tracciata da git),
cosi' le esecuzioni precedenti restano:

- `configurazione.json` — scenario base e bound usati
- `sensitivita.csv` — una riga per esecuzione del modello: parametro variato, valore, parametri, indicatori
- `sensitivita_<par>.png` — per ogni parametro, throughput, P(rifiuto), P(M1 bloccata), WIP e Ws al variare del parametro tra i bound
- `macchine_ai_bound.png` — M1 e M2 a lower bound, scenario base e upper bound: % del tempo in cui la macchina lavora / e' vuota / e' bloccata
- `tempo_macchine_K1.png`, `tempo_macchine_K2.png` — M1 e M2 per ogni valore di K1 (o di K2): colonne impilate lavora / vuota / bloccata (tesi, Figure 5.4 e 5.6)

## Analisi economica dei buffer

```bash
python costi.py                        # legge scenario base e sezione "costi" da input/parametri.json
python costi.py --input altro.json
```

Come in letteratura si guardano solo i costi e si prende la configurazione che li minimizza.
Per ogni coppia (K1, K2) da 0 a `K_max` il modello da' il throughput e i pezzi medi in attesa nei due
buffer, e il costo orario e'

```
costo = costo_pezzo_perso * (lam - throughput)          pezzi/ora rifiutati perche' non c'e' posto
      + costo_posto_ora   * (K1 + K2)                   posti di buffer installati
      + costo_attesa_ora  * (L_buffer1 + L_buffer2)     pezzi fermi ad aspettare
```

La coppia migliore e' quella col costo piu' basso. E' la stessa cosa che massimizzare il profitto a un
dato prezzo di vendita: il ricavo `prezzo * throughput` vale `prezzo * lam - prezzo * (lam - throughput)`
e `prezzo * lam` non dipende dai buffer, quindi il prezzo fa da costo del pezzo perso.

La griglia viene rifatta per ogni valore di `rho` della lista (lam = rho * mu, con mu al valore base) per
vedere con quali carichi convengono buffer grandi o piccoli; la sensitivita' ai costi moltiplica un costo
alla volta per i `fattori`, sulla griglia dello scenario base. Tutto sta nella sezione `"costi"` di
`input/parametri.json`; i valori dei costi sono di esempio, da sostituire con quelli reali:

```json
"costi": {
  "costo_pezzo_perso": 10.0,
  "costo_posto_ora": 1.0,
  "costo_attesa_ora": 0.5,
  "K_max": 10,
  "rho": [0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 0.9166666667, 0.9583333333],
  "fattori": [0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64],
  "K_max_sensitivita": 20
}
```

Ogni esecuzione salva in una cartella nuova `output/costi/AAAA-MM-GG_HHMMSS/` (non tracciata da git):

- `configurazione.json` — scenario base, costi, rho e fattori usati
- `griglia.csv` — una riga per (rho, K1, K2): indicatori, le tre voci di costo, costo totale
- `ottimo_vs_rho.csv` — per ogni rho la coppia migliore, il suo costo e quello senza buffer
- `ottimo_vs_costi.csv` — per ogni costo e fattore la coppia migliore
- `costo_griglia.png` — mappa del costo su (K1, K2), un pannello per rho, con la coppia migliore cerchiata
- `ottimo_vs_rho.png` — K1*, K2* e costo orario (con i buffer migliori e senza buffer) al variare di rho
- `ottimo_vs_costi.png` — K1*, K2* al variare di ciascun costo

Se una coppia migliore tocca `K_max`, lo script lo segnala: alza `K_max` nel JSON (il tempo cresce con
il quadrato di K_max: con 10 sono 121 esecuzioni per ogni rho, meno di un minuto in tutto). La sensitivita' ai
costi usa una griglia dello scenario base estesa fino a `K_max_sensitivita` (20): le coppie oltre `K_max` sono
risolte con la soluzione diretta, perche' con il costo del posto molto basso l'ottimo ha molti posti.

## Tempo delle macchine sulla griglia (K1, K2)

```bash
python tempo_macchine.py               # legge scenario base e sezione "tempo_macchine" da input/parametri.json
```

Per ogni coppia (K1, K2) da 0 a `K_max` il modello viene risolto con lam e mu al valore base (per convergenza
se K1 + K2 <= 20, con la soluzione diretta oltre), e si calcola la frazione di tempo in cui M1 lavora / e' vuota / e' bloccata e in cui M2 lavora / e'
vuota. M1 e M2 lavorano per la stessa frazione di tempo (conservazione del flusso). Sezione del JSON:

```json
"tempo_macchine": {
  "K_max": 20,
  "configurazioni": [[0, 0], [0, 10], [10, 0], [3, 0], [3, 1], [3, 10]]
}
```

Ogni esecuzione salva in `output/tempo_macchine/AAAA-MM-GG_HHMMSS/`:

- `griglia.csv` — una riga per (K1, K2): indicatori e frazioni di tempo
- `tempo_macchine_3d.png` — superfici su (K1, K2): lavoro (M1 e M2), M1 bloccata, M1 vuota (tesi, Figura 5.7)
- `tempo_macchine_configurazioni.png` — colonne impilate per le `configurazioni` (K1, K2) del JSON (tesi, Figura 7.1)
- `indicatori_3d.png` — superfici 3D di throughput, P(rifiuto), P(M1 bloccata), Ls e Ws su (K1, K2); sulla superficie di Ws i punti neri indicano, per ogni K1, il K2 con Ws minimo (tesi, Figura 5.8)

## Valori limite degli indicatori

```bash
python valori_limite.py                # legge scenario base e sezione "valori_limite" da input/parametri.json
```

Fa crescere una capacita' alla volta (K1 = 0 e K2 crescente; K2 fisso e K1 crescente, per ogni valore di
`K2_fissi`) oppure entrambe (K1 = K2 crescenti) e mostra verso quali valori tendono throughput, P(rifiuto),
P(M1 bloccata), Ls e Ws (tesi, Tabella 5.5). Con qualche centinaio di posti la convergenza richiederebbe
troppi passi, quindi qui la distribuzione stazionaria si ottiene risolvendo direttamente pi*Q = 0
(`tandem/diretto.py`) con la stessa matrice Q; per le capacita' fino a `K_max_confronto_convergenza` la
tabella riporta anche la differenza massima con la soluzione per convergenza (dell'ordine di 1e-13).

```json
"valori_limite": {
  "K_crescenti": [10, 50, 100, 300],
  "K2_fissi": [0, 1, 2, 4, 10],
  "K_entrambi": [10, 20, 40, 60],
  "K_max_confronto_convergenza": 10
}
```

Ogni esecuzione salva in `output/valori_limite/AAAA-MM-GG_HHMMSS/` il file `valori_limite.csv` e la stessa
tabella leggibile in `valori_limite.txt`.

## Ripartizione dei posti, obiettivi e carico

```bash
python allocazione.py                  # legge scenario base e sezione "allocazione" da input/parametri.json
```

Per ogni N da 0 a `N_max` si calcolano tutte le ripartizioni K1 + K2 = N e si prende quella con il
throughput massimo; dalla stessa serie si ricava, per ogni throughput obiettivo, il numero minimo di posti.
La ripartizione migliore viene poi ricalcolata per ogni valore di lam della lista (mu al valore base) e per
alcuni N, per vedere come cambia con il carico. Infine si calcola Ws al variare di K2 per i K1 di `W_K1`.
Le configurazioni sono circa 800, risolte per convergenza: meno di un minuto.
La serie dei migliori prosegue poi da N_max + 1 a `N_max_curva` (per vedere dove le curve si assestano):
qui le ripartizioni sono confrontate con la soluzione diretta di pi*Q = 0, la stessa di `valori_limite.py`,
che coincide con la convergenza (`verifica.py`) ma e' molto piu' rapida con molti stati. La colonna `metodo`
di `migliori_per_N.csv` indica quale delle due e' stata usata. Anche la dipendenza dal carico (`carico.csv`, ogni N da 1 a 20
per ogni lam della lista) usa la soluzione diretta, perche' le configurazioni sono alcune migliaia. Nel grafico `migliori_per_N.png` la linea
tratteggiata e' il valore con K1 = K2 = massimo di `K_entrambi` (sezione `valori_limite`).

```json
"allocazione": {
  "N_max": 20,
  "N_max_curva": 40,
  "obiettivi": [6, 7, 8, 9, 9.5, 9.9],
  "carico": {"lam": [4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5], "N": [1, 2, ..., 20]},
  "W_K1": [1, 2, 3, 4, 5],
  "W_K2_max": 20,
  "W_3d_K_max": 20,
  "N_max_3d": 40
}
```

Ogni esecuzione salva in `output/allocazione/AAAA-MM-GG_HHMMSS/`: `ripartizioni.csv`, `migliori_per_N.csv`,
`obiettivi.csv`, `carico.csv`, `W_K2.csv` e i grafici `ripartizione_3d.png`, `migliori_per_N.png`,
`carico.png`, `W_K2.png` e `W_3d.png` (superficie 3D di Ws su tutta la griglia K1, K2 da 0 a `W_3d_K_max`).
In `allocazione.py` le configurazioni con K1 + K2 oltre 20 (`LIMITE_CONVERGENZA`) sono risolte con la soluzione
diretta; `ripartizione_3d.png` copre tutte le coppie con K1 + K2 <= `N_max_3d`.
`ripartizione_3d.png` riporta il throughput di tutte le coppie con K1 + K2 <= `N_max` e, per ciascuna, lo scarto
percentuale dal throughput massimo con lo stesso N, riportato anche nella colonna `scarto_dal_massimo_perc` di `ripartizioni.csv`.

## Verifica del modello implementato

```bash
python verifica.py                     # legge scenario base e sezione "verifica" da input/parametri.json
```

Tre prove, indipendenti dai quattro controlli eseguiti a ogni calcolo:

- **forma chiusa**: con K1 = K2 = 0 e con K1 = 1, K2 = 0 la distribuzione per convergenza coincide con le
  formule ricavate a mano (paragrafi 1.4 e 3.2 della tesi);
- **convergenza contro soluzione diretta**: sulla griglia di K1, K2, lam, mu della sezione (48 configurazioni)
  la distribuzione per convergenza coincide con quella che risolve direttamente pi*Q = 0;
- **13 errori introdotti di proposito** nelle regole di transizione e nei parametri del calcolo (per esempio la
  regola di sblocco tolta, la diagonale di Q dimezzata, h troppo grande, una tolleranza troppo larga): per
  ciascuno la tabella mostra quali dei quattro controlli lo rilevano. Ogni errore deve essere rilevato da
  almeno uno.

```json
"verifica": {
  "K1": [0, 1, 2, 3], "K2": [0, 1, 2, 3], "lam": [5.0, 8.0, 11.0], "mu": [12.0],
  "errori_K1": 1, "errori_K2": 1
}
```

Il risultato e' in `output/verifica/AAAA-MM-GG_HHMMSS/verifica.txt` (con i dettagli nei csv).

## Diagrammi e schemi

```bash
python schemi/genera_diagrammi_K01.py     # diagrammi delle transizioni con K1, K2 <= 1 (Fig. 1.2, 3.2, 3.4, 3.6)
python schemi/genera_diagrammi_K2.py      # diagrammi con due posti (Fig. 4.2)
python schemi/genera_schema_metodo.py     # schema a blocchi del metodo (Fig. 2.1)
python schemi/genera_schema_programma.py  # schema a blocchi del programma (Fig. 4.1)
python schemi/genera_legenda.py           # legenda dei diagrammi delle transizioni
```

Ogni script scrive in `schemi/` un file `.drawio` (da aprire con draw.io o app.diagrams.net) e un'anteprima
`.svg`. I diagrammi delle transizioni usano le stesse sei regole di `tandem/modello.py`.

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
