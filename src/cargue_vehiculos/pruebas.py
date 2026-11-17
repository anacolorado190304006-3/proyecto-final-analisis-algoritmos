"""Suite consolidada de pruebas del cargue de vehículos (Caso 3).

Ejecutar desde la raíz del repositorio, sin ``-O`` para conservar los assert:

    python -B src/cargue_vehiculos/pruebas.py

Verifica:

* Que los generadores de ``datos.py`` sean reproducibles y respeten los
  rangos del caso, y que los registros originales no se modifiquen.
* Casos límite de la mochila 0/1 (DP), la exhaustiva y las reglas voraces.
* Al menos 20 instancias aleatorias (aquí 40) en las que la DP coincide con
  la solución exhaustiva.
* Que ninguna solución fraccione lotes ni supere la capacidad, incluidas
  rutas de tamaño real (300 a 600 lotes, 2.500 a 4.000 kg).
* Que ningún lote vencido llegue a los candidatos de despacho.

Al final ejecuta también las suites previas (``pruebas_mochila.py`` y
``pruebas_contraejemplos.py``) para tener un único punto de verificación.
"""

import contextlib
import dataclasses
import io
from collections.abc import Callable

import pruebas_contraejemplos
import pruebas_mochila
from datos import (
    CANDIDATOS_MAX,
    CANDIDATOS_MIN,
    CAPACIDAD_MAX_KG,
    CAPACIDAD_MIN_KG,
    CATEGORIAS,
    FECHA_DESPACHO,
    PESO_MAX_KG,
    PESO_MIN_KG,
    Lote,
    a_listas,
    a_tuplas,
    dias_para_vencer,
    filtrar_aptos,
    generar_instancia_pequena,
    generar_inventario,
    generar_ruta,
    valor_nutricional,
)
from estrategia import mochila_01
from exhaustivo import cargar_exhaustivo
from regla_actual import cargar_por_densidad, cargar_por_vencimiento

Solucion = tuple[int, list[int]]
Algoritmo = Callable[[list[Lote], int], Solucion]

INSTANCIAS_ALEATORIAS = 40   # El enunciado del rol exige al menos 20.
SEMILLA_ALEATORIAS = 1000
RUTAS_REALES = 3


# ---------------------------------------------------------------------------
# Utilidades de verificación
# ---------------------------------------------------------------------------

def dp_sobre_lotes(lotes: list[Lote], capacidad_kg: int) -> Solucion:
    """Adapta ``mochila_01`` a la interfaz de lista de tuplas.

    Args:
        lotes: Tuplas ``(peso_kg, valor_nutricional, dias_para_vencer)``.
        capacidad_kg: Capacidad del vehículo en kg.

    Returns:
        Tupla ``(valor, indices)`` de la mochila 0/1.
    """
    pesos, valores = a_listas(lotes)
    return mochila_01(pesos, valores, capacidad_kg)


ALGORITMOS: dict[str, Algoritmo] = {
    "DP": dp_sobre_lotes,
    "Exhaustiva": cargar_exhaustivo,
    "Vencimiento": cargar_por_vencimiento,
    "Densidad": cargar_por_densidad,
}


def verificar_cargue(
    lotes: list[Lote], capacidad_kg: int, solucion: Solucion, nombre: str
) -> None:
    """Comprueba que una solución sea un cargue válido de lotes completos.

    Un lote no se fracciona si aparece como índice entero, a lo sumo una vez,
    y si el peso y el valor del cargue son exactamente la suma de los
    registros completos elegidos.

    Args:
        lotes: Lotes candidatos.
        capacidad_kg: Capacidad del vehículo en kg.
        solucion: Tupla ``(valor, indices)`` devuelta por el algoritmo.
        nombre: Nombre del algoritmo, para los mensajes de error.

    Raises:
        AssertionError: Si la solución fracciona, repite o inventa lotes,
            supera la capacidad o reporta un valor inconsistente.
    """
    valor, indices = solucion
    assert type(valor) is int, f"{nombre}: el valor no es entero"
    assert isinstance(indices, list), f"{nombre}: los índices no son lista"
    assert all(type(i) is int for i in indices), f"{nombre}: índice no entero"
    assert indices == sorted(set(indices)), f"{nombre}: índices repetidos"
    assert all(0 <= i < len(lotes) for i in indices), f"{nombre}: índice fuera"
    peso = sum(lotes[i][0] for i in indices)
    assert peso <= capacidad_kg, f"{nombre}: {peso} kg > {capacidad_kg} kg"
    assert valor == sum(lotes[i][1] for i in indices), (
        f"{nombre}: el valor no corresponde a lotes completos"
    )


