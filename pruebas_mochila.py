"""Pruebas de la mochila 0/1 (estrategia.py) con assert."""
import random
from itertools import combinations

from estrategia import cargue_por_vencimiento, mochila_01


def fuerza_bruta(
    pesos: list[int], valores: list[int], capacidad: int
) -> int:
    """Mejor valor probando todos los subconjuntos (solo n pequeno)."""
    n = len(pesos)
    mejor = 0
    for k in range(n + 1):
        for grupo in combinations(range(n), k):
            if sum(pesos[i] for i in grupo) <= capacidad:
                mejor = max(mejor, sum(valores[i] for i in grupo))
    return mejor


def verificar_solucion(
    pesos: list[int], valores: list[int], capacidad: int,
    valor: int, indices: list[int],
) -> None:
    """Comprueba que la solucion sea coherente y respete la capacidad."""
    assert indices == sorted(set(indices)), "indices repetidos o desordenados"
    assert all(0 <= i < len(pesos) for i in indices)
    assert sum(pesos[i] for i in indices) <= capacidad, "supera capacidad"
    assert sum(valores[i] for i in indices) == valor, "valor inconsistente"


def probar_ejemplo_a_mano() -> None:
    """Ejemplo del informe: capacidad 7, tres lotes."""
    pesos, valores = [5, 4, 3], [10, 7, 5]
    valor, indices = mochila_01(pesos, valores, 7)
    assert valor == 12 and indices == [1, 2]
    verificar_solucion(pesos, valores, 7, valor, indices)
    # El cargue por vencimiento toma el lote 0 (5 kg) y el lote 1 ya no cabe.
    assert cargue_por_vencimiento(pesos, valores, 7)[0] == 10


def probar_casos_borde() -> None:
    """Listas vacias, capacidad cero, nada cabe, todo cabe, ajuste exacto."""
    assert mochila_01([], [], 10) == (0, [])
    assert mochila_01([3, 4], [5, 6], 0) == (0, [])
    assert mochila_01([8, 9], [5, 6], 7) == (0, [])          # nada cabe
    assert mochila_01([2, 3, 4], [1, 2, 3], 100) == (6, [0, 1, 2])
    assert mochila_01([7], [9], 7) == (9, [0])               # exacto
    assert mochila_01([7], [9], 6) == (0, [])
    assert mochila_01([2, 2], [5, 5], 2)[0] == 5             # empate: suma


def probar_no_modifica_entradas() -> None:
    """La funcion no altera las listas recibidas."""
    pesos, valores = [5, 4, 3], [10, 7, 5]
    copia_p, copia_v = list(pesos), list(valores)
    mochila_01(pesos, valores, 7)
    assert pesos == copia_p and valores == copia_v


def probar_contra_fuerza_bruta() -> None:
    """300 instancias aleatorias pequenas: el DP es optimo."""
    azar = random.Random(42)
    for _ in range(300):
        n = azar.randint(0, 12)
        pesos = [azar.randint(1, 20) for _ in range(n)]
        valores = [azar.randint(0, 50) for _ in range(n)]
        capacidad = azar.randint(0, 60)
        valor, indices = mochila_01(pesos, valores, capacidad)
        verificar_solucion(pesos, valores, capacidad, valor, indices)
        assert valor == fuerza_bruta(pesos, valores, capacidad)


def probar_supera_al_cargue_actual() -> None:
    """El DP nunca es peor que el cargue por vencimiento."""
    azar = random.Random(7)
    for _ in range(100):
        n = azar.randint(5, 40)
        pesos = [azar.randint(20, 600) for _ in range(n)]
        valores = [p * azar.randint(2, 12) for p in pesos]
        capacidad = azar.randint(2500, 4000)
        v_dp, _ = mochila_01(pesos, valores, capacidad)
        v_ref, idx_ref = cargue_por_vencimiento(pesos, valores, capacidad)
        assert v_dp >= v_ref
        assert sum(pesos[i] for i in idx_ref) <= capacidad


def probar_tamano_realista() -> None:
    """600 lotes y 4000 kg: respeta la capacidad."""
    azar = random.Random(1)
    pesos = [azar.randint(20, 600) for _ in range(600)]
    valores = [p * azar.randint(2, 12) for p in pesos]
    valor, indices = mochila_01(pesos, valores, 4000)
    verificar_solucion(pesos, valores, 4000, valor, indices)


def probar_excepciones() -> None:
    """Entradas invalidas lanzan ValueError."""
    entradas = [
        ([1, 2], [3], 5),            # largos distintos
        ([1], [1], -1),              # capacidad negativa
        ([0], [1], 5),               # peso no positivo
        ([1], [-1], 5),              # valor negativo
        ([1.5], [1], 5),             # peso no entero
        ([1], [1], 5.0),             # capacidad no entera
    ]
    for pesos, valores, capacidad in entradas:
        try:
            mochila_01(pesos, valores, capacidad)  # type: ignore[arg-type]
        except ValueError:
            continue
        raise AssertionError(f"Debio lanzar ValueError: {pesos, valores}")


if __name__ == "__main__":
    probar_ejemplo_a_mano()
    probar_casos_borde()
    probar_no_modifica_entradas()
    probar_contra_fuerza_bruta()
    probar_supera_al_cargue_actual()
    probar_tamano_realista()
    probar_excepciones()
    print("Todas las pruebas de la mochila 0/1 pasaron.")
