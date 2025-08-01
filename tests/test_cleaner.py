import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if root not in sys.path:
    sys.path.insert(0, root)

# Now we can import modules
from src.preprocess.cleaner import merge_isolated_letters


def test_merge_isolated_letters():
    assert merge_isolated_letters("B Ộ PHÁP T H U Ậ T") == "BỘ PHÁP THUẬT"
    assert merge_isolated_letters("Hehe\n\n\nHaha") == "Hehe\nHaha"
    assert (
        merge_isolated_letters("\nĐiều a khoản b bộ luật c\n")
        == "Điều a khoản b bộ luật c"
    )