def ejecutar_todos(lotes: list[Lote], capacidad_kg: int) -> dict[str, Solucion]:
    """Ejecuta los cuatro algoritmos, verifica cada salida y la inmutabilidad.

    Args:
        lotes: Lotes candidatos (no se modifican).
        capacidad_kg: Capacidad del vehículo en kg.

    Returns:
        Diccionario nombre -> solución.
    """
    copia = list(lotes)
    resultados: dict[str, Solucion] = {}
    for nombre, algoritmo in ALGORITMOS.items():
        resultados[nombre] = algoritmo(lotes, capacidad_kg)
        assert lotes == copia, f"{nombre} modificó los lotes"
        verificar_cargue(lotes, capacidad_kg, resultados[nombre], nombre)
    return resultados


def verificar_optimo(lotes: list[Lote], capacidad_kg: int) -> dict[str, Solucion]:
    """Verifica que DP = exhaustiva y que las reglas no superen el óptimo.

    Args:
        lotes: Lotes candidatos.
        capacidad_kg: Capacidad del vehículo en kg.

    Returns:
        Diccionario nombre -> solución.
    """
    resultados = ejecutar_todos(lotes, capacidad_kg)
    optimo = resultados["Exhaustiva"][0]
    assert resultados["DP"][0] == optimo, (
        f"DP={resultados['DP'][0]} distinto de exhaustiva={optimo}"
    )
    for nombre in ("Vencimiento", "Densidad"):
        assert resultados[nombre][0] <= optimo, f"{nombre} supera el óptimo"
    return resultados


# ---------------------------------------------------------------------------
# Pruebas de los generadores de datos
# ---------------------------------------------------------------------------

def probar_reproducibilidad() -> None:
    """La misma semilla produce los mismos datos; otra semilla, distintos."""
    assert generar_inventario(200, 5) == generar_inventario(200, 5)
    assert generar_inventario(200, 5) != generar_inventario(200, 6)
    assert generar_ruta(9) == generar_ruta(9)
    assert generar_instancia_pequena(10, 3) == generar_instancia_pequena(10, 3)


def probar_rangos_del_caso() -> None:
    """Los datos sintéticos respetan la estructura y los rangos del cliente."""
    inventario = generar_inventario(2000, 11)
    codigos = [lote.codigo_lote for lote in inventario]
    assert len(set(codigos)) == len(codigos), "códigos de lote repetidos"
    for lote in inventario:
        assert PESO_MIN_KG <= lote.peso_kg <= PESO_MAX_KG
        assert type(lote.peso_kg) is int and lote.raciones >= 0
        assert lote.categoria in CATEGORIAS
        assert valor_nutricional(lote) >= lote.raciones
    assert len(CATEGORIAS) == 40 and len(set(CATEGORIAS)) == 40

    for semilla in range(20):
        candidatos, capacidad = generar_ruta(semilla)
        assert CANDIDATOS_MIN <= len(candidatos) <= CANDIDATOS_MAX
        assert CAPACIDAD_MIN_KG <= capacidad <= CAPACIDAD_MAX_KG
        assert sum(l.peso_kg for l in candidatos) > capacidad, (
            "la ruta debe exigir selección: los candidatos no caben todos"
        )


def probar_registros_inmutables() -> None:
    """Los registros originales no pueden modificarse (trazabilidad)."""
    lote = generar_inventario(1, 1)[0]
    try:
        lote.peso_kg = 1  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("El registro original se pudo modificar")


