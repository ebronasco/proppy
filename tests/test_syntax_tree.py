import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")

from proppy.syntax_nodes import *

from proppy.base.run import Run
from proppy.base.const import Const
from proppy.base.id import N
from proppy.base.empty import E


def test_inputs():
    op = Run({
        'a': lambda s, x, y: x + y,
    })

    assert op(x=1, y=10, z=100) == {'a': 11}

def test_partial():
    op = Run({
        'a': lambda s, x, y: x + y,
    })

    op = ensure_syntax_node(op)

    assert op.partial(x=1)(y=10) == {'a': 11}

def test_composition():
    op1 = Run({
        'a': lambda s, x: x + 1,
        'b': lambda s, x, y: x + y,
    })

    op2 = Run({
        'c': lambda s, a, b: a + b,
    })

    c = N | op1 | op2

    assert c(x=1, y=10) == {'c': 13}


def test_concatenation():
    op1 = Const({
        'a': 1,
    })

    op2 = Run({
        'b': lambda s, x: x + 1,
        'c': lambda s, y: y + 1,
    })

    op3 = Run({
        'd': lambda s, z: z * 2,
    })

    c = E & op1 & op2 & op3

    assert c(x=1, y=10, z=100) == {'a': 1, 'b': 2, 'c': 11, 'd': 200}


def test_append():
    op = Run({
        'a': lambda s, x: x + 1,
    })

    c = +op

    assert c(x=1, y=10) == {'x': 1, 'y': 10, 'a': 2}


def test_composition_append():
    op1 = Run({
        'a': lambda s, x: x + 1,
        'b': lambda s, x, y: x + y,
    })

    op2 = Run({
        'c': lambda s, a, b: a + b,
    })

    c = N | op1 | +op2

    assert c(x=1, y=10) == {'a': 2, 'b': 11, 'c': 13}
