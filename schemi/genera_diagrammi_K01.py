# Diagrammi degli stati: un file .drawio (una pagina per caso) e un SVG di anteprima con la stessa geometria
# Uso: python schemi/genera_diagrammi_K01.py   (scrive .drawio e .svg nella cartella schemi/)
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from xml.sax.saxutils import escape

SQ, DASH, GAP, DOT = 28, 20, 4, 9          # misure del pittogramma
COLW, ROWH = 220, 150                       # distanza tra colonne e tra righe della griglia
NODE_H = 70

def stati(K1, K2):
    s = [("N", i, j) for i in range(K1 + 2) for j in range(K2 + 2)]
    return s + [("B", i, K2 + 1) for i in range(1, K1 + 2)]

def transizioni(K1, K2):
    out = []
    for t in stati(K1, K2):
        tipo, i, j = t
        if tipo == "N":
            if i < K1 + 1:              out.append((t, ("N", i + 1, j), "λ"))
            if i >= 1 and j < K2 + 1:   out.append((t, ("N", i - 1, j + 1), "μ"))
            if i >= 1 and j == K2 + 1:  out.append((t, ("B", i, K2 + 1), "μ"))
            if j >= 1:                  out.append((t, ("N", i, j - 1), "μ"))
        else:
            if i < K1 + 1:              out.append((t, ("B", i + 1, K2 + 1), "λ"))
            out.append((t, ("N", i - 1, K2 + 1), "μ"))
    return out

def nome(t, rif):
    tipo, i, j = t
    if rif:                                   # notazione del testo di riferimento
        return "(b, 1)" if tipo == "B" else f"({i}, {j})"
    return f"{tipo}({i}, {j})"

def pittogramma(t, K1, K2, rif):
    """elementi del pittogramma: (tipo, x, y, w, h, testo) relativi all'angolo del pittogramma"""
    tipo, i, j = t
    el, x, yc = [], 0, SQ / 2
    in_coda1, in_coda2 = max(i - 1, 0), max(j - 1, 0)
    for k in range(K1):                       # buffer davanti a M1: i posti si riempiono dal lato della macchina
        el.append(("dash", x, yc - 5, DASH, 10, ""))
        if k >= K1 - in_coda1: el.append(("dot", x + DASH / 2 - DOT / 2, yc - DOT / 2, DOT, DOT, ""))
        x += DASH + GAP
    el.append(("sq", x, 0, SQ, SQ, ("b" if rif else "B") if tipo == "B" else ""))
    if tipo == "N" and i >= 1: el.append(("dot", x + SQ / 2 - DOT / 2, yc - DOT / 2, DOT, DOT, ""))
    x += SQ + 10
    for k in range(K2):                       # buffer tra le macchine
        el.append(("dash", x, yc - 5, DASH, 10, ""))
        if k >= K2 - in_coda2: el.append(("dot", x + DASH / 2 - DOT / 2, yc - DOT / 2, DOT, DOT, ""))
        x += DASH + GAP
    el.append(("sq", x, 0, SQ, SQ, ""))
    if j >= 1: el.append(("dot", x + SQ / 2 - DOT / 2, yc - DOT / 2, DOT, DOT, ""))
    return el, x + SQ

def layout(K1, K2):
    W = pittogramma(("N", 0, 0), K1, K2, False)[1] + 28
    righe = K2 + 3                            # riga 0 = stati bloccati, poi j = K2+1 ... 0
    pos = {}
    for t in stati(K1, K2):
        tipo, i, j = t
        r = 0 if tipo == "B" else 1 + (K2 + 1 - j)
        pos[t] = (40 + i * COLW, 40 + r * ROWH, W, NODE_H)
    return pos

def clip(c, box):                              # punto sul bordo del rettangolo lungo la retta verso c
    x, y, w, h = box; cx, cy = x + w / 2, y + h / 2
    dx, dy = c[0] - cx, c[1] - cy
    s = min(w / 2 / abs(dx) if dx else 1e9, h / 2 / abs(dy) if dy else 1e9)
    return cx + dx * s, cy + dy * s

STY_NODE = "rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#8c8c8c;container=1;collapsible=0;recursiveResize=0;verticalAlign=bottom;spacingBottom=3;fontFamily=Helvetica;fontSize=12;"
STY = {"sq": "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;strokeWidth=1.5;fontStyle=1;fontSize=14;fontFamily=Helvetica;",
       "dash": "line;strokeWidth=2;html=1;strokeColor=#000000;",
       "dot": "ellipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=none;"}
