# Pedagogía y NEE — contratos de datos para un tero confiable

Investigación de producto y pedagogía para tero. **No** agrega reglas
pedagógicas al prompt: propone **campos** (contratos de datos) y **checks que
el host calcula**. El modelo sigue sin escribir archivos y la persona sigue
aprobando; lo que cambia es qué tan verificable es lo que se le muestra antes
de aprobar.

Leer junto con [CONVERSACIONAL.md](../CONVERSACIONAL.md) (protocolo
congelado), [ADVERSARIAL-LATEX-CURRICULO.md](../ADVERSARIAL-LATEX-CURRICULO.md)
(catálogo host-side) y [NORMAS.md](../NORMAS.md).

Fecha de verificación de fuentes: **2026-09-11**. Todo dato legal se cotejó
contra el texto oficial en BCN/LeyChile. Lo que no se pudo confirmar está
marcado **no confirmado**, y las afirmaciones negativas ("no existe API") se
declaran como hallazgos, no se omiten.

## Regla de oro

> El host aporta contratos y honestidad del catálogo; el modelo aporta
> redacción pedagógica. Un check del host **nunca** decide si el material es
> bueno: decide si el material **declara lo que dice declarar**. Los avisos no
> bloquean la aprobación.

Tres invariantes que esta investigación respeta y refuerza:

1. **Nada se escribe sin aprobación explícita.** Es el diseño vigente y
   además es la salvaguarda legal frente a decisiones automatizadas
   (Ley 21.719, art. 8 bis — ver §e).
2. **El catálogo es del host.** El modelo selecciona registros; no inventa
   códigos ni usa un OA de otro nivel para rellenar.
3. **`catalog_covers: false` es una respuesta válida.** Cuando el curso no
   está en el catálogo, el camino honesto es decirlo y trabajar con texto
   libre, no fabricar un OA.

Y una advertencia de alcance que hay que repetir en cada PR de checks:

> Los checks verifican **coherencia interna del documento**, no calidad
> pedagógica. Un material puede pasar el 100% de los checks y ser pobre; lo
> que ninguno puede es pasar los checks y estar internamente desalineado.

---

## (a) Modelo de datos para OA, indicadores y evaluación chilenos

### a.1 Dos premisas del encargo que resultaron falsas

Vale la pena dejarlas escritas para que nadie las vuelva a asumir.

**Premisa falsa 1: los indicadores de evaluación están en las Bases
Curriculares.** No están. La cadena "Indicadores de Evaluación" tiene **0
coincidencias** en las Bases Curriculares de 1°–6° básico, 7°–2° medio y
3°–4° medio. Los indicadores viven en los **Programas de Estudio**, en la
tabla `OBJETIVOS DE APRENDIZAJE E INDICADORES DE EVALUACIÓN`, con las
columnas:

- `OBJETIVOS DE APRENDIZAJE` — "Se espera que las y los estudiantes sean
  capaces de:"
- `INDICADORES DE EVALUACIÓN` — "Las y los estudiantes que han alcanzado
  este aprendizaje:"

Y son **"de carácter sugerido"** (en 1°–6° el encabezado dice literalmente
`INDICADORES DE EVALUACIÓN SUGERIDOS`). El catálogo necesita **dos fuentes**,
no una: Bases para los OA, Programas para los indicadores.

**Premisa falsa 2: `LEN-4B-OA04` es un identificador oficial.** No existe
ningún código alfanumérico oficial de OA. La identidad oficial es la tupla
**(asignatura, curso, número)**. Evidencia: los Programas referencian
`OA 5`, `OA 24` —sin prefijo y sin cero a la izquierda, nunca `OA04`— y
cuando citan fuera de su contexto usan la forma larga literal
*"Lengua y Literatura, OA 21 y OA 22 de 1º medio"*. El buscador oficial
filtra por asignatura + curso, no por código.

Consecuencia de contrato: `LEN-4B-OA04` sirve como **clave primaria interna**
solo si se documenta como subrogante y siempre viaja acompañado de
`asignatura`, `curso` y `numero`. Nunca se le muestra a la docente como si
fuera un identificador oficial.

Dos detalles que se derivan de esto:

- **La numeración de OA es continua entre ejes y reinicia por curso.**
  Matemática 1° básico: "Números y Operaciones" llega a OA 10 y "Patrones y
  Álgebra" continúa en **OA 11**. Lenguaje 1° básico: Lectura hasta 12,
  Escritura sigue en 13. Por lo tanto **`eje` es un atributo, no parte del
  identificador**.
