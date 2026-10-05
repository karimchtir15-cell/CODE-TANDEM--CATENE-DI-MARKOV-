# Schema a blocchi del metodo di lavoro (Figura 2.1): file .drawio + SVG, nello stile degli schemi del sistema
# Uso: python schemi/genera_schema_metodo.py   (scrive .drawio e .svg nella cartella schemi/)
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from xml.sax.saxutils import escape

FS = 17            # dimensione del testo nei blocchi
FSL = 18           # dimensione delle etichette delle fasi
X0 = 130           # margine sinistro dei blocchi (a sinistra passa la freccia di ritorno)
CW, GAP = 200, 40  # larghezza dei blocchi e spazio tra i blocchi
BH = 64            # altezza dei blocchi
COLS = [X0 + k * (CW + GAP) for k in range(3)]       # 130, 370, 610
XR = COLS[-1] + CW                                   # bordo destro dei blocchi: 810
W_TOT = XR + 40

STY_BLK = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;strokeWidth=1.5;fontSize=%d;fontFamily=Helvetica;" % FS
STY_BOX = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;dashed=1;dashPattern=8 6;strokeWidth=1.2;verticalAlign=bottom;labelPosition=center;verticalLabelPosition=top;align=left;spacingLeft=4;spacingBottom=4;fontSize=%d;fontFamily=Helvetica;" % FSL
STY_E = "endArrow=block;endFill=1;endSize=8;html=1;rounded=0;strokeWidth=1.5;strokeColor=#000000;edgeStyle=orthogonalEdgeStyle;"
STY_T = "text;html=1;align=center;verticalAlign=middle;fontSize=%d;fontFamily=Helvetica;" % FS

cells, svg, n = [], [], [1]
def nid(): n[0] += 1; return f"c{n[0]}"

def blocco(x, y, w, h, righe):
    """rettangolo con testo su più righe; restituisce l'id draw.io"""
    g = nid()
    cells.append(f'<mxCell id="{g}" value="{escape("<br>".join(righe))}" style="{STY_BLK}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="1.5"/>')
    lh = FS + 4
    y0 = y + h / 2 - lh * (len(righe) - 1) / 2 + FS * 0.35
    for k, r in enumerate(righe):
        svg.append(f'<text x="{x + w/2}" y="{y0 + k*lh}" font-size="{FS}" text-anchor="middle">{escape(r)}</text>')
    return g

def riquadro(x, y, w, h, etichetta, destra=False):
    cells.append(f'<mxCell id="{nid()}" value="{escape(etichetta)}" style="{STY_BOX.replace("align=left;spacingLeft=4", "align=right;spacingRight=4") if destra else STY_BOX}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#000" stroke-width="1.2" stroke-dasharray="8 6"/>')
    svg.append(f'<text x="{x + w - 4 if destra else x + 4}" y="{y - 8}" font-size="{FSL}" text-anchor="{"end" if destra else "start"}">{escape(etichetta)}</text>')

def freccia(src, dst, punti, exit=None, entry=None):
    """freccia ortogonale: punti = lista di (x, y) per l'SVG, dal bordo di partenza al bordo di arrivo"""
    st = STY_E
    if exit: st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
    if entry: st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    interni = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in punti[1:-1])
    arr = f'<Array as="points">{interni}</Array>' if interni else ""
    cells.append(f'<mxCell id="{nid()}" style="{st}" edge="1" parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')
    d = " ".join(f"{px},{py}" for px, py in punti)
    svg.append(f'<polyline points="{d}" fill="none" stroke="#000" stroke-width="1.5" marker-end="url(#fr)"/>')

# ---- blocco di partenza ----
Y0 = 30
b_rif = blocco(COLS[0], Y0, CW, BH, ["Modello di riferimento", "(par. 1.4): due stazioni,", "nessun buffer"])
# testo a fianco: cosa manca
cells.append(f'<mxCell id="{nid()}" value="{escape("Risolto analiticamente: cinque stati.<br>Con i buffer gli stati crescono<br>e il calcolo va automatizzato")}" style="text;html=1;align=left;verticalAlign=middle;fontSize={FS};fontFamily=Helvetica;" vertex="1" parent="1"><mxGeometry x="{COLS[1]}" y="{Y0}" width="{2*CW+GAP}" height="{BH}" as="geometry"/></mxCell>')
for k, r in enumerate(["Risolto analiticamente: cinque stati.", "Con i buffer gli stati crescono", "e il calcolo va automatizzato"]):
    svg.append(f'<text x="{COLS[1]}" y="{Y0 + 18 + k*(FS+4)}" font-size="{FS}">{escape(r)}</text>')

# ---- fase 1 ----
F1Y, F1H = 150, 250
riquadro(X0 - 30, F1Y, XR - X0 + 60, F1H, "Fase 1 – Costruzione e soluzione del modello (capitoli 3 e 4)", destra=True)
R1 = F1Y + 30; R2 = R1 + BH + 60
b_dati = blocco(COLS[0], R1, CW, BH, ["Ipotesi e dati", "λ, μ, K₁, K₂"])
b_stati = blocco(COLS[1], R1, CW, BH, ["Generazione degli stati", "N(i, j) e B(i, K₂+1)"])
b_reg = blocco(COLS[2], R1, CW, BH, ["Matrice generatrice Q", "dalle regole di transizione"])
b_Q = blocco(COLS[0], R2, CW, BH, ["Matrice di transizione", "P(h) = I + Q h"])
b_conv = blocco(COLS[1], R2, CW, BH, ["Convergenza", "p(n) = p(n−1) P(h) → π"])
b_ind = blocco(COLS[2], R2, CW, BH, ["Indici di prestazione:", "X, P_rif, P(M1 bloccata),", "L, W"])
freccia(b_rif, b_dati, [(COLS[0] + CW/2, Y0 + BH), (COLS[0] + CW/2, R1)], (0.5, 1), (0.5, 0))
freccia(b_dati, b_stati, [(COLS[0] + CW, R1 + BH/2), (COLS[1], R1 + BH/2)], (1, 0.5), (0, 0.5))
freccia(b_stati, b_reg, [(COLS[1] + CW, R1 + BH/2), (COLS[2], R1 + BH/2)], (1, 0.5), (0, 0.5))
ym = R1 + BH + 30
freccia(b_reg, b_Q, [(COLS[2] + CW/2, R1 + BH), (COLS[2] + CW/2, ym), (COLS[0] + CW/2, ym), (COLS[0] + CW/2, R2)], (0.5, 1), (0.5, 0))
freccia(b_Q, b_conv, [(COLS[0] + CW, R2 + BH/2), (COLS[1], R2 + BH/2)], (1, 0.5), (0, 0.5))
freccia(b_conv, b_ind, [(COLS[1] + CW, R2 + BH/2), (COLS[2], R2 + BH/2)], (1, 0.5), (0, 0.5))

