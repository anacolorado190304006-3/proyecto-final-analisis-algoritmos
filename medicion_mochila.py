"""Medicion de la mochila 0/1: tiempo, operaciones y energia."""
import os
import random
import time

import matplotlib.pyplot as plt

from estrategia import cargue_por_vencimiento, mochila_01

SEMILLA = 42
REPETICIONES = 3
POTENCIA_W = 150.0            # consumo del equipo bajo carga (cliente)
DIAS_ANIO = 300
VEHICULOS = 14
CAPACIDAD_FIJA = 4000
TAMANOS = [50, 100, 200, 400, 600, 1000, 2000]
N_FIJO = 400
CAPACIDADES = [500, 1000, 2000, 4000, 8000]
CARPETA = os.path.dirname(os.path.abspath(__file__))
CARPETA_GRAFICAS = os.path.join(CARPETA, "graficas")


def generar_lotes(n: int, semilla: int) -> tuple[list[int], list[int]]:
    """Genera n lotes sinteticos con semilla fija.

    Args:
        n: cantidad de lotes candidatos.
        semilla: semilla del generador.

    Returns:
        Pesos (kg) y valores nutricionales (raciones ponderadas).
    """
    azar = random.Random(semilla)
    pesos = [azar.randint(20, 600) for _ in range(n)]
    valores = [p * azar.randint(2, 12) for p in pesos]
    return pesos, valores


def celdas_evaluadas(pesos: list[int], capacidad: int) -> int:
    """Cuenta las actualizaciones del ciclo interno de la mochila.

    Args:
        pesos: peso de cada lote.
        capacidad: capacidad del vehiculo.

    Returns:
        Numero de celdas (lote, capacidad) que el algoritmo evalua.
    """
    return sum(max(0, capacidad - p + 1) for p in pesos)


def medir(pesos: list[int], valores: list[int], capacidad: int) -> float:
    """Mide el menor tiempo de la mochila entre varias repeticiones.

    Args:
        pesos: peso de cada lote.
        valores: valor de cada lote.
        capacidad: capacidad del vehiculo.

    Returns:
        Tiempo en segundos.
    """
    mejor = float("inf")
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        mochila_01(pesos, valores, capacidad)
        mejor = min(mejor, time.perf_counter() - inicio)
    return mejor


def experimento_n() -> tuple[list[float], list[int]]:
    """Varia n con capacidad fija.

    Returns:
        Tiempos (s) y celdas evaluadas por cada n.
    """
    tiempos: list[float] = []
    celdas: list[int] = []
    for n in TAMANOS:
        pesos, valores = generar_lotes(n, SEMILLA)
        t = medir(pesos, valores, CAPACIDAD_FIJA)
        c = celdas_evaluadas(pesos, CAPACIDAD_FIJA)
        tiempos.append(t)
        celdas.append(c)
        print(f"A) n={n:>5} W={CAPACIDAD_FIJA}  t={t:8.4f} s  "
              f"celdas={c:>9}  ns/celda={t / c * 1e9:6.1f}")
    return tiempos, celdas


def experimento_w() -> tuple[list[float], list[int]]:
    """Varia la capacidad con n fijo.

    Returns:
        Tiempos (s) y celdas evaluadas por cada capacidad.
    """
    pesos, valores = generar_lotes(N_FIJO, SEMILLA)
    tiempos: list[float] = []
    celdas: list[int] = []
    for w in CAPACIDADES:
        t = medir(pesos, valores, w)
        c = celdas_evaluadas(pesos, w)
        tiempos.append(t)
        celdas.append(c)
        print(f"B) n={N_FIJO} W={w:>5}  t={t:8.4f} s  "
              f"celdas={c:>9}  ns/celda={t / c * 1e9:6.1f}")
    return tiempos, celdas


