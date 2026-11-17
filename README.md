# Cargue de vehículos: mochila 0/1 con programación dinámica

**Caso 3 — Banco Regional de Alimentos**  
**Laboratorio Evaluativo 04 / Avance de Proyecto Final**

**Integrantes y roles**

* **Walter Alexander Pino Vásquez** — Estrategia algorítmica, modelado y recurrencia.
* **Ana María Colorado Varela** — Solución exhaustiva, reglas de cargue y contraejemplos.
* **Franco Moncayo Uribe** — Mediciones, gráficas e integración.

**Código fuente en `src/cargue_vehiculos/`:**  
[estrategia.py](src/cargue_vehiculos/estrategia.py) · [pruebas_mochila.py](src/cargue_vehiculos/pruebas_mochila.py) · [medicion.py](src/cargue_vehiculos/medicion.py) · [exhaustivo.py](src/cargue_vehiculos/exhaustivo.py) · [regla_actual.py](src/cargue_vehiculos/regla_actual.py) · [pruebas_contraejemplos.py](src/cargue_vehiculos/pruebas_contraejemplos.py)

El Laboratorio 4 del 18 de noviembre de 2026 aborda la operación 3: cargue de vehículos. Los apartados pendientes del proyecto final se identifican para la entrega del 23 de noviembre.

**Preparación del entorno**

Desde la raíz del repositorio, en WSL Ubuntu:

```bash
# Crear el entorno virtual la primera vez
python3 -m venv .venvAnalisis

# Activar el entorno
source .venvAnalisis/bin/activate

# Instalar las dependencias
python -m pip install -r requirements.txt
```

