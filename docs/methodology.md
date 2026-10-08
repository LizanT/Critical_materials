# Metodología

Proyecto: análisis de minerales críticos (producción, reservas, precios y concentración de suministro).
Todos los datos son del USGS (dominio público, CC0). El pipeline se ejecuta con `python -m etl.main`.

## 1. Fuentes de datos

- **USGS Mineral Commodity Summaries 2025, Data Release (ver. 2.0, abril 2025)**, DOI 10.5066/P13XCP3R.
  - *World Data* (`World_Data.csv`): producción 2024 (estimada), capacidad y reservas 2024 por país y commodity.
  - *Salient Commodity Data Release* (un CSV por commodity): precios 2020-2024.
- **Lista de minerales críticos 2025** (USGS / Departamento del Interior): 60 minerales.

## 2. Cobertura

De los 60 minerales críticos, 55 aparecen en el archivo World Data. No aparecen: cesium, scandium, rubidium, metallurgical coal y uranium.

Cobertura de datos por mineral:
- **Germanium**: tiene precio, pero el USGS no publica su producción por país (campo vacío en todos los países) ni reservas. No entra en ningún KPI.
- **Gallium, bismuth, silicon, aluminum, arsenic, beryllium** (entre otros): tienen producción, pero no reservas publicadas.

## 3. Limpieza de datos de origen

El archivo del USGS tiene inconsistencias típicas de datos publicados a mano. Se corrigen antes de cargar:

- **Nombres de commodity con espacios sobrantes** (`"Barite  "`, `"Tungsten "`) y un error tipográfico (`"Gemanium"` → `"Germanium"`).
- **Nombres de país inconsistentes**: espacios sobrantes, espacio duro (`\xa0`) y notas de proceso entre paréntesis que no forman parte del país (`"Brazil (beneficiated)"` → `"Brazil"`, `"United States (crude)"` → `"United States"`).
- **Congo**: `"Congo (Kinshasa)"` se resuelve como `"Democratic Republic of the Congo"`, para no confundirlo con la República del Congo. Importa porque la RD Congo domina el cobalto.
- **Filas `"World total (rounded)"` y `"Other Countries"`**: se excluyen del análisis por país y no se cargan a la base de datos.
- **`"United States and Canada"`** (dato conjunto sin desglose): se excluye para no duplicar los datos de EE. UU. y Canadá.
- **Reservas con prefijo `">"`** (por ejemplo `">2,000,000"`): se elimina el símbolo y se conserva el número. Todos los casos observados son filas de total mundial, no de países.
- **Unidad vacía**: una fila de Titanium Mineral Concentrates (Sierra Leone) no trae unidad; se asume `metric tons`, como el resto del commodity.
- **Códigos ISO** de país con `pycountry`, con excepciones manuales (`Burma`, `Korea, North`, `Turkey`, `Côte d’Ivoire`, `Democratic Republic of the Congo`).

## 4. Normalización de unidades

### Producción y reservas
El archivo mezcla tres unidades: `metric tons`, `thousand metric tons` y `kilograms`. Todo se convierte a toneladas métricas. Afecta, entre otros, a aluminio, cobre, fosfato y potasa (miles de toneladas) y a galio, PGM y renio (kilogramos).

### Precios
Todos los precios se pasan a USD por tonelada métrica según el sufijo de la columna fuente (`_dlb`, `_ctslb`, `_dkg`, `_dtoz`/`_dto`, `_dt`, `_t`).

Casos en los que la base del precio no coincide con la de la producción y se ajusta a mano:

| Mineral | Producción (base) | Precio fuente | Ajuste |
|---|---|---|---|
| Chromium | mineral de cromita, peso bruto | `Price_Ore_dt`, mineral de cromita, peso bruto | Se usa el precio de mineral. El del ferrocromo (por libra de cromo contenido) inflaba el valor unas 10 veces. |
| Manganese | contenido de manganeso | `Price_CN_CIF_dt`, USD por *metric ton unit* (1 % de Mn) | × 100 para pasar a tonelada de manganeso contenido. El precio es el del mineral (44 % Mn), no el del metal refinado. |
| Tungsten | contenido de wolframio | `Price_WO3_dt`, USD por *metric ton unit* de WO3 | × 1000 / 7,93 (1 mtu de WO3 contiene 7,93 kg de W). |
| Titanium | ilmenita + rutilo (suma) | `Price_dt` (rutilo) y `Price_dt.2` (ilmenita) | Promedio de ambos. Se excluyen ilmenita/leucoxeno y escoria. |

Fuentes citadas en los metadatos del USGS: Argus Media (cromo, wolframio), CRU Group (manganeso), Fast Markets IM (rutilo).

