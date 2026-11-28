"""The applications `modal_compare.py` measures (`T1.C.9`): the three Express applications of `benchmarks/noir-binding/apps.py` at their
commits, and `tududi` at the commit of `benchmarks/system-map/modal_map.py` (`CASES`). Nothing of them is in the repository: each is fetched
at its commit while the Modal image is built (`https://codeload.github.com/<repository>/tar.gz/<commit>`) and only read there.
`test_express_compare.py` checks that the three commits are noir-binding's.
"""

# name -> (repository, commit, licence)
CASES = {
    "node-express-boilerplate": ("hagopj13/node-express-boilerplate", "179ae84efec61b14206d0305d941daed6c6d07f9", "MIT"),
    "anything-llm": ("Mintplex-Labs/anything-llm", "593c0943facbe0a5e1cfac2d7616f15707a9317a", "MIT"),
    "juice-shop": ("juice-shop/juice-shop", "c9f99228d9d56afb5f5ca7925376292f7fa44b13", "MIT"),
    "tududi": ("chrisvel/tududi", "71da9d7b34dfd1600657e9c5ddf40420206fd263", "MIT"),
}
RULES = "benchmarks/tududi-flow/rules.json"  # the `offre` rule of tududi: the third comparison
