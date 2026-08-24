import sys
import pytest

sys.exit(pytest.main(["dpo_system/tests/test_csf_ingest.py", "dpo_system/tests/test_ooma_dialer.py"]))