- **"OA 4" no es único globalmente.** "OA 4" en 4° básico ≠ "OA 4" en
  1° medio, y además cambia el nombre de la asignatura ("Lenguaje y
  Comunicación" en 1°–6° vs "Lengua y Literatura" en 7°–2° medio).

### a.2 Estado actual del contrato (lo que hay hoy)

`OARecord` en `src/tero/curriculum/catalog.py` tiene exactamente:

```json
{
  "id": "LEN-4B-OA04", "curso": "4b", "asignatura": "lenguaje",
  "codigo": "OA 4", "eje": "Lectura",
  "texto_corto": "Extraer información explícita e implícita de textos literarios y no literarios, con evidencia."
}
```

`meta` declara `cursos_cubiertos`, `asignaturas_cubiertas` y un
`disclaimer` de paráfrasis. Esa base es honesta y es la correcta. Faltan
cuatro cosas para que el material sea **verificable** en vez de solo
plausible: cobertura explícita de lo que **no** está, procedencia del texto,
indicadores y actitudes.

### a.3 Modelo propuesto

#### `curriculum/chile/catalogo.json` → `meta` (cobertura honesta)

```json
{
  "pais": "CL",
  "curriculum_version": "bases-2012-actualizaciones-2016",
  "nivel": "basica",
  "cursos_cubiertos": ["4b", "5b", "6b"],
  "asignaturas_cubiertas": ["lenguaje", "matematica", "ciencias"],
  "no_cubierto": [
    {"curso": "1m", "asignatura": "*", "motivo": "fuera-de-alcance"},
    {"curso": "*",  "asignatura": "historia", "motivo": "pendiente-carga"}
  ],
  "texto_oficial_disponible": false,
  "licencia_contenido": "ver §a.5",
  "disclaimer": "Paráfrasis orientativas para selección de OA en tero. No es texto oficial MINEDUC verbatim. Contrastar con bases curriculares vigentes."
}
```

`no_cubierto` es lo que permite responder `catalog_covers: false` **con
motivo**, en vez de un vacío ambiguo que el modelo rellena con un OA de otro
nivel (el fallo ya documentado: "1° medio rellena `CIE-5B-OA02`").

Decretos que aprueban las Bases, leídos de los propios PDF, para poblar
`fuente_decreto`: **439/2012** y **433/2012** (1°–6° básico), **614/2013** y
**369/2015** (7° básico–2° medio), **193/2019** (3°–4° medio), **481**
(parvularia; *año exacto no confirmado*), **97** (pueblos originarios),
**10** (EPJA).

#### `oas[]` — registro enriquecido

| Campo | Tipo | Procedencia | Para qué |
| --- | --- | --- | --- |
| `id` | str | tero (clave subrogante) | PK interna |
| `asignatura` | str | oficial | Parte de la identidad real |
| `curso` | str | oficial | Parte de la identidad real |
| `numero` | int | **oficial** | Parte de la identidad real ("OA 4" → 4) |
| `codigo` | str | **oficial** | "OA 4" (forma de citación) |
| `eje` | str | **oficial** | Atributo, no identidad |
| `texto_corto` | str | tero (paráfrasis) | Búsqueda y chips |
| `texto` | str? | **oficial (verbatim)** | Fundamento citable |
| `procedencia_texto` | enum | tero | `oficial-verbatim` \| `resumen-host` |
| `indicadores[]` | obj[] | **oficiales, sugeridos** | Evidencia observable |
| `actitudes[]` | str[] | **oficiales** | OAT del curso/asignatura |
| `prerrequisitos[]` | str[] (ids) | tero | Progresión |
| `fuente_url` | str | oficial | Documento de origen |
| `fuente_decreto` | str? | oficial | Ej. "D.S. 439/2012" |
| `licencia` | str | oficial | Ver §a.5 |
| `verificado_por` | str? | humano | Quién cargó el verbatim |

#### `indicadores[]` — el campo que más cambia el producto

```json
{
  "codigo": "OA 4 · IE 2",
  "texto": "Inferieren información implícita a partir de indicios del texto.",
  "es_sugerido": true,
  "fuente": "programa-estudio"
}
```

`es_sugerido` es **siempre `true`** y es un campo obligatorio, no un adorno:
el propio MINEDUC declara los indicadores como sugeridos, y tero no puede
presentarlos como criterio obligatorio. Es exactamente el mismo tipo de
honestidad que `verified: false` en las citas de la carpeta.

Los indicadores son la pieza que hoy no existe y que convierte
"objetivo → evidencia → actividad" en algo comprobable: la **evidencia** de
una planificación deja de ser una frase que el modelo eligió y pasa a ser un
indicador del catálogo.

#### Regla de honestidad del verbatim

```python
# pseudo-contrato, no código final
procedencia_texto = "oficial-verbatim" if texto else "resumen-host"
```

Si `texto_oficial_disponible` es `false`, el host **no puede** afirmar en la
vista previa ni en el `.md` exportado que el texto es oficial. Regla de
producto: **paráfrasis rotulada, nunca paráfrasis disfrazada de cita.**

### a.4 Datasets y APIs: qué existe de verdad

Todo verificado en vivo el 2026-09-11:

| Qué se buscó | Resultado |
| --- | --- |
| `datos.gob.cl` (portal CKAN oficial) | `count: 0` para `curriculum` y para `bases curriculares`. La organización "Ministerio de Educación" expone **1 dataset**, y no es currículo. Reproducible: <https://datos.gob.cl/api/3/action/package_search?q=curriculum> |
| `datosabiertos.mineduc.cl` "Planes y Programas" | **No son OA**: es un CSV de ~327 MB / 1,3 M filas de **matrícula** |
| `github.com/curriculumnacional/2025` | **Andamio, no dataset.** `estructura.md` dice literalmente `*(Explicación de cómo se organizan OA, indicadores, actividades...)*`; el README pide "reemplaza los archivos placeholder con contenido limpio del programa oficial" y deja la licencia como `Indica aquí la licencia`. Sin contenido curricular y sin licencia declarada. **No usarlo.** |
| API REST en el portal de currículum | **No existe** (`/jsonapi`, `/api/*`, `/rest/*`: sin respuesta) |
| `bibliotecadigital.mineduc.cl` | 403 a acceso automatizado |

**Decisión de producto:** el catálogo se carga **a mano, curado y
verificado**. Es más lento y es lo correcto. El repo ya prohíbe scrapear
MINEDUC con navegador (`docs/ADVERSARIAL-CORE-CALIDAD.md`, fila
"Browser / Nova Act"), y un catálogo parcial pero honesto vale más que uno
completo pero inventado.

Dos trampas operativas medidas, que conviene dejar escritas:

1. **`curriculumnacional.cl` no responde** desde esta red (timeout a `curl`
   directo). El espejo oficial que sí sirve los mismos archivos es
   **`aprendoenlinea.mineduc.gob.cl`**, con la misma numeración
   `articles-<ID>_<nombre>.pdf`. La descarga directa de PDF con `curl` **no**
   es scrapear un sitio con navegador: es descargar un archivo.
2. **Una IP de borde de MINEDUC devuelve HTTP 200 con un placeholder para
   cualquier ruta.** Un `200` de ese host no es evidencia de nada. Cualquier
   verificación futura debe comprobar que el cuerpo descargado es el
   documento esperado, no solo el código de estado.

### a.5 Licencias: contradicción no resuelta → tratar como no comercial

Hallazgo incómodo y que hay que declarar en el producto:

- En el portal vigente, las fichas de las Bases Curriculares están marcadas
  como **"Dominio público"** (campo `field_licencia`; de 139 fichas
  revisadas: 43 "Dominio público", 18 YouTube, 15 Copyright, 8 CC BY-NC-ND,
  1 CC BY-NC-SA, 1 CC BY-NC, 34 sin campo).
- Pero el sitio anterior declara uso "exclusivamente para fines
  educacionales… prohibido… propósitos comerciales" bajo **CC BY-NC-SA 3.0
  CL**, y los términos del portal nuevo exigen fines "de enseñanza,
  aprendizaje, informativos, académicos o personales" y abstenerse de
  "propósitos comerciales".
- "Dominio público" es **jurídicamente incompatible** con esas condiciones.
- Los PDF **no llevan licencia impresa** (0 coincidencias de "Creative
  Commons" / "licencia" en 1.188 páginas).

**Recomendación:** tratar el contenido como **CC BY-NC-SA 3.0 CL + atribución
a MINEDUC/UCE, no comercial**, hasta consulta formal al MINEDUC. Y atención a
un detalle que rompe el plan de "adaptar y redistribuir": **6 Programas de
lenguas originarias son CC BY-NC-ND**, es decir **sin obra derivada**.

Qué implica para tero, en concreto:

| Uso | ¿Permitido con esta lectura? |
| --- | --- |
| Cargar OA en el catálogo del host y mostrarlos en la vista previa | Sí (atribución + no comercial) |
| Citar el texto de un OA en el material que tero escribe | Sí, con atribución |
| Redistribuir los PDF de MINEDUC dentro del repo | **No** |
| Usar el contenido para un producto comercial | **No**, mientras no haya clarificación |
| Adaptar/derivar el contenido CC BY-NC-ND | **No** |

Esto refuerza la decisión de §a.4: catálogo curado, paráfrasis rotulada, y el
verbatim solo cuando se pueda acreditar la fuente y la licencia.

### a.6 Escala de notas, exigencia y niveles de logro

Verificado contra el texto íntegro del **Decreto 67/2018** (obtenido vía
`https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=1127255`), que deroga
los decretos exentos N° 511/1997, N° 112/1999 y N° 83/2001:

| Dato | Valor | Norma |
| --- | --- | --- |
| Escala de calificación | **1.0 a 7.0**, hasta un decimal | art. 8° |
| Calificación mínima de aprobación | **4.0** | art. 8° |
| Evaluación formativa / sumativa | ambas reconocidas; la formativa se integra a la enseñanza | art. 4° |
| Cantidad de calificaciones | **sin mínimo obligatorio**; tope de 30% para la evaluación final | art. 9°; art. 18 h |
| Promoción | aprueba todo; o 1 reprobada con promedio ≥ 4.5; o 2 reprobadas con promedio ≥ 5.0; asistencia ≥ 85% | art. 10 |
| Reglamento de evaluación | **obligatorio por establecimiento** | arts. 3, 16–19 |
| Eximición de asignaturas | **no existe** | art. 5° |

#### El 60% de exigencia NO está normado

Verificado en tres frentes: **0 coincidencias** de "exigencia" y de "60%" en
el texto completo del Decreto 67/2018; **0 coincidencias** de "exigencia" en
las *Orientaciones para la implementación del Decreto 67* de la Unidad de
Currículum y Evaluación (las únicas menciones de "60%" ahí son ponderaciones
en ejemplos de planificación); y **0 coincidencias** de una fórmula oficial
de conversión puntaje→nota.

Es **convención de cada establecimiento**. Existe y es real —reglamentos
escolares publicados la fijan explícitamente ("El nivel de exigencia es de un
60% de logro de objetivos de aprendizaje"; "La nota 4,0 corresponde al 60% de
logro")— pero es local, no nacional.

Consecuencia de contrato: tero **no debe hardcodear 60%** como verdad
normativa. Debe declararlo como parámetro del establecimiento. La fórmula
habitual (exigencia `e` = 0,6, puntaje máximo `PM`):

```
si P ≥ e·PM:  N = 4,0 + 3,0 · (P − e·PM) / (PM − e·PM)
si P < e·PM:  N = 1,0 + 3,0 · P / (e·PM)
```

Etiquetada como **práctica docente, no norma**, y con `procedencia:
"reglamento-establecimiento"` en el payload.

#### Niveles de logro: la única escala oficial es para evaluación nacional

- **SIMCE / Estándares de Aprendizaje** → **Adecuado / Elemental /
  Insuficiente** (inclusivos: quien alcanza Adecuado cumple también
  Elemental). Es oficial, pero rige **evaluaciones nacionales**, no la sala
  de clases. Fuente: *Informe Técnico SIMCE 2024*, §3.4.
- **En el aula no hay escala nacional obligatoria.** Ni las Bases ni el
  Decreto 67 fijan categorías. Los Programas usan rúbricas **sugeridas**
  (`DESTACADO / LOGRADO / MEDIANAMENTE LOGRADO / NO LOGRADO`), y cada
  establecimiento define la suya.

Modelar como **configuración del establecimiento**, con la rúbrica del
Programa como valor por defecto. No hardcodear.

---

## (b) Principio pedagógico → campo o check → verificación

Sin recetas de aula. Cada fila dice: si el principio es cierto, el material
**debe declarar** este campo, y el host lo verifica **así**.

| # | Principio | Fuente | Campo o check del host | Cómo se verifica |
| --- | --- | --- | --- | --- |
| 1 | Diseño inverso: resultados → evidencia → actividades | Wiggins & McTighe, UbD | `objetivo`, `evidencia[]`, `actividades[]` | El host exige `evidencia[]` no vacía **antes** de aceptar `actividades[]` |
| 2 | **Cobertura inversa** (el check que prueba UbD de verdad) | UbD Etapa 1–2 | `comprensiones[]` × `evidencia[]` | Toda comprensión declarada tiene ≥1 evidencia asociada |
| 3 | Preguntas esenciales | UbD Etapa 1 | `preguntas_esenciales[]` | Presencia y no-vacío |
| 4 | Alineación constructiva | Biggs | `items[].oa_id` | Todo ítem apunta a un OA del catálogo o a `texto-libre` explícito |
| 5 | **Cobertura** de OA | Biggs; Webb | `especificaciones[]` | ∀ OA declarado, ∃ ≥1 ítem |
| 6 | **No-huérfano** | Biggs | `items[]` | ∀ ítem, su OA ∈ declarados |
| 7 | Tabla de especificaciones | práctica estándar (ITESM) | `especificaciones[]` | Aritmética de §b.2 |
| 8 | Coherencia cognitiva | Bloom / DOK | `nivel_cognitivo` (Tipo B) | Comparación con confianza declarada; **advierte, no bloquea** |
| 9 | Evaluación formativa | Black & Wiliam | `criterios_logro[]`, `retroalimentacion{}` | Todo criterio referenciado por ≥1 instrumento |
| 10 | Feed up / back / forward | Hattie & Timperley | `retroalimentacion.{hacia_donde, como_va, paso_siguiente}` | Tres campos separados |
| 11 | Preguntas de diagnóstico | Black & Wiliam | `preguntas_diagnostico[].error_frecuente` + `que_hacer_si_falla` | Par completo o warning |
| 12 | Aprendizaje colaborativo con rendición individual | Slavin; Springer | `agrupamiento`, `roles[]`, `responsabilidad_individual` | Si `grupo` → roles y responsabilidad individual obligatorios |
| 13 | UDL: representación | CAST UDL 3.0 / Decreto 83 | `dua.representacion[]` (ids 1.x–3.x) | ≥ 2 consideraciones con id oficial |
| 14 | UDL: acción y expresión | CAST UDL 3.0 / Decreto 83 | `dua.accion_expresion[]` (ids 4.x–6.x) | ≥ 1 opción alternativa de respuesta |
| 15 | UDL: implicación / compromiso | CAST UDL 3.0 / Decreto 83 | `dua.implicacion[]` (ids 7.x–9.x) | Ids oficiales de la directriz 7–9 |
| 16 | UDL proactivo, no retrofitted | CAST; Decreto 83 | `dua.diseño: "universal" \| "adaptado"` | `universal` = apoyos desde el inicio para todo el curso |
| 17 | **Escalonamiento: primero DUA, después adecuación** | **Decreto 83** | `nee.tipo` ausente si `dua.diseño == "universal"` | La adecuación individual es el **paso siguiente**, no el primero |
| 18 | Adecuación de acceso vs de objetivo | Decreto 83 | `nee.tipo: "acceso" \| "objetivos"` | Coherencia tipo ↔ cambio de OA (§c) |
| 19 | No bajar el OA por acceso | Decreto 83 | `nee.oa_id == material_origen.oa_id` | Comparación con el material de origen |
| 20 | Progresión / espiral | Bruner; MINEDUC | `progresion.{linea, oa_anterior, prerrequisitos}` | El OA previo existe en el catálogo o se declara fuera de alcance |
| 21 | Diversidad de evidencia | lineamientos del repo | `items[].tipo_tarea` | Warning si un solo tipo monopoliza > ~70% del puntaje |
| 22 | Accesibilidad | WCAG 2.2 | Encabezados, alt, contraste | Checks deterministas (§d.2) |
| 23 | Legibilidad adecuada | Fernández-Huerta / Índice Mu | `legibilidad.indice`, `nivel_curso_estimado` | Fórmula sobre el texto (§d.2) |
| 24 | Identidad y pertenencia | CAST UDL 3.0 (7.2, 8.4) | `dua.implicacion[]` incluye 7.2 / 8.4 | Presencia de ids |
| 25 | No sustituir el juicio docente | UNESCO; Ley 21.719 art. 8 bis | Toda propuesta requiere aprobación explícita | La duda no aprueba |

### b.1 Diseño inverso (UbD) — qué campos exige de verdad

Wiggins & McTighe estructuran el diseño en 3 etapas; la Etapa 1 tiene
componentes con nombre canónico:

| Etapa | Componente | Campo propuesto |
| --- | --- | --- |
| 1. Resultados | Metas establecidas | `objetivo.oa_id` |
| 1 | **Transferencia** | `transferencia` |
| 1 | **Comprensiones** (grandes ideas) | `comprensiones[]` |
| 1 | **Preguntas esenciales** | `preguntas_esenciales[]` |
| 1 | Conocimientos | `conocimientos[]` |
| 1 | Habilidades | `habilidades[]` |
| 2. Evidencia | Tareas de desempeño + otros | `evidencia[]` |
| 3. Aprendizaje | Secuencia de experiencias | `actividades[]` |

El check que **realmente** prueba diseño inverso no es la presencia de
campos, sino la **cobertura inversa** (fila 2): toda comprensión declarada
debe tener al menos una evidencia en la Etapa 2. Sin eso, el material es una
secuencia de actividades hacia adelante disfrazada de planificación.

### b.2 Tabla de especificaciones — el bloque más convertible

Es la estructura de evaluación con columnas reales y públicas (ITESM,
<https://sitios.itesm.mx/va/evaluacioneducativa/4_2.htm>):

`SUB-ÁREA | Peso% | Objetivo Específico de Evaluación | Peso% | Cantidad de
reactivos | Tipo de reactivo | Nivel cognitivo | Número del reactivo`

con las fórmulas `P = incidencia · 100 / total` y
`R = peso · (#preguntas) / 100`.

Traducido a contrato, esto habilita checks **aritméticos** (Tipo A, §d.0):
la suma de pesos es 100; la suma de reactivos es el total; los `reactivos[]`
de cada fila forman una **partición** de `items[]` (sin duplicados ni ítems
huérfanos); y el puntaje de cada fila es `peso_obj_pct · puntaje_total / 100`.

### b.3 Alineación con umbrales: Webb y Porter

**Webb** define cuatro criterios con umbrales numéricos publicados:

| Criterio | Aceptable | Débil | No aceptable |
| --- | --- | --- | --- |
| Categorical concurrence | ≥ 6 ítems por estándar | 4–5 | < 4 |
| Depth-of-knowledge consistency | > 50% | 41–50% | ≤ 40% |
| Range-of-knowledge correspondence | ≥ 50% de objetivos con ≥1 ítem | 41–49% | ≤ 40% |
| Balance of representation | índice ≥ 0,70 | 0,60–0,69 | < 0,60 |

Webb agrega un quinto criterio, **Source of Challenge**. Niveles DOK:
1 recuerdo · 2 habilidades y conceptos · 3 pensamiento estratégico ·
4 razonamiento extendido.

Precedente chileno directo y verificado: el *Alignment Study of the PSU to the
Chilean National Curriculum* (Pearson / Educación 2020) aplica los cinco
criterios de Webb a la PSU. El método es factible en el sistema nacional.

**Porter** da una fórmula exacta y calculable
(<https://www.aera.net/Portals/38/docs/Presidential%20Addresses/2002_Porter,%20Andrew.pdf>,
p. 5, Figura 3):

```
Alignment Index = 1 − ( Σ |X − Y| ) / 2
```

donde `X` e `Y` son las **proporciones de celda** de dos matrices
contenido × demanda cognitiva; `1.0` es alineación perfecta. La variante de
"suma de mínimos" que circula **no es rival, es algebraicamente idéntica**
(como cada matriz suma 1, `Σ|X−Y| = 2·Σmin(X,Y)`). **No debe citarse como
arcocoseno ni producto punto**: no hay fuente primaria de Porter para eso.

Advertencia del propio Porter, textual: *"there is still no easy way to think
about how big the alignment index value must be to be considered 'good.'"* →
El host **calcula y reporta el índice como termómetro**; el punto de corte es
una decisión curricular, no algorítmica.

### b.4 El techo humano: por qué los niveles cognitivos no pueden ser un booleano

Evidencia dura de que clasificar un ítem por nivel cognitivo es un **juicio
con techo humano medido**, no un cálculo:

- **Li, Rakovic, Poh, Gašević & Chen (2022)**, EDM: dos codificadores
  humanos entrenados alcanzan **Cohen's κ = 0.63**, y suben a 0.80 **solo
  después de discutir las discrepancias**. La fuente principal de desacuerdo
  es *entender* vs *aplicar*: <https://eric.ed.gov/?id=ED624058>
- **Pincay & Ochoa (2013)**, en español: **α de Krippendorff = 0.7189** entre
  tres humanos, con umbral propuesto α ≥ 0.75.
- **La clasificación supervisada no generaliza**: sobre 5 datasets y 4.179
  preguntas, un SVM con TF-IDF cae ~0,25 de F1 ponderado en datasets no
  vistos y BERT fine-tuneado cae ~0,28; los LLM se mantienen estables, y la
  mejor estrategia medida es **prompt con ejemplos en contexto + verbos de
  acción específicos del curso** (F1 ≈ 0,84) — Faraji et al. (2026), AIED,
  <https://arxiv.org/abs/2606.13684>. Un SVM previo reportó 87,4% de accuracy
  pero **recall 29,1%** (Yahya & Osman, 2011).

Consecuencia de contrato, y es la decisión de diseño más importante de este
documento:

> Los campos **clasificatorios** (`nivel_cognitivo`, `nivel_lector`,
> `sesgo`) **no son booleanos verificados**: son
> `{valor, fuente, metodo, confianza, revisado_por_docente}`. Sus checks
> **nunca bloquean**: advierten y piden revisión humana.

Para tero esto implica una decisión técnica concreta: **no entrenar un
clasificador de Bloom propio** (no generaliza y no hay datos etiquetados
chilenos) y **no presentar el nivel como hecho**. Si se usa un LLM para
sugerir el nivel, el campo queda marcado como sugerencia y la docente puede
corregirlo.

### b.5 Dos correcciones de honestidad

1. **No existe lista canónica de verbos de Bloom en español.** Las que
   circulan suelen ser traducciones automáticas con artefactos. Si tero usa
   una lista en español, es **interpretación de tero** y debe rotularse como
   tal, no como cita de Bloom.
2. **Instrumentos descartados o acotados:** Marzano es redundante con Bloom;
   no agregar un tercer vocabulario de niveles. Se adoptan SOLO (para
   rúbricas cualitativas), la autenticidad de Wiggins como booleano, y
   DOK / demanda cognitiva (Stein & Smith) donde aporten una distinción que
   Bloom no da. **DIF psicométrico queda explícitamente fuera** (§d.4).

---

## (c) Contrato de datos para adaptación NEE

### c.0 Por qué el ancla es chilena y no extranjera

El mejor fundamento del contrato NEE de tero **no es CAST: es el Decreto
83/2015**, porque es normativo en Chile, es gratis, y **ya trae el contrato
de datos escrito**. Además, el propio decreto **cita el DUA y lo adopta como
primer paso**:

> "El Diseño Universal para el Aprendizaje es una estrategia de respuesta a
> la diversidad, cuyo fin es maximizar las oportunidades de aprendizaje de
> todos los estudiantes, considerando la amplia gama de habilidades, estilos
> de aprendizaje y preferencias."

> "…cuyos criterios buscan promover prácticas inclusivas constituyendo el
> **primer paso** para responder a las diferencias individuales en el
> aprendizaje."

Y enumera sus **tres principios** (letras a, b, c del decreto), que equivalen
a los de CAST en otro orden:

| Decreto 83 (verbatim) | CAST UDL 3.0 |
| --- | --- |
| a) Proporcionar múltiples medios de **presentación y representación** | Representación |
| b) Proporcionar múltiples medios de **ejecución y expresión** | Acción y Expresión |
| c) Proporcionar múltiples medios de **participación y compromiso** | Compromiso |

La **regla de escalonamiento** del decreto es la que ordena todo el flujo:

> "Cuando las estrategias de respuesta a la diversidad basadas en el Diseño
> Universal para el Aprendizaje **no permitan** responder a las necesidades
> de aprendizaje de algunos estudiantes, es necesario que se realice un
> proceso de **evaluación diagnóstica individual** para identificar si estos
> presentan necesidades educativas especiales y si requieren medidas de
> adecuación curricular."

Es decir: **primero se diseña para la diversidad; la adecuación individual es
el paso siguiente, no el primero.** Esto convierte a UDL en un campo del
material (§b fila 16–17), no en una buena intención.

### c.1 Pautas CAST UDL 3.0 — vocabulario oficial para los ids

Las pautas UDL 3.0 (CAST, 30-07-2024) son **3 principios, 9 directrices y 36
consideraciones** (verificado por conteo sobre el organizador gráfico oficial
con números). Se agrupan además en tres filas: **Acceso · Apoyo · Función
ejecutiva** (en 2.2 eran cuatro filas con otros nombres: Access · Build ·
Internalize · Goal — **no confundir ambas taxonomías**).

La numeración **no es consecutiva por principio** (arrastra la de 1.0):
Compromiso = 7-8-9; Representación = 1-2-3; Acción y Expresión = 4-5-6.

| Fila | Compromiso | Representación | Acción y Expresión |
| --- | --- | --- | --- |
| Acceso | 7 Acoger intereses e identidades | 1 Percepción | 4 Interacción |
| Apoyo | 8 Mantener el esfuerzo y la persistencia | 2 Lenguaje y los símbolos | 5 Expresión y la Comunicación |
| Función ejecutiva | 9 Capacidad emocional | 3 Construcción del conocimiento | 6 Desarrollo de Estrategias |

Terminología oficial en español disponible en
<https://udlguidelines.cast.org/es/> (traducción coordinada por el Dr. Juan
Carlos Araya Vargas, Universidad Central de Chile; hay además organizador en
**español latinoamericano**). Usar los ids oficiales evita que el modelo
invente nombres de apoyo.

