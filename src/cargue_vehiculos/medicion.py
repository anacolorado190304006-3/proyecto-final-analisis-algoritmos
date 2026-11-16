"""Mediciones, conteo de operaciones, gráficas y extrapolación energética.

Integrante 4 — Mediciones, gráficas e integración [Experimentos].
Módulo de experimentos para la Operación 3: Cargue de vehículos (Caso 3).
"""
import os
import random
import time
from itertools import combinations
import matplotlib.pyplot as plt

from estrategia import cargue_por_vencimiento, mochila_01

# Parámetros del caso del cliente
SEMILLA = 42
REPETICIONES = 3
POTENCIA_W = 150.0  # Consumo sostenido del servidor del cliente (W)
DIAS_ANIO = 300
VEHICULOS = 14
CAPACIDAD_FIJA = 4000  # Capacidad máxima típica de un camión (kg)
TAMANOS_GRANDES = [50, 100, 200, 400, 600, 1000, 2000]
N_FIJO = 400
CAPACIDADES = [500, 1000, 2000, 4000, 8000]

# Tamaños donde la solución exhaustiva (fuerza bruta) puede correr en segundos
TAMANOS_EXHAUSTIVO = [4, 6, 8, 10, 12, 14, 16, 18]

CARPETA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_GRAFICAS = os.path.abspath(
    os.path.join(CARPETA_ACTUAL, "..", "..", "graficas", "cargue_vehiculos")
)


def generar_lotes(n: int, semilla: int = SEMILLA) -> tuple[list[int], list[int]]:
    """Genera n lotes candidatos sintéticos con semilla fija.

    Args:
        n: Cantidad de lotes candidatos.
        semilla: Semilla fija para reproducibilidad.

    Returns:
        Tupla con las listas de pesos (kg) y valores nutricionales (raciones).
    """
    azar = random.Random(semilla)
    pesos = [azar.randint(20, 600) for _ in range(n)]
    valores = [p * azar.randint(2, 12) for p in pesos]
    return pesos, valores


def fuerza_bruta(
    pesos: list[int], valores: list[int], capacidad: int
) -> tuple[int, list[int]]:
    """Solución exhaustiva que prueba todas las combinaciones 2^n.

    Args:
        pesos: Peso de cada lote.
        valores: Valor de cada lote.
        capacidad: Capacidad máxima del vehículo.

    Returns:
        Tupla (mejor_valor, indices_elegidos).
    """
    n = len(pesos)
    mejor_valor = 0
    mejores_indices: list[int] = []
    for r in range(n + 1):
        for combo in combinations(range(n), r):
            peso_actual = sum(pesos[i] for i in combo)
            if peso_actual <= capacidad:
                valor_actual = sum(valores[i] for i in combo)
                if valor_actual > mejor_valor:
                    mejor_valor = valor_actual
                    mejores_indices = list(combo)
    return mejor_valor, mejores_indices


# ==============================================================================
# CONTEO DE OPERACIONES ELEMENTALES
# ==============================================================================

def celdas_evaluadas_mochila(pesos: list[int], capacidad: int) -> int:
    """Cuenta el número de celdas de la tabla evaluadas por la mochila 0/1.

    Fórmula: sum(max(0, capacidad - peso_i + 1) for peso_i in pesos).
    Complejidad: Theta(n * W).
    """
    return sum(max(0, capacidad - p + 1) for p in pesos)


def operaciones_fuerza_bruta(n: int) -> int:
    """Calcula el número de combinaciones de subconjuntos evaluados.

    Fórmula: 2^n combinaciones. Complejidad: Theta(2^n).
    """
    return 2**n


def operaciones_vencimiento(pesos: list[int], capacidad: int) -> int:
    """Cuenta las comparaciones lineales realizadas por el cargue por vencimiento.

    Se detiene en el primer lote que no cabe.
    """
    peso_acumulado = 0
    ops = 0
    for p in pesos:
        ops += 1
        if peso_acumulado + p <= capacidad:
            peso_acumulado += p
        else:
            break
    return ops


# ==============================================================================
# MEDICIONES DE TIEMPO
# ==============================================================================

def cronometrar(funcion, *args, repeticiones: int = REPETICIONES) -> float:
    """Mide el menor tiempo de ejecución en segundos tras varias repeticiones."""
    mejor = float("inf")
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion(*args)
        mejor = min(mejor, time.perf_counter() - inicio)
    return mejor


