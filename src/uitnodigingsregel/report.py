"""Rendering of the Quarto model analysis report and selection of its input data."""

import os
import subprocess
import tempfile
from pathlib import Path

TRAIN_DATA_ENV = "UITNODIGINGSREGEL_TRAIN_DATA"
TRAIN_LABEL_ENV = "UITNODIGINGSREGEL_TRAIN_LABEL"
REPORT_SOURCE = "Model_analysis.qmd"
REPORT_OUTPUT = "Model_analysis.html"
REPORT_MODELS_DIR = Path("models/report")
DEMO_LABEL = "de synthetische demo-data"


class ReportError(RuntimeError):
    """The report could not be rendered; the message holds the end of Quarto's output."""


def resolve_report_data(settings: dict) -> tuple[Path, str]:
    """Determine which training data the report describes.

    Order: the file passed by the caller of render_report(), then the user's
    own training file, then the synthetic demo data.

    Args:
        settings: Settings dictionary (from load_settings()).

    Returns:
        Tuple of (path to the training CSV, Dutch description of that data).
    """
    passed_path = os.environ.get(TRAIN_DATA_ENV)
    if passed_path:
        path = Path(passed_path)
        return path, os.environ.get(TRAIN_LABEL_ENV) or f"het bestand {path.name}"

    user_path = Path(settings["user_data_dir_train"])
    if user_path.exists():
        return user_path, f"het bestand {user_path.name} van de instelling"

    return Path(settings["synth_data_dir_train"]), DEMO_LABEL


def render_report(
    quarto_bin: str,
    train_source: str | Path | bytes,
    train_label: str,
    root_dir: Path,
) -> bytes:
    """Render the model analysis report for the given training data.

    Uploaded data is written to a temporary file that is removed after rendering.

    Args:
        quarto_bin: Path to the Quarto executable.
        train_source: Path to the training CSV, or its raw content (from an upload).
        train_label: Dutch description of the data, shown in the report.
        root_dir: Directory containing the report source.

    Returns:
        The rendered report as HTML bytes.

    Raises:
        ReportError: If Quarto fails or produces no HTML file.
    """
    html_path = root_dir / REPORT_OUTPUT
    html_path.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        if isinstance(train_source, bytes):
            train_path = Path(tmp_dir) / "train.csv"
            train_path.write_bytes(train_source)
        else:
            train_path = Path(train_source).resolve()

        result = subprocess.run(
            [quarto_bin, "render", REPORT_SOURCE],
            cwd=root_dir,
            env={**os.environ, TRAIN_DATA_ENV: str(train_path), TRAIN_LABEL_ENV: train_label},
            capture_output=True,
            text=True,
        )

    if result.returncode != 0:
        raise ReportError(result.stderr[-500:])
    if not html_path.exists():
        raise ReportError("Quarto meldt geen fout, maar het rapportbestand is niet aangemaakt.")
    return html_path.read_bytes()
