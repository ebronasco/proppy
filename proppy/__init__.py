"""Loading the doctests so they can be run by unittest and pytest."""
import doctest

from . import base
from . import syntax_nodes
from . import unions
from . import validators


# This is the standard unittest function.
def load_tests(loader, tests, ignore):  # pylint: disable=unused-argument
    """Load the tests."""
    tests.addTests(doctest.DocTestSuite(base))
    tests.addTests(doctest.DocTestSuite(syntax_nodes))
    tests.addTests(doctest.DocTestSuite(unions))
    tests.addTests(doctest.DocTestSuite(validators))
    return tests
