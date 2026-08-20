# etl/mappings.py
from collections import defaultdict

critical_to_csv = {
    'aluminum': ['Aluminum'], 'antimony': ['Antimony'], 'arsenic': ['Arsenic'],
    'barite': ['Barite'], 'beryllium': ['Beryllium'], 'bismuth': ['Bismuth'],
    'boron': ['Boron'], 'chromium': ['Chromium'], 'cobalt': ['Cobalt'],
    'copper': ['Copper'], 'fluorspar': ['Fluorspar'], 'gallium': ['Gallium'],
    'germanium': ['Germanium'], 'graphite': ['Graphite'], 'indium': ['Indium'],
    'lead': ['Lead'], 'lithium': ['Lithium'], 'magnesium': ['Magnesium Compounds', 'Magnesium metal'],
    'manganese': ['Manganese'], 'nickel': ['Nickel'], 'niobium': ['Niobium'],
    'phosphate': ['Phosphate rock'], 'potash': ['Potash'], 'rhenium': ['Rhenium'],
    'silicon': ['Silicon'], 'silver': ['Silver'], 'tantalum': ['Tantalum'],
    'tellurium': ['Tellurium'], 'tin': ['Tin'],
    'titanium': ['Titanium Mineral Concentrates'],
    'tungsten': ['Tungsten'], 'vanadium': ['Vanadium'], 'zinc': ['Zinc'],
    'zirconium': ['Zirconium and Hafnium'], 'hafnium': ['Zirconium and Hafnium'],
    'platinum': ['Platinum-Group metals'], 'palladium': ['Platinum-Group metals'],
    'iridium': ['Platinum-Group metals'], 'rhodium': ['Platinum-Group metals'],
    'ruthenium': ['Platinum-Group metals'],
    'cerium': ['Rare earths'], 'dysprosium': ['Rare earths'], 'erbium': ['Rare earths'],
    'europium': ['Rare earths'], 'gadolinium': ['Rare earths'], 'holmium': ['Rare earths'],
    'lanthanum': ['Rare earths'], 'lutetium': ['Rare earths'], 'neodymium': ['Rare earths'],
    'praseodymium': ['Rare earths'], 'samarium': ['Rare earths'], 'terbium': ['Rare earths'],
    'thulium': ['Rare earths'], 'ytterbium': ['Rare earths'], 'yttrium': ['Rare earths'],
}

csv_to_criticals = defaultdict(list)
for critical_name, csv_names in critical_to_csv.items():
    for csv_name in csv_names:
        csv_to_criticals[csv_name].append(critical_name)