"""Solución exhaustiva del cargue 0/1 para validar instancias pequeñas."""

from itertools import combinations

Lote = tuple[int, int, int]


def _validar_entradas(lotes: list[Lote], capacidad_kg: int) -> None:
    """Valida el formato y los valores de entrada sin modificarlos.

    Args:
        lotes: Tuplas (peso_kg, valor_nutricional, dias_para_vencer).
        capacidad_kg: Capacidad máxima del vehículo en kilogramos.

    Raises:
        ValueError: Si la capacidad no es un entero no negativo, los lotes
            no son una lista de tuplas de tres enteros, algún peso no es
            positivo o algún valor nutricional es negativo. No se aceptan
            booleanos como enteros.
    """
    if isinstance(capacidad_kg, bool) or not isinstance(capacidad_kg, int):
        raise ValueError("La capacidad debe ser un entero.")
    if capacidad_kg < 0:
        raise ValueError("La capacidad no puede ser negativa.")
    if not isinstance(lotes, list):
        raise ValueError("Los lotes deben ser una lista.")
    for lote in lotes:
        if not isinstance(lote, tuple) or len(lote) != 3:
            raise ValueError("Cada lote debe ser una tupla de tres enteros.")
        if any(
            isinstance(dato, bool) or not isinstance(dato, int)
            for dato in lote
        ):
            raise ValueError("Los datos de cada lote deben ser enteros.")
        peso, valor, _ = lote
        if peso <= 0:
            raise ValueError("Los pesos deben ser enteros positivos.")
        if valor < 0:
            raise ValueError(
                "Los valores nutricionales no pueden ser negativos."
            )


def cargar_exhaustivo(
    lotes: list[Lote], capacidad_kg: int
) -> tuple[int, list[int]]:
    """Encuentra el valor nutricional máximo enumerando todos los subconjuntos.

    Los subconjuntos se generan por cantidad de lotes y, para igual cantidad,
    por orden lexicográfico de índices. En un empate de valor se conserva
    la primera solución: menos lotes y luego menores índices lexicográficos.
    Los días para vencer no intervienen en la optimización ni se utilizan
    para filtrar lotes; la entrada debe contener los candidatos elegibles.

    Complejidad:
        Tiempo Theta(n * 2**n) para n >= 1, suponiendo aritmética de costo
        constante: hay 2**n subconjuntos y la suma de sus tamaños es
        n * 2**(n - 1). Se calculan peso y valor para cada subconjunto.
        La capacidad no determina el número de iteraciones. Al duplicar n,
        el término n * 2**n se multiplica por 2**(n + 1).
        Memoria auxiliar O(n): el iterador conserva un conjunto de índices
        y una combinación a la vez. La mejor selección y la salida ocupan
        O(n) adicional; no se almacenan los 2**n subconjuntos. La memoria
        total adicional es O(n). Usar únicamente con instancias pequeñas.

    Args:
        lotes: Lista de tuplas (peso_kg, valor_nutricional, dias_para_vencer),
            con peso entero positivo y valor entero no negativo. No se
            modifica la lista ni sus registros.
        capacidad_kg: Capacidad máxima entera no negativa, en kilogramos.

    Returns:
        Tupla (valor_optimo, indices), con índices originales en base cero,
        ascendentes y sin repeticiones. Si el óptimo es cero, devuelve
        (0, []). Todos los lotes seleccionados se cargan completos.

    Raises:
        ValueError: Si las entradas incumplen el formato o los valores
            descritos, incluidos booleanos utilizados como enteros.
    """
    _validar_entradas(lotes, capacidad_kg)
    cantidad_lotes = len(lotes)
    mejor_valor = 0
    mejores_indices: list[int] = []

    for cantidad in range(cantidad_lotes + 1):
        for indices in combinations(range(cantidad_lotes), cantidad):
            peso_total = sum(lotes[i][0] for i in indices)
            valor_total = sum(lotes[i][1] for i in indices)
            if peso_total <= capacidad_kg and valor_total > mejor_valor:
                mejor_valor = valor_total
                mejores_indices = list(indices)

    return mejor_valor, mejores_indices
