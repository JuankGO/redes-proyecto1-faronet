import json
import sys

COLS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def p(s):
    return (COLS.index(s[0]), int(s[1:]))


def name(c, r):
    return f'{COLS[c]}{r:02d}'


def seg(a, b):
    (c1, r1), (c2, r2) = p(a), p(b)
    assert c1 == c2 or r1 == r2, (a, b)
    out = []
    if c1 == c2:
        for r in range(min(r1, r2), max(r1, r2) + 1):
            out.append(name(c1, r))
    else:
        for c in range(min(c1, c2), max(c1, c2) + 1):
            out.append(name(c, r1))
    return out



PARTS = {
    'J1': ('header', 'Header 7 pines', {
        '1': ('B16', '3V3'), '2': ('B17', 'GND'), '3': ('B18', 'TX'), '4': ('B19', 'RX'),
        '5': ('B20', 'TXL'), '6': ('B21', 'RXL'), '7': ('B22', 'BTN')}),
    'D1': ('irled', 'LED IR transparente', {'A': ('I04', '3V3'), 'K': ('J04', 'IRK')}),
    'Q2': ('photo', 'PT333 negro', {'C': ('O04', 'RX'), 'E': ('P04', 'GND')}),
    'R1': ('res', '330 Ω', {'1': ('J05', 'IRK'), '2': ('J09', 'COL')}),
    'Q1': ('npn', '2N2222A', {'E': ('H10', 'GND'), 'B': ('I10', 'BASE'), 'C': ('J10', 'COL')}),
    'R2': ('res', '2,2 kΩ', {'1': ('E11', 'TX'), '2': ('I11', 'BASE')}),
    'R3': ('res', '10 kΩ', {'1': ('I12', 'BASE'), '2': ('M12', 'GND')}),
    'R4': ('res', '10 kΩ', {'1': ('O06', 'RX'), '2': ('S06', '3V3')}),
    'C1': ('cap', '100 nF (104)', {'1': ('S10', '3V3'), '2': ('S12', 'GND')}),
    'D2': ('led', 'LED TX', {'K': ('G16', 'GND'), 'A': ('G17', 'LTXA')}),
    'R5': ('res', '1 kΩ', {'1': ('G18', 'LTXA'), '2': ('G22', 'TXL')}),
    'D3': ('led', 'LED RX', {'K': ('K16', 'GND'), 'A': ('K17', 'LRXA')}),
    'R6': ('res', '1 kΩ', {'1': ('K18', 'LRXA'), '2': ('K22', 'RXL')}),
    'SW1': ('button', 'Botón de pánico', {
        'a1': ('N17', 'GND'), 'a2': ('S17', 'GND'), 'b1': ('N19', 'BTN'), 'b2': ('S19', 'BTN')}),
}


TRACKS = [
    ('3V3', 'B02', 'B16'), ('3V3', 'B02', 'S02'), ('3V3', 'I02', 'I04'), ('3V3', 'S02', 'S10'),
    ('GND', 'B17', 'D17'), ('GND', 'D14', 'D17'), ('GND', 'D14', 'S14'),
    ('GND', 'G10', 'H10'), ('GND', 'G10', 'G16'), ('GND', 'K14', 'K16'),
    ('GND', 'M12', 'M14'), ('GND', 'N14', 'N17'), ('GND', 'P04', 'Q04'),
    ('GND', 'Q04', 'Q14'), ('GND', 'S12', 'S14'),
    ('IRK', 'J04', 'J05'), ('COL', 'J09', 'J10'), ('BASE', 'I10', 'I12'),
    ('TX', 'B18', 'C18'), ('TX', 'D11', 'E11'),
    ('RX', 'B19', 'C19'), ('RX', 'O04', 'O06'),
    ('TXL', 'B20', 'C20'), ('TXL', 'G22', 'G23'),
    ('RXL', 'B21', 'C21'), ('RXL', 'K22', 'K23'),
    ('BTN', 'B22', 'C22'), ('BTN', 'M19', 'N19'),
    ('LTXA', 'G17', 'G18'), ('LRXA', 'K17', 'K18'),
]


WIRES = [
    ('W1', 'TX', 'C18', 'D11', 'naranja'),
    ('W2', 'RX', 'C19', 'O05', 'azul'),
    ('W3', 'TXL', 'C20', 'G23', 'verde'),
    ('W4', 'RXL', 'C21', 'K23', 'amarillo'),
    ('W5', 'BTN', 'C22', 'M19', 'blanco'),
]

