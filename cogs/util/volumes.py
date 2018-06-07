volume_units = {
    'ml': ('millilitres', 1),
    'cc': ('cubic centimetres', 1),
    'l': ('litres', 1000),
    'm3': ('cubic metres', 1000*1000),
    'cm3': ('cubic centimetres', 1),
    'gill': ('gills', 118.294),
    'gi': ('gills', 118.294),
    'pint': ('pints', 473.176),
    'pt': ('pints', 473.176),
    'p': ('pints', 473.176),
    'gal': ('gallons', 3785.4118),
    'gallon': ('gallons', 3785.4118),
    'cup': ('cups', 236.5882375),
    'tablespoon': ('tablespoons', 14.7868),
    'tbsp': ('tablespoons', 14.7868),
    'teaspoon': ('teaspoons', 5),
    'tsp': ('teaspoons', 5),
    'floz': ('fluid ounces', 29.5735),
    'ozfl': ('fluid ounces', 29.5735),
    'cuin': ('cubic inches', 16.387064),
    'in3': ('cubic inches', 16.387064),
    'cuft': ('cubic feet', 1000*28.316846592),
    'ft3': ('cubic feet', 1000*28.316846592),
    'cuyd': ('cubic yards', 1000*764.554857984),
    'yd3': ('cubic yards', 1000*764.554857984),
    'acreft': ('acre-feet', 1000*1000*1233.482),
    'acre-feet': ('acre-feet', 1000*1000*1233.482),
    'minim': ('minims', 0.0616115),
    'min': ('minims', 0.0616115),
    'fldr': ('fluid drams', 3.6966911953125),
    'shot': ('shots', 44.36029434375),
    'jig': ('shots', 44.36029434375),
    'quart': ('quarts', 946,352946),
    'qt': ('quarts', 946,352946),
    'barrel': ('barrels', 1000*119.240471196),
    'bbl': ('barrels', 1000*119.240471196),
    'hogshead': ('hogsheads', 1000*238.480942392)
}

def volume(arg):
    num = ''
    for c in arg:
        if c in '0123456789.': num += c
        else: break

    units = arg[len(num):]
    return [float(num), units.lower().replace(' ', '').replace('.', '')]

