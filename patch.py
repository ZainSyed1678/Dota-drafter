import json

with open('notebooks/second.ipynb') as f:
    d = json.load(f)

for cell in d['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if 'print(Counter(hero_roles.values()))' in line:
                source[i] = line.replace('print(Counter(hero_roles.values()))', 'pass')

with open('notebooks/second.ipynb', 'w') as f:
    json.dump(d, f)
