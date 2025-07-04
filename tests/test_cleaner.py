import os
import sys


# Define get_project_root locally to avoid circular import issues
def get_project_root():
    """Get the root directory of the project."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
            os.path.join(current_dir, "src")
        ):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise FileNotFoundError(
                "Check the project structure. 'data' and 'src' directories not found."
            )
        current_dir = parent_dir


# Set up paths
root = get_project_root()
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
