LIBERAL_DEMOCRATS = "Lib-Dem"
LABOUR = "Labour"
CONSERVATIVE = "Conservative"

all_parties = {
    'libdem': {
    'name': LIBERAL_DEMOCRATS,
    'id': 'libdem',
    'short_name': 'LD',
    'colour': [255, 179, 22]
    },
    'lab': {
    'name': LABOUR,
    'id': 'lab',
    'short_name': 'LAB',
    'colour': [204, 0, 0]
    },
    'con': {
    'name': CONSERVATIVE,
    'id': 'con',
    'short_name': 'CON',
    'colour': [4, 133, 190]
    }    
}

def all():
    return all_parties.values()
    
