# Metodología.


## Fuente de datos.
USGS Mineral Commodity Summaries 2025, Data Release (World Data), 
https://www.usgs.gov/data/us-geological-survey-mineral-commodity-summaries-2025-data-release-ver-20-april-2025

## Cobertura.
De los 60 minerales críticos de la lista oficial 2025 (USGS/Departamento de Interior),
55 están representados en este dataset. No tienen datos disponibles: cesium, scandium,
rubidium, metallurgical coal, uranium.


## Limpieza de datos de origen.
El archivo fuente de USGS contiene varias inconsistencias típicas de datos gubernamentales,
corregidas antes de cargar a la base de datos:

- **Nombres de commodity con espacios sobrantes** (ej. `"Barite  "`, `"Tungsten "`) y un
  error tipográfico (`"Gemanium"` → corregido a `"Germanium"`).

- **Nombres de país inconsistentes**: espacios sobrantes, caracteres especiales (espacio
  duro `\xa0`), y notas de proceso entre paréntesis que no forman parte del nombre real
  del país (ej. `"Brazil (beneficiated)"` → `"Brazil"`, `"United States (crude)"` →
  `"United States"`).

- **Excepción notable**: `"Congo (Kinshasa)"` se resolvió como
  `"Democratic Republic of the Congo"`, distinguiéndolo explícitamente de la República
  del Congo (Brazzaville, no presente en este dataset) — una distinción importante dado
  que la RD Congo domina la producción mundial de cobalto.

- **Filas de "World total (rounded)" y "Other Countries"** excluidas del análisis por país
  (se conservan aparte como referencia de totales mundiales).

- **`"United States and Canada"`** (dato combinado bilateral, sin desglose) excluido del
  análisis por país para evitar doble conteo con los datos individuales de EE.UU. y Canadá.

- **Valores de reservas con prefijo `">"`** (ej. `">2,000,000"`, indicando reserva mínima
  conocida) — el símbolo se elimina y se conserva el valor numérico; todos los casos
  observados corresponden a filas de "World total", no a países individuales.

- **Códigos ISO de país** asignados con la librería `pycountry`, con excepciones manuales
  para nombres no estándar (`"Burma"` → Myanmar, `"Korea, North"`, `"Turkey"` → nombre
  actualizado a Türkiye en bases ISO recientes, etc.).



## Decisiones de agregación y limpieza.

- **Rare earths**: tratado como categoría agregada. Los 15 elementos individuales
  (cerium, dysprosium, erbium, europium, gadolinium, holmium, lanthanum, lutetium,
  neodymium, praseodymium, samarium, terbium, thulium, ytterbium, yttrium) comparten
  el mismo valor de producción/reservas del grupo. Marcado con `is_aggregated = TRUE`.

- **Platinum-Group metals**: igual que rare earths, agregado entre platinum, palladium,
  iridium, rhodium, ruthenium.

- **Titanium**: se usa solo "Titanium Mineral Concentrates" (ilmenita + rutilo, sumados).
  Se excluye "Titanium & titanium dioxide" (sponge metal / pigment capacity) por medir
  conceptos distintos y solaparse con la fuente elegida.

- **Copper**: se usa solo producción minera ("Mine production, recoverable copper content").
  Se excluye producción de refinería para no mezclar etapas distintas de la cadena de valor.

- **Potash**: reservas medidas en K2O equivalente (estándar de la industria), 
  excluyendo "Reserves, recoverable ore" (mismo dato en otra unidad).

- **Magnesium**: "Magnesium Compounds" y "Magnesium metal" sumados en un único valor.



## Limitaciones conocidas.
Los valores de producción y reservas para categorías agregadas (Rare earths, PGM) 
no reflejan la contribución real de cada elemento individual, sino el total del grupo.
Cualquier cálculo económico o de criticidad a nivel de elemento individual dentro de
estos grupos debe interpretarse con esta limitación en mente.