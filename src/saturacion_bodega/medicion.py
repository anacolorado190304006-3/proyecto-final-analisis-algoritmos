"""Mediciones de saturación: exhaustiva, dividir y vencer y Kadane."""

import argparse
import json
import platform
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from datos import SEMILLA_BASE, generar_historico, generar_serie  # noqa: E402
from estrategia import tramo_maximo_dividir, tramo_maximo_kadane  # noqa: E402
from exhaustivo import tramo_maximo_exhaustivo  # noqa: E402

REPETICIONES = 5
POTENCIA_W = 150.0
DIAS_ANIO = 300
HORAS_REALES = 36000
TAMANOS_EXHAUSTIVO = [250, 500, 1000, 2000, 4000]
TAMANOS_RAPIDOS = [1000, 2250, 4500, 9000, 18000, 36000]
CARPETA = Path(__file__).resolve().parents[2] / "graficas/saturacion_bodega"
ARCHIVO_JSON = CARPETA / "resultados.json"
ARCHIVO_GRAFICA = CARPETA / "tiempo_vs_n.png"

Estrategia = Callable[[list[int]], tuple[int, int, int]]
ESTRATEGIAS: dict[str, Estrategia] = {
    "exhaustiva": tramo_maximo_exhaustivo,
    "dividir": tramo_maximo_dividir,
    "kadane": tramo_maximo_kadane,
}


def medir(funcion: Estrategia, serie: list[int]) -> list[float]:
    """Devuelve los tiempos (s) de las repeticiones de una estrategia."""
    funcion(serie)  # calentamiento
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        funcion(serie)
        tiempos.append(time.perf_counter() - inicio)
    return tiempos


def ejecutar() -> dict:
    """Mide todas las estrategias y valida que coincidan en la suma."""
    resultados: dict = {"series": {}, "categorias_reales": {}}
    for nombre, tamanos in (
        ("exhaustiva", TAMANOS_EXHAUSTIVO),
        ("dividir", TAMANOS_RAPIDOS),
        ("kadane", TAMANOS_RAPIDOS),
    ):
        filas = []
        for n in tamanos:
            serie = generar_serie(n, SEMILLA_BASE)
            esperado = tramo_maximo_kadane(serie)[0]
            if ESTRATEGIAS[nombre](serie)[0] != esperado:
                raise AssertionError(f"{nombre} difiere con n={n}")
            tiempos = medir(ESTRATEGIAS[nombre], serie)
            filas.append({"n": n, "media_s": statistics.mean(tiempos),
                          "tiempos_s": tiempos})
            print(f"{nombre:10s} n={n:6d} {statistics.mean(tiempos):.6f} s")
        resultados["series"][nombre] = filas

    historico = list(generar_historico(HORAS_REALES).values())
    for nombre in ("dividir", "kadane"):
        inicio = time.perf_counter()
        sumas = [ESTRATEGIAS[nombre](serie)[0] for serie in historico]
        total = time.perf_counter() - inicio
        resultados["categorias_reales"][nombre] = {
            "tiempo_total_s": total, "sumas": sumas}
        print(f"{nombre:10s} 40 x 36000: {total:.4f} s")
    if (resultados["categorias_reales"]["dividir"]["sumas"]
            != resultados["categorias_reales"]["kadane"]["sumas"]):
        raise AssertionError("Las sumas de las 40 categorias difieren")

    resultados["entorno"] = {"python": sys.version.split()[0],
                             "sistema": platform.platform()}
    CARPETA.mkdir(parents=True, exist_ok=True)
    ARCHIVO_JSON.write_text(json.dumps(resultados, indent=2),
                            encoding="utf-8")
    return resultados


def graficar(resultados: dict) -> None:
    """Dibuja tiempo frente a n en escala logarítmica."""
    figura, eje = plt.subplots(figsize=(7, 4.5))
    etiquetas = {"exhaustiva": "Exhaustiva", "dividir": "Dividir y vencer",
                 "kadane": "Kadane"}
    for nombre, filas in resultados["series"].items():
        eje.plot([f["n"] for f in filas], [f["media_s"] for f in filas],
                 marker="o", label=etiquetas[nombre])
    eje.set_xscale("log")
    eje.set_yscale("log")
    eje.set_xlabel("Horas por categoría (n)")
    eje.set_ylabel("Tiempo medio (s)")
    eje.set_title("Saturación: tiempo frente a n")
    eje.grid(True, which="both", alpha=0.3)
    eje.legend()
    figura.tight_layout()
    CARPETA.mkdir(parents=True, exist_ok=True)
    figura.savefig(ARCHIVO_GRAFICA, dpi=150)
    plt.close(figura)


def main() -> None:
    """Punto de entrada."""
    analizador = argparse.ArgumentParser()
    analizador.add_argument("--solo-graficas", action="store_true")
    argumentos = analizador.parse_args()
    if argumentos.solo_graficas:
        resultados = json.loads(ARCHIVO_JSON.read_text(encoding="utf-8"))
    else:
        resultados = ejecutar()
    graficar(resultados)
    print(f"Gráfica en {ARCHIVO_GRAFICA}")


if __name__ == "__main__":
    main()