def probar_filtrado_de_vencidos() -> None:
    """Ningún lote vencido llega a los candidatos y el original no cambia."""
    inventario = generar_inventario(3000, 21, incluir_vencidos=True)
    copia = list(inventario)
    vencidos = [l for l in inventario if dias_para_vencer(l, FECHA_DESPACHO) < 0]
    assert vencidos, "el inventario de prueba debe incluir lotes vencidos"

    aptos = filtrar_aptos(inventario, FECHA_DESPACHO)
    assert inventario == copia, "filtrar_aptos modificó el inventario"
    assert len(aptos) + len(vencidos) == len(inventario)
    assert all(dias_para_vencer(l, FECHA_DESPACHO) >= 0 for l in aptos)

    tuplas = a_tuplas(aptos, FECHA_DESPACHO)
    for nombre, algoritmo in ALGORITMOS.items():
        if nombre == "Exhaustiva":
            continue
        _, indices = algoritmo(tuplas, 3000)
        assert all(tuplas[i][2] >= 0 for i in indices), (
            f"{nombre} despachó un lote vencido"
        )


def probar_adaptadores() -> None:
    """a_tuplas y a_listas conservan orden y correspondencia de índices."""
    lotes, _ = generar_instancia_pequena(8, 4)
    tuplas = a_tuplas(lotes)
    pesos, valores = a_listas(tuplas)
    for i, lote in enumerate(lotes):
        assert tuplas[i] == (
            lote.peso_kg, valor_nutricional(lote),
            dias_para_vencer(lote, FECHA_DESPACHO),
        )
        assert pesos[i] == lote.peso_kg and valores[i] == tuplas[i][1]


# ---------------------------------------------------------------------------
# Casos límite de los algoritmos de cargue
# ---------------------------------------------------------------------------

def probar_casos_limite() -> None:
    """Casos borde comunes a DP, exhaustiva y reglas voraces."""
    casos: list[tuple[str, list[Lote], int, int]] = [
        # (descripción, lotes, capacidad, valor óptimo esperado)
        ("sin lotes", [], 100, 0),
        ("capacidad cero", [(3, 5, 1), (4, 6, 2)], 0, 0),
        ("nada cabe", [(8, 5, 1), (9, 6, 2)], 7, 0),
        ("todo cabe", [(2, 1, 1), (3, 2, 2), (4, 3, 3)], 100, 6),
        ("ajuste exacto", [(7, 9, 1)], 7, 9),
        ("un kg de menos", [(7, 9, 1)], 6, 0),
        ("capacidad = total", [(2, 3, 1), (5, 4, 2), (3, 8, 3)], 10, 15),
        ("total - 1", [(2, 3, 1), (5, 4, 2), (3, 8, 3)], 9, 12),
        ("valores cero", [(1, 0, 1), (2, 0, 2)], 3, 0),
        ("pesos iguales", [(5, 4, 1), (5, 9, 2), (5, 7, 3)], 10, 16),
        ("empate de valor", [(2, 5, 1), (2, 5, 2)], 2, 5),
        ("lote de 1 kg", [(1, 10, 1), (100, 50, 2)], 1, 10),
        ("lote mayor que vehículo", [(4001, 9999, 1), (100, 7, 2)], 4000, 7),
        ("vence hoy", [(10, 4, 0), (10, 5, 3)], 10, 5),
    ]
    for descripcion, lotes, capacidad, esperado in casos:
        resultados = verificar_optimo(lotes, capacidad)
        assert resultados["DP"][0] == esperado, (
            f"{descripcion}: DP={resultados['DP'][0]}, esperado={esperado}"
        )


def probar_excepciones() -> None:
    """Entradas inválidas lanzan ValueError en todas las interfaces."""
    invalidas: list[tuple[list[Lote], int]] = [
        ([(1, 1, 1)], -1),          # capacidad negativa
        ([(0, 1, 1)], 5),           # peso no positivo
        ([(1, -1, 1)], 5),          # valor negativo
        ([(1.5, 1, 1)], 5),         # type: ignore[list-item]  peso no entero
        ([(1, 1, 1)], 5.0),         # type: ignore[list-item]  capacidad no entera
        ([(True, 1, 1)], 5),        # booleano como entero
    ]
    for lotes, capacidad in invalidas:
        for nombre, algoritmo in ALGORITMOS.items():
            try:
                algoritmo(lotes, capacidad)
            except ValueError:
                continue
            raise AssertionError(f"{nombre} aceptó {lotes}, {capacidad}")


