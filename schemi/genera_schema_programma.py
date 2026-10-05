# Schema a blocchi del programma (paragrafo 3.5): file .drawio + SVG, stesso stile della Figura 2.1
# Uso: python schemi/genera_schema_programma.py   (scrive .drawio e .svg nella cartella schemi/)
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from xml.sax.saxutils import escape
FS, FSL = 16, 17
XC, BW, BH = 360, 330, 66          # centro della colonna, larghezza e altezza dei blocchi
DW, DH = 300, 96                  # rombi
GAP = 24
XL = 60                            # freccia di ritorno
XA, AW, AH = 640, 210, 74          # blocco di arresto
STY_BLK = f"rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;strokeWidth=1.5;fontSize={FS};fontFamily=Helvetica;"
STY_ROM = f"rhombus;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;strokeWidth=1.5;fontSize={FS};fontFamily=Helvetica;"
STY_BOX = f"rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;dashed=1;dashPattern=8 6;strokeWidth=1.2;verticalAlign=bottom;labelPosition=center;verticalLabelPosition=top;align=right;spacingRight=4;spacingBottom=4;fontSize={FSL};fontFamily=Helvetica;"
STY_E = "endArrow=block;endFill=1;endSize=8;html=1;rounded=0;strokeWidth=1.5;strokeColor=#000000;edgeStyle=orthogonalEdgeStyle;"
STY_T = f"text;html=1;align=center;verticalAlign=middle;fontSize={FS};fontFamily=Helvetica;"
cells, svg, n = [], [], [1]
def nid(): n[0] += 1; return f"c{n[0]}"
def testo(x, y, righe, anchor="middle"):
    lh = FS + 4; y0 = y - lh * (len(righe) - 1) / 2 + FS * 0.35
    for k, r in enumerate(righe):
        svg.append(f'<text x="{x}" y="{y0 + k*lh}" font-size="{FS}" text-anchor="{anchor}">{escape(r)}</text>')
