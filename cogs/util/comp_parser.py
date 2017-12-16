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
        elif c in ascii_lowercase+ascii_digits and curr:
            curr += c
        elif c == '(':
            groups.append({})
        elif c == ')':
            group = groups.pop()
            mult = ''
            for i in comp[n+1:]:
                if i not in ascii_digits:
                    break
                mult += i
                skip += 1
            if mult:
                mult = int(mult)
                for k in group.keys():
                    group[k] *= mult

            for k, v in group.items():
                try:
                    groups[-1][k] += v
                except KeyError:
                    groups[-1][k] = v

        elif c in '+-':
            skip = 1

        if curr and (n == len(comp)-1 or comp[n+1] not in ascii_digits+ascii_lowercase):
            number = symbols.index(re.sub('[0-9]', '', curr))+1
            try:
                count = int(re.sub('[A-z]', '', curr))
            except ValueError:
                count = 1
            try:
                groups[-1][number] += count
            except KeyError:
                groups[-1][number] = count
            curr = ''

    if len(groups) != 1: raise ValueError
    return groups[0]


def get_mass(composition):
    acc = 0
    for k, v in composition.items():
        acc += masses[k-1]*v
    return acc


if __name__ == '__main__':
    print(get_mass(parse_comp('AuXe4(Sb2F11)2')))
