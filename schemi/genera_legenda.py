# Legenda dei diagrammi delle transizioni: file .drawio (modificabile) e SVG con la stessa geometria
# Uso: python schemi/genera_legenda.py   (scrive .drawio e .svg nella cartella schemi/)
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from xml.sax.saxutils import escape
W, H = 780, 252
FS = 13
cells, svg = [], []
n = [2]
def nid(): n[0] += 1; return f"c{n[0]}"
GRIGIO = "#8c8c8c"

def testo(x, y, w, s, size=FS, bold=False, italic=False):
    st = f"text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontFamily=Helvetica;fontSize={size};" + ("fontStyle=1;" if bold else "") + ("fontStyle=2;" if italic else "")
    cells.append(f'<mxCell id="{nid()}" value="{escape(s)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y-11}" width="{w}" height="22" as="geometry"/></mxCell>')
    fw = ' font-weight="bold"' if bold else ''
    fi = ' font-style="italic"' if italic else ''
    svg.append(f'<text x="{x}" y="{y+4.5}" font-size="{size}"{fw}{fi}>{escape(s)}</text>')

def rett(x, y, w, h, stroke="#000", sw=1.5, rx=0, label="", bold=True, size=14, fill="#fff"):
    st = f"rounded={1 if rx else 0};arcSize=20;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth={sw};fontFamily=Helvetica;fontSize={size};" + ("fontStyle=1;" if bold else "")
    cells.append(f'<mxCell id="{nid()}" value="{escape(label)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    if label:
        fw = ' font-weight="bold"' if bold else ''
        svg.append(f'<text x="{x+w/2}" y="{y+h/2+size*0.36}" font-size="{size}" text-anchor="middle"{fw}>{escape(label)}</text>')

def punto(cx, cy, d=9):
    cells.append(f'<mxCell id="{nid()}" value="" style="ellipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=none;" vertex="1" parent="1"><mxGeometry x="{cx-d/2}" y="{cy-d/2}" width="{d}" height="{d}" as="geometry"/></mxCell>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{d/2}" fill="#000"/>')

def trattino(x, cy, w=20):
    cells.append(f'<mxCell id="{nid()}" value="" style="line;strokeWidth=2;html=1;strokeColor=#000000;" vertex="1" parent="1"><mxGeometry x="{x}" y="{cy-5}" width="{w}" height="10" as="geometry"/></mxCell>')
    svg.append(f'<line x1="{x}" y1="{cy}" x2="{x+w}" y2="{cy}" stroke="#000" stroke-width="2"/>')

def freccia(x1, y1, x2, y2, label="", tratt=False):
    st = "endArrow=block;endFill=1;endSize=7;html=1;rounded=0;strokeWidth=1.2;fontFamily=Helvetica;fontSize=14;labelBackgroundColor=#ffffff;" + ("dashed=1;" if tratt else "")
    cells.append(f'<mxCell id="{nid()}" value="{escape(label)}" style="{st}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" as="targetPoint"/></mxGeometry></mxCell>')
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-width="1.2" marker-end="url(#fr)"/>')
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        svg.append(f'<rect x="{mx-6}" y="{my-9}" width="12" height="16" fill="#fff"/><text x="{mx}" y="{my+5}" font-size="14" text-anchor="middle">{escape(label)}</text>')

# cornice e titolo
cells.append(f'<mxCell id="{nid()}" value="" style="rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={GRIGIO};strokeWidth=1;" vertex="1" parent="1"><mxGeometry x="1" y="1" width="{W-2}" height="{H-2}" as="geometry"/></mxCell>')
svg.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="#fff" stroke="{GRIGIO}" stroke-width="1"/>')
testo(18, 22, 200, "Legenda", size=14, bold=True)

Y0, DY = 52, 30
XS, XT = 22, 92          # colonna sinistra: simbolo, testo
XA, XT2 = 396, 474       # colonna destra: freccia, testo
# colonna sinistra
y = Y0;           rett(XS, y-13, 56, 26, stroke=GRIGIO, sw=1, rx=6, label="N(i, j)", bold=False, size=11); testo(XT, y, 300, "stato del sistema (un nodo del grafo)")
y += DY;          rett(XS+14, y-12, 24, 24); testo(XT, y, 300, "macchina (M1 o M2) vuota")
y += DY;          rett(XS+14, y-12, 24, 24); punto(XS+26, y); testo(XT, y, 300, "macchina con un pezzo in lavorazione")
y += DY;          rett(XS+14, y-12, 24, 24, label="B", size=13); testo(XT, y, 300, "M1 bloccata con il pezzo finito (b nel par. 1.4)")
y += DY;          trattino(XS+16, y); testo(XT, y, 300, "posto libero nel buffer")
y += DY;          trattino(XS+16, y); punto(XS+26, y); testo(XT, y, 300, "posto occupato nel buffer")
# colonna destra: direzioni fisse degli archi
y = Y0;           freccia(XA, y, XA+46, y, "λ"); testo(XT2, y, 300, "arrivo di un pezzo")
y += DY;          freccia(XA+23, y-13, XA+23, y+13, ""); testo(XA+52, y, 30, "μ", size=14); testo(XT2, y, 300, "fine lavorazione su M2, il pezzo esce")
y += DY;          freccia(XA+40, y+11, XA+8, y-11, ""); testo(XA+52, y, 30, "μ", size=14); testo(XT2, y, 300, "fine lavorazione su M1, il pezzo passa a M2")
y += DY;          freccia(XA+23, y+13, XA+23, y-13, ""); testo(XA+52, y, 30, "μ", size=14); testo(XT2, y, 300, "fine lavorazione su M1 con lato M2 pieno: blocco")
y += DY;          freccia(XA+40, y-11, XA+8, y+11, ""); testo(XA+52, y, 30, "μ", size=14); testo(XT2, y, 300, "fine lavorazione su M2 che sblocca M1")
# cappio (non disegnato nei diagrammi)
y += DY
cx, cy = XA+24, y
cells.append(f'<mxCell id="{nid()}" value="" style="rounded=1;arcSize=30;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={GRIGIO};strokeWidth=1;" vertex="1" parent="1"><mxGeometry x="{cx-16}" y="{cy-2}" width="32" height="14" as="geometry"/></mxCell>')
svg.append(f'<rect x="{cx-16}" y="{cy-2}" width="32" height="14" rx="4" fill="#fff" stroke="{GRIGIO}"/>')
cells.append(f'<mxCell id="{nid()}" value="" style="endArrow=block;endFill=1;endSize=6;html=1;curved=1;dashed=1;strokeWidth=1.2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{cx-8}" y="{cy-2}" as="sourcePoint"/><mxPoint x="{cx+8}" y="{cy-2}" as="targetPoint"/><Array as="points"><mxPoint x="{cx-12}" y="{cy-16}"/><mxPoint x="{cx+12}" y="{cy-16}"/></Array></mxGeometry></mxCell>')
svg.append(f'<path d="M{cx-8},{cy-2} C{cx-14},{cy-20} {cx+14},{cy-20} {cx+8},{cy-3}" fill="none" stroke="#000" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#fr)"/>')
testo(XT2, y, 300, "cappio: il sistema resta nello stato")
# nota finale
testo(18, H-20, W-36, "I cappi, cioè le transizioni di uno stato in se stesso, non sono disegnati nei diagrammi per semplicità di rappresentazione.", size=12, italic=True)

open("legenda.svg", "w", encoding="utf-8").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif">'
    '<defs><marker id="fr" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L9,3.5 L0,7 z"/></marker></defs>'
    + "".join(svg) + "</svg>")
modello = f'<mxGraphModel dx="{W}" dy="{H}" grid="1" gridSize="10" guides="1" page="1" pageWidth="{W}" pageHeight="{H}"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(cells)}</root></mxGraphModel>'
open("legenda_diagrammi.drawio", "w", encoding="utf-8").write(f'<mxfile host="app.diagrams.net"><diagram name="Legenda" id="legenda">{modello}</diagram></mxfile>')
print("ok", W, H)
