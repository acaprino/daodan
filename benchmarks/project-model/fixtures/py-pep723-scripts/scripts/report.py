# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas>=2.2"]
#
# [tool.uv]
# exclude-newer = "2024-10-01T00:00:00Z"
# ///
import pandas as pd

print(pd.DataFrame({"a": [1]}).to_string())