STY_EDGE = "endArrow=block;endFill=1;endSize=7;html=1;rounded=0;strokeWidth=1.2;fontFamily=Helvetica;fontSize=14;labelBackgroundColor=#ffffff;"

def pagina(K1, K2, titolo, rif=False):
    pos = layout(K1, K2); ids = {}; cells = []; svg = []; n = [2]
    def nid(): n[0] += 1; return f"c{n[0]}"
    for t, (x, y, w, h) in pos.items():
        g = nid(); ids[t] = g
        cells.append(f'<mxCell id="{g}" value="{escape(nome(t, rif))}" style="{STY_NODE}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff" stroke="#8c8c8c"/>')
        svg.append(f'<text x="{x + w/2}" y="{y + h - 7}" font-size="12" text-anchor="middle">{escape(nome(t, rif))}</text>')
        el, pw = pittogramma(t, K1, K2, rif); ox, oy = (w - pw) / 2, 10
        for k, ex, ey, ew, eh, txt in el:
            cells.append(f'<mxCell id="{nid()}" value="{txt}" style="{STY[k]}" vertex="1" parent="{g}"><mxGeometry x="{ox+ex}" y="{oy+ey}" width="{ew}" height="{eh}" as="geometry"/></mxCell>')
            X, Y = x + ox + ex, y + oy + ey
            if k == "sq":
                svg.append(f'<rect x="{X}" y="{Y}" width="{ew}" height="{eh}" fill="#fff" stroke="#000" stroke-width="1.5"/>')
                if txt: svg.append(f'<text x="{X+ew/2}" y="{Y+eh/2+5}" font-size="14" font-weight="bold" text-anchor="middle">{txt}</text>')
            elif k == "dash": svg.append(f'<line x1="{X}" y1="{Y+eh/2}" x2="{X+ew}" y2="{Y+eh/2}" stroke="#000" stroke-width="2"/>')
            else: svg.append(f'<circle cx="{X+ew/2}" cy="{Y+eh/2}" r="{ew/2}" fill="#000"/>')
    for a, b, lab in transizioni(K1, K2):
        cells.append(f'<mxCell id="{nid()}" value="{lab}" style="{STY_EDGE}" edge="1" parent="1" source="{ids[a]}" target="{ids[b]}"><mxGeometry relative="1" as="geometry"/></mxCell>')
        A, B = pos[a], pos[b]
        ca, cb = (A[0] + A[2]/2, A[1] + A[3]/2), (B[0] + B[2]/2, B[1] + B[3]/2)
        p1, p2 = clip(cb, A), clip(ca, B)
        svg.append(f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="#000" stroke-width="1.2" marker-end="url(#fr)"/>')
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        svg.append(f'<rect x="{mx-8}" y="{my-10}" width="16" height="19" fill="#fff"/><text x="{mx}" y="{my+5}" font-size="14" text-anchor="middle">{lab}</text>')
    Wt = max(x + w for x, y, w, h in pos.values()) + 40; Ht = max(y + h for x, y, w, h in pos.values()) + 40
    xml = f'<diagram name="{escape(titolo)}"><mxGraphModel dx="1000" dy="800" grid="1" gridSize="10" guides="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(cells)}</root></mxGraphModel></diagram>'
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wt}" height="{Ht}" font-family="Helvetica, Arial, sans-serif">'
         '<defs><marker id="fr" markerWidth="9" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L9,4 L0,8 z"/></marker></defs>'
         f'<rect width="100%" height="100%" fill="#fff"/>{"".join(svg)}</svg>')
    return xml, s, len(stati(K1, K2)), len(transizioni(K1, K2))

casi = [(0, 0, "Modello di riferimento", True), (1, 0, "K1 = 1, K2 = 0", False),
        (0, 1, "K1 = 0, K2 = 1", False), (1, 1, "K1 = 1, K2 = 1", False)]
pagine = []
for K1, K2, tit, rif in casi:
    xml, s, ns, nt = pagina(K1, K2, tit, rif); pagine.append(xml)
    open(f"K1_{K1}_K2_{K2}.svg", "w", encoding="utf-8").write(s)
    print(tit, ns, "stati", nt, "frecce")
open("diagrammi_stati.drawio", "w", encoding="utf-8").write(f'<mxfile host="app.diagrams.net">{"".join(pagine)}</mxfile>')