### Fechas
`price_date` es el 1 de enero de cada año por convención: el dato original es un promedio anual.

## 5. Decisiones de modelado

- **Rare earths** (15 elementos), **Platinum-Group metals** (5 elementos) y **Zirconium + Hafnium**: el USGS publica un único valor para el grupo. Todos los miembros comparten ese valor de producción y reservas y se marcan con `is_aggregated = TRUE`.
  - En PGM, la producción publicada solo incluye platino y paladio (sumados). Iridio, rodio y rutenio comparten esa cifra, que no es su producción real.
- **Titanium**: se usa solo *Titanium Mineral Concentrates* (ilmenita + rutilo sumados). Se excluye *Titanium & titanium dioxide* (esponja y capacidad de pigmento), que mide otra cosa.
- **Copper**: solo producción minera. Se excluye refinería para no mezclar etapas de la cadena.
- **Potash**: reservas en equivalente K2O; se excluye *Reserves, recoverable ore* (mismo dato en otra unidad).
- **Silicon**: ferrosilicio y silicio metal se suman.
- **Magnesium**: compuestos y metal se suman.
- Cuando dos commodities del CSV corresponden al mismo mineral (magnesio, titanio), sus valores se suman por país.

## 6. Precios

### Selección de columna
Si un mineral tiene varias formas comerciales, se prioriza el precio LME cuando existe (cobalto, cobre, plomo, estaño, zinc). Si no, se usa la forma comercial dominante (fluorita grado ácido, potasa como muriato, etc.).

### Tierras raras: precios proxy
6 de los 15 elementos tienen precio propio (cerium, dysprosium, europium, lanthanum, neodymium, terbium), y el itrio tiene el suyo en un archivo aparte. Los otros 8 (erbium, gadolinium, holmium, lutetium, praseodymium, samarium, thulium, ytterbium) usan como proxy el precio de *mischmetal* (`Price_Mischmetal_dkg`) y se marcan con `is_proxy = TRUE`. Es una aproximación, no un precio de mercado de esos elementos.

## 7. KPIs

### Concentración (HHI)
Suma de las cuotas de mercado (%) al cuadrado por mineral y año, sobre producción (`hhi_production`) y reservas (`hhi_reserves`). Un valor cercano a 10.000 indica un único país dominante. Se calcula solo con 2024. Los minerales con `is_aggregated = TRUE` del mismo grupo tienen HHI idéntico.

### Criticality Score (`criticality_index`)
`0,6 × HHI de producción + 0,4 × HHI de reservas`. La ponderación es una simplificación deliberada que da más peso al riesgo actual que al futuro; no incluye importancia económica ni sustituibilidad.

La vista usa `LEFT JOIN`: si falta uno de los dos datos, el score usa solo el HHI disponible y se señala con `has_production_data` / `has_reserves_data`. Esos scores no son directamente comparables con los que usan ambos datos. Quedan 54 de 55 minerales (falta germanio).

### Mining Value Score (`mining_value_score`)
`toneladas producidas × precio` por mineral, país y año (2024), en USD. Exclusiones:
- Filas con `is_aggregated = TRUE` (tierras raras, PGM, zirconio y hafnio): la producción es la del grupo y el precio es de un solo elemento.
- **Magnesium**: la producción suma compuestos y metal, y el precio es solo del metal.
- **Germanium**: sin producción por país.

## 8. Limitaciones conocidas

- Producción y reservas son solo de 2024; los precios cubren 2020-2024.
- Los precios son estadísticas del USGS (en parte valores unitarios de importaciones a EE. UU.), no un mercado global único. Son USD nominales, sin ajuste por inflación.
- Las filas *Other Countries* se excluyen, así que las cuotas se calculan sobre los países listados.
- **La coincidencia de base entre producción y precio solo se ha comprobado a fondo para cromo, manganeso y wolframio.** Hay diferencias de base evidentes por los nombres de columna que aún no se han corregido:
  - Vanadium: producción en vanadio contenido, precio en V2O5.
  - Tantalum: producción en tantalio contenido, precio en Ta2O5.
  - Potash: producción en K2O, precio de muriato de potasio.
  - Beryllium: producción en berilio contenido, precio de aleación.
  Su Mining Value Score no debe interpretarse hasta revisarlos. El resto de minerales está pendiente de la misma auditoría.
- **Silicon**: la producción mezcla ferrosilicio y silicio metal, y se valora al precio del silicio metal, así que puede estar sobrestimada.
- Para PGM, la producción real de iridio, rodio y rutenio no está publicada.