INTERNAL = [('N17', 'S17'), ('N19', 'S19')]


def check():
    errors = []
    owner = {}

    def claim(hole, net, who):
        if hole in owner and owner[hole][0] != net:
            errors.append(f'{hole}: {who} ({net}) choca con {owner[hole][1]} ({owner[hole][0]})')
        owner.setdefault(hole, (net, who))

    pins = {}
    for pid, (_, _, pp) in PARTS.items():
        for pin, (hole, net) in pp.items():
            if hole in pins:
                errors.append(f'{hole} tiene dos patas: {pins[hole]} y {pid}.{pin}')
            pins[hole] = f'{pid}.{pin}'
            claim(hole, net, f'{pid}.{pin}')
    for net, a, b in TRACKS:
        for h in seg(a, b):
            claim(h, net, f'pista {a}-{b}')
    for wid, net, a, b, _ in WIRES:
        for h in (a, b):
            if h in pins:
                errors.append(f'{wid}: {h} ya tiene la pata {pins[h]}')
            claim(h, net, wid)


    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for net, a, b in TRACKS:
        s = seg(a, b)
        for x, y in zip(s, s[1:]):
            union(x, y)
    for _, _, a, b, _ in WIRES:
        union(a, b)
    for a, b in INTERNAL:
        union(a, b)
    nets = {}
    for hole, (net, _) in owner.items():
        nets.setdefault(net, set()).add(find(hole))
    for net, roots in sorted(nets.items()):
        if len(roots) != 1:
            errors.append(f'Red {net} quedó partida en {len(roots)} pedazos')


    def dist(a, b):
        (c1, r1), (c2, r2) = p(a), p(b)
        return abs(c1 - c2) + abs(r1 - r2), (c1 == c2 or r1 == r2)
    for pid, (kind, _, pp) in PARTS.items():
        holes = [h for h, _ in pp.values()]
        if kind in ('res',):
            d, straight = dist(*holes)
            if d != 4 or not straight:
                errors.append(f'{pid}: separación {d} (se esperan 4 agujeros en línea)')
        if kind in ('led', 'irled', 'photo', 'cap'):
            d, straight = dist(*holes)
            if d not in (1, 2) or not straight:
                errors.append(f'{pid}: separación {d}')
    q = [p(PARTS['Q1'][2][k][0]) for k in 'EBC']
    if not (q[0][1] == q[1][1] == q[2][1] and q[1][0] - q[0][0] == 1 and q[2][0] - q[1][0] == 1):
        errors.append('Q1 debe tener E, B y C seguidos en la misma fila')
    sw = {k: p(v[0]) for k, v in PARTS['SW1'][2].items()}
    if sw['a2'][0] - sw['a1'][0] != 5 or sw['b1'][1] - sw['a1'][1] != 2:
        errors.append('SW1 debe medir 5 x 2 agujeros (12,7 x 5,1 mm)')


    caution = []
    for hole, (net, _) in owner.items():
        c, r = p(hole)
        for dc, dr in ((1, 0), (0, 1)):
            if c + dc >= len(COLS):
                continue
            other = name(c + dc, r + dr)
            if other in owner and owner[other][0] != net:
                caution.append((hole, other))
    return errors, sorted(caution), owner


if __name__ == '__main__':
    errors, caution, owner = check()
    for e in errors:
        print('ERROR:', e)
    print(f'{len(owner)} agujeros usados, {len(caution)} pares vecinos de redes distintas')
    for a, b in caution:
        print('  cuidado:', a, owner[a][0], '|', b, owner[b][0])
    if errors:
        sys.exit(1)
    data = {
        'parts': {k: {'kind': v[0], 'value': v[1],
                      'pins': {pin: {'hole': h, 'net': n} for pin, (h, n) in v[2].items()}}
                  for k, v in PARTS.items()},
        'tracks': [{'net': n, 'from': a, 'to': b} for n, a, b in TRACKS],
        'wires': [{'id': i, 'net': n, 'from': a, 'to': b, 'color': c} for i, n, a, b, c in WIRES],
        'caution': caution,
    }
    with open(sys.argv[1] if len(sys.argv) > 1 else 'layout.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print('OK: todas las redes coinciden con el circuito probado')
