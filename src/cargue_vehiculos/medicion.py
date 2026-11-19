"""Experimentos reproducibles de cargue: tiempos medios, conteos y energía."""

import argparse
import hashlib
import inspect
import json
import math
import platform
import statistics
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from types import FrameType
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from datos import a_tuplas, generar_inventario, generar_ruta
from estrategia import cargar_vehiculo, mochila_01
from exhaustivo import Lote, cargar_exhaustivo
from pruebas import verificar_cargue
from regla_actual import cargar_por_densidad, cargar_por_vencimiento

SEMILLA = 42
REPETICIONES = 5
POTENCIA_W = 150.0
DIAS_ANIO = 300
VEHICULOS = 14
CAPACIDAD_FIJA = 4000
TAMANOS_GRANDES = [50, 100, 200, 400, 600, 1000, 2000]
TAMANOS_EXHAUSTIVO = [4, 6, 8, 10, 12, 14, 16, 18]
N_FIJO = 400
CAPACIDADES = [500, 1000, 2000, 4000, 8000]
CARPETA_GRAFICAS = Path(__file__).resolve().parents[2] / (
    "graficas/cargue_vehiculos"
)
ARCHIVO_RESULTADOS = CARPETA_GRAFICAS / "resultados.json"

Algoritmo = Callable[[list[Lote], int], tuple[int, list[int]]]
ALGORITMOS: dict[str, Algoritmo] = {
    "DP": cargar_vehiculo,
    "Exhaustiva": cargar_exhaustivo,
    "Vencimiento": cargar_por_vencimiento,
    "Densidad": cargar_por_densidad,
}
# Se cuentan ejecuciones reales de una operación identificable de cada función.
OPERACIONES = {
    "DP": (mochila_01, "candidato = mejor[w - peso] + valor"),
    "Exhaustiva": (cargar_exhaustivo, "peso_total = sum("),
    "Vencimiento": (cargar_por_vencimiento,
                   "if peso_total + peso > capacidad_kg:"),
    "Densidad": (cargar_por_densidad,
                 "if peso_total + peso > capacidad_kg:"),
}
NOMBRES_RAPIDOS = ("DP", "Vencimiento", "Densidad")


def contar_operaciones(
    nombre: str, lotes: list[Lote], capacidad: int
) -> int:
    """Cuenta celdas, subconjuntos o comparaciones en una ejecución aparte.

    La traza no participa en el cronometraje. Los conteos no incluyen todas
    las operaciones: en las reglas se cuentan comparaciones de capacidad,
    no las comparaciones internas de sorted ni la validación.

    Args:
        nombre: Clave del algoritmo.
        lotes: Candidatos elegibles.
        capacidad: Capacidad en kg.

    Returns:
        Número de ejecuciones de la línea observada.

    Raises:
        ValueError: Si cambió el código observado o la exhaustiva es grande.
    """
    if nombre == "Exhaustiva" and len(lotes) > 18:
        raise ValueError("El experimento exhaustivo admite hasta 18 lotes.")
    funcion, fragmento = OPERACIONES[nombre]
    fuente, inicio = inspect.getsourcelines(funcion)
    lineas = [
        inicio + i for i, linea in enumerate(fuente)
        if fragmento in linea
    ]
    if len(lineas) != 1:
        raise ValueError("Revisar la operación observada tras cambiar código.")
    contador = 0

    def traza(frame: FrameType, evento: str, arg: Any) -> Any:
        """Incrementa el contador al ejecutar la línea del algoritmo.

        Args:
            frame: Marco de ejecución.
            evento: Evento emitido por el intérprete.
            arg: Información adicional del evento.

        Returns:
            La traza local para la función observada, o None.
        """
        nonlocal contador
        if frame.f_code is funcion.__code__:
            if evento == "line" and frame.f_lineno == lineas[0]:
                contador += 1
            return traza
        return None

    anterior = sys.gettrace()
    try:
        sys.settrace(traza)
        ALGORITMOS[nombre](lotes, capacidad)
    finally:
        sys.settrace(anterior)
    if nombre == "DP":
        assert contador == sum(max(0, capacidad - p + 1) for p, _, _ in lotes)
    elif nombre == "Exhaustiva":
        assert contador == 2 ** len(lotes)
    else:
        assert 0 <= contador <= len(lotes)
    return contador


def cronometrar(
    funcion: Algoritmo, lotes: list[Lote], capacidad: int
) -> list[float]:
    """Mide cinco ejecuciones sin generación, validación externa ni traza.

    Args:
        funcion: Solución que recibe lotes y capacidad.
        lotes: Misma instancia para todas las soluciones.
        capacidad: Capacidad en kg.

    Returns:
        Tiempos individuales en segundos; se publica su media aritmética.
    """
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        funcion(lotes, capacidad)
        tiempos.append(time.perf_counter() - inicio)
    return tiempos


