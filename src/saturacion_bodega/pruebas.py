"""Pruebas del análisis de saturación de la bodega (Caso 3, operación 4).

Ejecutar desde la raíz del repositorio, sin ``-O`` para conservar los assert:

    python -B src/saturacion_bodega/pruebas.py

Contrato que deben cumplir todas las estrategias (ver ``IMPLEMENTACIONES``):

* Firma ``funcion(cambios: list[int]) -> tuple[int, int, int]``.
* Devuelve ``(suma, inicio, fin)``: el tramo de horas consecutivas
  ``cambios[inicio:fin + 1]`` con mayor crecimiento acumulado. Índices en
  base cero y ``fin`` incluido.
* El tramo no es vacío: si todas las horas son negativas, se reporta la
  hora menos negativa.
* Una serie vacía lanza ``ValueError``.
* Con varios tramos óptimos se acepta cualquiera; la suma debe ser exacta.
* No modifica la serie recibida.

Si una implementación aún no existe, la suite la reporta como pendiente y
termina con código de salida 1, aunque las demás pruebas pasen.
"""

import importlib
import sys
from collections.abc import Callable

from datos import (
    CATEGORIAS,
    DIAS_POR_ANIO,
    DIAS_TEMPORADA,
    HORAS_HISTORICO,
    HORAS_POR_DIA,
    NUM_CATEGORIAS,
    RegistroHorario,
    Serie,
    a_serie,
    describir_hora,
    generar_historico,
    generar_registros,
    generar_serie,
    generar_serie_pequena,
)

Tramo = tuple[int, int, int]
Estrategia = Callable[[Serie], Tramo]

# (módulo, función, ¿es exhaustiva?). Ajustar si el equipo usa otros nombres.
IMPLEMENTACIONES: list[tuple[str, str, bool]] = [
    ("estrategia", "tramo_maximo_dividir", False),
    ("estrategia", "tramo_maximo_kadane", False),
    ("exhaustivo", "tramo_maximo_exhaustivo", True),
]

INSTANCIAS_ALEATORIAS = 200    # El mínimo exigido es 20.
SEMILLA_ALEATORIAS = 4000
CATEGORIAS_VOLUMEN_REAL = 3


# ---------------------------------------------------------------------------
# Carga de implementaciones y oráculos independientes
# ---------------------------------------------------------------------------

def cargar_implementaciones() -> tuple[dict[str, Estrategia], set[str], list[str]]:
    """Importa las estrategias declaradas en ``IMPLEMENTACIONES``.

    Returns:
        Tupla ``(disponibles, exhaustivas, pendientes)``: funciones
        encontradas por nombre, nombres de las exhaustivas y nombres de
        las que aún no existen.
    """
    disponibles: dict[str, Estrategia] = {}
    exhaustivas: set[str] = set()
    pendientes: list[str] = []
    for modulo, funcion, es_exhaustiva in IMPLEMENTACIONES:
        nombre = f"{modulo}.{funcion}"
        try:
            disponibles[nombre] = getattr(importlib.import_module(modulo), funcion)
        except (ImportError, AttributeError):
            pendientes.append(nombre)
            continue
        if es_exhaustiva:
            exhaustivas.add(nombre)
    return disponibles, exhaustivas, pendientes


def oraculo_cuadratico(serie: Serie) -> int:
    """Suma máxima por definición: revisa todos los tramos no vacíos.

    Es independiente del código del equipo. Tiempo Theta(n^2).

    Args:
        serie: Serie no vacía.

    Returns:
        La mayor suma de un tramo consecutivo no vacío.
    """
    mejor = serie[0]
    for inicio in range(len(serie)):
        acumulado = 0
        for fin in range(inicio, len(serie)):
            acumulado += serie[fin]
            mejor = max(mejor, acumulado)
    return mejor


def oraculo_prefijos(serie: Serie) -> int:
    """Suma máxima con sumas prefijas: max(P[j] - min P[i]), i < j.

    Tiempo Theta(n); sirve para series largas donde el cuadrático no
    alcanza. Se contrasta con ``oraculo_cuadratico`` en las pruebas.

    Args:
        serie: Serie no vacía.

    Returns:
        La mayor suma de un tramo consecutivo no vacío.
    """
    prefijo = 0
    minimo_prefijo = 0
    mejor = serie[0]
    for cambio in serie:
        prefijo += cambio
        mejor = max(mejor, prefijo - minimo_prefijo)
        minimo_prefijo = min(minimo_prefijo, prefijo)
    return mejor