def experimento_tres_soluciones() -> tuple[list[int], list[float], list[float], list[float], list[int], list[int], list[int]]:
    """Mide tiempo y operaciones de las tres soluciones para n pequeño."""
    tiempos_fb: list[float] = []
    tiempos_dp: list[float] = []
    tiempos_venc: list[float] = []

    ops_fb: list[int] = []
    ops_dp: list[int] = []
    ops_venc: list[int] = []

    w_pequeno = 1000
    for n in TAMANOS_EXHAUSTIVO:
        pesos, valores = generar_lotes(n, SEMILLA + n)

        t_fb = cronometrar(fuerza_bruta, pesos, valores, w_pequeno, repeticiones=2)
        t_dp = cronometrar(mochila_01, pesos, valores, w_pequeno, repeticiones=3)
        t_venc = cronometrar(cargue_por_vencimiento, pesos, valores, w_pequeno, repeticiones=5)

        tiempos_fb.append(t_fb)
        tiempos_dp.append(t_dp)
        tiempos_venc.append(t_venc)

        ops_fb.append(operaciones_fuerza_bruta(n))
        ops_dp.append(celdas_evaluadas_mochila(pesos, w_pequeno))
        ops_venc.append(operaciones_vencimiento(pesos, w_pequeno))

        print(
            f"Comparativa 3 soluciones | n={n:2d} | "
            f"Exhaustivo: {t_fb*1000:9.3f} ms ({ops_fb[-1]:7,d} ops) | "
            f"Mochila DP: {t_dp*1000:7.3f} ms ({ops_dp[-1]:6,d} celdas) | "
            f"Vencimiento: {t_venc*1000:6.4f} ms ({ops_venc[-1]:2d} ops)"
        )

    return (
        TAMANOS_EXHAUSTIVO,
        tiempos_fb,
        tiempos_dp,
        tiempos_venc,
        ops_fb,
        ops_dp,
        ops_venc,
    )


def experimento_n_escalabilidad() -> tuple[list[int], list[float], list[float], list[int]]:
    """Mide la escalabilidad de Mochila DP y Vencimiento para n grande (hasta 2.000)."""
    tiempos_dp: list[float] = []
    tiempos_venc: list[float] = []
    celdas_dp: list[int] = []

    for n in TAMANOS_GRANDES:
        pesos, valores = generar_lotes(n, SEMILLA)
        t_dp = cronometrar(mochila_01, pesos, valores, CAPACIDAD_FIJA)
        t_venc = cronometrar(cargue_por_vencimiento, pesos, valores, CAPACIDAD_FIJA)
        c = celdas_evaluadas_mochila(pesos, CAPACIDAD_FIJA)

        tiempos_dp.append(t_dp)
        tiempos_venc.append(t_venc)
        celdas_dp.append(c)

        print(
            f"Escalabilidad | n={n:5d} W={CAPACIDAD_FIJA} | "
            f"t_dp={t_dp:7.4f} s | celdas={c:9,d} | "
            f"ns/celda={t_dp / c * 1e9:5.1f} ns | t_venc={t_venc*1e6:6.1f} us"
        )
    return TAMANOS_GRANDES, tiempos_dp, tiempos_venc, celdas_dp


def experimento_capacidad() -> tuple[list[int], list[float], list[int]]:
    """Mide con número de lotes fijo (n=400) y capacidad creciente W."""
    pesos, valores = generar_lotes(N_FIJO, SEMILLA)
    tiempos: list[float] = []
    celdas: list[int] = []

    for w in CAPACIDADES:
        t = cronometrar(mochila_01, pesos, valores, w)
        c = celdas_evaluadas_mochila(pesos, w)
        tiempos.append(t)
        celdas.append(c)
        print(f"Capacidad W | n={N_FIJO} W={w:5d} kg | t={t:7.4f} s | celdas={c:9,d} | ns/celda={t / c * 1e9:5.1f} ns")

    return CAPACIDADES, tiempos, celdas


# ==============================================================================
# GENERACIÓN DE LAS TRES GRÁFICAS EXIGIDAS
# ==============================================================================

