"""
VERIFICHE: i controlli sulla soluzione DOPO la convergenza.

Corrisponde alla sezione "6. VERIFICHE SULLA SOLUZIONE" dello script originale.
La classe VerificheSoluzione controlla che il punto di convergenza sia davvero la soluzione
(p*Q = 0) e che il flusso si conservi.
"""
from .controlli import EsitoControllo


class VerificheSoluzione:

    def __init__(self, modello, toll=1e-9):
        self.modello = modello
        self.toll = toll

    def equilibrio(self, p):
        # 3) il punto di convergenza soddisfa le equazioni di equilibrio p*Q = 0: e' davvero la soluzione,
        #    non un punto in cui la convergenza e' solo diventata lenta
        Q = self.modello.Q
        return EsitoControllo(
            "3. il punto di convergenza soddisfa p*Q = 0",
            max(abs(p @ Q)) < self.toll,
            "max|p*Q| = " + str(float(max(abs(p @ Q)))),
        )

    def conservazione_flusso(self, indicatori):
        # 4) conservazione del flusso: cio' che entra = cio' che lavora M1 = cio' che esce da M2
        toll = self.toll
        return EsitoControllo(
            "4. conservazione del flusso: lambda_eff = mu*P(M1) = mu*P(M2)",
            abs(indicatori.lam_eff - indicatori.throughput_M1) < toll and abs(indicatori.lam_eff - indicatori.throughput) < toll,
            "valori: " + str(round(indicatori.lam_eff, 6)) + ", " + str(round(indicatori.throughput_M1, 6)) + ", " + str(round(indicatori.throughput, 6)),
        )

    def esegui(self, p, indicatori):
        return [self.equilibrio(p), self.conservazione_flusso(indicatori)]