def tramo_por_prefijos(serie: Serie) -> Tramo:
    """Como ``oraculo_prefijos``, pero devuelve también el tramo.

    Solo se usa para caracterizar los datos sintéticos, no como estrategia.

    Args:
        serie: Serie no vacía.

    Returns:
        Tupla ``(suma, inicio, fin)`` de un tramo de suma máxima.
    """
    prefijo = 0
    minimo_prefijo, indice_minimo = 0, -1
    mejor: Tramo = (serie[0], 0, 0)
    for j, cambio in enumerate(serie):
        prefijo += cambio
        if prefijo - minimo_prefijo > mejor[0]:
            mejor = (prefijo - minimo_prefijo, indice_minimo + 1, j)
        if prefijo < minimo_prefijo:
            minimo_prefijo, indice_minimo = prefijo, j
    return mejor


def verificar_tramo(
    serie: Serie, resultado: Tramo, optimo: int, nombre: str
) -> None:
    """Comprueba que el resultado sea un tramo válido y de suma máxima.

    Args:
        serie: Serie analizada.
        resultado: Tupla ``(suma, inicio, fin)`` devuelta.
        optimo: Suma máxima calculada por un oráculo.
        nombre: Nombre de la estrategia, para los mensajes.

    Raises:
        AssertionError: Si el formato, los índices o la suma son incorrectos.
    """
    assert isinstance(resultado, tuple) and len(resultado) == 3, (
        f"{nombre}: debe devolver (suma, inicio, fin)"
    )
    suma, inicio, fin = resultado
    assert all(type(x) is int for x in resultado), f"{nombre}: no enteros"
    assert 0 <= inicio <= fin < len(serie), (
        f"{nombre}: índices inválidos {inicio}..{fin} para n={len(serie)}"
    )
    assert suma == sum(serie[inicio:fin + 1]), (
        f"{nombre}: la suma {suma} no corresponde al tramo {inicio}..{fin}"
    )
    assert suma == optimo, f"{nombre}: suma {suma}, óptimo {optimo}"


# ---------------------------------------------------------------------------
# Pruebas de los datos sintéticos
# ---------------------------------------------------------------------------

def probar_reproducibilidad() -> None:
    """Misma semilla, misma serie; semilla distinta, serie distinta."""
    assert generar_serie(5000, 7) == generar_serie(5000, 7)
    assert generar_serie(5000, 7) != generar_serie(5000, 8)
    assert generar_serie_pequena(30, 1) == generar_serie_pequena(30, 1)
    assert generar_historico(100) == generar_historico(100)


def probar_volumen_del_caso() -> None:
    """Los parámetros reproducen el volumen informado por el cliente."""
    assert HORAS_HISTORICO == 36_000
    assert NUM_CATEGORIAS == len(CATEGORIAS) == len(set(CATEGORIAS)) == 40
    historico = generar_historico(240)
    assert list(historico) == list(CATEGORIAS)
    assert all(len(serie) == 240 for serie in historico.values())
    assert len({tuple(serie) for serie in historico.values()}) == 40, (
        "cada categoría debe tener su propia serie"
    )


def probar_forma_de_la_serie() -> None:
    """Series del tamaño real: enteros, ambos signos y saturación de temporada.

    El tramo máximo no debe ser toda la serie ni una sola hora, y debe durar
    menos de un año: es la saturación de una temporada la que interesa para
    dimensionar el cuarto frío.
    """
    horas_por_anio = HORAS_POR_DIA * DIAS_POR_ANIO
    for semilla in range(5):
        serie = generar_serie(HORAS_HISTORICO, semilla)
        assert len(serie) == HORAS_HISTORICO
        assert all(type(cambio) is int for cambio in serie)
        assert any(c > 0 for c in serie) and any(c < 0 for c in serie)
        assert sum(serie) < 0, "el saldo de diez años debe ser negativo"
        optimo, inicio, fin = tramo_por_prefijos(serie)
        assert optimo > max(serie), "el tramo máximo no debe ser una hora"
        assert HORAS_POR_DIA <= fin - inicio + 1 < horas_por_anio, (
            f"semilla {semilla}: el tramo dura {fin - inicio + 1} horas"
        )
        # Empieza al abrir la temporada (puede extenderse a las primeras
        # mañanas del año siguiente, que también tienen entradas).
        dia_inicio = inicio // HORAS_POR_DIA % DIAS_POR_ANIO
        assert dia_inicio >= DIAS_POR_ANIO - DIAS_TEMPORADA - 5, (
            f"semilla {semilla}: el tramo no empieza en temporada"
        )


