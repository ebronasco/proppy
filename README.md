# proppy

Should support python 3.8

str used for inline representation, repr used for full-debug-level representation.
 * Repr always surrounded by \n
 * str by ""
 * Name of variables by ``

all errors must use raise-from, example, ValidationError in operation.py

Linting:
    flake8: flake8 src
    flake8-errmsg: flake8-errmsg <file>
Hard linting:
    pylint: pylint src
Type checking:
    mypy: mypy src
Testing:
    pytest: pytest --doctest-modules --cov=proppy
Documentation:
    MkDocs
