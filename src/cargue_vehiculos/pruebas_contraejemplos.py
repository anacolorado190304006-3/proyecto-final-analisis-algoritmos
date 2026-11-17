"""Contraejemplos sintéticos de cargue del Banco Regional de Alimentos.

Ejecutar desde la raíz: python src/cargue_vehiculos/pruebas_contraejemplos.py
Las instancias reducidas usan 1000 kg para facilitar su revisión manual.
Los índices son originales, en base cero; los lotes son indivisibles.
"""

from collections.abc import Callable
from fractions import Fraction

from estrategia import mochila_01
from exhaustivo import Lote, cargar_exhaustivo
from pruebas_mochila import verificar_solucion
from regla_actual import cargar_por_densidad, cargar_por_vencimiento

Solucion = tuple[int, list[int]]


def _comparar_soluciones(
    lotes: list[Lote],
    capacidad_kg: int,
    regla: Callable[[list[Lote], int], Solucion],
) -> dict[str, Solucion]:
    """Ejecuta la regla y los dos algoritmos exactos, y valida sus salidas.

    Args:
        lotes: Entre cuatro y ocho lotes candidatos, sin modificar.
        capacidad_kg: Capacidad positiva del vehículo, en kilogramos.
        regla: Función voraz que se contrasta con el óptimo.

    Returns:
        Resultados de Regla, Exhaustiva y DP, con índices originales.

    Raises:
        AssertionError: Si hay mutación, una salida inválida, discrepancia
            entre algoritmos exactos o la regla alcanza el óptimo.
    """
    assert 4 <= len(lotes) <= 8
    assert type(capacidad_kg) is int and capacidad_kg > 0
    copia = lotes.copy()
    pesos = [lote[0] for lote in lotes]
    valores = [lote[1] for lote in lotes]
    resultados: dict[str, Solucion] = {}

    for nombre, algoritmo in (
        ("Regla", regla), ("Exhaustiva", cargar_exhaustivo)
    ):
        resultados[nombre] = algoritmo(lotes, capacidad_kg)
        assert lotes == copia, f"{nombre} modificó los lotes"

    resultados["DP"] = mochila_01(pesos, valores, capacidad_kg)
    assert pesos == [lote[0] for lote in copia], "DP modificó los pesos"
    assert valores == [lote[1] for lote in copia], "DP modificó los valores"
    assert lotes == copia

    for valor, indices in resultados.values():
        assert type(valor) is int
        assert all(type(indice) is int for indice in indices)
        # Sumar cada registro completo verifica el cargue sin fracciones.
        verificar_solucion(pesos, valores, capacidad_kg, valor, indices)

    optimo = resultados["Exhaustiva"][0]
    assert optimo == resultados["DP"][0], "Exhaustiva y DP discrepan"
    assert resultados["Regla"][0] < optimo, "No es un contraejemplo"
    return resultados


def _mostrar_resultados(
    nombre: str,
    lotes: list[Lote],
    capacidad_kg: int,
    resultados: dict[str, Solucion],
    explicacion: str,
) -> None:
    """Imprime los datos y las comparaciones calculadas en tablas Markdown.

    Args:
        nombre: Regla evaluada.
        lotes: Registros originales de la instancia.
        capacidad_kg: Capacidad máxima, en kilogramos.
        resultados: Salidas ya verificadas de los tres algoritmos.
        explicacion: Decisión que explica la pérdida de valor nutricional.
    """
    print(f"\nContraejemplo por {nombre}")
    print(f"Capacidad: {capacidad_kg} kg. Índices en base cero.\n")
    print("| Índice | Peso (kg) | Valor nutricional | Días para vencer |")
    print("|---|---|---|---|")
    for indice, (peso, valor, dias) in enumerate(lotes):
        print(f"| {indice} | {peso} | {valor} | {dias} |")

    print("\n| Método | Índices | Peso (kg) | Valor | Diferencia al óptimo |")
    print("|---|---|---|---|---|")
    optimo = resultados["Exhaustiva"][0]
    for metodo, (valor, indices) in resultados.items():
        peso = sum(lotes[indice][0] for indice in indices)
        diferencia = optimo - valor
        print(f"| {metodo} | {indices} | {peso} | {valor} | {diferencia} |")
    print(f"\n{explicacion}")


