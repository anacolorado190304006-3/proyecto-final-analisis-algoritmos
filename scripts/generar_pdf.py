"""Exporta el README completo a PDF con fórmulas vectoriales y enlaces.

Requiere las dependencias de requirements-pdf.txt, Node.js y mathjax-full
en .venvAnalisis/pdf-node. No ejecuta algoritmos ni regenera gráficas.
"""

import base64
import hashlib
import html
import json
import re
import subprocess
import unicodedata
from collections.abc import Callable
from pathlib import Path

import pypandoc
from weasyprint import HTML

RAIZ = Path(__file__).resolve().parents[1]
REPOSITORIO = (
    "https://github.com/anacolorado190304006-3/"
    "proyecto-final-analisis-algoritmos/blob/main/"
)

ESTILO = """
@page {
    size: A4;
    margin: 12mm 13mm 14mm;
    @bottom-left {
        content: "Análisis de Algoritmos · Banco Regional de Alimentos";
        font-family: "DejaVu Sans"; font-size: 7pt; color: #555;
    }
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-family: "DejaVu Sans"; font-size: 7pt; color: #555;
    }
}
body { font-family: "DejaVu Sans"; font-size: 9pt; line-height: 1.14;
       color: #20252b; }
h1 { font-size: 19pt; line-height: 1.15; color: #163b51; }
h2 { font-size: 13pt; border-bottom: .6pt solid #aab9c2;
     padding-bottom: 3pt; margin: 10pt 0 5pt; color: #163b51; }
h3 { font-size: 10.5pt; margin: 7pt 0 3pt; }
h4 { font-size: 9.5pt; margin: 6pt 0 3pt; }
h1, h2, h3, h4 { break-after: avoid; }
h2[id^="anexo-a"] { break-before: page; }
p { margin: 2.5pt 0; orphans: 3; widows: 3; }
ul, ol { margin: 3pt 0; padding-left: 15pt; }
li { margin: 1pt 0; }
a { color: #175976; text-decoration: none; overflow-wrap: anywhere; }
table { width: 100%; border-collapse: collapse; margin: 5pt 0;
        table-layout: auto; font-size: 8pt; line-height: 1.12; }
.columnas-2 th:first-child { width: 25%; }
.columnas-4 th:first-child, .columnas-5 th:first-child { width: 14%; }
th, td { padding: 1.8pt 4pt; border: .4pt solid #bac5ca;
         overflow-wrap: anywhere; vertical-align: top; }
th { background: #e9f0f4; text-align: left; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
pre { font-family: "DejaVu Sans Mono"; font-size: 7.4pt;
      white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.15;
      background: #f2f4f5; padding: 6pt; }
code { font-family: "DejaVu Sans Mono"; font-size: .87em;
       overflow-wrap: anywhere; }
figure { margin: 7pt 0; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 63mm; width: auto; }
figcaption { font-size: 8pt; color: #555; }
img { max-width: 100%; }
.formula { display: inline-block; max-width: 100%; }
.formula-bloque { display: block; text-align: center; margin: 5pt 0; }
.formula img { max-width: 100%; }
hr { border: 0; margin: 5pt 0; }
"""

MATHJAX = r"""
const fs = require('fs');
const root = process.argv[1];
const {mathjax} = require(root + '/js/mathjax.js');
const {TeX} = require(root + '/js/input/tex.js');
const {SVG} = require(root + '/js/output/svg.js');
const {liteAdaptor} = require(root + '/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require(root + '/js/handlers/html.js');
const {AllPackages} = require(root + '/js/input/tex/AllPackages.js');
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const mathDocument = mathjax.document('', {
    InputJax: new TeX({packages: AllPackages}),
    OutputJax: new SVG({fontCache: 'none'})
});
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = input.map(([display, tex]) => {
    const node = mathDocument.convert(tex, {display});
    const result = adaptor.innerHTML(node);
    if (result.includes('data-mml-node="merror"')) {
        throw new Error('Fórmula inválida: ' + tex);
    }
    return result;
});
process.stdout.write(JSON.stringify(output));
"""


def recorrer(nodo: object, accion: Callable[[dict], None]) -> None:
    """Visita los nodos de un documento de Pandoc.

    Args:
        nodo: Nodo o lista del árbol JSON.
        accion: Función que recibe cada diccionario del árbol.
    """
    if isinstance(nodo, dict):
        accion(nodo)
        for valor in list(nodo.values()):
            recorrer(valor, accion)
    elif isinstance(nodo, list):
        for valor in nodo:
            recorrer(valor, accion)


