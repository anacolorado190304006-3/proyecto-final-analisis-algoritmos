"""Generación de datos sintéticos del Banco Regional de Alimentos (Caso 3).

Produce lotes con la estructura descrita por el cliente (codigo_lote,
categoria, fecha_vencimiento, peso_kg, raciones, donante) y los adapta a
las interfaces de los algoritmos de cargue:

* ``Lote = (peso_kg, valor_nutricional, dias_para_vencer)`` para
  ``exhaustivo.py`` y ``regla_actual.py``.
* Listas separadas ``pesos`` y ``valores`` para ``estrategia.mochila_01``.

Todos los generadores reciben una semilla y usan su propio
``random.Random``, de modo que la misma semilla produce siempre los mismos
datos sin alterar el estado global de ``random``. Los registros son
inmutables (``dataclass(frozen=True)``) para respetar la restricción de no
modificar el registro original de cada lote.

Parámetros del caso: rutas de 300 a 600 lotes candidatos y vehículos de
2.500 a 4.000 kg. El valor nutricional se define como raciones ponderadas
por la prioridad de la categoría (proteína 3, frutas y verduras 2, otros 1).
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta

Lote = tuple[int, int, int]

# ---------------------------------------------------------------------------
# Parámetros del caso y semillas fijas
# ---------------------------------------------------------------------------

SEMILLA_BASE = 2026
FECHA_DESPACHO = date(2026, 11, 18)

PESO_MIN_KG = 20
PESO_MAX_KG = 600
RACIONES_POR_KG_MIN = 2
RACIONES_POR_KG_MAX = 4

CAPACIDAD_MIN_KG = 2500
CAPACIDAD_MAX_KG = 4000
CANDIDATOS_MIN = 300
CANDIDATOS_MAX = 600

DIAS_VENCIMIENTO_MAX = 30   # Horizonte de vencimiento de los candidatos.
DIAS_VENCIDOS_MAX = 5       # Antigüedad máxima de lotes ya vencidos.
NUM_DONANTES = 120

PRIORIDAD_POR_GRUPO: dict[str, int] = {
    "proteina": 3,
    "frutas_verduras": 2,
    "otros": 1,
}

CATEGORIAS_POR_GRUPO: dict[str, tuple[str, ...]] = {
    "proteina": (
        "carne de res", "carne de cerdo", "pollo", "pescado", "atun enlatado",
        "huevos", "leche", "queso", "yogur", "frijol", "lenteja", "garbanzo",
    ),
    "frutas_verduras": (
        "banano", "naranja", "mango", "papaya", "tomate", "cebolla",
        "zanahoria", "papa", "yuca", "platano",
    ),
    "otros": (
        "arroz", "pasta", "harina de trigo", "harina de maiz", "avena",
        "pan", "galletas", "cereal", "aceite", "azucar", "panela", "sal",
        "cafe", "chocolate", "salsas", "enlatados vegetales", "compotas",
        "bebidas",
    ),
}

CATEGORIAS: tuple[str, ...] = tuple(
    categoria
    for categorias in CATEGORIAS_POR_GRUPO.values()
    for categoria in categorias
)

PRIORIDAD_CATEGORIA: dict[str, int] = {
    categoria: PRIORIDAD_POR_GRUPO[grupo]
    for grupo, categorias in CATEGORIAS_POR_GRUPO.items()
    for categoria in categorias
}


@dataclass(frozen=True)
class RegistroLote:
    """Registro original e inmutable de un lote del inventario.

    Attributes:
        codigo_lote: Identificador único del lote.
        categoria: Una de las 40 categorías de producto.
        fecha_vencimiento: Fecha de vencimiento del lote.
        peso_kg: Peso entero del lote en kilogramos (positivo).
        raciones: Raciones que aporta el lote (no negativo).
        donante: Código del donante que lo entregó.
    """

    codigo_lote: str
    categoria: str
    fecha_vencimiento: date
    peso_kg: int
    raciones: int
    donante: str


# ---------------------------------------------------------------------------
# Generadores
# ---------------------------------------------------------------------------

def _generar_registro(
    azar: random.Random,
    indice: int,
    fecha_despacho: date,
    dias_min: int,
    dias_max: int,
    peso_min: int,
    peso_max: int,
) -> RegistroLote:
    """Crea un registro sintético con la estructura del cliente.

    Args:
        azar: Generador pseudoaleatorio con semilla ya fijada.
        indice: Consecutivo del lote, usado en el código.
        fecha_despacho: Fecha de referencia del despacho.
        dias_min: Mínimo de días para vencer (negativo = ya vencido).
        dias_max: Máximo de días para vencer.
        peso_min: Peso mínimo del lote en kg.
        peso_max: Peso máximo del lote en kg.

    Returns:
        Un ``RegistroLote`` nuevo.
    """
    peso = azar.randint(peso_min, peso_max)
    raciones = peso * azar.randint(RACIONES_POR_KG_MIN, RACIONES_POR_KG_MAX)
    return RegistroLote(
        codigo_lote=f"L{fecha_despacho:%Y%m%d}-{indice:06d}",
        categoria=azar.choice(CATEGORIAS),
        fecha_vencimiento=fecha_despacho
        + timedelta(days=azar.randint(dias_min, dias_max)),
        peso_kg=peso,
        raciones=raciones,
        donante=f"DON-{azar.randint(1, NUM_DONANTES):03d}",
    )


def generar_inventario(
    n: int,
    semilla: int = SEMILLA_BASE,
    fecha_despacho: date = FECHA_DESPACHO,
    incluir_vencidos: bool = True,
) -> list[RegistroLote]:
    """Genera un inventario sintético de ``n`` lotes con semilla fija.

    Si ``incluir_vencidos`` es verdadero, algunos lotes vencen antes de
    ``fecha_despacho``; sirven para probar que nunca se despachen.

    Args:
        n: Cantidad de lotes (entero no negativo).
        semilla: Semilla para reproducibilidad.
        fecha_despacho: Fecha de referencia del despacho.
        incluir_vencidos: Si se generan lotes ya vencidos.

    Returns:
        Lista de ``n`` registros con códigos únicos.

    Raises:
        ValueError: Si ``n`` es negativo.
    """
    if n < 0:
        raise ValueError("n no puede ser negativo.")
    azar = random.Random(semilla)
    dias_min = -DIAS_VENCIDOS_MAX if incluir_vencidos else 0
    return [
        _generar_registro(
            azar, i, fecha_despacho, dias_min, DIAS_VENCIMIENTO_MAX,
            PESO_MIN_KG, PESO_MAX_KG,
        )
        for i in range(n)
    ]


def generar_ruta(
    semilla: int = SEMILLA_BASE,
    n: int | None = None,
    fecha_despacho: date = FECHA_DESPACHO,
) -> tuple[list[RegistroLote], int]:
    """Genera una ruta representativa: candidatos y capacidad del vehículo.

    Usa los rangos del cliente: entre 300 y 600 candidatos y capacidad
    entre 2.500 y 4.000 kg. Todos los candidatos son aptos para despacho.

    Args:
        semilla: Semilla para reproducibilidad.
        n: Número de candidatos; si es ``None`` se sortea en el rango.
        fecha_despacho: Fecha de referencia del despacho.

    Returns:
        Tupla ``(candidatos, capacidad_kg)``.
    """
    azar = random.Random(semilla)
    cantidad = n if n is not None else azar.randint(
        CANDIDATOS_MIN, CANDIDATOS_MAX
    )
    capacidad = azar.randint(CAPACIDAD_MIN_KG, CAPACIDAD_MAX_KG)
    candidatos = generar_inventario(
        cantidad, azar.randrange(2**32), fecha_despacho,
        incluir_vencidos=False,
    )
    return candidatos, capacidad


def generar_instancia_pequena(
    n: int,
    semilla: int,
    peso_max: int = 30,
    fecha_despacho: date = FECHA_DESPACHO,
) -> tuple[list[RegistroLote], int]:
    """Genera una instancia pequeña para contrastar con la exhaustiva.

    La capacidad se sortea entre el 30 % y el 70 % del peso total, para que
    la selección no sea trivial (ni todo cabe ni nada cabe).

    Args:
        n: Cantidad de lotes (pensado para n <= 16).
        semilla: Semilla para reproducibilidad.
        peso_max: Peso máximo de cada lote, en kg.
        fecha_despacho: Fecha de referencia del despacho.

    Returns:
        Tupla ``(lotes, capacidad_kg)``.
    """
    azar = random.Random(semilla)
    lotes = [
        _generar_registro(
            azar, i, fecha_despacho, 0, DIAS_VENCIMIENTO_MAX, 1, peso_max
        )
        for i in range(n)
    ]
    peso_total = sum(lote.peso_kg for lote in lotes)
    capacidad = azar.randint(peso_total * 3 // 10, peso_total * 7 // 10)
    return lotes, capacidad


# ---------------------------------------------------------------------------
# Adaptadores hacia las interfaces de los algoritmos
# ---------------------------------------------------------------------------

def valor_nutricional(lote: RegistroLote) -> int:
    """Raciones del lote ponderadas por la prioridad de su categoría.

    Args:
        lote: Registro del lote.

    Returns:
        Valor nutricional entero no negativo.
    """
    return lote.raciones * PRIORIDAD_CATEGORIA[lote.categoria]


def dias_para_vencer(lote: RegistroLote, fecha_despacho: date) -> int:
    """Días entre la fecha de despacho y el vencimiento (negativo si venció).

    Args:
        lote: Registro del lote.
        fecha_despacho: Fecha de referencia del despacho.

    Returns:
        Diferencia en días.
    """
    return (lote.fecha_vencimiento - fecha_despacho).days


def filtrar_aptos(
    lotes: list[RegistroLote], fecha_despacho: date = FECHA_DESPACHO
) -> list[RegistroLote]:
    """Devuelve una lista nueva solo con los lotes no vencidos.

    Un lote es apto si vence el mismo día del despacho o después. No
    modifica la lista recibida y conserva el orden original.

    Args:
        lotes: Inventario o candidatos.
        fecha_despacho: Fecha de referencia del despacho.

    Returns:
        Lista nueva con los lotes aptos.
    """
    return [
        lote for lote in lotes
        if dias_para_vencer(lote, fecha_despacho) >= 0
    ]


def a_tuplas(
    lotes: list[RegistroLote], fecha_despacho: date = FECHA_DESPACHO
) -> list[Lote]:
    """Convierte registros a tuplas de peso, valor y días para vencer.

    Conserva el orden, de modo que el índice i de la salida corresponde al
    registro i de la entrada.

    Args:
        lotes: Registros de los lotes.
        fecha_despacho: Fecha de referencia del despacho.

    Returns:
        Lista de tuplas compatible con ``exhaustivo`` y ``regla_actual``.
    """
    return [
        (lote.peso_kg, valor_nutricional(lote),
         dias_para_vencer(lote, fecha_despacho))
        for lote in lotes
    ]


def a_listas(lotes: list[Lote]) -> tuple[list[int], list[int]]:
    """Separa tuplas de lotes en listas de pesos y valores para la DP.

    Args:
        lotes: Tuplas ``(peso_kg, valor_nutricional, dias_para_vencer)``.

    Returns:
        Tupla ``(pesos, valores)`` en el mismo orden.
    """
    return [lote[0] for lote in lotes], [lote[1] for lote in lotes]


if __name__ == "__main__":
    candidatos, capacidad = generar_ruta()
    tuplas = a_tuplas(candidatos)
    print(f"Ruta de ejemplo (semilla {SEMILLA_BASE}): {len(candidatos)} "
          f"candidatos, capacidad {capacidad} kg, peso total "
          f"{sum(t[0] for t in tuplas)} kg.")
    for registro in candidatos[:5]:
        print(f"  {registro}  valor={valor_nutricional(registro)}")