def probar_contraejemplo_vencimiento() -> None:
    """Comprueba la parada anticipada pese a existir un cargue de mayor valor.

    Raises:
        AssertionError: Si cambia la selección, el óptimo o la parada
            ante el primer lote que no cabe.
    """
    lotes: list[Lote] = [
        (450, 900, 4),
        (300, 180, 1),
        (550, 1100, 5),
        (500, 250, 2),
        (250, 400, 3),
        (150, 200, 6),
    ]
    capacidad_kg = 1000
    resultados = _comparar_soluciones(
        lotes, capacidad_kg, cargar_por_vencimiento
    )
    orden = sorted(range(len(lotes)), key=lambda i: lotes[i][2])
    assert orden == [1, 3, 4, 0, 2, 5]
    assert resultados["Regla"] == (430, [1, 3])
    assert resultados["Exhaustiva"] == (2000, [0, 2])
    assert resultados["Exhaustiva"][0] - resultados["Regla"][0] == 1570
    restante = capacidad_kg - sum(lotes[i][0] for i in [1, 3])
    assert lotes[4][0] > restante
    assert lotes[5][0] <= restante and 5 not in resultados["Regla"][1]

    _mostrar_resultados(
        "vencimiento", lotes, capacidad_kg, resultados,
        "Orden por vencimiento: [1, 3, 4, 0, 2, 5]. Carga 1 y 3 "
        "(800 kg) y se detiene ante el lote 4 (250 kg), pues quedan "
        "200 kg. No llega al lote 5, que sí cabría. Priorizar fechas "
        "deja fuera los lotes 0 y 2: juntos pesan 1000 kg y aportan "
        "2000 unidades de valor, frente a 430 de la regla.",
    )


def probar_contraejemplo_densidad() -> None:
    """Comprueba que continuar tras omisiones no corrige la elección inicial.

    Raises:
        AssertionError: Si aparecen empates de densidad o cambian el orden,
            la selección voraz o el valor óptimo comprobado.
    """
    lotes: list[Lote] = [
        (500, 950, 4),
        (600, 1320, 1),
        (100, 80, 5),
        (500, 1000, 2),
        (200, 100, 3),
    ]
    capacidad_kg = 1000
    resultados = _comparar_soluciones(
        lotes, capacidad_kg, cargar_por_densidad
    )
    densidades = [Fraction(valor, peso) for peso, valor, _ in lotes]
    assert len(set(densidades)) == len(lotes), "Hay densidades empatadas"
    orden = sorted(
        range(len(lotes)), key=lambda i: densidades[i], reverse=True
    )
    assert orden == [1, 3, 0, 2, 4]
    assert resultados["Regla"] == (1500, [1, 2, 4])
    assert resultados["Exhaustiva"] == (1950, [0, 3])
    assert resultados["Exhaustiva"][0] - resultados["Regla"][0] == 450
    restante = capacidad_kg - lotes[1][0]
    assert lotes[3][0] > restante and lotes[0][0] > restante
    assert lotes[2][0] + lotes[4][0] <= restante

    _mostrar_resultados(
        "densidad", lotes, capacidad_kg, resultados,
        "Orden por densidad: [1, 3, 0, 2, 4], con razones exactas "
        "11/5 > 2 > 19/10 > 4/5 > 1/2. El lote 1 deja 400 kg: "
        "los lotes 3 y 0, de 500 kg cada uno, ya no caben. La regla "
        "continúa y carga 2 y 4, alcanzando 1500 unidades de valor. "
        "Elegir juntos 0 y 3 permite obtener 1950; la elección inicial "
        "por densidad impide esa combinación de lotes indivisibles.",
    )


if __name__ == "__main__":
    probar_contraejemplo_vencimiento()
    probar_contraejemplo_densidad()
    print("\nLos dos contraejemplos pasaron todas las verificaciones.")
