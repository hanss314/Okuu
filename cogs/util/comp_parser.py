import re

from .elems import masses, symbols
from string import ascii_lowercase, ascii_uppercase
ascii_digits = '0123456789'


def parse_comp(comp):
    groups = [{}]
    curr = ''
    skip = 0
    for n, c in enumerate(comp):
        if skip:
            skip -= 1
            continue
        if c in ascii_uppercase:
            curr = c
        elif c in ascii_lowercase+ascii_digits+'+-' and curr:
            curr += c
        elif c == '(':
            groups.append({})
        elif c == ')':
            group = groups.pop()
            mult = ''
            for i in comp[n+1:]:
                if i not in ascii_digits+'+-':
                    break
                mult += i
                skip += 1

            if mult:
                if '+' in mult:
                    parts = mult.split('+')
                    count = int(parts[1] or 1)
                    charge = int(parts[0] or 1)
                elif '-' in mult:
                    parts = mult.split('-')
                    count = int(parts[1] or 1)
                    charge = -int(parts[0] or 1)
                else:
                    count = int(mult)
                    charge = 0

                for k in group.keys():
                    group[k] *= count

                try:
                    group[0] += charge * count
                except KeyError:
                    group[0] = charge * count

            for k, v in group.items():
                try:
                    groups[-1][k] += v
                except KeyError:
                    groups[-1][k] = v

        if curr and (n == len(comp)-1 or comp[n+1] in ascii_uppercase+'()'):
            number = symbols.index(''.join(
                x for x in curr if x in ascii_uppercase + ascii_lowercase)
            ) + 1

            if '-' in curr:
                parts = curr.split('-')
                charge = -int(''.join(x for x in parts[0] if x in ascii_digits) or '1')
                curr = parts[1]
            elif '+' in curr:
                parts = curr.split('+')
                charge = +int(''.join(x for x in parts[0] if x in ascii_digits) or '1')
                curr = parts[1]
            else:
                charge = 0

            try:
                count = int(re.sub('[A-z]', '', curr))
            except ValueError:
                count = 1

            try:
                groups[-1][number] += count
            except KeyError:
                groups[-1][number] = count

            try:
                groups[-1][0] += count*charge
            except KeyError:
                groups[-1][0] = count*charge

            curr = ''

    if len(groups) != 1:
        raise ValueError('Imbalanced parentheses')

    return groups[0]


def get_mass(composition):
    acc = 0
    for k, v in composition.items():
        if k > 0:
            acc += masses[k-1]*v
    return acc, composition[0] if 0 in composition else 0


if __name__ == '__main__':
    print(get_mass(parse_comp('AuXe4(Sb2F11)2')))