def calidad_flota() -> tuple[float, float, float, float]:
    """Compara mochila y cargue por vencimiento en 14 vehiculos.

    Returns:
        Ocupacion media del cargue actual, ocupacion media de la mochila,
        mejora media de valor (%) y tiempo total de la mochila (s).
    """
    azar = random.Random(SEMILLA)
    ocup_ref: list[float] = []
    ocup_dp: list[float] = []
    mejoras: list[float] = []
    total = 0.0
    for v in range(VEHICULOS):
        n = azar.randint(300, 600)
        capacidad = azar.randint(2500, 4000)
        pesos, valores = generar_lotes(n, 1000 + v)
        inicio = time.perf_counter()
        v_dp, idx_dp = mochila_01(pesos, valores, capacidad)
        total += time.perf_counter() - inicio
        v_ref, idx_ref = cargue_por_vencimiento(pesos, valores, capacidad)
        ocup_dp.append(sum(pesos[i] for i in idx_dp) / capacidad)
        ocup_ref.append(sum(pesos[i] for i in idx_ref) / capacidad)
        mejoras.append((v_dp - v_ref) / v_ref * 100 if v_ref else 0.0)
    media = len(mejoras)
    return (sum(ocup_ref) / media * 100, sum(ocup_dp) / media * 100,
            sum(mejoras) / media, total)


def graficar(
    x: list[int], tiempos: list[float], etiqueta_x: str,
    titulo: str, nombre: str, curva: str,
) -> None:
    """Guarda una grafica tiempo vs. parametro.

    Args:
        x: valores del eje X.
        tiempos: tiempos en segundos.
        etiqueta_x: rotulo del eje X.
        titulo: titulo de la grafica.
        nombre: nombre del archivo PNG.
        curva: texto de la leyenda.
    """
    os.makedirs(CARPETA_GRAFICAS, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(x, tiempos, marker="o", label=curva)
    ax.set_title(titulo)
    ax.set_xlabel(etiqueta_x)
    ax.set_ylabel("Tiempo de ejecución (segundos)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA_GRAFICAS, nombre), dpi=150)
    plt.close(fig)


def energia_wh(segundos: float) -> float:
    """Convierte un tiempo en energia consumida (Wh) a 150 W.

    Args:
        segundos: tiempo de ejecucion.

    Returns:
        Energia en vatios-hora.
    """
    return POTENCIA_W * segundos / 3600


if __name__ == "__main__":
    t_n, c_n = experimento_n()
    t_w, c_w = experimento_w()
    graficar(TAMANOS, t_n, "Número de lotes candidatos n (lotes)",
             "Mochila 0/1: tiempo vs. n (W = 4000 kg)",
             "mochila_tiempo_vs_n.png", "Programación dinámica  Θ(n·W)")
    graficar(CAPACIDADES, t_w, "Capacidad del vehículo W (kg)",
             "Mochila 0/1: tiempo vs. capacidad (n = 400 lotes)",
             "mochila_tiempo_vs_w.png", "Programación dinámica  Θ(n·W)")

    # Constante por celda, tomada del punto mayor de cada experimento.
    c_celda = t_n[-1] / c_n[-1]
    print(f"\nConstante (n=2000): {c_celda * 1e9:.1f} ns por celda")
    celdas_real = 600 * 4000          # peor caso por vehiculo
    t_veh = c_celda * celdas_real
    t_dia = t_veh * VEHICULOS
    print(f"Estimado por vehiculo (600 lotes, 4000 kg): {t_veh:.2f} s")
    print(f"Estimado por dia (14 vehiculos): {t_dia:.1f} s")
    print(f"Energia diaria: {energia_wh(t_dia):.3f} Wh  | "
          f"anual (300 dias): {energia_wh(t_dia) * DIAS_ANIO / 1000:.3f} kWh")
    print(f"Segunda bodega (28 vehiculos): {2 * t_dia:.1f} s por dia")

    o_ref, o_dp, mejora, t_flota = calidad_flota()
    print(f"\nCalidad (14 vehiculos sinteticos): ocupacion actual "
          f"{o_ref:.1f}% | mochila {o_dp:.1f}% | mejora de valor "
          f"{mejora:.1f}% | tiempo flota {t_flota:.2f} s")
