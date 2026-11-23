"""Búsqueda exhaustiva del tramo de mayor crecimiento de inventario."""


def tramo_maximo_exhaustivo(cambios: list[int]) -> tuple[int, int, int]:
    """Encuentra el tramo consecutivo no vacío con mayor suma.

    Recorre los inicios y finales en orden ascendente. Para cada inicio,
    acumula el siguiente cambio sin volver a sumar el tramo completo.
    En empates conserva el primer tramo encontrado: menor inicio y,
    para ese inicio, menor fin. No modifica la lista de entrada.

    Evalúa n(n + 1) / 2 tramos: tiempo Theta(n^2) y memoria auxiliar
    O(1), bajo el modelo de operaciones aritméticas de costo constante.
    No almacena los tramos ni crea copias de la serie. Debe utilizarse
    en instancias pequeñas o mediciones acotadas, no en el histórico
    completo de 36.000 horas por categoría.

    Args:
        cambios: Cambios netos horarios del inventario, en kg y en orden
            cronológico. Se asumen valores enteros válidos.

    Returns:
        Tupla (suma, inicio, fin) del tramo óptimo. Los índices parten
        de cero y ambos extremos están incluidos. Si todos los cambios
        son negativos, devuelve la hora menos negativa.

    Raises:
        ValueError: Si la lista de cambios está vacía.
    """
    if not cambios:
        raise ValueError("La serie debe contener al menos una hora.")

    mejor_suma = cambios[0]
    mejor_inicio = 0
    mejor_fin = 0

    for inicio in range(len(cambios)):
        suma = 0
        for fin in range(inicio, len(cambios)):
            suma += cambios[fin]
            if suma > mejor_suma:
                mejor_suma = suma
                mejor_inicio = inicio
                mejor_fin = fin

    return mejor_suma, mejor_inicio, mejor_fin
