from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from renderer import render_pdf, test_pdf_path
from report_data import get_report_data


if __name__ == "__main__":
    path = render_pdf(get_report_data(), test_pdf_path())
    print(path)