def medir_instancia(
    n: int, capacidad: int, nombres: tuple[str, ...], semilla: int = SEMILLA
) -> dict[str, Any]:
    """Genera, valida y mide una instancia común a las estrategias.

    Args:
        n: Cantidad de candidatos.
        capacidad: Capacidad en kg.
        nombres: Estrategias incluidas.
        semilla: Semilla del generador de datos.

    Returns:
        Datos de reproducción, tiempos, conteos y selecciones comprobadas.

    Raises:
        ValueError: Si se solicita exhaustiva con más de 18 lotes.
        AssertionError: Si las salidas incumplen las restricciones.
    """
    if "Exhaustiva" in nombres and n > 18:
        raise ValueError("No ejecutar exhaustiva en instancias grandes.")
    registros = generar_inventario(n, semilla, incluir_vencidos=False)
    lotes = a_tuplas(registros)
    copia = list(lotes)
    salidas = {}
    for nombre in nombres:
        salidas[nombre] = ALGORITMOS[nombre](lotes, capacidad)
        verificar_cargue(lotes, capacidad, salidas[nombre], nombre)
        assert lotes == copia
    if "Exhaustiva" in nombres:
        assert salidas["DP"][0] == salidas["Exhaustiva"][0]
    for nombre in nombres:
        assert salidas[nombre][0] <= salidas["DP"][0]

    resultados = {}
    for nombre in nombres:
        tiempos = cronometrar(ALGORITMOS[nombre], lotes, capacidad)
        assert lotes == copia
        valor, indices = salidas[nombre]
        resultados[nombre] = {
            "tiempos_s": tiempos,
            "media_s": statistics.mean(tiempos),
            "operaciones": contar_operaciones(nombre, lotes, capacidad),
            "valor": valor,
            "peso_kg": sum(lotes[i][0] for i in indices),
            "indices": indices,
        }
    huella = hashlib.sha256(json.dumps(lotes).encode()).hexdigest()
    print(f"Validado y medido: n={n}, W={capacidad}", flush=True)
    return {
        "n": n, "capacidad_kg": capacidad, "semilla": semilla,
        "sha256_lotes": huella, "resultados": resultados,
    }


def extrapolar(
    pequenas: list[dict[str, Any]], grandes: list[dict[str, Any]]
) -> dict[str, Any]:
    """Extrapola a 14 rutas de 600 lotes y capacidad de 4000 kg.

    Se calibra DP con nW, las reglas con n log2(n) y la exhaustiva con
    n * 2**n. Son modelos, no ejecuciones ni mediciones eléctricas.
    La potencia de 150 W se supone constante durante el cómputo.

    Args:
        pequenas: Mediciones con exhaustiva.
        grandes: Mediciones de DP y reglas a mayor escala.

    Returns:
        Tiempos, energía y diferencia anual DP menos vencimiento.
    """
    salida = {}
    for nombre in ALGORITMOS:
        referencia = pequenas[-1] if nombre == "Exhaustiva" else grandes[-1]
        n = referencia["n"]
        w = referencia["capacidad_kg"]
        t = referencia["resultados"][nombre]["media_s"]
        if nombre == "DP":
            factor = (600 * 4000) / (n * w)
        elif nombre == "Exhaustiva":
            factor = (600 / n) * 2.0 ** (600 - n)
        else:
            factor = (600 * math.log2(600)) / (n * math.log2(n))
        segundos = t * factor
        flota = segundos * VEHICULOS
        diario = (POTENCIA_W / 1000) * (flota / 3600)
        salida[nombre] = {
            "referencia_n": n, "referencia_W": w, "referencia_s": t,
            "factor": factor, "segundos_vehiculo": segundos,
            "segundos_flota": flota, "kwh_dia": diario,
            "kwh_anual": diario * DIAS_ANIO,
        }
    salida["diferencia_anual_dp_menos_vencimiento"] = (
        salida["DP"]["kwh_anual"] - salida["Vencimiento"]["kwh_anual"]
    )
    return salida


def evaluar_flota() -> list[dict[str, Any]]:
    """Compara el valor y la ocupación en catorce rutas sintéticas.

    Returns:
        Semillas, capacidades, lotes y resultados por ruta; no mide tiempos.
    """
    rutas = []
    for numero in range(VEHICULOS):
        semilla = SEMILLA + 100 + numero
        registros, capacidad = generar_ruta(semilla)
        lotes = a_tuplas(registros)
        copia = list(lotes)
        resultados = {}
        for nombre in NOMBRES_RAPIDOS:
            valor, indices = ALGORITMOS[nombre](lotes, capacidad)
            verificar_cargue(lotes, capacidad, (valor, indices), nombre)
            assert lotes == copia
            resultados[nombre] = {
                "valor": valor, "indices": indices,
                "peso_kg": sum(lotes[i][0] for i in indices),
            }
        assert all(
            r["valor"] <= resultados["DP"]["valor"]
            for r in resultados.values()
        )
        rutas.append({
            "ruta": numero, "semilla": semilla, "n": len(lotes),
            "capacidad_kg": capacidad, "resultados": resultados,
        })
    return rutas