def blocco(x, y, w, h, righe, sty=STY_BLK):
    g = nid()
    cells.append(f'<mxCell id="{g}" value="{escape("<br>".join(righe))}" style="{sty}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    if sty == STY_ROM:
        svg.append(f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="#fff" stroke="#000" stroke-width="1.5"/>')
    else:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="1.5"/>')
    testo(x + w/2, y + h/2, righe); return g
def freccia(src, dst, punti, exit, entry, etichetta=None, pos=None):
    st = STY_E + f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    interni = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in punti[1:-1])
    arr = f'<Array as="points">{interni}</Array>' if interni else ""
    val = f' value="{escape(etichetta)}"' if etichetta else ""
    cells.append(f'<mxCell id="{nid()}"{val} style="{st}fontSize={FS};fontFamily=Helvetica;labelBackgroundColor=#ffffff;" edge="1" parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')
    svg.append(f'<polyline points="{" ".join(f"{px},{py}" for px, py in punti)}" fill="none" stroke="#000" stroke-width="1.5" marker-end="url(#fr)"/>')
    if etichetta: svg.append(f'<text x="{pos[0]}" y="{pos[1]}" font-size="{FS}" text-anchor="middle">{escape(etichetta)}</text>')

y = 20; X = XC - BW/2
b = {}
def avanti(chiave, righe, rombo=False):
    global y
    if rombo: b[chiave] = (blocco(XC - DW/2, y, DW, DH, righe, STY_ROM), y, DH); y += DH + GAP + 10
    else: b[chiave] = (blocco(X, y, BW, BH, righe), y, BH); y += BH + GAP
avanti("dati", ["Dati in ingresso", "λ, μ, K₁, K₂"])
y += 16; F_TOP = y - 18
avanti("stati", ["Generazione degli stati", "lista S degli n stati", "(Algoritmo 4.1)"])
avanti("Q", ["Costruzione della matrice generatrice", "Q e tabella simbolica T", "(Algoritmo 4.2)"])
avanti("P", ["Passo e matrice di transizione", "h e P(h) = I + Q h", "(Algoritmo 4.3)"])
avanti("c12", ["Controlli 1 e 2", "superati?", "(Algoritmo 4.4)"], True)
avanti("conv", ["Convergenza", "p(n) = p(n − 1) P(h) fino a π", "(Algoritmo 4.5)"])
avanti("ind", ["Indici di prestazione", "P_rif, λ_eff, X, P(M1 bloccata), L, W", "(Algoritmo 4.6)"])
avanti("c34", ["Controlli 3 e 4", "esito salvato in output", "(Algoritmo 4.7)"])
avanti("ris", ["Risultati della configurazione", "π, indici, esito dei controlli"])
F_BOT = y - GAP + 18
y += 20
avanti("ok", ["Tutti i controlli", "superati?", "(Algoritmo 4.8)"], True)
avanti("salva", ["Salvataggio degli indici", "configurazione successiva", "(Algoritmo 4.8)"])
H_TOT = y - GAP + 30

# frecce lungo la colonna
ordine = ["dati", "stati", "Q", "P", "c12", "conv", "ind", "c34", "ris", "ok", "salva"]
for a, c in zip(ordine, ordine[1:]):
    ya = b[a][1] + b[a][2]; yc = b[c][1]
    et = "sì" if a in ("c12", "ok") else None
    freccia(b[a][0], b[c][0], [(XC, ya), (XC, yc)], (0.5, 1), (0.5, 0), et, (XC + 16, ya + 20) if et else None)
# arresto
yc12 = b["c12"][1] + DH/2; yok = b["ok"][1] + DH/2
YA = (yc12 + yok) / 2 - AH/2
b_arr = blocco(XA, YA, AW, AH, ["Arresto del calcolo", "con segnalazione", "dell'errore"])
freccia(b["c12"][0], b_arr, [(XC + DW/2, yc12), (XA + AW/2, yc12), (XA + AW/2, YA)], (1, 0.5), (0.5, 0), "no", (XC + DW/2 + 24, yc12 - 8))
freccia(b["ok"][0], b_arr, [(XC + DW/2, yok), (XA + AW/2, yok), (XA + AW/2, YA + AH)], (1, 0.5), (0.5, 1), "no", (XC + DW/2 + 24, yok - 8))
# ritorno
ys = b["salva"][1] + BH/2; yd = b["dati"][1] + BH/2
freccia(b["salva"][0], b["dati"][0], [(X, ys), (XL, ys), (XL, yd), (X, yd)], (0, 0.5), (0, 0.5))
ylab = (ys + yd) / 2
lab = "programma delle analisi: si ripete per ogni configurazione dell'elenco"
cells.append(f'<mxCell id="{nid()}" value="{escape(lab)}" style="{STY_T}rotation=-90;" vertex="1" parent="1"><mxGeometry x="{XL - 18 - 300}" y="{ylab - 12}" width="600" height="24" as="geometry"/></mxCell>')
svg.append(f'<text x="{XL - 12}" y="{ylab}" font-size="{FS}" text-anchor="middle" transform="rotate(-90 {XL - 12} {ylab})">{escape(lab)}</text>')
# riquadro del programma del modello
FX0, FX1 = X - 40, XA + AW + 20
lab2 = "Programma del modello (Algoritmi 4.1–4.7)"
cells.append(f'<mxCell id="{nid()}" value="{escape(lab2)}" style="{STY_BOX}" vertex="1" parent="1"><mxGeometry x="{FX0}" y="{F_TOP}" width="{FX1-FX0}" height="{F_BOT-F_TOP}" as="geometry"/></mxCell>')
svg.insert(0, f'<rect x="{FX0}" y="{F_TOP}" width="{FX1-FX0}" height="{F_BOT-F_TOP}" fill="none" stroke="#000" stroke-width="1.2" stroke-dasharray="8 6"/><text x="{FX1 - 4}" y="{F_TOP - 8}" font-size="{FSL}" text-anchor="end">{escape(lab2)}</text>')
W_TOT = FX1 + 20
xml = f'<mxfile host="app.diagrams.net"><diagram name="Programma"><mxGraphModel dx="1000" dy="800" grid="1" gridSize="10" guides="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>'
s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TOT}" height="{H_TOT}" font-family="Helvetica, Arial, sans-serif">'
     '<defs><marker id="fr" markerWidth="10" markerHeight="8" refX="10" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L10,4 L0,8 z"/></marker></defs>'
     f'<rect width="100%" height="100%" fill="#fff"/>{"".join(svg)}</svg>')
for a, sub in [("P_rif", "rif"), ("λ_eff", "eff")]:
    base = a.split("_")[0]
    xml = xml.replace(a, f"{base}&lt;sub&gt;{sub}&lt;/sub&gt;")
    s = s.replace(a, f'{base}<tspan baseline-shift="sub" font-size="11">{sub}</tspan>')
open("schema_programma.drawio", "w", encoding="utf-8").write(xml)
open("schema_programma.svg", "w", encoding="utf-8").write(s)
print(W_TOT, H_TOT)
