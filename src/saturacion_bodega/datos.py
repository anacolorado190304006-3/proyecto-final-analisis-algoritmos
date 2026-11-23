"""Datos sintéticos para el análisis de saturación de la bodega (Caso 3).

Operación 4 del Banco Regional de Alimentos: para cada categoría se registra,
por cada hora de operación, el cambio neto del inventario en kilogramos (lo
que entró menos lo que salió o se descartó; puede ser negativo). Se busca el
tramo de horas consecutivas con mayor crecimiento acumulado.

Volumen del caso: 40 categorías, 12 horas diarias, 300 días al año y diez
años de histórico, es decir, 36.000 registros horarios por categoría.

Modelo sintético de cada hora (supuestos del equipo, en kg):

* Patrón diario: en la mañana predominan las entradas de donaciones y en la
  tarde las salidas por despacho; su promedio diario es cero.
* Temporada: en los últimos 50 días operativos de cada año (noviembre y
  diciembre) las donaciones aumentan. Es la saturación que debe detectarse.
* Sesgo negativo fuera de temporada, mayor que lo que suma la temporada,
  para que el saldo de cada año sea negativo. Así el tramo máximo queda
  dentro de una temporada y no es, trivialmente, toda la serie.
* Ruido gaussiano, donaciones grandes ocasionales (picos positivos) y
  descartes ocasionales (picos negativos).

Cada generador usa su propio ``random.Random(semilla)``: la misma semilla
produce siempre la misma serie, sin alterar el estado global de ``random``.
Los registros son inmutables para conservar la trazabilidad del dato
original.
"""

import random
from dataclasses import dataclass

Serie = list[int]

# ---------------------------------------------------------------------------
# Parámetros del caso y semillas fijas
# ---------------------------------------------------------------------------

SEMILLA_BASE = 2026

NUM_CATEGORIAS = 40
HORAS_POR_DIA = 12
HORA_APERTURA = 6               # La operación va de 06:00 a 18:00.
DIAS_POR_ANIO = 300
ANIOS_HISTORICO = 10
HORAS_HISTORICO = HORAS_POR_DIA * DIAS_POR_ANIO * ANIOS_HISTORICO  # 36.000

DIAS_TEMPORADA = 50             # Últimos días operativos de cada año.
AMPLITUD_MIN_KG = 20            # Escala horaria de una categoría pequeña.
AMPLITUD_MAX_KG = 200           # Escala horaria de una categoría grande.

# Fracción de la amplitud que entra (+) o sale (-) en cada hora del día.
PATRON_DIARIO: tuple[float, ...] = (
    0.9, 0.8, 0.6, 0.3, 0.1, -0.1, -0.2, -0.4, -0.5, -0.6, -0.5, -0.4,
)
SESGO_FUERA_TEMPORADA = -0.20   # Fracción de la amplitud por hora.
AUMENTO_TEMPORADA = 0.40        # Fracción de la amplitud por hora.
DESVIACION_RUIDO = 0.50         # Fracción de la amplitud.
PROB_DONACION_GRANDE = 0.010
PROB_DESCARTE = 0.005

CATEGORIAS: tuple[str, ...] = tuple(
    f"categoria_{k:02d}" for k in range(1, NUM_CATEGORIAS + 1)
)


@dataclass(frozen=True)
class RegistroHorario:
    """Registro original e inmutable del cambio neto de una hora.

    Attributes:
        categoria: Categoría de producto.
        dia: Día operativo, desde 0 (300 días por año).
        hora: Hora del día de operación, de 0 a 11 (06:00 a 17:00).
        cambio_kg: Entradas menos salidas y descartes, en kg (entero).
    """

    categoria: str
    dia: int
    hora: int
    cambio_kg: int


# ---------------------------------------------------------------------------
# Generadores
# ---------------------------------------------------------------------------

def _es_temporada(dia: int) -> bool:
    """Indica si un día operativo pertenece a la temporada alta de donaciones.

    Args:
        dia: Día operativo desde 0.

    Returns:
        True en los últimos ``DIAS_TEMPORADA`` días de cada año.
    """
    return dia % DIAS_POR_ANIO >= DIAS_POR_ANIO - DIAS_TEMPORADA


def _cambio_horario(
    azar: random.Random, amplitud: float, dia: int, hora: int
) -> int:
    """Calcula el cambio neto sintético de una hora, en kg.

    Args:
        azar: Generador pseudoaleatorio con semilla ya fijada.
        amplitud: Escala horaria de la categoría, en kg.
        dia: Día operativo desde 0.
        hora: Hora del día de operación, de 0 a 11.

    Returns:
        Cambio neto entero (puede ser negativo).
    """
    media = PATRON_DIARIO[hora] + (
        AUMENTO_TEMPORADA if _es_temporada(dia) else SESGO_FUERA_TEMPORADA
    )
    cambio = amplitud * (media + azar.gauss(0.0, DESVIACION_RUIDO))
    sorteo = azar.random()
    if sorteo < PROB_DONACION_GRANDE:
        cambio += azar.uniform(2.0, 6.0) * amplitud
    elif sorteo < PROB_DONACION_GRANDE + PROB_DESCARTE:
        cambio -= azar.uniform(2.0, 4.0) * amplitud
    return round(cambio)