def generar_graficas(datos: dict[str, Any]) -> None:
    """Dibuja las tres gráficas a partir del mismo registro de resultados.

    Args:
        datos: Resultado guardado por ejecutar_experimentos.
    """
    CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
    estilos = {
        "DP": "bs-", "Exhaustiva": "ro-",
        "Vencimiento": "g^-", "Densidad": "md-",
    }
    fig, ejes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, clave, titulo in zip(
        ejes, ("pequenas", "grandes"),
        ("Instancias pequeñas: W = 1000 kg", "Escalabilidad: W = 4000 kg"),
    ):
        filas = datos[clave]
        for nombre in filas[0]["resultados"]:
            ax.plot(
                [r["n"] for r in filas],
                [r["resultados"][nombre]["media_s"] * 1000 for r in filas],
                estilos[nombre], label=nombre,
            )
        ax.set(xlabel="Número de lotes (n)", ylabel="Tiempo medio (ms)",
               title=titulo, yscale="log")
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.suptitle("Cargue de vehículos: tiempo de las funciones completas")
    fig.tight_layout()
    fig.savefig(CARPETA_GRAFICAS / "tiempo_vs_n.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    unidades = {
        "DP": "celdas", "Exhaustiva": "subconjuntos",
        "Vencimiento": "comparaciones de capacidad",
        "Densidad": "comparaciones de capacidad",
    }
    for nombre in ALGORITMOS:
        filas = datos["pequenas"]
        ax.plot(
            [r["n"] for r in filas],
            [r["resultados"][nombre]["operaciones"] for r in filas],
            estilos[nombre], label=f"{nombre}: {unidades[nombre]}",
        )
    ax.set(xlabel="Número de lotes (n)", ylabel="Conteo (escala logarítmica)",
           title="Cargue: celdas, subconjuntos y comparaciones; W = 1000 kg",
           yscale="log")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CARPETA_GRAFICAS / "operaciones_vs_n.png", dpi=150)
    plt.close(fig)

    filas = datos["capacidades"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        [r["capacidad_kg"] for r in filas],
        [r["resultados"]["DP"]["media_s"] for r in filas],
        "bo-", label="DP: cargar_vehiculo",
    )
    ax.set(xlabel="Capacidad del vehículo W (kg)",
           ylabel="Tiempo medio (s)",
           title="Cargue: tiempo frente a capacidad, n = 400 lotes")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CARPETA_GRAFICAS / "tiempo_vs_capacidad.png", dpi=150)
    plt.close(fig)


def ejecutar_experimentos() -> dict[str, Any]:
    """Mide, guarda evidencia y genera las gráficas.

    Returns:
        Registro completo de experimentos y proyecciones.
    """
    if not __debug__:
        raise RuntimeError("Ejecutar sin -O para conservar los assert.")
    datos = {
        "entorno": {
            "fecha_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "plataforma": platform.platform(),
            "procesador": platform.processor(),
            "repeticiones": REPETICIONES,
            "estadistico": "media aritmetica",
            "potencia_w": POTENCIA_W, "dias_anio": DIAS_ANIO,
            "vehiculos": VEHICULOS, "semilla": SEMILLA,
        },
        "pequenas": [
            medir_instancia(n, 1000, tuple(ALGORITMOS))
            for n in TAMANOS_EXHAUSTIVO
        ],
        "grandes": [
            medir_instancia(n, CAPACIDAD_FIJA, NOMBRES_RAPIDOS)
            for n in TAMANOS_GRANDES
        ],
        "capacidades": [
            medir_instancia(N_FIJO, w, ("DP",)) for w in CAPACIDADES
        ],
        "flota": evaluar_flota(),
    }
    datos["extrapolacion"] = extrapolar(datos["pequenas"], datos["grandes"])
    CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
    ARCHIVO_RESULTADOS.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    generar_graficas(datos)
    print(f"Evidencia: {ARCHIVO_RESULTADOS}")
    print(json.dumps(datos["extrapolacion"], ensure_ascii=False, indent=2))
    return datos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--solo-graficas", action="store_true",
        help="Regenerar PNG desde resultados.json, sin volver a medir.",
    )
    argumentos = parser.parse_args()
    if argumentos.solo_graficas:
        generar_graficas(json.loads(ARCHIVO_RESULTADOS.read_text("utf-8")))
    else:
        ejecutar_experimentos()