Ejemplos de consideraciones que se traducen directo a apoyos declarables
—esta es la lista de la que el host debería poblar `nee.apoyos[].id`:

| id | Consideración (es) | Apoyo típico |
| --- | --- | --- |
| 1.1 | Personalizar la presentación de información | Letra grande, alto contraste |
| 1.2 | Múltiples formas de percibir información | Audio del texto, versión visual |
| 2.1 | Aclarar vocabulario, símbolos y estructuras | Glosario, instrucciones simplificadas |
| 2.2 | Apoyar la decodificación de texto y notación | Apoyo lector, lectura en voz alta |
| 4.1 | Variar los métodos de respuesta, navegación y movimiento | Responder oral, dictado, tiempo extra |
| 4.2 | Acceso a materiales y tecnologías de asistencia | Lupa, audífonos, teclado adaptado |
| 5.1 | Usar múltiples medios para la comunicación | Responder con dibujo o esquema |
| 6.4 | Seguimiento al progreso | Lista de chequeo propia |
| 7.2 | Relevancia, valor y autenticidad | Ejemplos del contexto local |
| 8.2 | Optimizar desafíos y apoyo | Metas intermedias, apoyo graduado |

**Advertencia de licencia, importante para un repo MIT:** CAST **no** publica
las Pautas bajo Creative Commons. Los términos son restrictivos: se pueden
**citar y mapear** los identificadores (`7.4`, `1.1`, …), pero **no**
redistribuir el organizador gráfico ni derivar una especificación técnica de
él sin permiso escrito. Por eso el contrato guarda **ids y una descripción
propia**, nunca el texto ni la imagen de CAST.

### c.2 La taxonomía exacta del Decreto 83

El decreto agrupa todo bajo "adecuaciones curriculares" y distingue **dos
tipos**:

**a) Adecuaciones curriculares de ACCESO** (verbatim):

> "Son aquellas que intentan reducir o incluso eliminar las barreras a la
> participación, al acceso a la información, expresión y comunicación,
> facilitando así el progreso en los aprendizajes curriculares y equiparando
> las condiciones con los demás estudiantes, **sin disminuir las expectativas
> de aprendizaje**."

Con **4 criterios**:

| Criterio (verbatim) | Ejemplos que da el decreto |
| --- | --- |
| **Presentación de la información** | Ampliación de letra o imágenes, contrastes, color para resaltar, videos, ayudas técnicas (lupa, multimedia, amplificación de audio), lengua de señas, apoyo de intérprete, Braille, gráficos táctiles |
| **Formas de respuesta** | Discurso, ilustración, diseño, manipulación de materiales, música, artes visuales, persona que transcriba las respuestas, calculadora, organizadores gráficos |
| **Entorno** | Ubicación estratégica en el aula, acceso y desplazamiento, ruido ambiental, luminosidad |
| **Organización del tiempo y el horario** | Adecuar el tiempo de una tarea o evaluación, espacios de distensión, cambio de jornada para rendir una evaluación |

Y una regla que enlaza acceso con evaluación, textual:

> "Estas adecuaciones curriculares de acceso, aplicadas según las necesidades
> educativas especiales de los estudiantes, para sus procesos de aprendizaje,
> **deben ser congruentes con las utilizadas en sus procesos de evaluación**,
> de modo que, al momento de evaluar, sean conocidas por los estudiantes para
> que no constituyan una dificultad adicional."

Nótese que las cuatro categorías del propio decreto —presentación, formas de
respuesta, entorno y tiempo— son **modos alternativos de percibir, expresar y
organizar**. Eso es UDL con otro nombre, aplicado a un estudiante puntual.

**b) Adecuaciones curriculares en los OBJETIVOS DE APRENDIZAJE**, con **5
criterios** (los cinco son verbatim del decreto):

| Criterio | Qué es |
| --- | --- |
| **Graduación del nivel de complejidad** | Ajustar el grado de complejidad de un contenido; operacionalizar y secuenciar con metas más pequeñas o más amplias |
| **Priorización de objetivos y contenidos** | Jerarquizar unos OA por sobre otros, sin renunciar a los de segundo orden |
| **Temporalización** | Ajustar el tiempo previsto para el logro |
| **Enriquecimiento del currículum** | Ampliar o profundizar más allá de lo prescrito |
| **Eliminación de aprendizajes** | Quitar un OA. **Última instancia**, con criterios taxativos y un límite duro |

Y el límite duro, textual:

> "Las adecuaciones curriculares a utilizar […] **no deberían afectar los
> aprendizajes básicos imprescindibles**; por lo tanto, es importante
> considerar **en primera instancia las adecuaciones curriculares de acceso
> antes de afectar los objetivos de aprendizaje** del currículum."

#### `eliminacion` no es un valor más: es el último y tiene candado

El decreto es explícito sobre la eliminación, y esto se traduce en un
**bloqueo duro del host**, no en un aviso:

> "La eliminación de objetivos de aprendizaje se debe considerar **sólo cuando
> otras formas de adecuación curricular […] no resultan efectivas**. Esta será
> siempre una decisión a tomar **en última instancia** y después de agotar
> otras alternativas…"

Sus 5 criterios taxativos:

1. cuando la naturaleza o severidad de la NEE hace que los otros tipos de
   adecuación no permitan dar respuesta;
