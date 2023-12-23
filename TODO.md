 * Package

 * Too many non-toplevel imports in syntax_tree.py?

 X Refactor finished, all test pass.

 X Get rid of utils.py, types.py
   FIX: I think types.py is fine.

 X Refactor Switch.
   FIX: I reread it, its good.

 X Invert the format of the arguments of Pass? The dict one only, the tuple is intuitively clear.
   FIX: now Pass doesn't accept dict at all and the typing system became stricter.

 X Rewrite docstring in markdown format like gpt4all. 

 X Replace OperationAliasT and SyntaxNodeAliasT by Union[Operation, PassAliasT] or Union[SyntaxNode, PassAliasT], respectively.

 X Generate reference using docstrings

 X Standardize error messages.

 X Check types everywhere (duck-typing).

 X Add types everywhere and check them everywhere giving appropriate errors.

 X Write example applications and extract tests from these examples.

 X Write a good documentation. I need it myself.

 X Introduce syntax for:
     X Cycle
     X Switch.

 X Fix the computation of the type tree of Switch.

 X Go through Cycle and Switch, and update the __repr__. Check that the type trees are computed correctly.

 X Remove Conditional, running conditions(lambdas) on the whole inputs break the modularity and can be abused. Use only Switch for branching. Move Switch to .compose?

 X Fix composition, so Id works appropriately. 

 X Add a function to display all the debug information about the operation. What it is composed of, what are the input and output type trees of each part, etc.

 X Make operations immutable HOW: 
    X replace the +x operator by a wrapper. 
    X | and & build a syntax tree that assembles an Operation when called.

 X Rewrite Switch using a dict. 

 X Check how Conditional, Switch, Compose, Concatenate, Cycle should change after introducing pydantic and the `extend` parameter to the Operation.
    X Make input_type_tree of Conditional and Switch into the union of input_type_trees of the operations. (Similar to Concat)
    X Check in Conditional and Switch that the outputs of the operations match taking into account the `append` parameter and use that type tree for the output_type_tree. (Similar to Compose)

 X Use `to_operation` from utils more widely, so that if a non-Operation is passed to an argument that expects Operation, then it is transformed to Pass accordingly.

 X Write the ror and rand magic methods.
