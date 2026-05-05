"""CLI entrypoint: launches the Uitnodigingsregel Streamlit app."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    app_file = Path(__file__).parent / "app" / "main.py"
    sys.exit(
        subprocess.call(
            [
                "streamlit",
                "run",
                str(app_file),
                "--server.headless=true",
                "--browser.gatherUsageStats=false",
                "--server.maxUploadSize=1500",
                *sys.argv[1:],
            ]
        )
    )