def main() -> None:
    """Convierte el README sin omitir secciones y guarda informe.pdf."""
    fuente = RAIZ / "README.md"
    texto = fuente.read_text(encoding="utf-8")
    documento = json.loads(pypandoc.convert_text(
        texto, "json", format="markdown+tex_math_dollars"
    ))
    formulas: list[tuple[bool, str]] = []

    def recoger(nodo: dict) -> None:
        if nodo.get("t") == "Math":
            clave = (nodo["c"][0]["t"] == "DisplayMath", nodo["c"][1])
            if clave not in formulas:
                formulas.append(clave)

    recorrer(documento, recoger)
    paquete = RAIZ / ".venvAnalisis/pdf-node/node_modules/mathjax-full"
    resultado = subprocess.run(
        ["node", "-e", MATHJAX, str(paquete)],
        input=json.dumps(formulas), text=True, capture_output=True, check=True,
    )
    imagenes = dict(zip(formulas, json.loads(resultado.stdout), strict=True))

    def convertir(nodo: dict) -> None:
        if nodo.get("t") == "Math":
            bloque = nodo["c"][0]["t"] == "DisplayMath"
            tex = nodo["c"][1]
            svg = imagenes[(bloque, tex)]
            ancho = re.search(r'width="([\d.]+)ex"', svg).group(1)
            alto = re.search(r'height="([\d.]+)ex"', svg).group(1)
            descenso = re.search(r'vertical-align: ([\d.-]+)ex', svg)
            base = descenso.group(1) if descenso else "0"
            datos = base64.b64encode(svg.encode()).decode()
            clase = "formula formula-bloque" if bloque else "formula"
            contenido = (
                f'<span class="{clase}"><img alt="{html.escape(tex)}" '
                f'style="width:{ancho}ex;height:{alto}ex;'
                f'vertical-align:{base}ex" '
                f'src="data:image/svg+xml;base64,{datos}"></span>'
            )
            nodo.update(t="RawInline", c=["html", contenido])
        elif nodo.get("t") == "Link":
            destino = nodo["c"][-1][0]
            if destino.startswith("#"):
                destino = destino.replace("#8-", "#", 1)
                nodo["c"][-1][0] = unicodedata.normalize(
                    "NFKD", destino
                ).encode("ascii", "ignore").decode()
            elif not destino.startswith(("https:", "http:", "#")):
                nodo["c"][-1][0] = REPOSITORIO + destino
        elif nodo.get("t") == "Header":
            nodo["c"][1][0] = unicodedata.normalize(
                "NFKD", nodo["c"][1][0]
            ).encode("ascii", "ignore").decode()
        elif nodo.get("t") == "Image":
            destino = nodo["c"][-1][0]
            if not destino.startswith(("https:", "http:", "data:")):
                ruta = RAIZ / destino
                if not ruta.is_file():
                    raise FileNotFoundError(ruta)
                nodo["c"][-1][0] = ruta.as_uri()
        elif nodo.get("t") == "Table":
            columnas = len(nodo["c"][2])
            nodo["c"][0][1].append(f"columnas-{columnas}")
            for especificacion in nodo["c"][2]:
                especificacion[1] = {"t": "ColWidthDefault"}

    recorrer(documento, convertir)
    cuerpo = pypandoc.convert_text(
        json.dumps(documento), "html5", format="json"
    )
    huella = hashlib.sha256(fuente.read_bytes()).hexdigest()
    pagina = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<title>Banco Regional de Alimentos — Proyecto final</title>'
        '<meta name="author" content="Walter Alexander Pino Vásquez; '
        'Ana María Colorado Varela; Juan David Machado Mosquera; '
        'Franco Moncayo Uribe">'
        f'<meta name="description" content="README SHA-256: {huella}">'
        f'<style>{ESTILO}</style></head><body>{cuerpo}</body></html>'
    )
    salida = RAIZ / "informe.pdf"
    pdf = HTML(string=pagina, base_url=str(RAIZ)).render()
    pdf.write_pdf(salida)
    print(f"PDF: {salida} ({len(pdf.pages)} páginas)")
    print(f"README SHA-256: {huella}; fórmulas distintas: {len(formulas)}")


if __name__ == "__main__":
    main()