Si el entorno ya existe, basta con activarlo. Los comandos para ejecutar las pruebas y las mediciones están en el [apartado 8](#8-instrucciones-de-reproducción).

---

## 1. Análisis del problema

### 1.1. Operación 3: cargue de vehículos

* **Entradas:** Para un vehículo, $n$ lotes candidatos (300 a 600 lotes por ruta), cada uno con `peso_kg` (entero positivo) y valor nutricional (raciones ponderadas por prioridad de categoría), y la capacidad máxima $W$ del vehículo (2.500 a 4.000 kg).
* **Salida:** El subconjunto de lotes que maximiza el valor nutricional transportado sin superar la capacidad $W$, junto con los índices ordenados de los lotes seleccionados.
* **Restricciones:**

  1. $\sum \text{peso}_i \le W$ (el vehículo nunca puede sobrecargarse).
  2. Lotes indivisibles (0/1: sube completo o no sube).
  3. El valor transportado debe ser el **máximo exacto**, no una heurística o aproximación.
  4. Los datos de entrada no se modifican (inmutabilidad para conservar la trazabilidad sanitaria).
* **Situación actual, según el caso de estudio:** El coordinador carga por orden de vencimiento (FEFO) hasta que el siguiente lote no cabe. Es un método voraz rápido, pero se detiene en el primer lote que no cabe y deja los camiones saliendo en promedio al **78 %** de su capacidad útil.

### 1.2. Análisis de las cuatro operaciones del banco

Pendiente para la entrega del 23 de noviembre

---

## 2. Diseño de la solución

### 2.1. Justificación de la programación dinámica

El problema tiene **subestructura óptima** y **subproblemas que se repiten (traslapados)**:

* **Subestructura óptima:** Si el lote $i$ está en la solución óptima para la capacidad $w$, el resto debe ser óptimo para los primeros $i-1$ lotes con capacidad residual $w - \text{peso}_i$.
* **Subproblemas traslapados:** Las mismas combinaciones de prefijo de lotes $i$ y capacidad residual $w$ se evalúan repetidamente. Sin memoria, una búsqueda exhaustiva revisa $2^n$ combinaciones; para $n = 600$, $2^{600} \approx 4 \times 10^{180}$, lo cual es completamente inviable.
* **Falla de reglas voraces:** Una regla voraz (sea por orden de vencimiento o por densidad de valor/peso) no garantiza el óptimo con objetos indivisibles (mochila 0/1). Con el ejemplo de la sección 2.3, el cargue por vencimiento obtiene valor 10 y el óptimo es 12. Como el cliente exige el valor máximo exacto, la regla voraz no cumple.

### 2.2. Recurrencia

Sea $V[i][w]$ el valor nutricional máximo alcanzable considerando únicamente los primeros $i$ lotes con una capacidad disponible de $w$ kg:

$$V[0][w] = 0 \quad \forall w \in [0, W]$$
$$V[i][w] = V[i-1][w] \quad \text{si } \text{peso}_i > w$$
$$V[i][w] = \max\Big(V[i-1][w], \; V[i-1][w - \text{peso}_i] + \text{valor}_i\Big) \quad \text{si } \text{peso}_i \le w$$

* El primer término representa la opción *(a)*: "no subir el lote $i$".
* El segundo término representa la opción *(b)*: "subir el lote $i$".
* La respuesta óptima final es $V[n][W]$.
* En [estrategia.py](src/cargue_vehiculos/estrategia.py) se optimiza la memoria usando un solo arreglo recorrido de derecha a izquierda ($W$ hacia $\text{peso}_i$) para asegurar que cada lote se tome a lo sumo una vez, registrando marcas por lote y capacidad en un `bytearray` para reconstruir la solución exacta en $\Theta(n)$.

### 2.3. Ejemplo resuelto a mano

Capacidad $W = 7$ kg; lotes (peso, valor): Lote 1 = (5, 10), Lote 2 = (4, 7), Lote 3 = (3, 5).

| $i$ \ $w$ | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0 (ninguno)** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **1 (+ Lote 1)** | 0 | 0 | 0 | 0 | 0 | 10 | 10 | 10 |
| **2 (+ Lote 2)** | 0 | 0 | 0 | 0 | 7 | 10 | 10 | 10 |
| **3 (+ Lote 3)** | 0 | 0 | 0 | 5 | 7 | 10 | 10 | **12** |

* $V[3][7] = \max(V[2][7], V[2][4] + 5) = \max(10, 7 + 5) = 12$.
* **Reconstrucción:** $V[3][7] \neq V[2][7]$ $\to$ se toma el lote 3 ($w$ pasa a $7 - 3 = 4$). $V[2][4] = 7 \neq V[1][4] = 0$ $\to$ se toma el lote 2 ($w$ pasa a $4 - 4 = 0$). Fin.
* **Solución óptima:** Lotes 2 y 3 (peso $4 + 3 = 7$ kg), valor nutricional **12**.
* **Contraste con regla actual:** El cargue por vencimiento sube el lote 1 (5 kg), el lote 2 ya no cabe, y obtiene valor **10**, dejando 2 kg sin utilizar.

En este ejemplo se supone que los lotes ya están en orden de vencimiento. Su numeración empieza en 1; los índices devueltos por el código y usados en los contraejemplos de la sección 5 empiezan en 0.

### 2.4. Estrategias de contraste

| Estrategia | Decisión y alcance |
|---|---|
| Exhaustiva | Genera los subconjuntos uno a uno, calcula peso y valor y conserva una selección factible de valor máximo. Sirve como referencia exacta para instancias pequeñas. |
| Vencimiento | Ordena por días para vencer ascendentes y carga lotes completos. Se detiene en el primer lote que no cabe. |
| Densidad | Ordena por valor nutricional/peso descendente. Omite los lotes que no caben y continúa con los restantes, sin fraccionarlos. |

Ambas reglas producen selecciones factibles, pero una decisión local puede excluir una combinación de mayor valor. Los dos contraejemplos de la sección 5 verifican esta limitación frente a la exhaustiva y la programación dinámica.

### 2.5. Estructuras de datos, diseño general y segunda operación crítica

Pendiente para la entrega del 23 de noviembre

---

## 3. Implementación

### 3.1. Interfaces y decisiones de implementación

Las funciones de `exhaustivo.py` y `regla_actual.py` utilizan `Lote = tuple[int, int, int]`, correspondiente a `(peso_kg, valor_nutricional, dias_para_vencer)`. Reciben `lotes: list[Lote]` y `capacidad_kg: int`; devuelven `tuple[int, list[int]]`: valor nutricional e índices originales en base cero, ascendentes y sin repeticiones.

| Módulo | Funciones y particularidades |
|---|---|
| [exhaustivo.py](src/cargue_vehiculos/exhaustivo.py) | `cargar_exhaustivo(lotes, capacidad_kg)`: enumera por cantidad de lotes y luego por orden lexicográfico de índices. Entre óptimos empatados conserva el de menos lotes y, después, el menor orden lexicográfico. No almacena todos los subconjuntos. |
| [regla_actual.py](src/cargue_vehiculos/regla_actual.py) | `cargar_por_vencimiento(lotes, capacidad_kg)` y `cargar_por_densidad(lotes, capacidad_kg)`: conservan el orden de entrada en empates. La segunda compara razones exactamente con `Fraction`. |
| [estrategia.py](src/cargue_vehiculos/estrategia.py) | `mochila_01(pesos, valores, capacidad)`: recibe listas separadas. Las pruebas extraen peso y valor de cada lote sin alterar su orden, para conservar la correspondencia de índices. |

La solución exhaustiva y las dos reglas no modifican la lista ni sus registros. Validan pesos enteros positivos, valores nutricionales enteros no negativos, días enteros y capacidad entera no negativa; rechazan booleanos como enteros. Las reglas reutilizan la validación de `exhaustivo.py`, sin ejecutar la búsqueda exhaustiva. Los candidatos deben ser aptos para despacho: estas funciones no filtran lotes vencidos.

### 3.2. Verificación

La suite de pruebas en [pruebas_mochila.py](src/cargue_vehiculos/pruebas_mochila.py) comprueba con `assert`:

* El ejemplo a mano (valor 12, lotes 2 y 3).
* Casos borde: lista vacía, capacidad 0, nada cabe, todo cabe, ajuste exacto y empates.
* 300 instancias aleatorias pequeñas comparadas contra la función `fuerza_bruta` de esa misma suite, verificando que el valor coincida exactamente y que los lotes elegidos no superen la capacidad.
* 100 instancias con parámetros del caso (pesos de 20 a 600 kg, $W$ de 2.500 a 4.000 kg) comprobando que la mochila 0/1 no es inferior a `cargue_por_vencimiento` de `estrategia.py` en esas instancias.
* Inmutabilidad de las listas de entrada y validación de tipos con `ValueError`.

[pruebas_contraejemplos.py](src/cargue_vehiculos/pruebas_contraejemplos.py) ejecuta dos instancias fijas de seis y cinco lotes. Comprueba con aserciones:

- Igualdad del valor óptimo entre `cargar_exhaustivo` y `mochila_01`, y valor estrictamente menor para la regla evaluada.
- Peso dentro de la capacidad, índices originales enteros, ordenados y únicos, y valor reconstruido sumando los registros completos, sin fraccionamiento.
- Inmutabilidad de los lotes y de las listas adaptadas para DP.
- Parada de vencimiento ante el primer lote que no cabe y continuación de densidad tras omitir lotes; ausencia de empates de densidad en ese contraejemplo.

Se reutiliza `verificar_solucion` de la suite existente. Los resultados exactos aparecen en la sección 5; los contraejemplos no miden tiempos ni energía.

**Integración pendiente del Laboratorio 4 — Integrante 3:** consolidar `datos.py` y `pruebas.py`, incorporar fechas de vencimiento a los datos y coordinar las pruebas de las nuevas interfaces. Las suites actuales permanecen separadas y ejecutables.

---

## 4. Evaluación del desempeño

### 4.1. Complejidad teórica

Sea $n$ el número de lotes y $W$ la capacidad entera en kilogramos. Las cotas se expresan bajo aritmética de costo constante y, para DP, con $n,W \ge 1$.

| Estrategia | Tiempo | Memoria adicional | Operaciones dominantes |
|---|---|---|---|
| Programación dinámica existente | $\Theta(nW)$ | $\Theta(nW)$ | Actualización de valores y matriz de marcas para reconstrucción. |
| Exhaustiva | $\Theta(n2^n)$ | $O(n)$ | Evaluación de los elementos de cada subconjunto. |
| Vencimiento | $O(n\log n)$, peor caso | $O(n)$ | Ordenación por fecha y ordenación final de los índices elegidos. |
| Densidad | $O(n\log n)$, peor caso | $O(n)$ | Ordenación por razón valor/peso y de los índices elegidos. |

* **Programación dinámica — tiempo:** Hay $n$ lotes candidatos y, para cada uno, se evalúan a lo sumo $W$ capacidades en tiempo constante. La creación de marcas también recorre un espacio proporcional a $nW$; la reconstrucción toma $\Theta(n)$.
* **Programación dinámica — espacio:** El arreglo unidimensional de valores ocupa $\Theta(W)$. La matriz de marcas para reconstruir ocupa $\Theta(nW)$ bytes (con 600 lotes y $W = 4000$ kg son $\approx 2{,}4\text{ MB}$, sin incluir la sobrecarga de los objetos Python).
* **Naturaleza pseudopolinomial:** el costo depende del valor numérico de $W$, no de su número de bits. Expresar los mismos pesos y capacidad en gramos multiplicaría $W$ por 1000, aumentando proporcionalmente el trabajo de la tabla y las marcas.

**Exhaustiva:** se generan $2^n$ subconjuntos, pero cada uno requiere sumar los pesos y valores de sus elementos. La suma de sus tamaños es $n2^{n-1}$ para $n\ge1$, lo que justifica $\Theta(n2^n)$. El iterador, la combinación actual y la mejor selección ocupan $O(n)$; no se guardan todas las combinaciones. Aumentar $W$ no cambia el número de subconjuntos.

**Reglas:** validar y recorrer cuesta $O(n)$; ordenar los candidatos y los índices seleccionados domina el peor caso. `Fraction` evita errores de redondeo al comparar densidades, aunque su costo aritmético depende del tamaño en bits de pesos y valores. La capacidad modifica las decisiones, sin crear una tabla de tamaño $W$.

**Crecimiento:** con $W$ fijo, duplicar $n$ duplica el término $nW$; en exhaustiva, el término $n2^n$ se multiplica por $2^{n+1}$. La cota $n\log n$ de las reglas crece algo más del doble. Aumentar $W$ afecta directamente al costo de DP. Estas relaciones son teóricas, no tiempos medidos.

### 4.2. Mediciones y gráficas — Integrante 4: Franco Moncayo Uribe

Se conservan las tablas temporales y las tres gráficas del aporte del Integrante 4. [medicion.py](src/cargue_vehiculos/medicion.py) usa semilla fija (`SEMILLA = 42`) y `time.perf_counter()`, excluye la generación de datos del cronómetro y toma el menor tiempo de varias repeticiones.

**Alcance de las series actuales:** se miden `fuerza_bruta` de `medicion.py`, `mochila_01` y `cargue_por_vencimiento` de `estrategia.py`. Esta última supone entradas previamente ordenadas y no recibe fechas; el generador actual produce únicamente pesos y valores. Los tiempos no corresponden a `cargar_exhaustivo`, `cargar_por_vencimiento` ni `cargar_por_densidad` de los módulos `exhaustivo.py` y `regla_actual.py`.

Los conteos publicados se contrastaron con el generador y las funciones actuales. Los tiempos dependen del equipo y están redondeados; se requiere conservar la salida original con suficiente precisión para auditar las razones de tiempo por celda.

#### 4.2.1. Tiempo frente al número de lotes

Con $W = 1000$ kg, se registraron las siguientes implementaciones:

1. **`fuerza_bruta` de `medicion.py`:** $\Theta(n \cdot 2^n)$
2. **Mochila 0/1 (Programación Dinámica):** $\Theta(n \cdot W)$
3. **`cargue_por_vencimiento` de `estrategia.py`, sin ordenación:** $\Theta(n)$, incluida su validación de entrada.

![Tiempo vs n](graficas/cargue_vehiculos/tiempo_vs_n.png)

| $n$ (lotes) | Exhaustivo (ms) | Mochila DP (ms) | Vencimiento (ms) |
|:---:|:---:|:---:|:---:|
| 4 | 0,017 | 0,353 | 0,0016 |
| 6 | 0,037 | 0,309 | 0,0016 |
| 8 | 0,141 | 0,461 | 0,0019 |
| 10 | 0,606 | 0,713 | 0,0022 |
| 12 | 2,454 | 0,712 | 0,0024 |
| 14 | 10,255 | 0,808 | 0,0032 |
| 16 | 45,529 | 0,994 | 0,0034 |
| 18 | **192,150** | **1,179** | **0,0035** |

* **Análisis:** de $n=8$ a $n=16$, la razón temporal publicada de fuerza bruta es $45{,}529/0{,}141 \approx 322{,}90$; DP presenta $0{,}994/0{,}461 \approx 2{,}16$. En teoría, los subconjuntos se multiplican por 256 y el término $n2^n$ por 512. Estas cantidades representan métricas distintas; las mediciones finitas no tienen que reproducir exactamente el factor de la cota asintótica. Con $W$ fijo, la tendencia de DP es compatible con su dependencia lineal de $n$.

---

#### 4.2.2. Conteos de subconjuntos, celdas y comparaciones

Se registran unidades distintas de trabajo para cada implementación:

* **Exhaustivo:** Combinaciones evaluadas ($2^n$).
* **Mochila DP:** Celdas efectivas calculadas en la tabla ($\sum \max(0, W - \text{peso}_i + 1)$).
* **Vencimiento:** Comparaciones de capacidad del recorrido, sin contar la validación de entrada ni una ordenación por fecha.

![Operaciones vs n](graficas/cargue_vehiculos/operaciones_vs_n.png)

| $n$ (lotes) | Subconjuntos exhaustivos ($2^n$) | Celdas Mochila DP ($\Theta(n \cdot W)$) | Comparaciones de capacidad |
|:---:|:---:|:---:|:---:|
| 4 | 16 | 3.163 | 4 |
| 8 | 256 | 4.988 | 3 |
| 12 | 4.096 | 7.305 | 3 |
| 16 | 65.536 | 11.246 | 6 |
| 18 | **262.144** | **13.303** | 4 |

La escala logarítmica permite comparar el crecimiento de estas métricas. Los $2^n$ subconjuntos no equivalen a todas las operaciones elementales de la exhaustiva: evaluar sus elementos exige trabajo adicional. Tampoco se contabiliza aquí el costo completo de las otras funciones.

---

#### 4.2.3. Tiempo frente a capacidad ($n = 400$)

Para evidenciar el carácter pseudopolinomial de la mochila, se fijó $n = 400$ lotes candidatos y se incrementó la capacidad $W$ del camión:

![Tiempo vs capacidad](graficas/cargue_vehiculos/tiempo_vs_capacidad.png)

| $W$ (kg) | Tiempo (s) | Celdas evaluadas | ns por celda |
|:---:|:---:|:---:|:---:|
| 500 | 0,0056 | 84.223 | 66,9 |
| 1.000 | 0,0181 | 280.428 | 64,7 |
| 2.000 | 0,0451 | 680.428 | 66,3 |
| 4.000 | 0,1033 | 1.480.428 | 69,8 |
| 8.000 | 0,2380 | 3.080.428 | 77,3 |

* **Contraste empírico con $\Theta(n \cdot W)$:**

  - Al duplicar $W$ de 1.000 a 2.000 kg, el cociente de tiempos publicados es $0{,}0451 / 0{,}0181 \approx \mathbf{2{,}49}$; las celdas útiles crecen $680428/280428 \approx 2{,}43$ debido al rango de capacidades evaluado para cada peso.
  - De 2.000 a 4.000 kg, el tiempo crece aproximadamente $\mathbf{2{,}29}$ veces y las celdas $1480428/680428 \approx 2{,}18$ veces.
  - El costo por celda publicado varía entre 64,7 y 77,3 ns. La tendencia observada es compatible con el análisis teórico, pero no constituye una demostración de la complejidad.

---

### 4.3. Extrapolación de tiempo y energía

**Supuesto de extrapolación pendiente de validación experimental:** se utiliza el coeficiente de **$67{,}2\text{ ns}$ por celda** recogido en el informe previo para $n = 2000$. No se dispone de un registro experimental que respalde ese valor. Las cifras siguientes son estimaciones condicionadas a este coeficiente y a la potencia indicada, no resultados experimentales comprobados.

El escenario considera 300 días operativos anuales, según la información suministrada en el Caso 3:

* **Lotes candidatos:** 600 lotes por ruta.
* **Capacidad:** 4.000 kg.
* **Flota:** 14 vehículos despachados en la madrugada.
* **Potencia supuesta del computador bajo carga:** 150 W ($0{,}150\text{ kW}$).
* **Días de operación:** 300 días al año.

| Métrica | Estimación con 67,2 ns/celda |
|:---|:---:|
| **Tiempo por vehículo (600 lotes, 4.000 kg)** | **0,16128 s** |
| **Tiempo total para la flota (14 vehículos)** | **2,25792 s** |
| **Energía diaria de DP (14 vehículos)** | **0,09408 Wh** |
| **Energía anual de DP (14 vehículos, 300 días)** | **0,028224 kWh** |
| **Escenario de crecimiento (segunda bodega, 28 vehículos)** | **4,51584 s por día** |

El modelo usa $t_{\text{vehículo}} = 600 \cdot 4000 \cdot 67{,}2 \cdot 10^{-9} = 0{,}16128$ s y $t_{\text{flota}} = 14t_{\text{vehículo}} = 2{,}25792$ s por día. Con $150\text{ W} = 0{,}15\text{ kW}$, se aplica $E\text{ (kWh)} = P\text{ (kW)} \cdot t\text{ (h)}$:

$$E_{\text{anual}} = 0{,}15 \cdot \frac{2{,}25792}{3600} \cdot 300 = 0{,}028224\text{ kWh}.$$

Este resultado representa la energía estimada del computador durante la ejecución de DP para los 14 vehículos, una vez al día durante 300 días. No representa una diferencia entre estrategias, un ahorro energético ni el consumo total anual del banco. El término $600\cdot4000$ es una cota de trabajo; las celdas efectivamente evaluadas dependen de los pesos. Sin validar el coeficiente temporal y sin medición eléctrica directa, el resultado permanece condicionado a los supuestos del modelo.

### 4.4. Ajuste a la ventana operativa

* **Ventana permitida:** 2 horas (03:00 – 05:00) compartida con las demás operaciones.
* **Tiempo estimado de DP para la flota:** aproximadamente **2,26 segundos**, bajo los supuestos anteriores.
* La estimación de esta operación es muy inferior a las dos horas disponibles; no certifica el tiempo total de planeación, compartido con las demás operaciones.

### 4.5. Dependencias de integración experimental

El Integrante 4 debe integrar las funciones definitivas, medir su costo completo y revisar etiquetas, tablas y gráficas. La nueva regla por vencimiento incluye ordenación y no debe heredar la serie lineal anterior; densidad aún no tiene una serie medida. También quedan pendientes la validación experimental del coeficiente por celda y la reproducción de la simulación de flota citada en la sección 5.4.

### 4.6. Línea base energética del proceso actual

Pendiente para la entrega del 23 de noviembre

---

## 5. Análisis comparativo

Las instancias siguientes son sintéticas, con capacidad reducida de **1000 kg** para facilitar su revisión manual. No representan el volumen operativo real. Los índices son originales, en base cero. Los resultados se obtienen ejecutando [pruebas_contraejemplos.py](src/cargue_vehiculos/pruebas_contraejemplos.py); la diferencia es valor óptimo menos valor de la regla.

### 5.1. Contraejemplo por vencimiento

| Índice | Peso (kg) | Valor nutricional | Días para vencer |
|---|---:|---:|---:|
| 0 | 450 | 900 | 4 |
| 1 | 300 | 180 | 1 |
| 2 | 550 | 1100 | 5 |
| 3 | 500 | 250 | 2 |
| 4 | 250 | 400 | 3 |
| 5 | 150 | 200 | 6 |

| Método | Índices | Peso (kg) | Valor nutricional | Diferencia (unidades) |
|---|---|---:|---:|---:|
| Vencimiento | `[1, 3]` | 800 | 430 | 1570 |
| Exhaustiva | `[0, 2]` | 1000 | 2000 | 0 |
| DP | `[0, 2]` | 1000 | 2000 | 0 |

El orden por vencimiento es `[1, 3, 4, 0, 2, 5]`. Después de cargar 1 y 3 quedan 200 kg; el lote 4 pesa 250 kg y provoca la parada. La regla no alcanza el lote 5, que sí cabría. Además, priorizar fechas excluye la combinación de 0 y 2, cuyo valor supera al de la regla en **1570 unidades**. La exhaustiva y DP coinciden en valor y selección para esta instancia.

### 5.2. Contraejemplo por densidad

| Índice | Peso (kg) | Valor nutricional | Días para vencer |
|---|---:|---:|---:|
| 0 | 500 | 950 | 4 |
| 1 | 600 | 1320 | 1 |
| 2 | 100 | 80 | 5 |
| 3 | 500 | 1000 | 2 |
| 4 | 200 | 100 | 3 |

| Método | Índices | Peso (kg) | Valor nutricional | Diferencia (unidades) |
|---|---|---:|---:|---:|
| Densidad | `[1, 2, 4]` | 900 | 1500 | 450 |
| Exhaustiva | `[0, 3]` | 1000 | 1950 | 0 |
| DP | `[0, 3]` | 1000 | 1950 | 0 |

Las densidades exactas dan el orden `[1, 3, 0, 2, 4]`: $11/5 > 2 > 19/10 > 4/5 > 1/2$. No hay empates. El lote 1, de mayor densidad, deja 400 kg disponibles e impide cargar 0 y 3, de 500 kg cada uno. La regla los omite y continúa con 2 y 4, pero obtiene **450 unidades menos** que el óptimo. Continuar tras un lote que no cabe no corrige la decisión inicial.

### 5.3. Condición en que densidad sería óptima

Si se permitiera dividir los lotes y el valor nutricional fuera proporcional a la cantidad cargada, el problema sería una mochila fraccionaria. Cargar por densidad descendente y tomar la fracción necesaria del siguiente lote sería óptimo: sustituir peso de menor densidad por igual peso de mayor densidad no reduce el valor. Esta condición no se cumple en el banco, donde los lotes son indivisibles. `cargar_por_densidad` implementa una heurística 0/1, no la solución fraccionaria.

### 5.4. Calidad del cargue: simulación de flota del informe previo

Los valores de esta tabla se conservan del informe previo. Su origen está asociado a `calidad_flota` del archivo histórico `medicion_mochila.py` (commit `316def5`), eliminado en la integración posterior. El módulo actual no reproduce esa simulación; el Integrante 4 debe recuperar y verificar su procedimiento antes de considerarla un resultado experimental definitivo.

| Métrica | Cargue por vencimiento (actual) | Mochila 0/1 (propuesta) | Impacto |
|:---|:---:|:---:|:---:|
| **Ocupación promedio de los camiones** | 92,1 % | **100,0 %** | +7,9 puntos porcentuales de ocupación |
| **Mejora del valor nutricional ponderado** | Línea base | **+87,9 %** | Incremento del valor nutricional ponderado |

La ocupación mide peso/capacidad; el objetivo optimizado es el valor nutricional. Maximizar este último no garantiza ocupar el 100 % del vehículo ni permite inferir directamente raciones entregadas o emisiones evitadas. El 78 % indicado por el caso de estudio y el 92,1 % de la simulación corresponden a fuentes e instancias distintas.

### 5.5. Comparación integral de las operaciones

Pendiente para la entrega del 23 de noviembre

---

## 6. Implicaciones éticas, sociales y ambientales

* **Equidad en la distribución (personas):** Maximizar ciegamente el valor nutricional global podría desfavorecer a comedores comunitarios o jardines infantiles de rutas específicas si sus lotes solicitados aportan menor valor bruto. **Mitigación algorítmica:** Establecer cuotas mínimas reservadas por tipo de población beneficiaria o aplicar factores de ponderación social antes de resolver la mochila. Las cuotas requieren modificar el modelo y no están implementadas en la solución actual.
* **Seguridad alimentaria (FEFO):** La mochila optimiza *qué lotes suben*, no el orden de consumo. Antes de optimizar deben filtrarse los lotes vencidos, y dentro de cada categoría debe conservarse la política FEFO al descargar.
* **Trazabilidad sanitaria:** `mochila_01` no modifica los datos de entrada, lo que facilita vincular la selección con los registros originales; una auditoría sanitaria completa requiere además identificadores y registros persistentes.
* **Impacto ambiental y reducción de desperdicio:** El informe previo atribuye al cliente un factor de **2,5 kg de $\text{CO}_2$ equivalente** por kilogramo de alimento desechado, pendiente de contrastar con el documento original del caso. Este factor permitiría estimar emisiones evitadas si se midieran los kilogramos de desperdicio realmente reducidos. Los contraejemplos y la simulación sintética no permiten cuantificar ese impacto real.
* **Escenario de crecimiento:** Con una segunda bodega (28 camiones), el modelo de la sección 4.3 estima aproximadamente 4,52 segundos diarios si se conserva el tamaño de cada ruta y la misma constante temporal. La sostenibilidad integral requiere evaluar las demás operaciones y los efectos ambientales reales.

### 6.1. Normativa, impacto en organizaciones beneficiarias y trazabilidad sanitaria integral

Pendiente para la entrega del 23 de noviembre

---

## 7. Conclusiones

### 7.1. Conclusiones de la operación 3

En los dos contraejemplos, la exhaustiva y DP alcanzan el mismo valor óptimo. Vencimiento pierde 1570 unidades y densidad pierde 450 frente a ese óptimo; por tanto, ninguna regla garantiza maximizar el valor nutricional con lotes indivisibles. La exhaustiva sirve para verificar casos pequeños, pero su crecimiento exponencial impide aplicarla al volumen real. Se mantiene DP como estrategia propuesta, con costo pseudopolinomial en la capacidad. La evaluación temporal definitiva debe integrar las funciones actuales y conservar evidencia reproducible de las mediciones.

### 7.2. Conclusiones integrales del proyecto

Pendiente para la entrega del 23 de noviembre

---

## 8. Instrucciones de reproducción

Desde la raíz del repositorio, con el entorno `.venvAnalisis` activado. Se utilizó Python 3.14.7 y las dependencias de [requirements.txt](requirements.txt).

```bash
# Pruebas de mochila
python -B src/cargue_vehiculos/pruebas_mochila.py

# Contraejemplos de vencimiento y densidad
python -B src/cargue_vehiculos/pruebas_contraejemplos.py
```

Ambas suites se ejecutaron correctamente. La segunda imprime tablas de lotes, selecciones, pesos, valores y diferencias. Debe ejecutarse sin `-O`, para conservar las aserciones.

```bash
# Ejecutar mediciones y generar las tres gráficas
python -B src/cargue_vehiculos/medicion.py
```

El último comando sobrescribe las tres gráficas existentes. La actualización de las mediciones está pendiente, como se indica en la sección 4.5.

### 8.1. Exportación del informe a PDF

Pendiente para la entrega del 23 de noviembre