def generar_serie(n: int, semilla: int = SEMILLA_BASE) -> Serie:
    """Genera la serie de ``n`` cambios horarios de una categoría.

    La serie empieza en la primera hora del día 0 y avanza hora por hora;
    ``n = HORAS_HISTORICO`` reproduce los diez años del caso.

    Args:
        n: Cantidad de horas (entero no negativo).
        semilla: Semilla para reproducibilidad; también fija la amplitud.

    Returns:
        Lista de ``n`` enteros, en kg.

    Raises:
        ValueError: Si ``n`` es negativo.
    """
    if n < 0:
        raise ValueError("n no puede ser negativo.")
    azar = random.Random(semilla)
    amplitud = azar.uniform(AMPLITUD_MIN_KG, AMPLITUD_MAX_KG)
    return [
        _cambio_horario(azar, amplitud, t // HORAS_POR_DIA, t % HORAS_POR_DIA)
        for t in range(n)
    ]


def generar_registros(
    categoria: str, n: int, semilla: int = SEMILLA_BASE
) -> list[RegistroHorario]:
    """Genera los registros horarios originales de una categoría.

    Args:
        categoria: Nombre de la categoría.
        n: Cantidad de horas.
        semilla: Semilla para reproducibilidad.

    Returns:
        Lista de ``n`` registros inmutables en orden cronológico.
    """
    return [
        RegistroHorario(
            categoria, t // HORAS_POR_DIA, t % HORAS_POR_DIA, cambio
        )
        for t, cambio in enumerate(generar_serie(n, semilla))
    ]


def generar_historico(
    horas: int = HORAS_HISTORICO,
    categorias: tuple[str, ...] = CATEGORIAS,
    semilla: int = SEMILLA_BASE,
) -> dict[str, Serie]:
    """Genera la serie de cada categoría, con una semilla distinta por cada una.

    Con los valores por defecto produce el volumen real del caso:
    40 categorías por 36.000 horas.

    Args:
        horas: Horas por categoría.
        categorias: Nombres de las categorías.
        semilla: Semilla base; la categoría k usa ``semilla + k``.

    Returns:
        Diccionario categoría -> serie de cambios horarios.
    """
    return {
        categoria: generar_serie(horas, semilla + k)
        for k, categoria in enumerate(categorias)
    }


def generar_serie_pequena(
    n: int, semilla: int, rango_kg: int = 50
) -> Serie:
    """Genera una serie corta y uniforme para contrastar con la exhaustiva.

    Los valores son enteros uniformes en ``[-rango_kg, rango_kg]``; con
    rangos pequeños aparecen empates y ceros, útiles para las pruebas.

    Args:
        n: Cantidad de horas.
        semilla: Semilla para reproducibilidad.
        rango_kg: Valor absoluto máximo de cada cambio.

    Returns:
        Lista de ``n`` enteros.
    """
    azar = random.Random(semilla)
    return [azar.randint(-rango_kg, rango_kg) for _ in range(n)]


# ---------------------------------------------------------------------------
# Adaptadores y presentación del resultado
# ---------------------------------------------------------------------------

def a_serie(registros: list[RegistroHorario]) -> Serie:
    """Extrae los cambios en kg en el mismo orden de los registros.

    Args:
        registros: Registros horarios de una categoría.

    Returns:
        Lista nueva de cambios; no modifica los registros.
    """
    return [registro.cambio_kg for registro in registros]


def describir_hora(indice: int) -> str:
    """Convierte un índice de la serie en año, día del año y hora del reloj.

    Args:
        indice: Posición de la hora en la serie, desde 0.

    Returns:
        Texto como ``"año 3, día 251, 14:00"``.
    """
    dia, hora = divmod(indice, HORAS_POR_DIA)
    anio, dia_del_anio = divmod(dia, DIAS_POR_ANIO)
    return (f"año {anio + 1}, día {dia_del_anio + 1}, "
            f"{HORA_APERTURA + hora:02d}:00")


if __name__ == "__main__":
    serie = generar_serie(HORAS_HISTORICO)
    positivas = sum(cambio > 0 for cambio in serie)
    print(f"Serie de ejemplo (semilla {SEMILLA_BASE}): {len(serie)} horas, "
          f"{positivas} con crecimiento, suma total {sum(serie)} kg.")
    print(f"Primeras 12 horas: {serie[:12]}")
    print(f"Índice 0 = {describir_hora(0)}; "
          f"índice {HORAS_HISTORICO - 1} = {describir_hora(HORAS_HISTORICO - 1)}")
