"""Loading the doctests so they can be run by unittest and pytest."""
import doctest

from . import tree_utils
from . import base
from . import syntax_tree
from . import combine


# This is the standard unittest function.
def load_tests(loader, tests, ignore):  # pylint: disable=unused-argument
    """Load the tests."""
    tests.addTests(doctest.DocTestSuite(tree_utils))
    tests.addTests(doctest.DocTestSuite(base))
    tests.addTests(doctest.DocTestSuite(syntax_tree))
    tests.addTests(doctest.DocTestSuite(combine))
    return tests
