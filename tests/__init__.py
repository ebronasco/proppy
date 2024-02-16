"""Loading the doctests so they can be run by unittest and pytest."""

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")

import doctest

from proppy import base
from proppy import syntax_nodes
from proppy import unions
from proppy import validators


# This is the standard unittest function.
def load_tests(loader, tests, ignore):  # pylint: disable=unused-argument
    """Load the tests."""
    tests.addTests(doctest.DocTestSuite(base))
    tests.addTests(doctest.DocTestSuite(syntax_nodes))
    tests.addTests(doctest.DocTestSuite(unions))
    tests.addTests(doctest.DocTestSuite(validators))
    return tests