2. cuando los aprendizajes esperados suponen un nivel de dificultad al cual el
   estudiante no podrá acceder;
3. cuando los aprendizajes resultan irrelevantes para el desempeño del
   estudiante en relación con el esfuerzo que supondría alcanzarlos;
4. cuando los recursos y apoyos extraordinarios utilizados no han tenido
   resultados satisfactorios;
5. **cuando esta medida no afecte los aprendizajes básicos imprescindibles**.

Y define cuáles son esos aprendizajes básicos imprescindibles, textualmente:
**"el aprendizaje de la lectoescritura, operaciones matemáticas y todas
aquellas que permitan al estudiante desenvolverse en la vida cotidiana."**

Consecuencia de contrato: si `nee.modificacion.criterio == "eliminacion"`, el
host exige que se declaren los criterios 1–4 y **rechaza** la combinación con
un OA de lectoescritura u operaciones matemáticas. `afecta_aprendizajes_imprescindibles:
true` deja de ser un aviso y pasa a ser **error de validación**.

#### Corrección de vocabulario (para no repetir el error)

- El decreto titula el segundo tipo **"adecuaciones curriculares en los
  objetivos de aprendizaje"**, no "adecuación curricular" a secas. La
  oposición correcta es **acceso** vs **objetivos de aprendizaje**.
- El instrumento individual se llama **PACI** (*Plan de Adecuaciones
  Curriculares Individualizado*), **no "ACI"**.

### c.3 El contrato de datos ya escrito: los 11 campos del PACI

El Decreto 83 enumera, textualmente, los aspectos mínimos del Plan. Esto es
**normativo, chileno y gratis**, y por lo tanto el mejor ancla del contrato:

> "…es necesario que se elabore el Plan de Adecuaciones Curriculares
> correspondiente, considerando como mínimo los siguientes aspectos:
> - Identificación del establecimiento.
> - Identificación del estudiante y sus necesidades educativas individuales y
>   contextuales.
> - Tipo de adecuación curricular y criterios a considerar.
> - Asignatura(s) en que se aplicarán.
> - Herramientas o estrategias metodológicas a utilizar.
> - Tiempo de aplicación.
> - Responsable(s) de su aplicación y seguimiento.
> - Recursos humanos y materiales involucrados.
> - Estrategias de seguimiento y evaluación de las medidas y acciones de
>   apoyo definidas en el Plan.
> - Evaluación de resultados de aprendizaje del estudiante.
> - Revisión y ajustes del Plan."

Dos hechos que ordenan el límite del producto:

1. **tero no genera el PACI, y no solo por falta de formato.** El PACI es "un
   documento oficial ante el Ministerio de Educación", debe registrarse "en un
   formato que el Ministerio de Educación dispondrá para estos efectos" y debe
   estar a disposición de la **familia** y de la **Superintendencia de
   Educación** y la **Agencia de la Calidad**. Además, el Anexo exige que su
   definición se haga "con la participación de los profesionales del
   establecimiento: docentes, docentes especialistas y profesionales de apoyo,
   **en conjunto con la familia**". Un documento oficial fiscalizable, con
   participación familiar obligatoria, **no puede emitirlo un sistema
   automatizado**.
2. **tero sí puede aportar la parte pedagógica** del PACI y debe declarar su
   correspondencia: tipo de adecuación y criterios (campo 3), asignaturas
   (4), estrategias metodológicas (5), tiempo (6) y evaluación de resultados
   (10) son exactamente lo que un material adaptado contiene.

**Salida máxima de tero para un material adaptado:**

```json
"estado": "borrador_propuesto"
```

rotulado en la portada como **"borrador para revisión del equipo PIE"**, con
campos de trazabilidad obligatorios junto al `nee`:

| Campo | Para qué |
| --- | --- |
| `revisado_por` | Quién del equipo revisó (vacío = sin revisar) |
| `fecha_revision` | Cuándo |
| `participacion_familia` | Booleano; el decreto la exige |
| `insumo_diagnostico` | Referencia al FUDEI del establecimiento — **solo la referencia**, nunca su contenido (§e.2) |

Esto convierte "el docente decide" en un campo con nombre y no en una
intención.

Ojo con los campos 1 y 2 del PACI: **identificación del estudiante y sus
necesidades** implica datos personales y, muy probablemente, datos de salud.
Eso choca de frente con §e.2 y es la razón por la que el contrato de tero
**no** tiene campo de estudiante ni de diagnóstico.

#### c.3.1 Alcance real del Decreto 83: solo parvularia y básica

El Decreto 83 cubre **educación parvularia y educación general básica**. Su
art. 5 deja pendiente la extensión a educación media ("hasta la total
tramitación del acto administrativo") y **no existe decreto de adecuación
curricular para educación media** (no confirmado que se haya dictado uno
posterior).

Consecuencia honesta para el catálogo: si el encargo es de 1° medio, tero no
puede citar el Decreto 83 como fundamento de la adecuación. Debe decir que el
marco de adecuación curricular vigente que conoce cubre parvularia y básica, y
que el establecimiento resuelve el caso de media según su reglamento.

#### c.3.2 El DUA que cita Chile no es el 3.0

Chile cita CAST en sus versiones **1.0/2.0 (2008/2011)**: el Anexo del D83 y
las *Orientaciones D83 (2017)* mencionan a CAST y sus tres principios, pero
**no** conocen la versión 3.0 (2024). Las tres formulaciones son
compatibles, pero **no son idénticas**: los ids `7.4`, `9.x` y la fila de
función ejecutiva son de 3.0 y no tienen equivalente en el texto chileno.

Regla de honestidad: cuando el material cite DUA **como fundamento normativo
chileno**, debe usar los tres principios del Decreto 83; cuando use los ids
`x.y`, debe rotularlos como **CAST UDL 3.0**, no como normativa chilena.
Mezclarlos sería atribuirle a Chile una versión que no citó.

### c.4 El campo `notas_nee` actual y por qué no alcanza

Hoy `propuesta.notas_nee` es `[]` de strings
([CONVERSACIONAL.md](../CONVERSACIONAL.md), objeto `propuesta`). Es honesto
pero no verificable: no se puede saber si una "nota" cambió el OA ni el
criterio. El contrato siguiente lo hace comprobable.

### c.5 Contrato propuesto

```json
{
  "nee": {
    "estado": "borrador_propuesto",
    "tipo": "acceso",
    "criterios": ["presentacion-informacion", "formas-de-respuesta", "organizacion-tiempo"],
    "apoyos": [
      {"id": "1.2", "ambito": "representacion",
       "descripcion": "Texto de la guía también en formato audio",
       "fuente": "CAST UDL 3.0"},
      {"id": "4.1", "ambito": "accion_expresion",
       "descripcion": "Puede responder oralmente en vez de escribir",
       "fuente": "CAST UDL 3.0"}
    ],
    "asignaturas": ["lenguaje"],
    "oa_id": "LEN-4B-OA04",
    "oa_modificado": false,
    "criterios_evaluacion_ajustados": [],
    "congruencia_evaluacion": true,
    "formatos_alternativos": ["audio", "letra-grande"],
    "tiempo_aplicacion": "unidad 2",
    "recursos": ["reproductor de audio", "audífonos"],
    "registro": {"paci_ref": null, "responsable": null,
                 "revisado_por": null, "fecha_revision": null,
                 "participacion_familia": false},
    "seguimiento": {"revision": null, "ajustes": []},
    "declaracion": "Adecuación de acceso: mismo OA y mismos criterios de evaluación; cambian el formato y el tiempo. Borrador para revisión del equipo PIE."
  }
}
```

Ejemplo **en objetivos de aprendizaje** (lo que exige salvaguarda):

```json
{
  "nee": {
    "estado": "borrador_propuesto",
    "tipo": "objetivos",
    "criterios": ["graduacion-complejidad", "temporalizacion"],
    "apoyos": [{"id": "8.2", "ambito": "implicacion",
                "descripcion": "Metas intermedias con apoyo graduado",
                "fuente": "CAST UDL 3.0"}],
    "asignaturas": ["matematica"],
    "oa_id": "MAT-4B-OA06",
    "oa_modificado": true,
    "modificacion": {
      "criterio": "graduacion-complejidad",
      "oa_referencia_texto": "Resolver problemas de suma y resta con números naturales…",
      "alcance_ajustado": "Resolver problemas de suma y resta con números hasta 1 000, con apoyo de material concreto.",
      "afecta_aprendizajes_imprescindibles": false
    },
    "criterios_evaluacion_ajustados": [
      "Resuelve problemas con números hasta 1 000 usando material concreto."
    ],
    "congruencia_evaluacion": true,
    "formatos_alternativos": ["material-concreto", "apoyo-visual"],
    "tiempo_aplicacion": "unidad 2",
    "registro": {"paci_ref": "PACI-2026-4B-07", "responsable": "equipo PIE",
                 "revisado_por": null, "fecha_revision": null,
                 "participacion_familia": true},
    "seguimiento": {"revision": "cierre de semestre", "ajustes": []},
    "declaracion": "Adecuación en objetivos de aprendizaje: el OA se gradúa en complejidad y el criterio de evaluación se ajusta. Borrador para revisión del equipo PIE; requiere firma antes de usarse."
  }
}
```

Valores válidos de `criterios` en cada caso:

| `tipo` | `criterios` permitidos |
| --- | --- |
| `acceso` | `presentacion-informacion`, `formas-de-respuesta`, `entorno`, `organizacion-tiempo` |
| `objetivos` | `graduacion-complejidad`, `priorizacion`, `temporalizacion`, `enriquecimiento`, `eliminacion` |

### c.6 Reglas del host sobre este contrato

1. **Coherencia tipo ↔ cambio.** `tipo: "acceso"` ⟹ `oa_modificado: false` y
   `criterios_evaluacion_ajustados: []`. Si el modelo los llena, es
   contradicción: el host emite warning y **no** rotula el material como "de
   acceso".
2. **Acceso primero.** Si `dua.diseño == "universal"`, el host **sugiere no**
   abrir un bloque `nee` individual: el decreto pide agotar DUA antes de
   individualizar.
3. **Curricular exige registro.** `tipo: "objetivos"` sin `paci_ref` ni
   `responsable` ⟹ aviso destacado, **no bloqueante**. tero propone; el
   equipo competente decide y firma.
4. **Marcado obligatorio en la portada.** Todo material adaptado imprime su
   `declaracion` y el `tipo`. La docente que fotocopia debe poder ver en el
   papel si el OA está modificado.
5. **Congruencia con la evaluación.** El decreto exige que las adecuaciones
   de acceso usadas para aprender sean las mismas al evaluar. Por eso
   `congruencia_evaluacion` es un campo explícito y verificable: si el
   material trae apoyos y la evaluación no los declara, hay warning.
6. **No afectar lo imprescindible es un candado, no un aviso.** Si
   `modificacion.criterio == "eliminacion"`:
   - el host exige que se declaren los criterios taxativos del decreto (1–4);
   - y **rechaza** la combinación con un OA de **lectoescritura u operaciones
     matemáticas**, porque el decreto las nombra como aprendizajes básicos
     imprescindibles.
   `afecta_aprendizajes_imprescindibles: true` es **error de validación**, no
   warning. Es la única excepción a la regla de que nada bloquea, y se
   justifica porque la norma usa un límite taxativo ("no deberían afectar").
7. **Nunca el diagnóstico.** El contrato tiene `apoyos` y `criterios`, no
   `diagnostico`. Ver §e.2: ingresar un diagnóstico de NEE a un sistema que
   llama a un modelo en la nube es un problema legal, no solo de estilo.
8. **Estado siempre `borrador_propuesto`.** tero no emite documentos
   oficiales (§c.3).

### c.7 Propuesta de UI para el campo

`propuesta.notas_nee` puede seguir siendo `[]` de strings **derivados** de
`nee`, para no romper la TUI congelada. El host serializa
`nee.declaracion` + `nee.apoyos[].descripcion` a esa lista. Así el protocolo
no cambia y la estructura gana profundidad donde importa: el material escrito
y los checks.

---

## (d) Checks automáticos de calidad

### d.0 La distinción que hace todo el diseño: Tipo A vs Tipo B

- **Tipo A (estructural).** Certeza aritmética o de referencias: "¿los
  puntajes suman?", "¿todo OA tiene evidencia?", "¿cada ítem tiene destino?".
  El host lo calcula sin modelo, es determinista y barato. Puede ser un error
  de validación.
- **Tipo B (clasificatorio).** "¿Este ítem es de nivel *analizar*?". Es un
  **juicio con techo humano medido** (§b.4): κ ≈ 0.63 entre codificadores
  entrenados. Nunca puede ser un booleano verificado, y sus checks **nunca
  bloquean**.

Un check nunca bloquea la aprobación. Los de Tipo A pueden mostrarse como
error de estructura; los de Tipo B solo advierten y piden revisión.

### d.1 Estructura y alineación — [H] host, Tipo A

| id | Check | Cómo |
| --- | --- | --- |
| `q01_estructura` | Faltan apartados del tipo de material | Ya existe: `missing_headings` (`src/tero/artifacts.py`) |
| `q02_oa_catalogo` | Todo `oa_id` existe en el catálogo, o el curso no está cubierto y se declara texto libre | Ya existe parcialmente: `oa_unknown`, `catalog_covers_curso` |
| `q03_alineacion_items` | Todo ítem apunta a un OA (o a texto libre explícito) | `items[].oa_id` no vacío; listar huérfanos |
| `q04_puntaje_suma` | La suma de puntajes por ítem = `puntaje_total` | Aritmética sobre el payload |
| `q05_particion_items` | Los `items[]` de las filas de especificaciones son una partición (sin duplicados ni huérfanos) | Cruce de conjuntos |
| `q06_especificaciones_pesos` | Σpesos = 100 y Σreactivos = len(items); `R = peso·total/100` | Aritmética (§b.2) |
| `q07_cobertura_oa` | ∀ OA declarado, ∃ ≥1 ítem | Conteo (Webb categorical concurrence) |
| `q08_diversidad_items` | Un solo tipo de ítem no monopoliza > ~70% del puntaje | Conteo por `tipo_tarea` |
| `q08b_histograma_cognitivo` | Concentración de niveles cognitivos en lo bajo (recordar/entender) | Histograma de `nivel_cognitivo`; ver §d.1.1 |
| `q09_criterios_antes` | Evaluación con `criterios[]` no vacío | Presencia de campo |
| `q10_pauta_niveles` | Cardinalidad de niveles y descriptores coherente por criterio | `len(niveles)` vs `len(descriptores)` |
| `q11_cobertura_inversa` | Toda `comprensión` tiene ≥1 `evidencia` | Cruce (el check que prueba UbD) |
| `q11b_eliminacion` | `criterio == "eliminacion"` exige criterios taxativos y **no** puede tocar lectoescritura ni operaciones matemáticas | **Candado** (§c.6 regla 6) |
| `q12_retroalimentacion` | `retroalimentacion` con los tres momentos no vacíos | Presencia de campos |
| `q13_grupo_rendicion` | Si `agrupamiento == "grupo"` → `roles[]` no vacío **y** `responsabilidad_individual == true` | Regla condicional |
| `q14_nee_coherencia` | `tipo` ↔ `oa_modificado` ↔ `criterios_evaluacion_ajustados` coherentes | Reglas de §c.6 |
| `q15_acceso_no_baja_oa` | Adaptación de acceso conserva el `oa_id` de origen | Comparación con el original |
| `q16_congruencia_evaluacion` | Los apoyos de acceso declarados reaparecen en la evaluación | Cruce `nee.apoyos` × `items` |
| `q17_imprescindibles` | `afecta_aprendizajes_imprescindibles` es `false` | Booleano + aviso alto |

#### d.1.1 El sesgo conocido de los LLM: empujan el material hacia lo bajo

Hay evidencia de que los planes generados por LLM se concentran en los
niveles cognitivos más bajos: de 15 planes de clase generados por 5 LLM, los
objetivos se agruparon en *Remember* y *Understand* (arXiv:2510.19866).

Esto convierte el histograma de niveles en un check de alto valor, y es
barato: **no exige clasificar bien cada ítem, solo mirar la forma de la
distribución.** Un material que solo pide recordar no está evaluando un OA
que pide analizar, y esa desalineación se ve en el agregado aunque el juicio
ítem por ítem sea imperfecto (κ ≈ 0.63, §b.4).

Ventaja de diseño: `q08b` es **robusto al error de clasificación** de una
manera en que `q08_nivel_cognitivo` no lo es. Por eso los dos viven en capas
distintas: el histograma es un aviso agregado (Tipo A en su forma), mientras
que la comparación ítem por ítem sigue siendo Tipo B.

### d.2 Accesibilidad y legibilidad — [H] host

| id | Check | Cómo |
| --- | --- | --- |
| `q18_encabezados` | Jerarquía de encabezados sin saltos (h1→h2→h3) | Parseo de markdown |
| `q19_alt` | Imágenes con texto alternativo | Atributo `alt` |
| `q20_contraste` | Contraste suficiente si el material lleva color | WCAG 2.2 SC 1.4.3: ratio ≥ 4.5:1 (≥ 3:1 si ≥18 pt o ≥14 pt negrita) |
| `q21_espaciado` | Espaciado de texto ajustable (no pisado) | WCAG 2.2 SC 1.4.12 |
| `q22_legibilidad` | Índice de legibilidad en rango del curso | Fórmula (§d.2.1) |
| `q23_oracion_larga` | Oraciones excesivamente largas para el nivel | Umbral configurable por curso |
| `q24_densidad_lexica` | Vocabulario fuera de rango del curso | Lista de frecuencia |
| `q25_instrucciones_largas` | Instrucciones que superan N palabras | Conteo |

#### d.2.1 Cómo calcular `q22` sin inventar

**Fórmulas verificadas para español** (textstat; el manual de `koRpus` para
Gutiérrez de Polini):

```
Fernández-Huerta:  L = 206.84 − 60·(S/P) − 1.02·(P/F)
Szigriszt-Pazos:   P = 206.835 − 62.3·(S/P) − (P/F)
Gutiérrez de Polini: C = 95.2 − 9.7·(L/P) − 0.35·(P/F)
Crawford:          A = −0.205·OP + 0.049·SP − 3.407
```

donde `S` = sílabas, `P` = palabras, `F` = frases, `L` = letras, `OP` =
oraciones por 100 palabras, `SP` = sílabas por 100 palabras.

⚠️ **Advertencia sobre una variante difundida y errónea.** La forma
`206.84 − 0.60·P − 1.02·F` con `P` = "sílabas por palabra" es incoherente
(da ~185 en un texto normal). La forma funcional correcta es
**60 × (sílabas/palabra)**, idéntica a `0.60 × (sílabas por 100 palabras)`.

⚠️ **Ninguna fórmula española es estándar en Chile** (no se encontró adopción
oficial por MINEDUC). Pero **sí existe un índice creado en Chile**:

```
Índice Mu (µ) = [ n/(n−1) ] · ( x̄ / σ² ) · 100
```

Muñoz Baquedano & Muñoz Urra (2006), Viña del Mar; escala 91–100 muy fácil …
0–30 muy difícil; herramienta viva en <https://www.legibilidadmu.cl/> (uso
gratuito con cita obligatoria), validada con 68 profesores de 1°, 2°, 4°, 5°
y 8° básico de 29 establecimientos municipales de Viña del Mar (Universidad
de Playa Ancha). **Es el candidato natural para tero** por pertinencia
chilena, con Fernández-Huerta como contraste.