def probar_registros_y_adaptadores() -> None:
    """Registros inmutables, en orden y coherentes con la serie."""
    registros = generar_registros("categoria_01", 30, 3)
    copia = list(registros)
    assert a_serie(registros) == generar_serie(30, 3)
    assert registros == copia
    assert registros[13].dia == 1 and registros[13].hora == 1
    try:
        registros[0].cambio_kg = 0  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("El registro original se pudo modificar")
    assert isinstance(registros[0], RegistroHorario)


def probar_describir_hora() -> None:
    """Conversión de índices a año, día y hora del reloj."""
    assert describir_hora(0) == "año 1, día 1, 06:00"
    assert describir_hora(HORAS_POR_DIA - 1) == "año 1, día 1, 17:00"
    assert describir_hora(HORAS_POR_DIA) == "año 1, día 2, 06:00"
    assert describir_hora(HORAS_HISTORICO - 1) == "año 10, día 300, 17:00"


def probar_oraculos() -> None:
    """Los dos oráculos de la suite coinciden entre sí."""
    for k in range(300):
        serie = generar_serie_pequena(1 + k % 40, 100 + k, 1 + k % 30)
        optimo = oraculo_cuadratico(serie)
        assert optimo == oraculo_prefijos(serie)
        verificar_tramo(serie, tramo_por_prefijos(serie), optimo, "prefijos")


# ---------------------------------------------------------------------------
# Pruebas de las estrategias
# ---------------------------------------------------------------------------

CASOS_LIMITE: list[tuple[str, Serie, int, tuple[int, int] | None]] = [
    # (descripción, serie, suma esperada, (inicio, fin) si es único)
    ("una hora positiva", [5], 5, (0, 0)),
    ("una hora negativa", [-3], -3, (0, 0)),
    ("una hora en cero", [0], 0, (0, 0)),
    ("todas negativas", [-5, -2, -8, -4], -2, (1, 1)),
    ("todas positivas", [2, 1, 4, 3], 10, (0, 3)),
    ("negativas con un cero", [-1, 0, -2], 0, (1, 1)),
    ("máximo al inicio", [9, -10, 1, 2], 9, (0, 0)),
    ("máximo al final", [1, 2, -10, 9], 9, (3, 3)),
    ("tramo en la mitad izquierda", [4, 5, -20, 1, 1, 1], 9, (0, 1)),
    ("tramo en la mitad derecha", [1, 1, 1, -20, 4, 5], 9, (4, 5)),
    ("tramo que cruza la mitad", [-5, 1, 2, 3, -5], 6, (1, 3)),
    ("pico aislado", [-1, -1, 50, -1, -1], 50, (2, 2)),
    ("ejemplo de CLRS",
     [13, -3, -25, 20, -3, -16, -23, 18, 20, -7, 12, -5, -22, 15, -4, 7],
     43, (7, 10)),
    ("empate entre tramos", [2, -2, 2], 2, None),
    ("todo en cero", [0, 0, 0], 0, None),
    ("negativas repetidas", [-3, -3], -3, None),
]

# Ejemplo resuelto a mano para el informe: 8 horas, en kg.
EJEMPLO_MANUAL: Serie = [3, -5, 4, -1, 2, 6, -9, 5]
RESULTADO_MANUAL: Tramo = (11, 2, 5)


def probar_casos_limite(estrategias: dict[str, Estrategia]) -> None:
    """Casos borde con resultado conocido, para cada estrategia."""
    for descripcion, serie, suma, indices in CASOS_LIMITE:
        assert oraculo_cuadratico(serie) == suma, descripcion
        for nombre, estrategia in estrategias.items():
            resultado = estrategia(list(serie))
            verificar_tramo(serie, resultado, suma, f"{nombre} ({descripcion})")
            if indices is not None:
                assert resultado[1:] == indices, (
                    f"{nombre} ({descripcion}): tramo {resultado[1:]}, "
                    f"esperado {indices}"
                )


def probar_ejemplo_manual(estrategias: dict[str, Estrategia]) -> None:
    """El ejemplo del informe da el tramo 2..5 con 11 kg.

    Con n = 8, dividir y vencer parte en 0..3 y 4..7: el óptimo cruza la
    mitad (izquierda 4 - 1 = 3, derecha 2 + 6 = 8).
    """
    assert oraculo_cuadratico(EJEMPLO_MANUAL) == RESULTADO_MANUAL[0]
    for nombre, estrategia in estrategias.items():
        assert estrategia(list(EJEMPLO_MANUAL)) == RESULTADO_MANUAL, nombre


def probar_serie_vacia(estrategias: dict[str, Estrategia]) -> None:
    """Una serie vacía no tiene tramo: debe lanzar ValueError."""
    for nombre, estrategia in estrategias.items():
        try:
            estrategia([])
        except ValueError:
            continue
        raise AssertionError(f"{nombre} no lanzó ValueError con serie vacía")


