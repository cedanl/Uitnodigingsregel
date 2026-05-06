"""CLI entrypoint: launches the Uitnodigingsregel Streamlit app."""

import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--open"]
    auto_open = len(args) < len(sys.argv[1:])

    if auto_open:

        def _open() -> None:
            time.sleep(2)
            webbrowser.open("http://localhost:8501")

        threading.Thread(target=_open, daemon=True).start()

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
                *args,
            ]
        )
    )