La escala **INFLESZ** (Barrio-Cantalejo et al., 2008,
<https://pubmed.ncbi.nlm.nih.gov/18953362/>) es la referencia canónica en
español para interpretar: Muy Difícil <40 · Algo Difícil 40–55 · Normal 55–65
· Bastante Fácil 65–80 · Muy Fácil >80.

Insumo técnico: **sílabas en español no es trivial** (diptongos, hiatos).
`pyphen` 0.18.1 (<https://pypi.org/project/pyphen/>) trae diccionarios de
partición silábica por idioma, incluido español.

⚠️ **Cuidado con la licencia si se agrega una dependencia de legibilidad.**
tero es MIT. Verificado en PyPI: `pyphen` es **tri-licencia GPLv2+ / LGPLv2+ /
MPL 1.1** (no es MIT), y `textstat` es MIT **pero depende de `pyphen`**. La
lectura razonable es que **MPL 1.1 permite usarlo como dependencia separada**
sin contaminar el código MIT, siempre que **no se copie ni vendorice** su
código dentro del repo. Si se quiere evitar la discusión por completo, existe
`syllabipy`, pero su licencia **no está declarada en PyPI**
(`license: UNKNOWN`) y por lo tanto **no se recomienda sin verificarla antes**
en su repositorio.

Advertencia de honestidad: `q22` es un **indicador**, no una nota. Un texto
con índice alto puede ser adecuado si la docente lo lee en voz alta. Se
muestra como aviso, nunca como veredicto. Y **no existe estándar chileno de
nivel lector por curso**: los Niveles de Aprendizaje del SIMCE
(Adecuado / Elemental / Insuficiente) son **cortes IRT** de una prueba
nacional (4° básico Lectura: 241 / 284), **no** índices de legibilidad, y no
permiten convertir un texto a "nivel 4° básico". Cualquier check que lo
pretenda sería inventado.

### d.3 Evidencia, honestidad y sesgo — [H] host

| id | Check | Cómo |
| --- | --- | --- |
| `q26_evidencia_verificada` | Citas textuales presentes en el archivo | Ya existe: `verify_evidence` + `unverified_citation` |
| `q27_fuente_existe` | Ruta citada está en la carpeta | Ya existe: `unknown_source` |
| `q28_hash` | Original no cambió | Ya existe: `hash_changed` |
| `q29_verbatim` | Texto rotulado "oficial" es verbatim del catálogo | `procedencia_texto` (§a.3) |
| `q30_indicador_sugerido` | Los indicadores se rotulan como sugeridos | `es_sugerido == true` |
| `q31_sin_diagnostico` | El material no contiene diagnóstico clínico de un estudiante | Lista de términos; ver §e.2 |
| `q32_lenguaje_no_sexista` | Señales de sexismo lingüístico | Ver abajo |
| `q33_balance_representacion` | Conteo de figuras/roles por género | Conteo + aviso |

#### d.3.1 La advertencia central sobre evaluar calidad con LLM

Existe un trabajo que implementa **exactamente** lo que tero querría hacer:
evaluación automática de materiales instruccionales K-12 usando la rúbrica
**EQuIP** (273 materiales, 13 criterios, N=3.549). Su resultado es la
advertencia que ordena este apartado: **ningún LLM comercial (GPT, Gemini,
Llama, Qwen) logra buen desempeño** en esa tarea; el ajuste fino de dominio
mejora apenas hasta +11% (SciEval, AIED 2026, arXiv:2604.25472).

Traducción para tero, y es exactamente la frontera que este documento
propone: **los checks de forma (host, deterministas) son fiables; los de
fondo (juicio del modelo) son señal, no veredicto.** Por eso `q01`–`q33`
viven en el host y ninguno de los clasificatorios bloquea.

Corolario: no construir un "evaluador de calidad con LLM" que puntúe el
material. Es la funcionalidad que la evidencia disponible dice que no
funciona bien todavía.

`q32` tiene fundamento oficial chileno y es **programable**: la ficha
*Educación No Sexista* (Unidad de Género, MINEDUC) define tres
manifestaciones textuales —(a) ocultamiento o invisibilidad de las mujeres
por uso del masculino genérico, (b) asimetría de género
(señorita/señora, señor), (c) estereotipos de género— y las orientaciones
*Promover la Igualdad de Género en el aprendizaje* piden textualmente
"equilibrar figuras masculinas y femeninas en las representaciones, ejemplos,
lecturas" y "revisar los textos escolares, lecturas o materiales que va a
utilizar, e incorpore mujeres en las referencias".

Para el sesgo de ítems, la referencia con criterios textuales convertibles en
checklist es **ETS, *Guidelines for Developing Fair Tests and
Communications* (2022)**: §6 barreras irrelevantes al constructo, §7.1 temas a
evitar, §7.2 temas que requieren cuidado, y §9 tabla terminológica
Preferred/Conditional/Avoid. Cita textual de §7 *Stereotypes*, directamente
convertible en regla: *"If some group members are shown in traditional roles,
other members of the group should be shown in nontraditional roles."*

### d.4 Lo que NO es automatizable — [P] persona

- **Adecuación al contexto real del curso.** Si el ejemplo de fracciones
  conecta con la feria del pueblo o con el estero que los niños conocen. Es
  información que no está ni en el material ni en el OA: está en el aula.
- **Pertinencia afectiva.** ETS §7.2 exige revisar "Topics Requiring Care",
  pero el propio manual reconoce que qué es ofensivo varía de país en país.
  Una lista negra detecta palabras; no detecta que un texto sobre terremotos
  es inapropiado para un curso que vivió uno.
- **Calidad de la retroalimentación.** Distinguir "respuesta correcta" de
  "respuesta que hace aprender" exige ver la reacción del estudiante.
- **Validez de contenido de fondo.** Un LLM puede *señalar* posibles errores
  factuales; confirmarlos requiere a la docente de la disciplina.
- **El punto de corte.** El host calcula el índice de alineación; decidir si
  0,42 es aceptable es una decisión curricular (Porter lo dice explícitamente).
- **Ponderación entre criterios.** Agregar checks en un score único es una
  decisión de valor; EQuIP lo atribuye a "professional judgment".
- **DIF y funcionamiento psicométrico.** Requiere ≥200–300 examinados por
  grupo y datos de respuesta reales que tero no tiene. **No simularlo.**
- **Juicio psicopedagógico** sobre qué adecuación corresponde a un estudiante.

Regla de producto: **todo check [H] puede mostrarse como aviso; nada [P] se
simula como si fuera [H].**

### d.5 Anti-patrón a evitar

Un score único de "calidad 87%" sería deshonesto: mezclaría aritmética
verificable con juicios que el host no puede hacer. Preferir **avisos
discretos y nombrados** (`thin_evidence`, `item_sin_oa`, `legibilidad_alta`)
antes que un número que parece una nota.

---

## (e) Obligaciones legales y éticas chilenas

> Fecha de esta investigación: **2026-09-11**. El calendario importa: la ley
> de datos entra en vigencia **2026-12-01**, a menos de tres meses.

### e.1 Ley 21.719 — Protección de Datos Personales

Publicada en el Diario Oficial el **13-12-2024**; entra en vigencia el
**01-12-2026** ([BCN LeyChile](https://www.bcn.cl/leychile/navegar?idNorma=1209272)).
Modifica la Ley 19.628 y crea la Agencia de Protección de Datos Personales.
(Fue a su vez modificada por la Ley 21.806, D.O. 05-02-2026.)

| Obligación | Norma | Cómo lo declara tero |
| --- | --- | --- |
| **Datos de salud recolectados en ámbito educativo**: se prohíbe su tratamiento y cesión, salvo que la ley lo autorice expresamente en casos calificados | Art. 16 bis inc. final | tero **no ingiere diagnósticos**. El contrato NEE guarda `apoyos`, no `diagnostico` (§c.5) |
| **Datos de NNA**: tratamiento solo por interés superior y autonomía progresiva; niñas y niños (<14) requieren consentimiento del representante legal; datos sensibles de adolescentes **menores de 16** también | Art. 16 quáter | Aviso en UI: tero trabaja sobre **material**, no sobre fichas de estudiantes |
| **Decisiones individuales automatizadas**: derecho a oponerse, a no ser objeto de ellas, y en todo caso a explicación, intervención humana y revisión | Art. 8 bis | El flujo **propone → la persona aprueba** es exactamente la salvaguarda exigida. Ver §e.2.2 |
| **Evaluación de impacto (DPIA)** obligatoria cuando hay evaluación sistemática basada en decisiones automatizadas o perfilamiento | Art. 15 ter | Declarar que tero no perfila estudiantes |
| **Encargado**: contrato obligatorio, prohibido uso para fin distinto, responsabilidad solidaria | Art. 15 bis | Si el material va a un modelo en la nube, hay encargado: declararlo |
| **Transferencia internacional** | Arts. 27–29 | Bedrock fuera de Chile = transferencia internacional |
| **Privacidad desde el diseño** y **reporte de brechas** | Arts. 14 quáter, 14 sexies | Sin telemetría de contenido; la carpeta local es el sistema de registro |
| **Multas**: leves hasta 5.000 UTM; graves hasta 10.000; gravísimas hasta 20.000; reincidencia hasta 3×; agravante expresa si hay datos sensibles o de NNA | Arts. 35, 37 | Riesgo real y cuantificable |

**Datos sensibles** (art. 2 letra g, desde 01-12-2026) incluyen **salud** y
**situación socioeconómica**. Consecuencia fina: las notas por sí solas no
están en el catálogo de sensibles, **pero sí lo están si se vinculan a
salud/NEE o a situación socioeconómica** (vulnerabilidad, becas, prioritario).
Por eso el contrato de tero no debe asociar calificaciones a condiciones.

### e.2 El bloqueante duro, dicho sin rodeos

El art. 16 bis inc. final prohíbe el tratamiento de datos de salud
recolectados en el **ámbito educativo**. Un diagnóstico de NEE (TEA, dislexia,
TEL) es dato de salud y se recolecta en el ámbito educativo.

> **Por lo tanto: tero no debe ingerir, almacenar ni enviar a un modelo
> diagnóstico clínico de un estudiante.** Ni desde la carpeta del docente, ni
> en un campo del payload, ni en una nota.

Esto no le quita valor al producto: le da una forma correcta. tero trabaja
sobre **el material y los apoyos**, que es información pedagógica, no sobre
el diagnóstico, que es información clínica. El PACI del establecimiento —que
sí puede contener esos antecedentes— se queda donde corresponde, bajo
responsabilidad del equipo competente.

Corolario de vocabulario en la UI: hablar de **apoyos y adecuaciones**, nunca
de **diagnósticos o condiciones**.

#### e.2.1 Hueco de implementación concreto (verificado en el código)

Esto no es hipotético. `Workspace._iter_source_files`
(`src/tero/workspace.py`) indexa **por extensión**:

```python
if path.suffix.lower() not in TEXT_SUFFIXES and path.suffix.lower() != PDF_SUFFIX:
    continue
```

donde `TEXT_SUFFIXES` incluye `.md .txt .csv .json .yml .yaml .oa .xml
.markdown` y además se indexan **PDF**. El único filtro es por **nombre de
directorio**, no por contenido.

Consecuencia: un `notas.csv` con calificaciones, un `informe-psicopedagogico.pdf`
o un certificado NEE que la docente haya dejado en su carpeta **entran al
índice sin filtro**, y desde ahí pueden llegar al modelo vía `read_source` /
`search_sources`. El art. 16 bis prohíbe exactamente eso.

Salvaguarda mínima propuesta, con tres capas independientes:

1. **Filtro de admisión en el índice.** Excluir del inventario los archivos
   cuyo nombre o contenido coincida con patrones de salud/NEE (diagnóstico,
   informe médico, certificado, PACI con antecedentes, situación
   socioeconómica). El archivo se queda en la carpeta: no se borra ni se
   mueve, simplemente tero no lo lee.
2. **Aviso no bloqueante `dato_sensible_detectado`** cuando se omite algo,
   para que la docente sepa *por qué* tero no vio ese archivo. Omitir en
   silencio sería peor que el riesgo.
3. **`--offline` como modo de máxima privacidad**, declarado como tal: sin
   Bedrock no hay encargado ni transferencia internacional (arts. 15 bis,
   27–29).

Un detalle importante: **el consentimiento no sanea esto.** El art. 16 bis es
una prohibición, no un deber de cuidado; los datos de salud de origen
educativo no se envían aunque haya autorización. La única salida limpia es no
ingerirlos.

#### e.2.2 Por qué el diseño "propone, no decide" es una defensa legal y no solo una filosofía

El art. 8 bis regula las **decisiones individuales automatizadas**, incluida la
elaboración de perfiles. El art. 2 letra w) define perfilamiento incluyendo
"rendimiento", y el art. 5 letra f) exige informar la lógica aplicada.

Lectura defendible: **si tero propone y la docente decide, no hay decisión
automatizada sobre el estudiante.** Si tero asignara niveles, puntuara o
clasificara estudiantes, sí la habría —con sus obligaciones de explicación,
intervención humana y revisión.

Esto valida el diseño ya acordado en `AGENTS.md` y conviene declararlo
explícito en el producto, no dejarlo como detalle de implementación: **la
aprobación humana obligatoria es la salvaguarda legal, y por eso no puede
volverse opcional ni "auto-aprobable" por conveniencia de UX.**

### e.3 Otras normas chilenas, verificadas

| Norma | Artículo | Qué importa para tero |
| --- | --- | --- |
| **Estatuto Docente (DFL 1/1996)** | art. 16 | **La norma que funda la autonomía docente** (ver abajo) |
| Estatuto Docente | art. 6 letra b; art. 18 | La función docente incluye "diagnóstico, planificación, ejecución y evaluación"; las horas no lectivas cubren "preparación y seguimiento de las actividades de aula" y "evaluación de los aprendizajes". **Art. 18: "Los profesionales de la educación son personalmente responsables de su desempeño."** |
| Estatuto Docente | arts. 68, 69, 80 | Jornada ≤ 44 h; docencia de aula ≤ 28:30; **≥50% de las horas no lectivas** para preparación y evaluación |
| **LGE (DFL 2/2010)** | art. 8°; art. 10 letra c; art. 11 inc. 10°; arts. 33–34 | La autonomía que consagra es **del establecimiento**, no del docente. **La expresión "libertad de cátedra" no aparece en la LGE.** El docente debe enseñar los contenidos de las bases curriculares; el art. 34 regula las adecuaciones curriculares para NEE. **Art. 11 inc. 10°: "En ningún caso se podrá cancelar la matrícula ni suspender o expulsar alumnos por presentar discapacidad o necesidades educativas especiales permanentes."** |
| **Decreto 67/2018**, art. 5° y 18 g) | — | **Corrección:** el decreto **no** usa la expresión "evaluación diferenciada" (eso es "formación diferenciada", otra cosa). Dice **"diversificaciones pertinentes"** y remite a los DEx 83/2015 y 170/2009; el art. 18 letra g) manda **"diversificar la evaluación"**. Tampoco fija reglas de promoción específicas para NEE: eso lo determina el PACI |
| **Decreto 170/2010** | arts. 2, 7, 94 | NEE permanentes/transitorias; **FUDEI** como instrumento de diagnóstico; tope de **2 NEE permanentes y 5 transitorias por curso**. Los profesionales de apoyo no están en el articulado: el art. 86 remite a orientaciones técnicas |
| **Ley 21.545 (TEA)** | arts. 18–21 | Obliga a educación inclusiva sin discriminación arbitraria y a que los establecimientos "efectúen **los ajustes necesarios** en sus reglamentos y procedimientos internos". **Corrección:** la ley **no** contiene artículo de confidencialidad del diagnóstico ni prohibición de exigir exámenes, y **no** usa la expresión "ajustes razonables" |
| **Ley 20.575** | art. 1° | No es principio general de finalidad; su inciso 3° prohíbe exigir datos económicos/financieros en "admisión pre-escolar, escolar o de educación superior" |
| **Ley 21.096** | artículo único | Consagró en el **art. 19 N° 4** de la Constitución "la protección de sus datos personales" |
| **Ley 21.180** | — | **No aplica**: rige los procedimientos de los órganos de la Administración del Estado; el texto no menciona educación |
| **Ley 17.336 (Propiedad Intelectual)** | arts. 1, 5, 7 | **Vacío legal confirmado sobre IA**: "inteligencia artificial" tiene 0 coincidencias en el texto vigente. El art. 5 define la obra como producida por "una sola persona natural" y el art. 7 da la titularidad al autor. Una IA no puede ser autora ni titular original |

