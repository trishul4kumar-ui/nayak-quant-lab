# Expression complexity

When two expressions carry comparable train-fold information, prefer the simpler tree.

The versioned score (`ic_complexity_v1`) combines node count, depth, operators, constants, and distinct features. Complexity weights are frozen with the grammar. Choosing weights after seeing holdout is `future_complexity_selection` FAIL.
