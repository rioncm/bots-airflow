"""
Local legacy-like X12 recorddefs source used by docs and tests.

This keeps the extraction utility examples self-contained inside the standalone
repo while still simulating a larger shared segment catalog.
"""

from bots_airflow.grammars.x12.segments_004010_ls_846 import recorddefs as _recorddefs_846
from bots_airflow.grammars.x12.segments_004010_ls_850 import recorddefs as _recorddefs_850


recorddefs = dict(_recorddefs_846)
recorddefs.update(_recorddefs_850)
