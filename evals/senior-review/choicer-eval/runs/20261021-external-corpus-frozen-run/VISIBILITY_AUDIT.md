# External corpus development visibility audit

Development cases only. Verification remains locked.

| Lens | Visible signal | Weak signal | External only |
| --- | ---: | ---: | ---: |
| security-auditor | 0 | 1 | 3 |
| data-integrity-auditor | 0 | 3 | 5 |
| temporal-resilience-auditor | 0 | 1 | 0 |
| resource-lifecycle-auditor | 0 | 0 | 1 |
| ui-race-auditor | 0 | 2 | 1 |
| distributed-flow-auditor | 1 | 1 | 4 |
| logic-integrity-auditor | 1 | 1 | 3 |
| cleanup-auditor | 0 | 0 | 4 |

## External-only positives

- F01 (X103, WellCommerce_WishlistBundle) cleanup-auditor: Removed unused use statements (cherry picked from commit fe<I>e8e<I>c0ee<I>de<I>a5cb4deb<I>f<I>c<I>)
- F02 (X112, WellCommerce_WishlistBundle) cleanup-auditor: Removed unused use statement in ProductDatagrid
- F03 (X117, openlayers_openlayers) cleanup-auditor: Remove unused 'opaque' property from ol/source/Stamen options And set the `layer` property as mandatory.
- F04 (X072, tensorflow_probability) cleanup-auditor: sort supported dtypes in host_callback_test.py (#<I>) * sort supported dtypes in host_callback_test.py This fixes issues I ran into with running `pytest -n auto tests/host_callback_test.py` or similar. * remove unused import
- F06 (X051, FFmpeg) security-auditor: Devign dataset target=True
- F08 (X057, FFmpeg) security-auditor: Devign dataset target=True
- F09 (X058, FFmpeg) security-auditor: Devign dataset target=True
- F11 (X036, fasterxml/jackson-databind) logic-integrity-auditor: Fix #4481: allow override of `READ_UNKNOWN_ENUM_VALUES_AS_NULL`; Unable to override `DeserializationFeature.READ_UNKNOWN_ENUM_VALUES_AS_NULL` with `JsonFormat.Feature.READ_UNKNOWN_ENUM_VALUES_AS_NULL`
- F15 (X027, mui/material-ui) data-integrity-auditor: [joy-ui][Stepper] Add new `Stepper` components; [joy-ui] Add `Stepper` component
- F17 (X009, astropy/astropy) distributed-flow-auditor: TimeSeries: misleading exception when required column check fails. <!-- This comments are hidden when you submit the issue, so you do not need to remove them! --> <!-- Please be sure to check out our contributing guidelines, https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md . Please be su
- F18 (X024, astropy/astropy) logic-integrity-auditor: Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels Consider the following model: ```python from astropy.modeling import models as m from astropy.modeling.separable import separability_matrix cm = m.Linear1D(10) & m.Linear1D(5) ``` It's separability mat
- F19 (X079, astropy/astropy) data-integrity-auditor: Inconsistency in double single-quote ('') management in FITS Card ### Description The management of single-quotes in FITS cards seem correct, except *sometimes* when dealing with null strings, i.e. double single quotes (`''`), which sometimes are transformed into single single quotes (`'`). E.g.: ``
- F20 (X001, django/django) data-integrity-auditor: Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- F20 (X001, django/django) distributed-flow-auditor: Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- F20 (X001, django/django) logic-integrity-auditor: Make URLValidator reject invalid characters in the username and password Description (last modified by Tim Bell) Since #20003, core.validators.URLValidator accepts URLs with usernames and passwords. RFC 1738 section 3.1 requires "Within the user and password field, any ":", "@", or "/" must be encod
- F21 (X005, django/django) data-integrity-auditor: Use Python stdlib html.escape() to in django.utils.html.escape() Description The function django.utils.html.escape() partially duplicates the Python stdlib function html.escape(). We can replace this duplication with wider community developed version. html.escape() has been available since Python 3.
- F22 (X074, django/django) data-integrity-auditor: HashedFilesMixin's post_process() yields multiple times for the same file Description As part of fixing #24452, the implementation of HashedFilesMixin (used by both ManifestStaticFilesStorage and CachedStaticFilesStorage) was changed such that it performs several passes against the found files, ther
- F23 (X011, matplotlib/matplotlib) ui-race-auditor: [Bug]: Datetime axis with usetex is unclear ### Bug summary The spacing for a datetime axis when using `usetex=True` is unclear in matplotlib version 3.4 when comparing it to 3.3. ### Code for reproduction ```python import matplotlib import matplotlib.pyplot as plt import numpy as np import pandas a
- F23 (X011, matplotlib/matplotlib) distributed-flow-auditor: [Bug]: Datetime axis with usetex is unclear ### Bug summary The spacing for a datetime axis when using `usetex=True` is unclear in matplotlib version 3.4 when comparing it to 3.3. ### Code for reproduction ```python import matplotlib import matplotlib.pyplot as plt import numpy as np import pandas a
- F25 (X080, psf/requests) resource-lifecycle-auditor: Unicode method names cause UnicodeDecodeError for some requests in Python 2.7.2 The following example works fine: ``` files = {u'file': open(u'/usr/bin/diff', u'rb')} response = requests.request(method='POST', url=u'http://httpbin.org/post', files=files) ``` But the following example (using `method=
- F27 (X022, sympy/sympy) distributed-flow-auditor: Factor with extension=True drops a factor of y-1 I guess this related (or a duplicate of?) #5786 This is from stackoverflow: https://stackoverflow.com/questions/60682765/python-sympy-factoring-polynomial-over-complex-numbers ```julia In [9]: z = expand((x-1)*(y-1)) In [10]: z Out[10]: x⋅y - x - y + 