# ---------------------------------------------------------------------------
# Contraste con la solución exhaustiva
# ---------------------------------------------------------------------------

def probar_aleatorias_contra_exhaustiva() -> None:
    """La DP coincide con la exhaustiva en 40 instancias aleatorias.

    Los tamaños van de 1 a 16 lotes (la exhaustiva es Theta(n * 2^n)).
    Cada instancia usa una semilla distinta y derivada de una semilla fija.
    """
    assert INSTANCIAS_ALEATORIAS >= 20
    brechas: list[int] = []
    for k in range(INSTANCIAS_ALEATORIAS):
        n = 1 + k % 16
        lotes_reg, capacidad = generar_instancia_pequena(
            n, SEMILLA_ALEATORIAS + k
        )
        lotes = a_tuplas(lotes_reg)
        resultados = verificar_optimo(lotes, capacidad)
        brechas.append(resultados["DP"][0] - resultados["Vencimiento"][0])
    print(f"  {INSTANCIAS_ALEATORIAS} instancias: DP = exhaustiva en todas; "
          f"la regla por vencimiento quedó por debajo en "
          f"{sum(b > 0 for b in brechas)}.")


def probar_rutas_tamano_real() -> None:
    """Rutas de 300 a 600 lotes y 2.500 a 4.000 kg: cargue válido y útil.

    La exhaustiva no es viable a este tamaño (2^300 subconjuntos), así que
    se verifica factibilidad, no fraccionamiento y que la DP no sea peor
    que las reglas voraces.
    """
    for semilla in range(RUTAS_REALES):
        candidatos, capacidad = generar_ruta(semilla)
        lotes = a_tuplas(candidatos)
        copia = list(lotes)
        resultados = {
            nombre: algoritmo(lotes, capacidad)
            for nombre, algoritmo in ALGORITMOS.items()
            if nombre != "Exhaustiva"
        }
        assert lotes == copia
        for nombre, solucion in resultados.items():
            verificar_cargue(lotes, capacidad, solucion, nombre)
        valor_dp = resultados["DP"][0]
        assert valor_dp >= resultados["Vencimiento"][0]
        assert valor_dp >= resultados["Densidad"][0]
        peso_dp = sum(lotes[i][0] for i in resultados["DP"][1])
        print(f"  Ruta {semilla}: {len(lotes)} lotes, {capacidad} kg, "
              f"DP usa {peso_dp} kg ({100 * peso_dp / capacidad:.1f} %).")


# ---------------------------------------------------------------------------
# Suites previas del equipo
# ---------------------------------------------------------------------------

def ejecutar_suites_previas() -> None:
    """Ejecuta pruebas_mochila y pruebas_contraejemplos sin sus tablas."""
    pruebas_previas: list[Callable[[], None]] = [
        pruebas_mochila.probar_ejemplo_a_mano,
        pruebas_mochila.probar_casos_borde,
        pruebas_mochila.probar_no_modifica_entradas,
        pruebas_mochila.probar_contra_fuerza_bruta,
        pruebas_mochila.probar_supera_al_cargue_actual,
        pruebas_mochila.probar_tamano_realista,
        pruebas_mochila.probar_excepciones,
        pruebas_contraejemplos.probar_contraejemplo_vencimiento,
        pruebas_contraejemplos.probar_contraejemplo_densidad,
    ]
    for prueba in pruebas_previas:
        with contextlib.redirect_stdout(io.StringIO()):
            prueba()


PRUEBAS: list[Callable[[], None]] = [
    probar_reproducibilidad,
    probar_rangos_del_caso,
    probar_registros_inmutables,
    probar_filtrado_de_vencidos,
    probar_adaptadores,
    probar_casos_limite,
    probar_excepciones,
    probar_aleatorias_contra_exhaustiva,
    probar_rutas_tamano_real,
    ejecutar_suites_previas,
]


if __name__ == "__main__":
    for prueba in PRUEBAS:
        print(f"[..] {prueba.__name__}")
        prueba()
        print(f"[ok] {prueba.__name__}")
    print(f"\nLas {len(PRUEBAS)} pruebas pasaron.")
