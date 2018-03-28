import math
import statistics
import shlex


rpncalc = {
    # constants
    'pi': ('Pushes the mathematical constant pi', lambda l, v: l.append(math.pi)),
    'e': ('Pushes euler\'s constant', lambda l, v: l.append(math.e)),

    # arithmetic
    '+': ('Pops two numbers, pushes the sum', lambda l, v: l.append(l.pop() + l.pop())),
    '-': ('Pops two numbers, pushes the first minus the second.', lambda l, v: l.append(l.pop() - l.pop())),
    '*': ('Pops two numbers, pushes the product', lambda l, v: l.append(l.pop() * l.pop())),
    '/': ('Pops two numbers, pushes the first divided by the second', lambda l, v: l.append(l.pop() / l.pop())),
    '//': (
        'Pops two numbers, pushes the first divided by the second, rounded down',
        lambda l, v: l.append(l.pop() // l.pop())
    ),
    '^': ('Pops two numbers, pushes the first to the power of the second', lambda l, v: l.append(l.pop() ** l.pop())),
    '**': ('Pops two numbers, pushes the first to the power of the second', lambda l, v: l.append(l.pop() ** l.pop())),
    '%': ('Pops two numbers, pushes the first modulo\'d by the second', lambda l, v: l.append(l.pop() % l.pop())),
    'sqrt': ('Pops one number, pushes its square root', lambda l, v: l.append(l.pop() ** 0.5)),

    # trig
    'sin': ('Sine operator', lambda l, v: l.append(math.sin(l.pop()))),
    'cos': ('Cosine operator', lambda l, v: l.append(math.cos(l.pop()))),
    'tan': ('Tangent operator', lambda l, v: l.append(math.tan(l.pop()))),
    'asin': ('Inverse sine', lambda l, v: l.append(math.asin(l.pop()))),
    'acos': ('Inverse cosine', lambda l, v: l.append(math.acos(l.pop()))),
    'atan': ('Inverse tangent', lambda l, v: l.append(math.atan(l.pop()))),

    # hyperbolic
    'sinh': ('Hyperbolic sine', lambda l, v: l.append(math.sinh(l.pop()))),
    'cosh': ('Hyperbolic cosine', lambda l, v: l.append(math.cosh(l.pop()))),
    'tanh': ('Hyperbolic tangent', lambda l, v: l.append(math.tanh(l.pop()))),
    'asinh': ('Inverse hyperbolic sine', lambda l, v: l.append(math.asinh(l.pop()))),
    'acosh': ('Inverse hyperbolic cosine', lambda l, v: l.append(math.acosh(l.pop()))),
    'atanh': ('Inverse hyperbolic tangent', lambda l, v: l.append(math.atanh(l.pop()))),

    # logs
    'ln': ('Natural logarithm', lambda l, v: l.append(math.log(l.pop()))),
    'log': ('Log in base 10', lambda l, v: l.append(math.log10(l.pop()))),
    'logb': (
        'Pops two numbers, takes logarithm of first in base of second',
        lambda l, v: l.append(math.log(l.pop(), l.pop()))
    ),

    # bitwise operators
    '&': ('Bitwise AND', lambda l, v: l.append(l.pop() & l.pop())),
    '|': ('Bitwise OR', lambda l, v: l.append(l.pop() | l.pop())),
    '^|': ('Bitwise XOR', lambda l, v: l.append(l.pop() ^ l.pop())),
    '!': ('Bitwise complement', lambda l, v: l.append(~l.pop())),
    '~': ('Bitwise complement', lambda l, v: l.append(~l.pop())),
    '<<': ('Pop two numbers, bitshift first left by second', lambda l, v: l.append(l.pop() << l.pop())),
    '>>': ('Pop two numbers, bitshift first right by second', lambda l, v: l.append(l.pop() >> l.pop())),

    # logical operators
    '==': ('Pushes `1` if top two equal, else `0`', lambda l, v: l.append(int(l.pop() == l.pop()))),
    '!=': ('Pushes `1` if top two inequal, else `0`', lambda l, v: l.append(int(l.pop() != l.pop()))),
    '<=': ('Pushes `1` if top less than or equal to second, else `0`', lambda l, v: l.append(int(l.pop() <= l.pop()))),
    '<': ('Pushes `1` if top less than second, else `0`', lambda l, v: l.append(int(l.pop() < l.pop()))),
    '>': ('Pushes `1` if top greater than second, else `0`', lambda l, v: l.append(int(l.pop() > l.pop()))),
    '>=': (
        'Pushes `1` if top greater than or equal to second, else `0`',
        lambda l, v: l.append(int(l.pop() <= l.pop()))
    ),

    # misc math
    'ceil': ('Ceiling function', lambda l, v: l.append(math.ceil(l.pop()))),
    'flr': ('Ceiling function', lambda l, v: l.append(math.floor(l.pop()))),

    # statistics
    'meana': ('Pushes mean of entire stack. Keeps stack', lambda l, v: l.append(statistics.mean(l))),
    'stdva': ('Pushes standard deviation of entire stack. Keeps stack', lambda l, v: l.append(statistics.stdev(l))),
    'mean': (
        'Pops one number as n, pushes mean of top n numbers and pops them.',
        lambda l, v: l.append(statistics.mean([l.pop() for _ in range(l.pop())]))
    ),
    'stdv': (
        'Pops one number as n, pushes standard deviation of top n numbers and pops them.',
        lambda l, v: l.append(statistics.stdev([l.pop() for _ in range(l.pop())]))
    ),
    'meanstdva': (
        'Pushes standard deviation, followed by mean, of entire stack. Keeps stack.',
        lambda l, v: l.extend([
            statistics.stdev(l),
            statistics.mean(l)
        ])
    ),
    'meanstdv': (
        'Pops one number as n, pushes standard deviation, followed by mean, of top n numbers and pops them.',
        lambda l, v: l.extend([
            statistics.stdev(l[1: l[0]+1]),
            statistics.mean([l.pop() for _ in range(l.pop())])
        ])
     ),

    # strings
    'chr': ('Converts the top item of the stack to a utf-8 character', lambda l, v: l.append(chr(l.pop()))),
    'str': (
        'Converts the top element to its string representation. The string representation of `"a"` is `"\'a\'"`',
        lambda l, v: l.append(to_str(l.pop()))
    ),
    "'": (
        "Pushes a string to stack. `'` will push an empty string, `'abc` pushes the string `'abc'`, "
        "`''` pushes the string `\"'\"`, `'1` pushes the string `'1'`",
        lambda l, v: l.append('')
    ),

    # meta
    'eval': (
        'Evaluate the top of the stack as an expression.',
        lambda l, v: eval_rpn(l.pop(), l, v)
    ),
    'veval': (
        'Evaluate the variable at the top of the stack',
        lambda l, v: eval_rpn(v[l.pop()], l, v)
    ),
    'evals': (
        'Evaluate the top of the stack as an expression, using an empty stack, '
        'then adds the new stack to the original stack. This is safer than `eval`',
        lambda l, v: l.extend(eval_rpn(l.pop(), [], v))
    ),
    'vevals': (
        'Evaluate the variable at the top of the stack, using an empty stack, '
        'then adds the new stack to the original stack. This is safer than `veval`',
        lambda l, v: l.extend(eval_rpn(v[l.pop()], [], v))
    ),
    'cond': (
        'Pop 3 values, if the top value is an empty string or `0`, push the third, else push the second',
        lambda l, v: l.append((lambda i, c: c[i-1])(bool(l.pop()), (l.pop(), l.pop())))
    ),

    # stack operations
    'swp': ('Swap the  top two items of the stack.', lambda l, v: l.extend([l.pop(), l.pop()])),
    'drp': ('Drop the top item of the stack', lambda l, v: l.pop()),
    'dup': ('Duplicate the top item of the stack', lambda l, v: l.extend([l.pop()]*2)),
    'rot': (
        'Pops the top number as n, rotates the stack from top to bottom by n places.',
        lambda l, v: [l.insert(0, l.pop()) for _ in range(l.pop() % len(l))]
    ),
    'clrs': ('Clear the stack', lambda l, v: l.clear()),


    # variables/heap
    'set': (
        'Pops two items from the stack, assigns the second to a variable with the name of the first. '
        'The integer `0` is considered a different variable than the string `"0"`, however, '
        'the integer `0`, the float `0.0` and the complex number `0+0i` are considered the same variable.',
        lambda l, v: v.__setitem__(l.pop(), l.pop())
    ),
    'get': (
        'Pops a value and pushes the value bound to that variable. See the `set` operator for help on variable names.',
        lambda l, v: l.append(v[l.pop()])
    ),
    'unset': (
        'Removes a variable.',
        lambda l, v: v.pop(l.pop())
    ),
    'clrv': ('Clear all variables', lambda l, v: v.clear()),

    'clra': ('Clear the stack and variables', lambda l, v: (v.clear(), l.clear())),
    'clr': ('Clear the stack and variables', lambda l, v: (v.clear(), l.clear())),
}


def eval_rpn(expression, stack, heap):
    s = shlex.shlex(expression)
    s.quotes = '"'
    s.whitespace_split = True
    for n, op in enumerate(list(s)):
        if op in rpncalc:
            try:
                rpncalc[op][1](stack, heap)
            except IndexError:
                raise RuntimeError(f'Stack size too small on operation {n+1}: `{op}`')
            except Exception as e:
                raise RuntimeError(f'{e}, on operation {n+1}')

        else:
            try:
                stack.append(convert(op))
            except ValueError:
                raise RuntimeError(f'Invalid value or operation: `{op}` on operation {n+1}')

    return stack


def std_complex(string) -> complex:
    try:
        return complex(string)
    except ValueError:
        return complex(string.replace('i', 'j'))


def std_str(string) -> str:
    if string.startswith("'"):
        return string[1:]
    else:
        raise ValueError


conv_list = [
    int,
    float,
    std_complex,
    std_str,
]


def convert(string):
    for func in conv_list:
        try:
            return func(string)
        except ValueError:
            pass

    raise ValueError


def to_str(value):
    out = repr(value)
    if isinstance(value, complex):
        out = out.replace('j', 'i')

    return out