### e.4 La norma que funda el producto: art. 16 del Estatuto Docente

Es la base legal de que tero exista, y conviene tenerla textual. El Estatuto
Docente (DFL 1/1996, verificado en el XML oficial) dice:

> "Los profesionales de la educación que desempeñen en la función docente
> **gozarán de autonomía en el ejercicio de ésta**, sujeta a las
> disposiciones legales que orientan al sistema educacional, del proyecto
> educativo del establecimiento y de los programas específicos de
> mejoramiento e innovación. Esta autonomía se ejercerá en:
> a) El planeamiento de los procesos de enseñanza y de aprendizaje que
> desarrollarán en su ejercicio lectivo y en la aplicación de los métodos y
> técnicas correspondientes;
> b) La evaluación de los procesos de enseñanza y del aprendizaje de sus
> alumnos, de conformidad con las normas nacionales y las acordadas por el
> establecimiento;
> c) **La aplicación de los textos de estudio y materiales didácticos en uso
> en los respectivos establecimientos**, teniendo en consideración las
> condiciones geográficas y ambientales y de sus alumnos, y
> d) La relación con las familias y los apoderados de sus alumnos…"

Cuatro lecturas de producto, y las cuatro importan:

1. **La autonomía existe y cubre exactamente lo que tero hace**: planear
   (a), evaluar (b) y aplicar materiales (c). No hace falta inventar un
   fundamento.