# ---- fase 2 ----
F2Y, F2H = F1Y + F1H + 60, 130
riquadro(X0 - 30, F2Y, XR - X0 + 60, F2H, "Fase 2 – Verifica del modello implementato (capitolo 4)")
W2 = (XR - X0 - GAP) / 2
R3 = F2Y + 33
b_ctrl = blocco(COLS[0], R3, W2, BH, ["Quattro controlli a ogni esecuzione:", "P(h) stocastica, irriducibilità,", "πQ = 0, conservazione del flusso"])
b_conf = blocco(COLS[0] + W2 + GAP, R3, W2, BH, ["Confronto con i casi noti:", "K₁ = K₂ = 0, soluzione analitica", "con K₁ = 1, soluzione diretta di πQ = 0"])
# freccia tra le fasi (dal riquadro 1 al riquadro 2), al centro
xc = X0 + (XR - X0) * 0.78   # a destra delle etichette delle fasi
cells.append(f'<mxCell id="{nid()}" style="{STY_E}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{xc}" y="{F1Y + F1H}" as="sourcePoint"/><mxPoint x="{xc}" y="{F2Y}" as="targetPoint"/></mxGeometry></mxCell>')
svg.append(f'<line x1="{xc}" y1="{F1Y + F1H}" x2="{xc}" y2="{F2Y}" stroke="#000" stroke-width="1.5" marker-end="url(#fr)"/>')

# ---- fase 3 ----
F3Y, F3H = F2Y + F2H + 60, 160
riquadro(X0 - 30, F3Y, XR - X0 + 60, F3H, "Fase 3 – Uso del modello (capitoli 5 e 6)")
R4 = F3Y + 33
BH3 = 94
b_sens = blocco(COLS[0], R4, W2, BH3, ["Analisi con il modello:", "effetto di ogni buffer,", "ripartizione di N posti,", "posti per un obiettivo, carico"])
b_econ = blocco(COLS[0] + W2 + GAP, R4, W2, BH3, ["Valutazione economica:", "costo dei posti e dei pezzi", "in attesa contro il ricavo", "della produzione"])
cells.append(f'<mxCell id="{nid()}" style="{STY_E}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{xc}" y="{F2Y + F2H}" as="sourcePoint"/><mxPoint x="{xc}" y="{F3Y}" as="targetPoint"/></mxGeometry></mxCell>')
svg.append(f'<line x1="{xc}" y1="{F2Y + F2H}" x2="{xc}" y2="{F3Y}" stroke="#000" stroke-width="1.5" marker-end="url(#fr)"/>')
freccia(b_sens, b_econ, [(COLS[0] + W2, R4 + BH3/2), (COLS[0] + W2 + GAP, R4 + BH3/2)], (1, 0.5), (0, 0.5))

# ---- ritorno: per ogni configurazione si ripete il calcolo ----
xl = 60
freccia(b_sens, b_dati, [(COLS[0], R4 + BH3/2), (xl, R4 + BH3/2), (xl, R1 + BH/2), (COLS[0], R1 + BH/2)], (0, 0.5), (0, 0.5))
ylab = (R1 + R4 + BH3) / 2
cells.append(f'<mxCell id="{nid()}" value="{escape("per ogni configurazione si ripete il calcolo")}" style="{STY_T}rotation=-90;" vertex="1" parent="1"><mxGeometry x="{xl - 22 - 190}" y="{ylab - 12}" width="380" height="24" as="geometry"/></mxCell>')
svg.append(f'<text x="{xl - 14}" y="{ylab}" font-size="{FS}" text-anchor="middle" transform="rotate(-90 {xl - 14} {ylab})">per ogni configurazione si ripete il calcolo</text>')

H_TOT = F3Y + F3H + 30
xml = f'<mxfile host="app.diagrams.net"><diagram name="Metodo di lavoro"><mxGraphModel dx="1000" dy="800" grid="1" gridSize="10" guides="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>'
s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TOT}" height="{H_TOT}" font-family="Helvetica, Arial, sans-serif">'
     '<defs><marker id="fr" markerWidth="10" markerHeight="8" refX="10" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L10,4 L0,8 z"/></marker></defs>'
     f'<rect width="100%" height="100%" fill="#fff"/>{"".join(svg)}</svg>')
xml = xml.replace("P_rif", "P&lt;sub&gt;rif&lt;/sub&gt;")
s = s.replace("P_rif", 'P<tspan baseline-shift="sub" font-size="12">rif</tspan>')
open("schema_metodo.drawio", "w", encoding="utf-8").write(xml)
open("schema_metodo.svg", "w", encoding="utf-8").write(s)
print(W_TOT, H_TOT)
