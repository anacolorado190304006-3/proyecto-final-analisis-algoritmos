"""Reglas voraces de cargue por vencimiento y densidad nutricional.

Ambas reglas reciben candidatos elegibles; no filtran lotes por vencimiento.
Reutilizan Lote = tuple[int, int, int] y la validación de exhaustivo.py,
sin ejecutar la búsqueda exhaustiva.

Para n lotes, cada regla usa O(n log n) tiempo en el peor caso: valida en
O(n), ordena los candidatos, recorre como máximo n lotes y ordena los k
índices seleccionados en O(k log k), con k <= n. La memoria auxiliar es
O(n), incluidas las estructuras de ordenación; la salida ocupa O(k).
La capacidad afecta la selección, pero no dimensiona ninguna tabla.
Estos costos suponen aritmética de costo constante. En densidad, crear y
comparar Fraction también depende del tamaño en bits de pesos y valores.
Ninguna regla garantiza el valor óptimo de la mochila 0/1.
"""

from fractions import Fraction

if __package__:
    from .exhaustivo import Lote, _validar_entradas
else:
    from exhaustivo import Lote, _validar_entradas


def cargar_por_vencimiento(
    lotes: list[Lote], capacidad_kg: int
) -> tuple[int, list[int]]:
    """Carga por vencimiento y se detiene en el primer lote que no cabe.

    Ordena los índices por días para vencer de menor a mayor. La ordenación
    es estable: los empates conservan el orden original de entrada. Cada
    lote se carga completo y como máximo una vez. No se modifica la entrada.
    Tiempo O(n log n) en el peor caso y memoria adicional O(n).

    Args:
        lotes: Lista de tuplas (peso_kg, valor_nutricional, dias_para_vencer),
            con peso entero positivo, valor entero no negativo y días
            enteros. Los candidatos deben haber sido validados como aptos
            para despacho antes de llamar a esta función.
        capacidad_kg: Capacidad máxima entera no negativa, en kilogramos.

    Returns:
        Tupla (valor_total, indices), con índices originales en base cero,
        ascendentes y sin repeticiones. Si no carga lotes, devuelve (0, []).

    Raises:
        ValueError: Si el formato o los valores de entrada son inválidos,
            incluidos booleanos utilizados como enteros.
    """
    _validar_entradas(lotes, capacidad_kg)
    orden = sorted(range(len(lotes)), key=lambda i: lotes[i][2])
    peso_total = 0
    valor_total = 0
    seleccionados: list[int] = []

    for indice in orden:
        peso, valor, _ = lotes[indice]
        if peso_total + peso > capacidad_kg:
            break
        peso_total += peso
        valor_total += valor
        seleccionados.append(indice)

    seleccionados.sort()
    return valor_total, seleccionados


def cargar_por_densidad(
    lotes: list[Lote], capacidad_kg: int
) -> tuple[int, list[int]]:
    """Carga por densidad descendente, omitiendo los lotes que no caben.

    Compara valor/peso exactamente con Fraction. La ordenación estable
    conserva el orden original en empates, incluso con razones equivalentes.
    Continúa tras un lote que no cabe; no fracciona ni repite lotes y no
    modifica la entrada. Tiempo O(n log n) en el peor caso y memoria
    adicional O(n), bajo el modelo aritmético indicado en el módulo.

    Args:
        lotes: Lista de tuplas (peso_kg, valor_nutricional, dias_para_vencer),
            con peso entero positivo, valor entero no negativo y días
            enteros. Los días no intervienen en la selección.
        capacidad_kg: Capacidad máxima entera no negativa, en kilogramos.

    Returns:
        Tupla (valor_total, indices), con índices originales en base cero,
        ascendentes y sin repeticiones. Si no carga lotes, devuelve (0, []).

    Raises:
        ValueError: Si el formato o los valores de entrada son inválidos,
            incluidos booleanos utilizados como enteros.
    """
    _validar_entradas(lotes, capacidad_kg)
    orden = sorted(
        range(len(lotes)),
        key=lambda i: Fraction(lotes[i][1], lotes[i][0]),
        reverse=True,
    )
    peso_total = 0
    valor_total = 0
    seleccionados: list[int] = []

    for indice in orden:
        peso, valor, _ = lotes[indice]
        if peso_total + peso > capacidad_kg:
            continue
        peso_total += peso
        valor_total += valor
        seleccionados.append(indice)

    seleccionados.sort()
    return valor_total, seleccionados