2. **Pero está acotada**: sujeta a las normas nacionales, al **proyecto
   educativo del establecimiento** y a los materiales "**en uso en los
   respectivos establecimientos**". tero **no es fuente de currículum
   propio**: propone material dentro del marco, no lo reemplaza.
3. **La letra b) es un límite explícito para las evaluaciones**: la
   evaluación se hace "de conformidad con las normas nacionales y las
   acordadas por el establecimiento". Por eso la escala de notas y la
   exigencia son configuración del establecimiento (§a.6), no constantes.
4. **El art. 18** ("Los profesionales de la educación son personalmente
   responsables de su desempeño") es la base legal de que **la decisión final
   sea de la docente**: quien responde es ella, así que quien aprueba es ella.

### e.5 Autoría del material generado por IA: declararlo como vacío, no como regla

En Chile **no hay norma** que atribuya autoría a una obra generada por IA
(Ley 17.336 sin menciones; sin jurisprudencia ni criterio del Registro
encontrados). **No confirmado** además: proyecto de ley sobre IA y propiedad
intelectual en trámite.

Cómo declararlo, entonces: el material sale **a nombre de la docente**, que es
quien revisa, decide y responde por él (art. 18 del Estatuto Docente). El
producto **no** se atribuye autoría pedagógica ni promete exclusividad de
derechos sobre lo generado.

### e.6 Sobrecarga docente: el dato que impone disciplina de producto

- Jornada autorreportada **40,6 h/semana** (2013: 30,9 → 2018: 40,3 → 2024:
  40,6). Desglose: docencia 30,3 h; **preparación de clases 8,7 h**;
  **evaluación y corrección 4,9 h**; administrativo 4,9 h. Chile supera el
  promedio OCDE en las tres últimas.
- **27,3% reporta mucho estrés** (2018: 19,9%); salud mental afectada subió de
  7,8% a **15,1%**; solo **6,9%** dice que el trabajo le deja tiempo personal.
  Factor nº 1 de estrés: **exceso de trabajo administrativo (56,9%)**.
- Índice de Bienestar Docente (1.327 docentes): **52%** con bajo ánimo que
  dificultó su trabajo; **23%** "muy/extremadamente difícil".
- Base normativa del tiempo: Estatuto Docente arts. 68, 69 y 80 (tope 44 h,
  máximo 28:30 de aula, ≥50% no lectivas para preparación y evaluación).

> **Lectura de producto:** las ~13,6 h semanales de preparación y evaluación
> son el mercado real de tero. El mismo dato impone disciplina: **si tero
> añade una revisión, un formato o un paso extra, destruye el ahorro que
> promete.**

Esto tiene una consecuencia de diseño concreta para §d: los checks deben
**resumirse** (un aviso agregado, no veinte), mostrarse **una vez** antes de
decidir, y nunca convertirse en un formulario que la docente tenga que
completar. La herramienta que agrega carga administrativa a un gremio cuyo
principal estrés es la carga administrativa fracasa aunque sus checks sean
correctos.

### e.7 Riesgo de alucinación de citas normativas y curriculares

Es un riesgo específico, medido en otros dominios y **sin estudio equivalente
en currículum chileno** (vacío declarado). Magnitud conocida:

- Herramientas legales comerciales **con RAG** (Lexis+ AI, Westlaw) alucinan
  entre **17% y 33%** (arXiv 2405.20362). LLMs generales: 14,23%–94,93%.
- El caso **Mata v. Avianca**, 678 F.Supp.3d 443 (S.D.N.Y. 2023): sanción de
  US$5.000 por presentar citas inventadas por IA. Es el precedente que
  muestra que "el modelo citó algo que no existe" tiene consecuencias reales.

Salvaguardas que tero ya tiene: el catálogo es del host y el modelo solo
**selecciona** ids; las citas de la carpeta se verifican por snippet
(`verified: false`); y existen los avisos `oa_unknown` y `oa_wrong_level`.

**El hueco concreto (verificado en el código):** el disclaimer existe en
`src/tero/tools.py` (salida de tool) y en `templates/latex/guia.tex`
("Catálogo curricular no oficial MINEDUC"), pero **no en
`planificacion.tex`, `evaluacion.tex` ni `pauta.tex`**. Es decir: el PDF de
una planificación o de una prueba —justo los documentos que la docente
fotocopia y entrega— puede salir **sin** el rótulo de que el catálogo no es
oficial.

Dos arreglos, ambos de bajo costo:

1. **Cobertura del rótulo, en un solo lugar.** El host ya hace
   `replace("{{key}}", value)` en `_fill` (`src/tero/latex/render.py`) y
   **borra los placeholders que quedan sin llenar**
   (`re.sub(r"\{\{[a-z0-9_]+\}\}", "", result)`). Eso tiene una consecuencia
   que hay que tener presente: si se agrega `{{disclaimer}}` a las plantillas
   pero el host no lo pasa en el `mapping`, **el rótulo desaparece en
   silencio** —el peor resultado posible, porque parece resuelto. Por eso el
   arreglo correcto es inyectar el disclaimer desde el host (una sola fuente
   de verdad) y **no** confiar en que cada plantilla lo traiga escrito.
2. **Regla de origen para citas normativas.** Nada del material exportado
   debe citar un decreto o artículo que el host no tenga en su tabla de
   normas (§e.3). Si el material menciona "Decreto 83" o "art. 8° del
   Decreto 67", ese texto viene de la tabla del host, no del modelo.

### e.8 Declaración propuesta en el material exportado

Añadir al `front_matter` de `materialize_markdown` (o al pie del `.md`):

```yaml
generado_por: tero
origen_contenido: resumen-host      # | oficial-verbatim | invencion-modelo
catalogo_version: bases-2012-actualizaciones-2016
catalogo_cubre: true                # false si el curso no está en el catálogo
indicadores_sugeridos: true         # los IE son sugeridos por MINEDUC
nee_tipo: acceso                    # | objetivos | null
requiere_revision: equipo-pie       # presente solo si nee_tipo = objetivos
exigencia_notas: 0.6                # del reglamento del establecimiento, no de la ley
algoritmo_con_ia: true              # se usó un modelo de lenguaje
disclaimer: >
  Material preparado con apoyo de tero. No es texto oficial MINEDUC ni
  asesoría legal. Contrastar con las bases curriculares y el reglamento de
  evaluación del establecimiento. La decisión pedagógica es de la docente.
```

### e.9 Salvaguardas mínimas, clasificadas

**(a) Obligación legal** (Ley 21.719 vigente 01-12-2026):

1. No tratar datos de salud de estudiantes recolectados en el ámbito
   educativo (art. 16 bis). **Acción concreta:** filtrar el índice de
   `workspace.py` (§e.2.1).
2. No tratar datos de NNA sin base de licitud ni sin intervención del
   representante legal cuando corresponda (art. 16 quáter).
3. No emitir decisiones automatizadas con efectos significativos sin
   explicación, intervención humana y posibilidad de revisión (art. 8 bis).
   **Acción concreta:** la aprobación explícita no puede volverse opcional.
4. Declarar el tratamiento por encargado y la transferencia internacional
   (arts. 15 bis, 27–29). **Acción concreta:** declarar que Bedrock saca el
   contenido de Chile, y ofrecer `--offline` como modo sin transferencia.
5. Evaluación de impacto cuando corresponda (art. 15 ter), y no perfilar
   estudiantes.

**(b) Buena práctica ética:**

5. El material se atribuye a la docente; tero no se declara autor pedagógico.
6. Los avisos no bloquean y no se agregan en un score único.
7. Lenguaje de apoyos, nunca de diagnósticos.
8. Honestidad del catálogo: `catalog_covers`, `procedencia_texto`,
   `es_sugerido`, licencia declarada.

**(c) Recomendación de producto:**

9. Un aviso agregado en vez de veinte (§e.5).
10. Nada cita un decreto que el host no tenga en su tabla de normas.
11. Sin telemetría de contenido: la carpeta local es el sistema de registro.

---

## (f) Bibliografía

**Currículum y normativa chilena**

- Decreto 67/2018, normas mínimas de evaluación, calificación y promoción —
  resumen oficial:
  <https://www.ayudamineduc.cl/ficha/normativa-de-evaluacion-y-promocion-educacion-basica>
  · texto íntegro vía XML:
  <https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=1127255>
  · preguntas frecuentes:
  <https://www.ayudamineduc.cl/sites/default/files/decreto_supremo_no_67_del_2018_preguntas_frecuentes.docx>
- **Decreto 83/2015**, criterios y orientaciones de adecuación curricular:
  <https://www.bcn.cl/leychile/navegar?idNorma=1074511> · texto íntegro vía
  XML: <https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=1074511>
  — vigencia gradual: parvularia, 1° y 2° básico desde **2017**; 3° y 4°
  básico desde **2018**; 5° básico y siguientes desde **2019**
  (artículo primero transitorio). Cubre **solo parvularia y básica**; su
  art. 5° deja pendiente la extensión a educación media.
- Decreto 170/2010 (NEE y subvención):
  <https://especial.mineduc.cl/wp-content/uploads/sites/31/2018/06/DTO-170_21-ABR-2010.pdf>
- Currículum Nacional (portal): <https://www.curriculumnacional.cl> · espejo
  operativo: <https://aprendoenlinea.mineduc.gob.cl>
- Superintendencia de Educación, NEE y barreras al aprendizaje:
  <https://www.supereduc.cl/contenidos-de-interes/necesidades-educativas-especiales-abordar-las-barreras-y-generar-condiciones-para-el-aprendizaje-y-la-participacion/>
- Superintendencia, Ley 21.545 en el ámbito educativo:
  <https://www.supereduc.cl/contenidos-de-interes/ley-tea-conoce-cual-es-su-aplicacion-en-el-ambito-educativo/>
- *Informe Técnico SIMCE 2024* (niveles Adecuado / Elemental / Insuficiente):
  <https://s3.us-east-1.amazonaws.com/archivos.agenciaeducacion.cl/Informe_Tecnico_2024.pdf>
- Datos abiertos del Estado de Chile (verificado: sin dataset curricular):
  <https://datos.gob.cl/api/3/action/package_search?q=curriculum>
- Estatuto Docente, DFL 1/1996:
  <https://www.bcn.cl/leychile/navegar?idNorma=60439>
- LGE, DFL 2/2010: <https://www.bcn.cl/leychile/navegar?idNorma=1014974>

**Diseño instruccional y evaluación**

- Wiggins, G. & McTighe, J., *Understanding by Design* (ASCD) — 3 etapas y
  componentes de la Etapa 1, reproducidos en Dack, *The Professional
  Counselor* 9(2):
  <https://tpcjournal.nbcc.org/wp-content/uploads/2019/06/Pages_80-99-Dack-Improving_Classroom_Guidance_Curriculum_With_UbD.pdf>
- Biggs, J., *Constructive alignment*: <https://doi.org/10.1007/bf00138871>
- Anderson, L. W. & Krathwohl, D. R. (2001), *A Taxonomy for Learning,
  Teaching, and Assessing*; Krathwohl (2002):
  <https://doi.org/10.1207/s15430421tip4104_2>
- Black, P. & Wiliam, D. (2009), *Developing the theory of formative
  assessment*:
  <https://kclpure.kcl.ac.uk/ws/files/9119063/Black2009_Developing_the_theory_of_formative_assessment.pdf>
- Hattie, J. & Timperley, H. (2007), *The Power of Feedback*.
- Webb, N., criterios y umbrales de alineación (CLEAR Exam Review, Winter
  2020):
  <https://www.dcu.ie/sites/default/files/inline-files/clear_exam_review_winter2020_alignment_arguments.pdf>
  · NAGB Design Document (balance of representation ≥ 0,70):
  <https://www.nagb.gov/content/dam/nagb/en/documents/publications/design-document-final.pdf>
- Aplicación chilena de Webb a la PSU (Pearson / Educación 2020):
  <https://www.educacion2020.cl/wp-content/uploads/2013/01/201301311057540.chile_psu-finalreport.pdf>
- Porter, A. C. (2002), *Measuring the Content of Instruction*,
  Educational Researcher 31(7), 3–14:
  <https://www.aera.net/Portals/38/docs/Presidential%20Addresses/2002_Porter,%20Andrew.pdf>
- Tabla de especificaciones, columnas y fórmulas (ITESM):
  <https://sitios.itesm.mx/va/evaluacioneducativa/4_2.htm>
- Ackerman, T. & colleagues, *Alignment arguments* (CLEAR Exam Review).
- Springer, Stanne & Donovan (1999), aprendizaje colaborativo:
  <https://doi.org/10.3102/00346543069001021>
- Kyndt et al. (2013): <https://doi.org/10.1016/j.edurev.2013.02.002>
- Slavin, R., sobre producto grupal y rendición individual:
  <https://doi.org/10.6018/analesps.30.3.201201>
- MINEDUC, *Progresiones de Aprendizaje en Espiral*:
  <https://especial.mineduc.cl/wp-content/uploads/sites/31/2019/04/Historia-Geografia-04-19.pdf>

**Clasificación cognitiva y calidad automática**

- Li, Rakovic, Poh, Gašević & Chen (2022), acuerdo humano en clasificación
  Bloom: <https://eric.ed.gov/?id=ED624058>
- Faraji et al. (2026), *Cross-Dataset Bloom Question Classification*, AIED:
  <https://arxiv.org/abs/2606.13684>
- Liu, Sharma & Shi (2026), *Fine-Grained Curriculum Standards Alignment on
  the MathFish Benchmark*, BEA: <https://aclanthology.org/2026.bea-1.15/>
- ETS, *Guidelines for Developing Fair Tests and Communications* (2022):
  <https://www.ets.org/content/dam/ets-org/pdfs/about/fair-tests-and-communications.pdf>
- Zwick, R. (2012), *A Review of ETS DIF Assessment Procedures*, ETS
  RR-12-08: <https://files.eric.ed.gov/fulltext/EJ1109842.pdf>
- Achieve, **EQuIP Rubric** (dimensiones y criterios de calidad de materiales).
- EdReports, criterios de revisión de materiales.
- SciEval (AIED 2026), evaluación automática de materiales K-12 con la rúbrica
  EQuIP: <https://arxiv.org/abs/2604.25472> — ningún LLM comercial logra buen
  desempeño.
- Liu (2025), concentración de planes de clase generados por LLM en niveles
  cognitivos bajos: <https://arxiv.org/abs/2510.19866>

**DUA / UDL**

- CAST (2024), *Universal Design for Learning Guidelines version 3.0*:
  <https://udlguidelines.cast.org> · español:
  <https://udlguidelines.cast.org/es/> · organizador 3.0 en español
  latinoamericano:
  <https://udlguidelines.cast.org/static/udlg3-graphicorganizer-digital-numbers-a11y-spanish-latin-america.pdf>
  — 3 principios, **9 directrices, 36 consideraciones**; licencia
  **propietaria/restrictiva** (citar y mapear ids, no redistribuir).

**Legibilidad en español**

- Barrio-Cantalejo et al. (2008), validación de la escala **INFLESZ**,
  Anales Sis San Navarra 31(2):135-52:
  <https://pubmed.ncbi.nlm.nih.gov/18953362/>
- Ballesteros-Peña & Fernández-Aedo (2013), Flesch-Szigriszt e INFLESZ:
  <https://pubmed.ncbi.nlm.nih.gov/24406353/>
- **Índice Mu** (Muñoz Baquedano & Muñoz Urra, 2006), único índice de
  legibilidad creado en Chile: <https://www.legibilidadmu.cl/>
- `pyphen` (partición silábica, incluye español):
  <https://pypi.org/project/pyphen/>
- `textstat` (implementa Fernández-Huerta y Flesch-Szigriszt para español).

**Datos personales, inclusión y ética**

- Ley 21.719, protección de datos personales (vigencia 01-12-2026):
  <https://www.bcn.cl/leychile/navegar?idNorma=1209272>
- Ley 20.422: <https://www.leychile.cl/Navegar?idLey=20422>
- Ley 21.545 (TEA): <https://www.bcn.cl/leychile/navegar?idNorma=1190123>
- Ley 21.096: <https://www.bcn.cl/leychile/navegar?idNorma=1119730>
- Ley 17.336: <https://www.bcn.cl/leychile/navegar?idNorma=28933>
- **Alucinación de citas legales:** *Mata v. Avianca, Inc.*, 678 F.Supp.3d 443
  (S.D.N.Y. 2023) — sanción por citas inventadas por IA. Tasa de alucinación
  en herramientas legales con RAG (17%–33%): <https://arxiv.org/abs/2405.20362>
- MINEDUC, *Educación No Sexista*:
  <https://educacionsinbrechas.mineduc.cl/wp-content/uploads/sites/129/2025/06/Ficha-Educacion-no-sexista.pdf>
- MINEDUC, *Promover la Igualdad de Género en el aprendizaje*:
  <https://educacionsinbrechas.mineduc.cl/wp-content/uploads/sites/129/2025/03/Promover-la-Igualdad-de-Genero-en-el-aprendizaje.pdf>
- UNESCO, *Guidance for generative AI in education and research* (2023):
  <https://unesdoc.unesco.org/ark:/48223/pf0000386693> *(acceso automatizado
  bloqueado; citada sin verificación de texto completo)*
