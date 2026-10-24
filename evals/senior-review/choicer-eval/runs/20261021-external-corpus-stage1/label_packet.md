# External corpus Stage 2 label packet

Only Devign security decisions are gold. Every other status is an adjudication state, not a frozen label.

## security-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 50 |
| gold_negative | 6 |
| gold_positive | 6 |
| proposed_positive_silver | 3 |
| proposed_positive_weak | 1 |
| unknown_below_threshold | 6 |

Proposed or gold positives:

- X001 (swe-bench-verified, django/django, development): proposed_positive_silver; Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- X012 (swe-bench-verified, psf/requests, development): proposed_positive_silver; quote qop options in Digest Auth Based on RFC2617 (http://tools.ietf.org/html/rfc2617), the value of 'qop-options' directive should be quoted with double quotes: ``` qop-options This directive is optional, but is made so only for backward compatibility with RFC 2069 [6]; it SHOULD be used by all imp
- X043 (multi-swe-bench, apache/dubbo, verification): proposed_positive_silver; Fix #11767, restore the original parameter pair instead of giving default value when doing URL.parse.; Dubbo service auth failed
- X045 (multi-swe-bench, apache/dubbo, verification): proposed_positive_weak; Fix ReflectUtils not support generic call with Future; Unable to refer interface with CompletableFuture<T>
- X050 (devign, qemu, verification): gold_positive; Devign dataset target=True
- X051 (devign, FFmpeg, development): gold_positive; Devign dataset target=True
- X054 (devign, qemu, verification): gold_positive; Devign dataset target=True
- X055 (devign, qemu, verification): gold_positive; Devign dataset target=True
- X057 (devign, FFmpeg, development): gold_positive; Devign dataset target=True
- X058 (devign, FFmpeg, development): gold_positive; Devign dataset target=True

## data-integrity-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 24 |
| proposed_positive_silver | 15 |
| unknown | 12 |
| unknown_below_threshold | 21 |

Proposed or gold positives:

- X001 (swe-bench-verified, django/django, development): proposed_positive_silver; Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- X002 (swe-bench-verified, pytest-dev/pytest, verification): proposed_positive_silver; Pytest 6: Dynamically adding xfail marker in test no longer ignores failure <!-- Thanks for submitting an issue! Here's a quick checklist for what to provide: --> ## Description With pytest 5.x, we can dynamically add an xfail to a test `request` object using `request.node.add_marker(mark)` (see exa
- X003 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Inconsistent behaviour with type alias documentation (not overwriting all the default messages, just some) **Describe the bug** Hello, I have 3 muiltiline docstrings for type aliases (using the next-line `"""` documentation syntax). For 1 one them the docstring is correctly shown in the rendered HTM
- X004 (swe-bench-verified, django/django, development): proposed_positive_silver; Optimize .delete() to use only required fields. Description Hi! We're in the process of upgrading our Django 1.11 installation from Python 2.7 to Python 3.6, however are hitting an unexpected UnicodeDecodeError during a .delete() run by our daily data purging management command. STR: Have an existin
- X005 (swe-bench-verified, django/django, development): proposed_positive_silver; Use Python stdlib html.escape() to in django.utils.html.escape() Description The function django.utils.html.escape() partially duplicates the Python stdlib function html.escape(). We can replace this duplication with wider community developed version. html.escape() has been available since Python 3.
- X006 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; [Bug]: Confusing deprecation warning when empty data passed to axis with category units ### Bug summary I'm seeing a `MatplotlibDeprecationWarning` when using calling axes methods on empty data structures for axes that are using string unit converters. I think this is either a false alarm or a non-a
- X007 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; AnnotationBbox gid not passed to renderer Hi, I'm creating matplotlib figures that contain images using AnnotationBbox (following the examples here https://matplotlib.org/stable/gallery/text_labels_and_annotations/demo_annotation_box.html) and my aim is to set the artist gid associated with each ima
- X008 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Message.locations duplicate unnecessary ### Describe the bug When running `make clean; make gettext` there are times the list of locations is duplicated unnecessarily, example: ``` #: ../../manual/render/shader_nodes/vector/vector_rotate.rst:38 #: ../../manual/modeling/hair.rst:0 #: ../../manual/mod
- X010 (swe-bench-verified, astropy/astropy, development): proposed_positive_silver; A direct approach to ITRS to Observed transformations that stays within the ITRS. <!-- This comments are hidden when you submit the issue, so you do not need to remove them! --> <!-- Please be sure to check out our contributing guidelines, https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md
- X014 (swe-bench-verified, pydata/xarray, verification): proposed_positive_silver; DataArray.integrate has a 'dim' arg, but Dataset.integrate has a 'coord' arg This is just a minor gripe but I think it should be fixed. The API syntax is inconsistent: ```python ds.differentiate(coord='x') da.differentiate(coord='x') ds.integrate(coord='x') da.integrate(dim='x') # why dim?? ``` It s
- X019 (swe-bench-verified, pytest-dev/pytest, verification): proposed_positive_silver; caplog.get_records and caplog.clear conflict # Description `caplog.get_records()` gets decoupled from actual caplog records when `caplog.clear()` is called. As a result, after `caplog.clear()` is called, `caplog.get_records()` is frozen: it does not get cleared, nor does it get new records. During t
- X022 (swe-bench-verified, sympy/sympy, development): proposed_positive_silver; Factor with extension=True drops a factor of y-1 I guess this related (or a duplicate of?) #5786 This is from stackoverflow: https://stackoverflow.com/questions/60682765/python-sympy-factoring-polynomial-over-complex-numbers ```julia In [9]: z = expand((x-1)*(y-1)) In [10]: z Out[10]: x⋅y - x - y + 
- X025 (multi-swe-bench, mui/material-ui, development): proposed_positive_silver; [system] Add outlineColor to defaultSxConfig; [system] `sx` field outlineColor doesn't take the theme into account
- X027 (multi-swe-bench, mui/material-ui, development): proposed_positive_silver; [joy-ui][Stepper] Add new `Stepper` components; [joy-ui] Add `Stepper` component
- X044 (multi-swe-bench, apache/dubbo, verification): proposed_positive_silver; Fix PojoUtils support localdatetime,lcaldate,localtime serializable and deserialize; The generalized call does not support the serialization and deserialization of LocalTime, LocalDate & LocalDateTime

## temporal-resilience-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 37 |
| proposed_positive_silver | 5 |
| unknown | 12 |
| unknown_below_threshold | 18 |

Proposed or gold positives:

- X037 (multi-swe-bench, vuejs/core, verification): proposed_positive_silver; fix(compiler-sfc): nested css supports atrule and comment; @ queries in scoped nested CSS lack nesting selector
- X039 (multi-swe-bench, vuejs/core, verification): proposed_positive_silver; fix(reactivity): pass oldValue to computed getter; [3.5.0+] Previous values from computed are always undefined
- X043 (multi-swe-bench, apache/dubbo, verification): proposed_positive_silver; Fix #11767, restore the original parameter pair instead of giving default value when doing URL.parse.; Dubbo service auth failed
- X046 (multi-swe-bench, tokio-rs/tokio, verification): proposed_positive_silver; chore: use [lints] to address unexpected_cfgs lint; Use `[lints.rust.unexpected_cfgs.check-cfg]` instead of hacky check-cfg workaround
- X047 (multi-swe-bench, tokio-rs/tokio, verification): proposed_positive_silver; macros: make select budget-aware; MPSC queue hangs on repeated polling

## resource-lifecycle-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 47 |
| proposed_positive_silver | 2 |
| proposed_positive_weak | 4 |
| unknown | 12 |
| unknown_below_threshold | 7 |

Proposed or gold positives:

- X002 (swe-bench-verified, pytest-dev/pytest, verification): proposed_positive_silver; Pytest 6: Dynamically adding xfail marker in test no longer ignores failure <!-- Thanks for submitting an issue! Here's a quick checklist for what to provide: --> ## Description With pytest 5.x, we can dynamically add an xfail to a test `request` object using `request.node.add_marker(mark)` (see exa
- X048 (multi-swe-bench, tokio-rs/tokio, verification): proposed_positive_silver; io: add AsyncFd::try_io() and try_io_mut(); Add `AsyncFd::try_io`
- X065 (commitbench, trec-kba_streamcorpus-pipeline, verification): proposed_positive_weak; adding a __main__ block for testing the matching regex
- X067 (commitbench, heroku_cli, development): proposed_positive_weak; Merge pull request #<I> from heroku/warning-rework trusted-ips: Aligning the error messaging with Dashboard
- X069 (commitbench, angr_angr, verification): proposed_positive_weak; Lint the code - pylint seems to have trouble supporting type hints.
- X070 (commitbench, backtrader_backtrader, development): proposed_positive_weak; Extra plotting defaults to lineiterator to simplify plotting code Added plotforce to force plotting of an indicator which relies on non-plotted/plottable data/clock sources

## ui-race-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 33 |
| proposed_positive_silver | 13 |
| unknown | 12 |
| unknown_below_threshold | 14 |

Proposed or gold positives:

- X002 (swe-bench-verified, pytest-dev/pytest, verification): proposed_positive_silver; Pytest 6: Dynamically adding xfail marker in test no longer ignores failure <!-- Thanks for submitting an issue! Here's a quick checklist for what to provide: --> ## Description With pytest 5.x, we can dynamically add an xfail to a test `request` object using `request.node.add_marker(mark)` (see exa
- X003 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Inconsistent behaviour with type alias documentation (not overwriting all the default messages, just some) **Describe the bug** Hello, I have 3 muiltiline docstrings for type aliases (using the next-line `"""` documentation syntax). For 1 one them the docstring is correctly shown in the rendered HTM
- X005 (swe-bench-verified, django/django, development): proposed_positive_silver; Use Python stdlib html.escape() to in django.utils.html.escape() Description The function django.utils.html.escape() partially duplicates the Python stdlib function html.escape(). We can replace this duplication with wider community developed version. html.escape() has been available since Python 3.
- X007 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; AnnotationBbox gid not passed to renderer Hi, I'm creating matplotlib figures that contain images using AnnotationBbox (following the examples here https://matplotlib.org/stable/gallery/text_labels_and_annotations/demo_annotation_box.html) and my aim is to set the artist gid associated with each ima
- X008 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Message.locations duplicate unnecessary ### Describe the bug When running `make clean; make gettext` there are times the list of locations is duplicated unnecessarily, example: ``` #: ../../manual/render/shader_nodes/vector/vector_rotate.rst:38 #: ../../manual/modeling/hair.rst:0 #: ../../manual/mod
- X011 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; [Bug]: Datetime axis with usetex is unclear ### Bug summary The spacing for a datetime axis when using `usetex=True` is unclear in matplotlib version 3.4 when comparing it to 3.3. ### Code for reproduction ```python import matplotlib import matplotlib.pyplot as plt import numpy as np import pandas a
- X021 (swe-bench-verified, sympy/sympy, development): proposed_positive_silver; Matrix determinant raises Invalid NaN comparison with particular symbolic entries >>> from sympy import * >>> from sympy.abc import a >>> f = lambda n: det(Matrix([[i + a*j for i in range(n)] for j in range(n)])) >>> f(1) 0 >>> f(2) -a >>> f(3) 2*a*(a + 2) + 2*a*(2*a + 1) - 3*a*(2*a + 2) >>> f(4) 0 
- X025 (multi-swe-bench, mui/material-ui, development): proposed_positive_silver; [system] Add outlineColor to defaultSxConfig; [system] `sx` field outlineColor doesn't take the theme into account
- X027 (multi-swe-bench, mui/material-ui, development): proposed_positive_silver; [joy-ui][Stepper] Add new `Stepper` components; [joy-ui] Add `Stepper` component
- X028 (multi-swe-bench, axios/axios, development): proposed_positive_silver; fix(adapters): improved adapters loading logic to have clear error messages;; Tests No Longer Passing since Upgrading to v1.5.0
- X030 (multi-swe-bench, axios/axios, development): proposed_positive_silver; Fixed handling of array values for AxiosHeaders;; [1.0.0] Set-Cookie header in a response interceptor is not an array anymore
- X039 (multi-swe-bench, vuejs/core, verification): proposed_positive_silver; fix(reactivity): pass oldValue to computed getter; [3.5.0+] Previous values from computed are always undefined
- X042 (multi-swe-bench, sveltejs/svelte, verification): proposed_positive_silver; fix: correctly handle `novalidate` attribute casing; Form `novalidate` attribute doesn't render when conditional (given a value)

## distributed-flow-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 7 |
| proposed_positive_silver | 44 |
| proposed_positive_weak | 3 |
| unknown | 12 |
| unknown_below_threshold | 6 |

Proposed or gold positives:

- X001 (swe-bench-verified, django/django, development): proposed_positive_silver; Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- X002 (swe-bench-verified, pytest-dev/pytest, verification): proposed_positive_silver; Pytest 6: Dynamically adding xfail marker in test no longer ignores failure <!-- Thanks for submitting an issue! Here's a quick checklist for what to provide: --> ## Description With pytest 5.x, we can dynamically add an xfail to a test `request` object using `request.node.add_marker(mark)` (see exa
- X003 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Inconsistent behaviour with type alias documentation (not overwriting all the default messages, just some) **Describe the bug** Hello, I have 3 muiltiline docstrings for type aliases (using the next-line `"""` documentation syntax). For 1 one them the docstring is correctly shown in the rendered HTM
- X004 (swe-bench-verified, django/django, development): proposed_positive_silver; Optimize .delete() to use only required fields. Description Hi! We're in the process of upgrading our Django 1.11 installation from Python 2.7 to Python 3.6, however are hitting an unexpected UnicodeDecodeError during a .delete() run by our daily data purging management command. STR: Have an existin
- X005 (swe-bench-verified, django/django, development): proposed_positive_silver; Use Python stdlib html.escape() to in django.utils.html.escape() Description The function django.utils.html.escape() partially duplicates the Python stdlib function html.escape(). We can replace this duplication with wider community developed version. html.escape() has been available since Python 3.
- X006 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; [Bug]: Confusing deprecation warning when empty data passed to axis with category units ### Bug summary I'm seeing a `MatplotlibDeprecationWarning` when using calling axes methods on empty data structures for axes that are using string unit converters. I think this is either a false alarm or a non-a
- X007 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; AnnotationBbox gid not passed to renderer Hi, I'm creating matplotlib figures that contain images using AnnotationBbox (following the examples here https://matplotlib.org/stable/gallery/text_labels_and_annotations/demo_annotation_box.html) and my aim is to set the artist gid associated with each ima
- X008 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Message.locations duplicate unnecessary ### Describe the bug When running `make clean; make gettext` there are times the list of locations is duplicated unnecessarily, example: ``` #: ../../manual/render/shader_nodes/vector/vector_rotate.rst:38 #: ../../manual/modeling/hair.rst:0 #: ../../manual/mod
- X009 (swe-bench-verified, astropy/astropy, development): proposed_positive_silver; TimeSeries: misleading exception when required column check fails. <!-- This comments are hidden when you submit the issue, so you do not need to remove them! --> <!-- Please be sure to check out our contributing guidelines, https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md . Please be su
- X010 (swe-bench-verified, astropy/astropy, development): proposed_positive_silver; A direct approach to ITRS to Observed transformations that stays within the ITRS. <!-- This comments are hidden when you submit the issue, so you do not need to remove them! --> <!-- Please be sure to check out our contributing guidelines, https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md
- X011 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; [Bug]: Datetime axis with usetex is unclear ### Bug summary The spacing for a datetime axis when using `usetex=True` is unclear in matplotlib version 3.4 when comparing it to 3.3. ### Code for reproduction ```python import matplotlib import matplotlib.pyplot as plt import numpy as np import pandas a
- X012 (swe-bench-verified, psf/requests, development): proposed_positive_silver; quote qop options in Digest Auth Based on RFC2617 (http://tools.ietf.org/html/rfc2617), the value of 'qop-options' directive should be quoted with double quotes: ``` qop-options This directive is optional, but is made so only for backward compatibility with RFC 2069 [6]; it SHOULD be used by all imp
- X013 (swe-bench-verified, psf/requests, development): proposed_positive_silver; Getting http://.example.com raises UnicodeError Attempting to get e.g. `http://.example.com` results in a `UnicodeError`. It seems like the intention so far has been to raise `InvalidUrl` instead (see e.g. [this line](https://github.com/psf/requests/blob/ca6f9af5dba09591007b15a7368bc0f006b7cc50/requ
- X014 (swe-bench-verified, pydata/xarray, verification): proposed_positive_silver; DataArray.integrate has a 'dim' arg, but Dataset.integrate has a 'coord' arg This is just a minor gripe but I think it should be fixed. The API syntax is inconsistent: ```python ds.differentiate(coord='x') da.differentiate(coord='x') ds.integrate(coord='x') da.integrate(dim='x') # why dim?? ``` It s
- X015 (swe-bench-verified, pydata/xarray, verification): proposed_positive_silver; Naming a dimension "method" throws error when calling ".loc" #### Code Sample, a copy-pastable example if possible ```python import numpy as np from xarray import DataArray empty = np.zeros((2,2)) D1 = DataArray(empty, dims=['dim1', 'dim2'], coords={'dim1':['x', 'y'], 'dim2':['a', 'b']}) D2 = DataAr
- X016 (swe-bench-verified, pydata/xarray, verification): proposed_positive_silver; `polyval` with timedelta64 coordinates produces wrong results ### What happened? I'm not sure if this is a bug or an expected breaking change, but I'm not able to reproduce the results generated by `polyval` using a timedelta64 coordinate. The results are correct in `xarray=2022.3.0`, whereas they a
- X017 (swe-bench-verified, pylint-dev/pylint, verification): proposed_positive_silver; `--recursive=y` ignores `ignore-paths` ### Bug description When running recursively, it seems `ignore-paths` in my settings in pyproject.toml is completely ignored ### Configuration ```ini [tool.pylint.MASTER] ignore-paths = [ # Auto generated "^src/gen/.*$", ] ``` ### Command used ```shell pylint -
- X018 (swe-bench-verified, pylint-dev/pylint, verification): proposed_positive_silver; bad-names-rgxs mangles regular expressions with commas ### Bug description Since pylint splits on commas in this option, instead of taking a list of strings, if there are any commas in the regular expression, the result is mangled before being parsed. The config below demonstrates this clearly by ca
- X019 (swe-bench-verified, pytest-dev/pytest, verification): proposed_positive_silver; caplog.get_records and caplog.clear conflict # Description `caplog.get_records()` gets decoupled from actual caplog records when `caplog.clear()` is called. As a result, after `caplog.clear()` is called, `caplog.get_records()` is frozen: it does not get cleared, nor does it get new records. During t
- X020 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Use of literalinclude prepend results in incorrect indent formatting for code eamples ### Describe the bug Cannot determine a mechanism to use literalinclude directive with `prepend` or `append` to match code example indentation, as leading whitespace is removed. ### How to Reproduce Example of incl
- X022 (swe-bench-verified, sympy/sympy, development): proposed_positive_silver; Factor with extension=True drops a factor of y-1 I guess this related (or a duplicate of?) #5786 This is from stackoverflow: https://stackoverflow.com/questions/60682765/python-sympy-factoring-polynomial-over-complex-numbers ```julia In [9]: z = expand((x-1)*(y-1)) In [10]: z Out[10]: x⋅y - x - y + 
- X023 (swe-bench-verified, sympy/sympy, development): proposed_positive_silver; `PolyElement.as_expr()` not accepting symbols The method `PolyElement.as_expr()` https://github.com/sympy/sympy/blob/193e3825645d93c73e31cdceb6d742cc6919624d/sympy/polys/rings.py#L618-L624 is supposed to let you set the symbols you want to use, but, as it stands, either you pass the wrong number of 
- X025 (multi-swe-bench, mui/material-ui, development): proposed_positive_silver; [system] Add outlineColor to defaultSxConfig; [system] `sx` field outlineColor doesn't take the theme into account
- X026 (multi-swe-bench, mui/material-ui, development): proposed_positive_silver; [material-ui][Rating] Fix the hover highlighting for spaced icons; Can't get correct position after changing spacing of icons in <Rating /> component in v5.
- X027 (multi-swe-bench, mui/material-ui, development): proposed_positive_silver; [joy-ui][Stepper] Add new `Stepper` components; [joy-ui] Add `Stepper` component
- X028 (multi-swe-bench, axios/axios, development): proposed_positive_silver; fix(adapters): improved adapters loading logic to have clear error messages;; Tests No Longer Passing since Upgrading to v1.5.0
- X029 (multi-swe-bench, axios/axios, development): proposed_positive_silver; fix(utils): make isFormData detection logic stricter to avoid unnecessary calling of the `toString` method on the target;; Uploading large files > 512 MB fails
- X030 (multi-swe-bench, axios/axios, development): proposed_positive_silver; Fixed handling of array values for AxiosHeaders;; [1.0.0] Set-Cookie header in a response interceptor is not an array anymore
- X031 (multi-swe-bench, grpc/grpc-go, development): proposed_positive_silver; rls: Manually implement equality of key builder maps.; rls: Do not use `cmp` package in non-test code
- X032 (multi-swe-bench, grpc/grpc-go, development): proposed_positive_silver; balancer/base: consider an empty address list an error; dns + round_robin not updating address list in v1.26
- X033 (multi-swe-bench, grpc/grpc-go, development): proposed_positive_silver; grpclb: support explicit fallback signal; Support explicit fallback in grpclb
- X034 (multi-swe-bench, fasterxml/jackson-databind, development): proposed_positive_silver; Prioritize constructor parameter over field if both are annotated with `@JsonAnySetter`, to fix #4634; `@JsonAnySetter` not working when annotated on both constructor parameter & field
- X035 (multi-swe-bench, fasterxml/jackson-databind, development): proposed_positive_silver; Fix #4443: detect `Iterable` as `IterationType`; (reverted) Add `Iterable<T>` as recognized `IterationType` instance (along with `Iterable`, `Stream`)
- X037 (multi-swe-bench, vuejs/core, verification): proposed_positive_silver; fix(compiler-sfc): nested css supports atrule and comment; @ queries in scoped nested CSS lack nesting selector
- X038 (multi-swe-bench, vuejs/core, verification): proposed_positive_silver; feat(compiler-sfc): correct scoped injection for nesting selector; CSS nesting inserts attribute selector at every level
- X039 (multi-swe-bench, vuejs/core, verification): proposed_positive_silver; fix(reactivity): pass oldValue to computed getter; [3.5.0+] Previous values from computed are always undefined
- X040 (multi-swe-bench, sveltejs/svelte, verification): proposed_positive_silver; fix: disallow $state/$derived in const tags; `$derived` and `$derived.by` in `{@const}` tags results in obscure error message
- X041 (multi-swe-bench, sveltejs/svelte, verification): proposed_positive_silver; fix: add check for is attribute; Different behavior for custom elements that extends builtin element.
- X043 (multi-swe-bench, apache/dubbo, verification): proposed_positive_silver; Fix #11767, restore the original parameter pair instead of giving default value when doing URL.parse.; Dubbo service auth failed
- X044 (multi-swe-bench, apache/dubbo, verification): proposed_positive_silver; Fix PojoUtils support localdatetime,lcaldate,localtime serializable and deserialize; The generalized call does not support the serialization and deserialization of LocalTime, LocalDate & LocalDateTime
- X046 (multi-swe-bench, tokio-rs/tokio, verification): proposed_positive_silver; chore: use [lints] to address unexpected_cfgs lint; Use `[lints.rust.unexpected_cfgs.check-cfg]` instead of hacky check-cfg workaround
- X047 (multi-swe-bench, tokio-rs/tokio, verification): proposed_positive_silver; macros: make select budget-aware; MPSC queue hangs on repeated polling
- X048 (multi-swe-bench, tokio-rs/tokio, verification): proposed_positive_silver; io: add AsyncFd::try_io() and try_io_mut(); Add `AsyncFd::try_io`
- X061 (commitbench, RedHatInsights_insights-core, verification): proposed_positive_silver; no longer needlessly processing api output
- X062 (commitbench, workhorsy_py-cpuinfo, development): proposed_positive_weak; Updated the asm code runner to free memory when done with it.
- X063 (commitbench, structured-log_structured-log, development): proposed_positive_weak; Added the serilog.event() function.
- X064 (commitbench, terraform-providers_terraform-provider-openstack, verification): proposed_positive_weak; Use env var OS_POOL_NAME as default for pool attribute To have the same behaviour for openstack_networking_floatingip_v2 and openstack_compute_foatingip_v2.

## logic-integrity-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 28 |
| proposed_positive_silver | 17 |
| unknown | 12 |
| unknown_below_threshold | 15 |

Proposed or gold positives:

- X001 (swe-bench-verified, django/django, development): proposed_positive_silver; Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- X003 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Inconsistent behaviour with type alias documentation (not overwriting all the default messages, just some) **Describe the bug** Hello, I have 3 muiltiline docstrings for type aliases (using the next-line `"""` documentation syntax). For 1 one them the docstring is correctly shown in the rendered HTM
- X004 (swe-bench-verified, django/django, development): proposed_positive_silver; Optimize .delete() to use only required fields. Description Hi! We're in the process of upgrading our Django 1.11 installation from Python 2.7 to Python 3.6, however are hitting an unexpected UnicodeDecodeError during a .delete() run by our daily data purging management command. STR: Have an existin
- X006 (swe-bench-verified, matplotlib/matplotlib, development): proposed_positive_silver; [Bug]: Confusing deprecation warning when empty data passed to axis with category units ### Bug summary I'm seeing a `MatplotlibDeprecationWarning` when using calling axes methods on empty data structures for axes that are using string unit converters. I think this is either a false alarm or a non-a
- X009 (swe-bench-verified, astropy/astropy, development): proposed_positive_silver; TimeSeries: misleading exception when required column check fails. <!-- This comments are hidden when you submit the issue, so you do not need to remove them! --> <!-- Please be sure to check out our contributing guidelines, https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md . Please be su
- X013 (swe-bench-verified, psf/requests, development): proposed_positive_silver; Getting http://.example.com raises UnicodeError Attempting to get e.g. `http://.example.com` results in a `UnicodeError`. It seems like the intention so far has been to raise `InvalidUrl` instead (see e.g. [this line](https://github.com/psf/requests/blob/ca6f9af5dba09591007b15a7368bc0f006b7cc50/requ
- X015 (swe-bench-verified, pydata/xarray, verification): proposed_positive_silver; Naming a dimension "method" throws error when calling ".loc" #### Code Sample, a copy-pastable example if possible ```python import numpy as np from xarray import DataArray empty = np.zeros((2,2)) D1 = DataArray(empty, dims=['dim1', 'dim2'], coords={'dim1':['x', 'y'], 'dim2':['a', 'b']}) D2 = DataAr
- X016 (swe-bench-verified, pydata/xarray, verification): proposed_positive_silver; `polyval` with timedelta64 coordinates produces wrong results ### What happened? I'm not sure if this is a bug or an expected breaking change, but I'm not able to reproduce the results generated by `polyval` using a timedelta64 coordinate. The results are correct in `xarray=2022.3.0`, whereas they a
- X017 (swe-bench-verified, pylint-dev/pylint, verification): proposed_positive_silver; `--recursive=y` ignores `ignore-paths` ### Bug description When running recursively, it seems `ignore-paths` in my settings in pyproject.toml is completely ignored ### Configuration ```ini [tool.pylint.MASTER] ignore-paths = [ # Auto generated "^src/gen/.*$", ] ``` ### Command used ```shell pylint -
- X018 (swe-bench-verified, pylint-dev/pylint, verification): proposed_positive_silver; bad-names-rgxs mangles regular expressions with commas ### Bug description Since pylint splits on commas in this option, instead of taking a list of strings, if there are any commas in the regular expression, the result is mangled before being parsed. The config below demonstrates this clearly by ca
- X020 (swe-bench-verified, sphinx-doc/sphinx, verification): proposed_positive_silver; Use of literalinclude prepend results in incorrect indent formatting for code eamples ### Describe the bug Cannot determine a mechanism to use literalinclude directive with `prepend` or `append` to match code example indentation, as leading whitespace is removed. ### How to Reproduce Example of incl
- X021 (swe-bench-verified, sympy/sympy, development): proposed_positive_silver; Matrix determinant raises Invalid NaN comparison with particular symbolic entries >>> from sympy import * >>> from sympy.abc import a >>> f = lambda n: det(Matrix([[i + a*j for i in range(n)] for j in range(n)])) >>> f(1) 0 >>> f(2) -a >>> f(3) 2*a*(a + 2) + 2*a*(2*a + 1) - 3*a*(2*a + 2) >>> f(4) 0 
- X023 (swe-bench-verified, sympy/sympy, development): proposed_positive_silver; `PolyElement.as_expr()` not accepting symbols The method `PolyElement.as_expr()` https://github.com/sympy/sympy/blob/193e3825645d93c73e31cdceb6d742cc6919624d/sympy/polys/rings.py#L618-L624 is supposed to let you set the symbols you want to use, but, as it stands, either you pass the wrong number of 
- X024 (swe-bench-verified, astropy/astropy, development): proposed_positive_silver; Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels Consider the following model: ```python from astropy.modeling import models as m from astropy.modeling.separable import separability_matrix cm = m.Linear1D(10) & m.Linear1D(5) ``` It's separability mat
- X030 (multi-swe-bench, axios/axios, development): proposed_positive_silver; Fixed handling of array values for AxiosHeaders;; [1.0.0] Set-Cookie header in a response interceptor is not an array anymore
- X036 (multi-swe-bench, fasterxml/jackson-databind, development): proposed_positive_silver; Fix #4481: allow override of `READ_UNKNOWN_ENUM_VALUES_AS_NULL`; Unable to override `DeserializationFeature.READ_UNKNOWN_ENUM_VALUES_AS_NULL` with `JsonFormat.Feature.READ_UNKNOWN_ENUM_VALUES_AS_NULL`
- X048 (multi-swe-bench, tokio-rs/tokio, verification): proposed_positive_silver; io: add AsyncFd::try_io() and try_io_mut(); Add `AsyncFd::try_io`

## cleanup-auditor

| Status | Count |
| --- | ---: |
| candidate_negative_from_absence | 50 |
| proposed_positive_silver | 1 |
| proposed_positive_weak | 3 |
| unknown | 12 |
| unknown_below_threshold | 6 |

Proposed or gold positives:

- X066 (commitbench, biocommons_hgvs, development): proposed_positive_weak; removed long-deprecated seq method
- X068 (commitbench, vibornoff_webcrypto-shim, verification): proposed_positive_weak; Fix for Safari <I>.x (technical preview) Safari <I> has deprecated webkitSubtle and added subtle
- X071 (commitbench, STRML_react-router-component, development): proposed_positive_weak; Remove replaceState (deprecated, all attrs are provided)
- X072 (commitbench, tensorflow_probability, development): proposed_positive_silver; sort supported dtypes in host_callback_test.py (#<I>) * sort supported dtypes in host_callback_test.py This fixes issues I ran into with running `pytest -n auto tests/host_callback_test.py` or similar. * remove unused import

