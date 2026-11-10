"""Tests for report data selection and rendering."""

import sys
from pathlib import Path

import pytest

from uitnodigingsregel.report import (
    DEMO_LABEL,
    REPORT_OUTPUT,
    TRAIN_DATA_ENV,
    TRAIN_LABEL_ENV,
    ReportError,
    render_report,
    resolve_report_data,
)


def _settings(tmp_path: Path) -> dict:
    return {
        "user_data_dir_train": str(tmp_path / "user" / "train.csv"),
        "synth_data_dir_train": str(tmp_path / "demo" / "synth.csv"),
    }


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TRAIN_DATA_ENV, raising=False)
    monkeypatch.delenv(TRAIN_LABEL_ENV, raising=False)


def test_resolve_falls_back_to_demo_data(tmp_path: Path) -> None:
    path, label = resolve_report_data(_settings(tmp_path))
    assert path == tmp_path / "demo" / "synth.csv"
    assert label == DEMO_LABEL


def test_resolve_prefers_user_file_over_demo(tmp_path: Path) -> None:
    user_file = tmp_path / "user" / "train.csv"
    user_file.parent.mkdir()
    user_file.write_text("x", encoding="utf-8")
    path, label = resolve_report_data(_settings(tmp_path))
    assert path == user_file
    assert "train.csv" in label


def test_resolve_prefers_passed_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    user_file = tmp_path / "user" / "train.csv"
    user_file.parent.mkdir()
    user_file.write_text("x", encoding="utf-8")
    monkeypatch.setenv(TRAIN_DATA_ENV, str(tmp_path / "upload.csv"))
    monkeypatch.setenv(TRAIN_LABEL_ENV, "het bestand cohort2025.csv")
    path, label = resolve_report_data(_settings(tmp_path))
    assert path == tmp_path / "upload.csv"
    assert label == "het bestand cohort2025.csv"


def _write_fake_quarto(tmp_path: Path, body: str) -> str:
    """Create an executable that stands in for Quarto and runs the given Python body."""
    script = tmp_path / "fake_quarto.py"
    script.write_text(body, encoding="utf-8")
    if sys.platform == "win32":
        launcher = tmp_path / "fake_quarto.cmd"
        launcher.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
    else:
        launcher = tmp_path / "fake_quarto"
        launcher.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8"
        )
        launcher.chmod(0o755)
    return str(launcher)


def test_render_passes_uploaded_data_and_removes_it(tmp_path: Path) -> None:
    quarto = _write_fake_quarto(
        tmp_path,
        "import os, pathlib\n"
        f"data = pathlib.Path(os.environ['{TRAIN_DATA_ENV}'])\n"
        f"label = os.environ['{TRAIN_LABEL_ENV}']\n"
        f"pathlib.Path('{REPORT_OUTPUT}').write_text(\n"
        "    f'{data}|{data.read_text()}|{label}', encoding='utf-8')\n",
    )
    html = render_report(quarto, b"inhoud", "het bestand a.csv", tmp_path).decode("utf-8")
    data_path, content, label = html.split("|")
    assert content == "inhoud"
    assert label == "het bestand a.csv"
    assert not Path(data_path).exists()


def test_render_does_not_return_stale_report(tmp_path: Path) -> None:
    (tmp_path / REPORT_OUTPUT).write_text("oud rapport", encoding="utf-8")
    quarto = _write_fake_quarto(tmp_path, "")
    with pytest.raises(ReportError, match="niet aangemaakt"):
        render_report(quarto, b"inhoud", "label", tmp_path)


def test_render_reports_quarto_failure(tmp_path: Path) -> None:
    quarto = _write_fake_quarto(tmp_path, "import sys\nsys.exit('kernel niet gevonden')\n")
    with pytest.raises(ReportError, match="kernel niet gevonden"):
        render_report(quarto, b"inhoud", "label", tmp_path)
