"""Estrategia de cargue de vehiculos: mochila 0/1 con programacion dinamica.

Cada lote candidato tiene un peso entero (kg) y un valor nutricional entero
(raciones ponderadas por prioridad). Un lote no se fracciona: sube completo
o no sube.
"""


def _validar(pesos: list[int], valores: list[int], capacidad: int) -> None:
    """Valida las entradas de las funciones de cargue.

    Args:
        pesos: peso en kg de cada lote.
        valores: valor nutricional de cada lote.
        capacidad: capacidad maxima del vehiculo en kg.

    Raises:
        ValueError: si las listas no tienen el mismo largo, si la
            capacidad es negativa o si algun peso o valor es invalido.
    """
    if len(pesos) != len(valores):
        raise ValueError("pesos y valores deben tener el mismo largo.")
    if isinstance(capacidad, bool) or not isinstance(capacidad, int):
        raise ValueError("La capacidad debe ser un entero.")
    if capacidad < 0:
        raise ValueError("La capacidad no puede ser negativa.")
    for peso in pesos:
        if isinstance(peso, bool) or not isinstance(peso, int) or peso <= 0:
            raise ValueError("Los pesos deben ser enteros positivos.")
    for valor in valores:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValueError("Los valores deben ser enteros no negativos.")


def mochila_01(
    pesos: list[int], valores: list[int], capacidad: int
) -> tuple[int, list[int]]:
    """Resuelve la mochila 0/1 con programacion dinamica.

    Recurrencia (V[i][w] = mejor valor con los primeros i lotes y
    capacidad w):

        V[i][w] = V[i-1][w]                              si pesos[i-1] > w
        V[i][w] = max(V[i-1][w],
                      V[i-1][w - pesos[i-1]] + valores[i-1])   en otro caso

    con V[0][w] = 0. Se usa un solo arreglo recorrido de derecha a
    izquierda y se guarda, para cada lote, en que capacidades conviene
    tomarlo; con esas marcas se reconstruyen los lotes elegidos.

    Args:
        pesos: peso en kg de cada lote (enteros positivos).
        valores: valor nutricional de cada lote (enteros no negativos).
        capacidad: capacidad maxima del vehiculo en kg.

    Returns:
        Una tupla (valor_maximo, indices) con el valor nutricional maximo
        alcanzable sin superar la capacidad y los indices (ordenados,
        base 0) de los lotes seleccionados.

    Raises:
        ValueError: si las entradas son invalidas.
    """
    _validar(pesos, valores, capacidad)
    n = len(pesos)

    mejor = [0] * (capacidad + 1)       # mejor[w]: valor maximo con cap. w
    tomar: list[bytearray] = []         # tomar[i][w] = 1 si el lote i se toma

    for i in range(n):
        peso, valor = pesos[i], valores[i]
        marca = bytearray(capacidad + 1)
        # De derecha a izquierda: cada lote se usa a lo sumo una vez.
        for w in range(capacidad, peso - 1, -1):
            candidato = mejor[w - peso] + valor
            if candidato > mejor[w]:
                mejor[w] = candidato
                marca[w] = 1
        tomar.append(marca)

    # Reconstruccion: se recorre desde el ultimo lote hacia el primero.
    seleccionados: list[int] = []
    w = capacidad
    for i in range(n - 1, -1, -1):
        if tomar[i][w]:
            seleccionados.append(i)
            w -= pesos[i]
    seleccionados.reverse()
    return mejor[capacidad], seleccionados


def cargue_por_vencimiento(
    pesos: list[int], valores: list[int], capacidad: int
) -> tuple[int, list[int]]:
    """Cargue actual: sube lotes en orden de vencimiento hasta que no cabe.

    Los lotes ya llegan ordenados por fecha de vencimiento (FEFO). Se
    cargan en ese orden y se detiene en el primer lote que no cabe.
    Sirve como referencia para medir cuanto mejora la mochila 0/1.

    Args:
        pesos: peso en kg de cada lote, en orden FEFO.
        valores: valor nutricional de cada lote, en orden FEFO.
        capacidad: capacidad maxima del vehiculo en kg.

    Returns:
        Una tupla (valor_total, indices) de los lotes cargados.

    Raises:
        ValueError: si las entradas son invalidas.
    """
    _validar(pesos, valores, capacidad)
    carga = 0
    valor_total = 0
    seleccionados: list[int] = []
    for i, peso in enumerate(pesos):
        if carga + peso > capacidad:
            break
        carga += peso
        valor_total += valores[i]
        seleccionados.append(i)
    return valor_total, seleccionados