def probar_no_modifica_entrada(estrategias: dict[str, Estrategia]) -> None:
    """Ninguna estrategia altera la serie original (trazabilidad)."""
    serie = generar_serie(500, 11)
    copia = list(serie)
    for nombre, estrategia in estrategias.items():
        estrategia(serie)
        assert serie == copia, f"{nombre} modificó la serie"


def probar_aleatorias_contra_oraculo(
    estrategias: dict[str, Estrategia]
) -> None:
    """200 series aleatorias de 1 a 64 horas: todas coinciden con el oráculo.

    Rangos pequeños fuerzan empates y ceros; rangos grandes, valores
    dispersos. Cada instancia usa una semilla distinta y fija.
    """
    assert INSTANCIAS_ALEATORIAS >= 20
    for k in range(INSTANCIAS_ALEATORIAS):
        serie = generar_serie_pequena(
            1 + k % 64, SEMILLA_ALEATORIAS + k, (2, 10, 50, 500)[k % 4]
        )
        optimo = oraculo_cuadratico(serie)
        for nombre, estrategia in estrategias.items():
            verificar_tramo(serie, estrategia(serie), optimo, nombre)
    print(f"  {INSTANCIAS_ALEATORIAS} series aleatorias: "
          f"{len(estrategias)} estrategia(s) coinciden con el oráculo.")


def probar_series_del_modelo(estrategias: dict[str, Estrategia]) -> None:
    """Series de 600 horas del modelo sintético, incluida la exhaustiva."""
    for semilla in range(5):
        serie = generar_serie(600, semilla)
        optimo = oraculo_cuadratico(serie)
        for nombre, estrategia in estrategias.items():
            verificar_tramo(serie, estrategia(serie), optimo, nombre)


def probar_volumen_real(
    estrategias: dict[str, Estrategia], exhaustivas: set[str]
) -> None:
    """36.000 horas por categoría: estrategias rápidas contra el oráculo.

    La exhaustiva no se ejecuta aquí: con Theta(n^2) serían unos 6,5 * 10^8
    tramos por categoría.
    """
    rapidas = {
        nombre: estrategia for nombre, estrategia in estrategias.items()
        if nombre not in exhaustivas
    }
    historico = generar_historico(
        categorias=CATEGORIAS[:CATEGORIAS_VOLUMEN_REAL]
    )
    for categoria, serie in historico.items():
        optimo = oraculo_prefijos(serie)
        tramos = [estrategia(serie) for estrategia in rapidas.values()]
        for nombre, resultado in zip(rapidas, tramos):
            verificar_tramo(serie, resultado, optimo, nombre)
        if tramos:
            _, inicio, fin = tramos[0]
            print(f"  {categoria}: +{optimo} kg entre "
                  f"{describir_hora(inicio)} y {describir_hora(fin)} "
                  f"({fin - inicio + 1} horas).")


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------

PRUEBAS_DATOS: list[Callable[[], None]] = [
    probar_reproducibilidad,
    probar_volumen_del_caso,
    probar_forma_de_la_serie,
    probar_registros_y_adaptadores,
    probar_describir_hora,
    probar_oraculos,
]

PRUEBAS_ESTRATEGIAS: list[Callable[[dict[str, Estrategia]], None]] = [
    probar_casos_limite,
    probar_ejemplo_manual,
    probar_serie_vacia,
    probar_no_modifica_entrada,
    probar_aleatorias_contra_oraculo,
    probar_series_del_modelo,
]


def main() -> int:
    """Ejecuta todas las pruebas y reporta las implementaciones pendientes.

    Returns:
        0 si todo pasó y no hay pendientes; 1 en caso contrario.
    """
    for prueba in PRUEBAS_DATOS:
        prueba()
        print(f"[ok] {prueba.__name__}")

    estrategias, exhaustivas, pendientes = cargar_implementaciones()
    for nombre in pendientes:
        print(f"[pendiente] {nombre} no existe todavía")
    if estrategias:
        for prueba_estrategia in PRUEBAS_ESTRATEGIAS:
            prueba_estrategia(estrategias)
            print(f"[ok] {prueba_estrategia.__name__}")
        probar_volumen_real(estrategias, exhaustivas)
        print("[ok] probar_volumen_real")

    total = len(PRUEBAS_DATOS) + (
        len(PRUEBAS_ESTRATEGIAS) + 1 if estrategias else 0
    )
    print(f"\n{total} pruebas pasaron con: "
          f"{', '.join(estrategias) or 'ninguna estrategia'}.")
    if pendientes:
        print(f"Faltan {len(pendientes)} implementación(es); "
              "la suite no está completa.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
