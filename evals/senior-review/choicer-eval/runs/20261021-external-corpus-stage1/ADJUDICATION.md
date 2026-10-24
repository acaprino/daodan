# External corpus Stage 2 adjudication

Gate passed: False. This file is not a frozen benchmark.

| Lens | Positives | Explicit negatives | Positive projects |
| --- | ---: | ---: | ---: |
| security-auditor | 8 | 36 | 4 |
| data-integrity-auditor | 5 | 15 | 4 |
| temporal-resilience-auditor | 2 | 25 | 2 |
| resource-lifecycle-auditor | 1 | 25 | 1 |
| ui-race-auditor | 5 | 23 | 5 |
| distributed-flow-auditor | 30 | 3 | 15 |
| logic-integrity-auditor | 8 | 17 | 6 |
| cleanup-auditor | 1 | 35 | 1 |

## Gate

- positives_at_least_6_per_lens: fail
- explicit_negatives_at_least_24: pass
- positive_projects_at_least_2_per_lens: fail
- adjudicated_candidates_at_least_48: pass

## Accepted positives

- X001 (swe-bench-verified, django/django, development): security-auditor, data-integrity-auditor, distributed-flow-auditor, logic-integrity-auditor; Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- X002 (swe-bench-verified, pytest-dev/pytest, verification): distributed-flow-auditor; Pytest 6: Dynamically adding xfail marker in test no longer ignores failure <!-- Thanks for submitting an issue! Here's a quick checklist for what to provide: --> ## Description With pytest 5.x, we can dynamically add an xfail to a test `request` object using `request.node.add_marker(mark)` (see exa
- X003 (swe-bench-verified, sphinx-doc/sphinx, verification): distributed-flow-auditor; Inconsistent behaviour with type alias documentation (not overwriting all the default messages, just some) **Describe the bug** Hello, I have 3 muiltiline docstrings for type aliases (using the next-line `"""` documentation syntax). For 1 one them the docstring is correctly shown in the rendered HTM
- X004 (swe-bench-verified, django/django, development): distributed-flow-auditor; Optimize .delete() to use only required fields. Description Hi! We're in the process of upgrading our Django 1.11 installation from Python 2.7 to Python 3.6, however are hitting an unexpected UnicodeDecodeError during a .delete() run by our daily data purging management command. STR: Have an existin
- X005 (swe-bench-verified, django/django, development): data-integrity-auditor, distributed-flow-auditor; Use Python stdlib html.escape() to in django.utils.html.escape() Description The function django.utils.html.escape() partially duplicates the Python stdlib function html.escape(). We can replace this duplication with wider community developed version. html.escape() has been available since Python 3.
- X006 (swe-bench-verified, matplotlib/matplotlib, development): distributed-flow-auditor; [Bug]: Confusing deprecation warning when empty data passed to axis with category units ### Bug summary I'm seeing a `MatplotlibDeprecationWarning` when using calling axes methods on empty data structures for axes that are using string unit converters. I think this is either a false alarm or a non-a
- X008 (swe-bench-verified, sphinx-doc/sphinx, verification): data-integrity-auditor, ui-race-auditor, distributed-flow-auditor; Message.locations duplicate unnecessary ### Describe the bug When running `make clean; make gettext` there are times the list of locations is duplicated unnecessarily, example: ``` #: ../../manual/render/shader_nodes/vector/vector_rotate.rst:38 #: ../../manual/modeling/hair.rst:0 #: ../../manual/mod
- X009 (swe-bench-verified, astropy/astropy, development): distributed-flow-auditor, logic-integrity-auditor; TimeSeries: misleading exception when required column check fails. <!-- This comments are hidden when you submit the issue, so you do not need to remove them! --> <!-- Please be sure to check out our contributing guidelines, https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md . Please be su
- X010 (swe-bench-verified, astropy/astropy, development): distributed-flow-auditor; A direct approach to ITRS to Observed transformations that stays within the ITRS. <!-- This comments are hidden when you submit the issue, so you do not need to remove them! --> <!-- Please be sure to check out our contributing guidelines, https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md
- X011 (swe-bench-verified, matplotlib/matplotlib, development): ui-race-auditor, distributed-flow-auditor; [Bug]: Datetime axis with usetex is unclear ### Bug summary The spacing for a datetime axis when using `usetex=True` is unclear in matplotlib version 3.4 when comparing it to 3.3. ### Code for reproduction ```python import matplotlib import matplotlib.pyplot as plt import numpy as np import pandas a
- X012 (swe-bench-verified, psf/requests, development): distributed-flow-auditor; quote qop options in Digest Auth Based on RFC2617 (http://tools.ietf.org/html/rfc2617), the value of 'qop-options' directive should be quoted with double quotes: ``` qop-options This directive is optional, but is made so only for backward compatibility with RFC 2069 [6]; it SHOULD be used by all imp
- X013 (swe-bench-verified, psf/requests, development): distributed-flow-auditor, logic-integrity-auditor; Getting http://.example.com raises UnicodeError Attempting to get e.g. `http://.example.com` results in a `UnicodeError`. It seems like the intention so far has been to raise `InvalidUrl` instead (see e.g. [this line](https://github.com/psf/requests/blob/ca6f9af5dba09591007b15a7368bc0f006b7cc50/requ
- X014 (swe-bench-verified, pydata/xarray, verification): distributed-flow-auditor; DataArray.integrate has a 'dim' arg, but Dataset.integrate has a 'coord' arg This is just a minor gripe but I think it should be fixed. The API syntax is inconsistent: ```python ds.differentiate(coord='x') da.differentiate(coord='x') ds.integrate(coord='x') da.integrate(dim='x') # why dim?? ``` It s
- X015 (swe-bench-verified, pydata/xarray, verification): distributed-flow-auditor, logic-integrity-auditor; Naming a dimension "method" throws error when calling ".loc" #### Code Sample, a copy-pastable example if possible ```python import numpy as np from xarray import DataArray empty = np.zeros((2,2)) D1 = DataArray(empty, dims=['dim1', 'dim2'], coords={'dim1':['x', 'y'], 'dim2':['a', 'b']}) D2 = DataAr
- X016 (swe-bench-verified, pydata/xarray, verification): logic-integrity-auditor; `polyval` with timedelta64 coordinates produces wrong results ### What happened? I'm not sure if this is a bug or an expected breaking change, but I'm not able to reproduce the results generated by `polyval` using a timedelta64 coordinate. The results are correct in `xarray=2022.3.0`, whereas they a
- X020 (swe-bench-verified, sphinx-doc/sphinx, verification): logic-integrity-auditor; Use of literalinclude prepend results in incorrect indent formatting for code eamples ### Describe the bug Cannot determine a mechanism to use literalinclude directive with `prepend` or `append` to match code example indentation, as leading whitespace is removed. ### How to Reproduce Example of incl
- X022 (swe-bench-verified, sympy/sympy, development): data-integrity-auditor, distributed-flow-auditor; Factor with extension=True drops a factor of y-1 I guess this related (or a duplicate of?) #5786 This is from stackoverflow: https://stackoverflow.com/questions/60682765/python-sympy-factoring-polynomial-over-complex-numbers ```julia In [9]: z = expand((x-1)*(y-1)) In [10]: z Out[10]: x⋅y - x - y + 
- X023 (swe-bench-verified, sympy/sympy, development): distributed-flow-auditor; `PolyElement.as_expr()` not accepting symbols The method `PolyElement.as_expr()` https://github.com/sympy/sympy/blob/193e3825645d93c73e31cdceb6d742cc6919624d/sympy/polys/rings.py#L618-L624 is supposed to let you set the symbols you want to use, but, as it stands, either you pass the wrong number of 
- X024 (swe-bench-verified, astropy/astropy, development): logic-integrity-auditor; Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels Consider the following model: ```python from astropy.modeling import models as m from astropy.modeling.separable import separability_matrix cm = m.Linear1D(10) & m.Linear1D(5) ``` It's separability mat
- X025 (multi-swe-bench, mui/material-ui, development): ui-race-auditor; [system] Add outlineColor to defaultSxConfig; [system] `sx` field outlineColor doesn't take the theme into account
- X027 (multi-swe-bench, mui/material-ui, development): data-integrity-auditor; [joy-ui][Stepper] Add new `Stepper` components; [joy-ui] Add `Stepper` component
- X028 (multi-swe-bench, axios/axios, development): distributed-flow-auditor; fix(adapters): improved adapters loading logic to have clear error messages;; Tests No Longer Passing since Upgrading to v1.5.0
- X029 (multi-swe-bench, axios/axios, development): distributed-flow-auditor; fix(utils): make isFormData detection logic stricter to avoid unnecessary calling of the `toString` method on the target;; Uploading large files > 512 MB fails
- X030 (multi-swe-bench, axios/axios, development): distributed-flow-auditor; Fixed handling of array values for AxiosHeaders;; [1.0.0] Set-Cookie header in a response interceptor is not an array anymore
- X032 (multi-swe-bench, grpc/grpc-go, development): distributed-flow-auditor; balancer/base: consider an empty address list an error; dns + round_robin not updating address list in v1.26
- X033 (multi-swe-bench, grpc/grpc-go, development): distributed-flow-auditor; grpclb: support explicit fallback signal; Support explicit fallback in grpclb
- X035 (multi-swe-bench, fasterxml/jackson-databind, development): distributed-flow-auditor; Fix #4443: detect `Iterable` as `IterationType`; (reverted) Add `Iterable<T>` as recognized `IterationType` instance (along with `Iterable`, `Stream`)
- X036 (multi-swe-bench, fasterxml/jackson-databind, development): logic-integrity-auditor; Fix #4481: allow override of `READ_UNKNOWN_ENUM_VALUES_AS_NULL`; Unable to override `DeserializationFeature.READ_UNKNOWN_ENUM_VALUES_AS_NULL` with `JsonFormat.Feature.READ_UNKNOWN_ENUM_VALUES_AS_NULL`
- X037 (multi-swe-bench, vuejs/core, verification): temporal-resilience-auditor, distributed-flow-auditor; fix(compiler-sfc): nested css supports atrule and comment; @ queries in scoped nested CSS lack nesting selector
- X038 (multi-swe-bench, vuejs/core, verification): distributed-flow-auditor; feat(compiler-sfc): correct scoped injection for nesting selector; CSS nesting inserts attribute selector at every level
- X039 (multi-swe-bench, vuejs/core, verification): ui-race-auditor, distributed-flow-auditor; fix(reactivity): pass oldValue to computed getter; [3.5.0+] Previous values from computed are always undefined
- X040 (multi-swe-bench, sveltejs/svelte, verification): distributed-flow-auditor; fix: disallow $state/$derived in const tags; `$derived` and `$derived.by` in `{@const}` tags results in obscure error message
- X042 (multi-swe-bench, sveltejs/svelte, verification): ui-race-auditor; fix: correctly handle `novalidate` attribute casing; Form `novalidate` attribute doesn't render when conditional (given a value)
- X043 (multi-swe-bench, apache/dubbo, verification): security-auditor, distributed-flow-auditor; Fix #11767, restore the original parameter pair instead of giving default value when doing URL.parse.; Dubbo service auth failed
- X044 (multi-swe-bench, apache/dubbo, verification): distributed-flow-auditor; Fix PojoUtils support localdatetime,lcaldate,localtime serializable and deserialize; The generalized call does not support the serialization and deserialization of LocalTime, LocalDate & LocalDateTime
- X047 (multi-swe-bench, tokio-rs/tokio, verification): temporal-resilience-auditor, distributed-flow-auditor; macros: make select budget-aware; MPSC queue hangs on repeated polling
- X048 (multi-swe-bench, tokio-rs/tokio, verification): resource-lifecycle-auditor, distributed-flow-auditor; io: add AsyncFd::try_io() and try_io_mut(); Add `AsyncFd::try_io`
- X050 (devign, qemu, verification): security-auditor; Devign dataset target=True
- X051 (devign, FFmpeg, development): security-auditor; Devign dataset target=True
- X054 (devign, qemu, verification): security-auditor; Devign dataset target=True
- X055 (devign, qemu, verification): security-auditor; Devign dataset target=True
- X057 (devign, FFmpeg, development): security-auditor; Devign dataset target=True
- X058 (devign, FFmpeg, development): security-auditor; Devign dataset target=True
- X072 (commitbench, tensorflow_probability, development): cleanup-auditor; sort supported dtypes in host_callback_test.py (#<I>) * sort supported dtypes in host_callback_test.py This fixes issues I ran into with running `pytest -n auto tests/host_callback_test.py` or similar. * remove unused import
