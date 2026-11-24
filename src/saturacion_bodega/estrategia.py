"""Estrategias para el tramo de mayor crecimiento del inventario.

Operación 4 del Banco Regional de Alimentos: dada la serie de cambios netos
horarios de una categoría (en kg, pueden ser negativos), encontrar el tramo
de horas consecutivas cuya suma es la mayor del histórico.

Contrato común con ``exhaustivo.tramo_maximo_exhaustivo``:

* Entrada: ``cambios: list[int]`` en orden cronológico; no se modifica.
* Salida: ``(suma, inicio, fin)``. El tramo es ``cambios[inicio:fin + 1]``,
  con índices en base cero y ``fin`` incluido.
* El tramo no es vacío: si todos los cambios son negativos se reporta la
  hora menos negativa.
* Una serie vacía lanza ``ValueError``.
* Con varios tramos óptimos se devuelve uno cualquiera; la suma es exacta.
"""

Serie = list[int]
Tramo = tuple[int, int, int]


def _validar_serie(cambios: Serie) -> None:
    """Comprueba que la serie tenga al menos una hora.

    Args:
        cambios: Cambios netos horarios del inventario, en kg.

    Raises:
        ValueError: Si la lista de cambios está vacía.
    """
    if not cambios:
        raise ValueError("La serie debe contener al menos una hora.")


def _tramo_cruzado(
    cambios: Serie, inicio: int, medio: int, fin: int
) -> Tramo:
    """Encuentra el mejor tramo que cruza el punto medio.

    Un tramo que cruza el medio es la unión de uno que termina en ``medio``
    y otro que empieza en ``medio + 1``. Cada lado se optimiza por separado
    con un barrido lineal que acumula la suma desde el medio hacia afuera.
    Cuesta Theta(fin - inicio + 1) tiempo y O(1) memoria.

    Args:
        cambios: Cambios netos horarios del inventario, en kg.
        inicio: Primer índice del rango considerado (incluido).
        medio: Último índice de la mitad izquierda; ``inicio <= medio < fin``.
        fin: Último índice del rango considerado (incluido).

    Returns:
        Tupla ``(suma, inicio_tramo, fin_tramo)`` del mejor tramo que
        incluye las horas ``medio`` y ``medio + 1``.
    """
    suma = 0
    mejor_izquierda = cambios[medio]
    inicio_tramo = medio
    for hora in range(medio, inicio - 1, -1):
        suma += cambios[hora]
        if suma > mejor_izquierda:
            mejor_izquierda = suma
            inicio_tramo = hora

    suma = 0
    mejor_derecha = cambios[medio + 1]
    fin_tramo = medio + 1
    for hora in range(medio + 1, fin + 1):
        suma += cambios[hora]
        if suma > mejor_derecha:
            mejor_derecha = suma
            fin_tramo = hora

    return mejor_izquierda + mejor_derecha, inicio_tramo, fin_tramo


def _tramo_dividir(cambios: Serie, inicio: int, fin: int) -> Tramo:
    """Resuelve ``cambios[inicio..fin]`` por dividir y vencer.

    Args:
        cambios: Cambios netos horarios del inventario, en kg.
        inicio: Primer índice del rango (incluido).
        fin: Último índice del rango (incluido).

    Returns:
        Tupla ``(suma, inicio_tramo, fin_tramo)`` del mejor tramo dentro
        del rango. En empates prefiere el izquierdo, luego el derecho y
        al final el cruzado.
    """
    if inicio == fin:
        return cambios[inicio], inicio, fin

    medio = (inicio + fin) // 2
    izquierdo = _tramo_dividir(cambios, inicio, medio)
    derecho = _tramo_dividir(cambios, medio + 1, fin)
    cruzado = _tramo_cruzado(cambios, inicio, medio, fin)

    mejor = izquierdo
    if derecho[0] > mejor[0]:
        mejor = derecho
    if cruzado[0] > mejor[0]:
        mejor = cruzado
    return mejor


def tramo_maximo_dividir(cambios: Serie) -> Tramo:
    """Encuentra el tramo de mayor crecimiento por dividir y vencer.

    Divide la serie por la mitad. El tramo óptimo está completo en la mitad
    izquierda, completo en la derecha o cruza el punto medio; los dos
    primeros casos son el mismo problema con la mitad de horas y el tercero
    se resuelve con dos barridos lineales. La recurrencia es
    T(n) = 2T(n/2) + Theta(n), que por el caso 2 del método maestro da
    Theta(n log n) en tiempo. La memoria auxiliar es O(log n) por la pila
    de recursión; no se copian sublistas.

    Args:
        cambios: Cambios netos horarios del inventario, en kg y en orden
            cronológico. Se asumen valores enteros válidos.

    Returns:
        Tupla ``(suma, inicio, fin)`` del tramo óptimo. Los índices parten
        de cero y ambos extremos están incluidos. Si todos los cambios
        son negativos, devuelve la hora menos negativa.

    Raises:
        ValueError: Si la lista de cambios está vacía.
    """
    _validar_serie(cambios)
    return _tramo_dividir(cambios, 0, len(cambios) - 1)


def tramo_maximo_kadane(cambios: Serie) -> Tramo:
    """Encuentra el tramo de mayor crecimiento con el algoritmo de Kadane.

    Recorre la serie una sola vez y lleva el mejor tramo que termina en la
    hora actual. Si el acumulado anterior es negativo, no ayuda a ningún
    tramo que continúe: se descarta y el tramo empieza de nuevo en la hora
    actual. En caso contrario, se extiende. Theta(n) tiempo y O(1) memoria
    auxiliar, sin recursión ni copias.

    Args:
        cambios: Cambios netos horarios del inventario, en kg y en orden
            cronológico. Se asumen valores enteros válidos.

    Returns:
        Tupla ``(suma, inicio, fin)`` del tramo óptimo. Los índices parten
        de cero y ambos extremos están incluidos. Si todos los cambios
        son negativos, devuelve la hora menos negativa.

    Raises:
        ValueError: Si la lista de cambios está vacía.
    """
    _validar_serie(cambios)

    mejor_suma = cambios[0]
    mejor_inicio = 0
    mejor_fin = 0
    suma_actual = cambios[0]
    inicio_actual = 0

    for hora in range(1, len(cambios)):
        if suma_actual < 0:
            suma_actual = cambios[hora]
            inicio_actual = hora
        else:
            suma_actual += cambios[hora]
        if suma_actual > mejor_suma:
            mejor_suma = suma_actual
            mejor_inicio = inicio_actual
            mejor_fin = hora

    return mejor_suma, mejor_inicio, mejor_fin