- Reglamento (UE) 2024/1689 (**AI Act**), Anexo III punto 3: la IA educativa
  que evalúa resultados de aprendizaje o guía el proceso es **alto riesgo**
  (obligaciones de alto riesgo aplicables desde el 02-08-2027). Referencia de
  buena práctica, no obligación chilena.
- Centro de Estudios MINEDUC, publicaciones TALIS 2024:
  <https://centroestudios.mineduc.cl/2025/10/15/publicaciones-talis-2024/>

**Cómo obtener el texto oficial de una norma chilena (hallazgo de infraestructura)**

`bcn.cl/leychile/navegar?idNorma=…` es una SPA Angular: devuelve ~9 KB de
cáscara **sin el texto**. La vía que sí sirve, verificada en esta
investigación:

```
https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=<ID>   → texto íntegro
https://www.leychile.cl/Consulta/obtxml?opt=61&cadena=<t>    → búsqueda full-text
```

La API JSON `nuevo.leychile.cl/servicios/Navegar/get_norma_json` devuelve
**solo encabezados** en el Decreto 67 y la Ley 21.545 (≈2,9 KB de texto en un
payload de 53 KB): los cuerpos de artículo están restringidos sin API key. El
XML los resuelve.

IDs verificados (útiles si el host llegara a poblar una tabla de normas):

| Norma | idNorma |
| --- | --- |
| Decreto 67/2018 | **1127255** |
| Decreto exento 83/2015 | 1074511 |
| Decreto 170/2009 | 1012570 |
| Ley 21.719 | 1209272 |
| Ley 21.545 | 1190123 |
| Ley 20.422 | 1010903 |
| Ley 20.845 | 1078172 |
| LGE (DFL 2/2009) | 1014974 |
| Estatuto Docente (DFL 1/1996) | 60439 |

Nota: este endpoint **no es una API pública documentada con términos de
servicio**; usarlo para poblar un catálogo distribuido requeriría revisar sus
condiciones. Para verificación puntual y para la tabla de normas del host, es
la fuente correcta.

**Estándares de datos educativos (referencia externa)**

- 1EdTech **CASE 1.1** (Competency and Academic Standards Exchange), modelo
  de información y binding REST/JSON, Final Release 2025-01-24:
  <https://standards.1edtech.org/case/specifications/standards/v1p1>
  — nótese que CASE modela el **licenciamiento dentro del propio framework**
  (`CFLicense`), que es exactamente el problema de §a.5.
- Learning Commons Knowledge Graph (JSONL público, CC BY 4.0 / MIT):
  <https://github.com/learning-commons-org/knowledge-graph> — cubre
  estándares de EE.UU., **no** el currículum chileno.
- schema.org, propiedades de accesibilidad (**CC BY-SA 3.0**):
  <https://schema.org>
- WCAG 2.2 (W3C Recommendation; W3C Document License, sin derivados):
  <https://www.w3.org/TR/WCAG22/>

---

## Apéndice — Resumen ejecutivo de cambios propuestos

| # | Cambio | Dónde | Costo |
| --- | --- | --- | --- |
| 1 | `meta.no_cubierto[]` + `catalog_covers` con motivo | `catalogo.json` | Bajo |
| 2 | Identidad oficial `(asignatura, curso, numero)`; `id` como clave subrogante documentada | `catalogo.json`, `OARecord` | Bajo |
| 3 | `procedencia_texto` + `texto` verbatim por OA, con licencia declarada | `catalogo.json` | Medio (carga manual) |
| 4 | `indicadores[]` con `es_sugerido: true`, desde los Programas | `catalogo.json` | Medio (carga manual) |
| 5 | `nee{}` estructurado según la taxonomía del Decreto 83 | `types.py`, protocolo | Medio |
| 6 | Checks `q01`–`q33` como avisos no bloqueantes, agregados | `evidence.py` | Medio |
| 7 | Campos Tipo B con `{valor, confianza, revisado_por_docente}` | payload | Bajo |
| 8 | `origen_contenido`, `indicadores_sugeridos`, `nee_tipo`, `exigencia_notas`, `algoritmo_con_ia` en el export | `artifacts.py` | Bajo |
| 9 | Escala de notas y exigencia configurables por establecimiento | payload/plantilla | Bajo |
| 10 | Tabla de normas del host; el material solo cita de ahí | `curriculum/chile/` | Bajo |
| 11 | **Filtro de salud/NEE en el índice** + aviso `dato_sensible_detectado` | `workspace.py` | **Alto (legal, urgente)** |
| 12 | Disclaimer como variable de plantilla en los 4 templates | `templates/latex/` | Bajo |

Nada de esto introduce reglas pedagógicas en el prompt, le da al modelo una
herramienta de escritura, ni scrapea MINEDUC con un navegador.

## Lo que quedó sin verificar (declarado, no escondido)

- **Texto articulado del Decreto 83**: sí se verificó verbatim (XML de
  LeyChile), pero **no** se verificaron los artículos *transitorios* de
  vigencia gradual.
- **Año del Decreto 481** (parvularia): 2017 vs 2018, sin confirmar.
- **UNESCO, *Guidance for generative AI in education* (2023)**: no se pudo
  acceder al texto (bloqueo anti-bot). Se cita **sin** verificar sus
  recomendaciones; ninguna cifra de ese documento se usa en este informe.
- **Ley 20.845** (Inclusión Escolar): mencionada en el marco, sin verificar
  artículo.
- **Nivel de logro "Logrado / Medianamente logrado / Por lograr"**: aparece
  en materiales MINEDUC y reglamentos como rúbrica **sugerida**, sin norma
  nacional que la imponga.
- **Adopción oficial de una fórmula de legibilidad por MINEDUC**: no
  encontrada.
- **Estudio de alucinación sobre referencias a bases curriculares chilenas**:
  no existe; el vacío es en sí un hallazgo.
- **Fórmula exacta de la escala INFLESZ por tramos**: verificada la escala
  publicada (Muy Difícil &lt;40 … Muy Fácil &gt;80) vía la fuente secundaria;
  los cortes conviene reconfirmarlos en el paper antes de codificarlos.