def generar_grafica_tiempo_vs_n(
    n_peq: list[int], t_fb: list[float], t_dp_peq: list[float], t_venc_peq: list[float]
) -> None:
    """Genera tiempo_vs_n.png con las tres soluciones en los mismos ejes."""
    os.makedirs(CARPETA_GRAFICAS, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.plot(n_peq, [t * 1000 for t in t_fb], "ro-", label="Exhaustivo / Fuerza Bruta $\\Theta(n \\cdot 2^n)$", linewidth=2)
    ax.plot(n_peq, [t * 1000 for t in t_dp_peq], "bs-", label="Mochila 0/1 (Prog. Dinámica) $\\Theta(n \\cdot W)$", linewidth=2)
    ax.plot(n_peq, [t * 1000 for t in t_venc_peq], "g^-", label="Cargue actual por vencimiento $\\Theta(n)$", linewidth=2)

    ax.set_title("Operación 3: Tiempo de ejecución vs. Número de lotes candidatos ($n$)")
    ax.set_xlabel("Número de lotes candidatos ($n$)")
    ax.set_ylabel("Tiempo de ejecución (milisegundos)")
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend()
    fig.tight_layout()

    ruta = os.path.join(CARPETA_GRAFICAS, "tiempo_vs_n.png")
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print(f"Gráfica 1 guardada: {ruta}")


def generar_grafica_operaciones_vs_n(
    n_peq: list[int], ops_fb: list[int], ops_dp: list[int], ops_venc: list[int]
) -> None:
    """Genera operaciones_vs_n.png con el conteo de operaciones elementales."""
    os.makedirs(CARPETA_GRAFICAS, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.plot(n_peq, ops_fb, "ro-", label="Exhaustivo: Subconjuntos evaluados $2^n$", linewidth=2)
    ax.plot(n_peq, ops_dp, "bs-", label="Mochila 0/1: Celdas evaluadas $\\Theta(n \\cdot W)$", linewidth=2)
    ax.plot(n_peq, ops_venc, "g^-", label="Vencimiento: Comparaciones lineales $\\Theta(n)$", linewidth=2)

    ax.set_title("Operación 3: Operaciones elementales vs. Número de lotes ($n$)")
    ax.set_xlabel("Número de lotes candidatos ($n$)")
    ax.set_ylabel("Número de operaciones / celdas evaluadas")
    ax.set_yscale("log")  # Escala logarítmica para apreciar la brecha exponencial
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend()
    fig.tight_layout()

    ruta = os.path.join(CARPETA_GRAFICAS, "operaciones_vs_n.png")
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print(f"Gráfica 2 guardada: {ruta}")


def generar_grafica_tiempo_vs_capacidad(capacidades: list[int], tiempos: list[float]) -> None:
    """Genera tiempo_vs_capacidad.png con n=400 fijo y W creciente."""
    os.makedirs(CARPETA_GRAFICAS, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.plot(capacidades, tiempos, "bo-", label="Mochila 0/1 (Prog. Dinámica) $\\Theta(n \\cdot W)$", linewidth=2)

    ax.set_title("Operación 3: Tiempo vs. Capacidad del vehículo $W$ ($n = 400$ lotes fijos)")
    ax.set_xlabel("Capacidad del vehículo $W$ (kilogramos)")
    ax.set_ylabel("Tiempo de ejecución (segundos)")
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend()
    fig.tight_layout()

    ruta = os.path.join(CARPETA_GRAFICAS, "tiempo_vs_capacidad.png")
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print(f"Gráfica 3 guardada: {ruta}")


# ==============================================================================
# EXTRAPOLACIÓN DE TIEMPO Y ENERGÍA
# ==============================================================================

def calcular_extrapolacion_energia(ns_por_celda: float) -> dict[str, float]:
    """Calcula las extrapolaciones de tiempo y energía en el volumen real."""
    celdas_por_vehiculo = 600 * 4000  # Peor caso: 600 lotes y 4.000 kg
    segundos_por_vehiculo = (celdas_por_vehiculo * ns_por_celda) / 1e9
    segundos_diarios = segundos_por_vehiculo * VEHICULOS
    energia_wh_dia = POTENCIA_W * (segundos_diarios / 3600)
    energia_kwh_anual = (energia_wh_dia * DIAS_ANIO) / 1000
    segundos_2da_bodega = segundos_diarios * 2

    return {
        "segundos_vehiculo": segundos_por_vehiculo,
        "segundos_diarios": segundos_diarios,
        "energia_wh_dia": energia_wh_dia,
        "energia_kwh_anual": energia_kwh_anual,
        "segundos_2da_bodega": segundos_2da_bodega,
    }


def ejecutar_experimentos() -> None:
    """Función principal que ejecuta todos los experimentos del Integrante 4."""
    print("=== INTEGRANTE 4: EXPERIMENTOS DE MEDICIÓN, OPERACIONES Y ENERGÍA ===")
    print("\n--- 1. Experimento: Medición de las tres soluciones (tiempo y operaciones) ---")
    n_peq, t_fb, t_dp_peq, t_venc_peq, ops_fb, ops_dp, ops_venc = experimento_tres_soluciones()

    print("\n--- 2. Experimento: Escalabilidad de n grande (Mochila DP) ---")
    n_g, t_dp_g, t_venc_g, celdas_g = experimento_n_escalabilidad()

    print("\n--- 3. Experimento: Medición con n fijo (400) y capacidad W creciente ---")
    caps, t_caps, celdas_caps = experimento_capacidad()

    print("\n--- 4. Generando las tres gráficas exigidas ---")
    generar_grafica_tiempo_vs_n(n_peq, t_fb, t_dp_peq, t_venc_peq)
    generar_grafica_operaciones_vs_n(n_peq, ops_fb, ops_dp, ops_venc)
    generar_grafica_tiempo_vs_capacidad(caps, t_caps)

    print("\n--- 5. Extrapolación de tiempo y consumo de energía ---")
    ns_por_celda = (t_dp_g[-1] / celdas_g[-1]) * 1e9
    extrap = calcular_extrapolacion_energia(ns_por_celda)
    print(f"Constante empírica (n=2000): {ns_por_celda:.1f} ns por celda")
    print(f"Tiempo estimado por vehículo (600 lotes, 4.000 kg): {extrap['segundos_vehiculo']:.3f} s")
    print(f"Tiempo diario para la flota (14 vehículos): {extrap['segundos_diarios']:.2f} s")
    print(f"Consumo de energía diario (150 W): {extrap['energia_wh_dia']:.4f} Wh")
    print(f"Consumo de energía anual (300 días): {extrap['energia_kwh_anual']:.5f} kWh")
    print(f"Escenario de 2da bodega (28 vehículos): {extrap['segundos_2da_bodega']:.2f} s")


if __name__ == "__main__":
    ejecutar_experimentos()
