"""Tests and demo script for the BrickPlotter class."""
from __future__ import annotations

import base64
import warnings
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Safe default for headless test environments
import matplotlib.pyplot as plt
import numpy as np
import pytest
from PIL import Image
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

try:
    from functions.src.BrickPlotter import BrickPlotter
except ModuleNotFoundError:  # pragma: no cover - fallback when tests run from repo root
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from functions.src.BrickPlotter import BrickPlotter

MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "fitted_on_Pr"
    / "model_[3]_stm+flex+cumul+rbs.dmp"
)
TEST_DATA_DIR = Path(__file__).resolve().parent
TXT_SEQUENCE_PATH = TEST_DATA_DIR / "test_sequence.txt"
FASTA_SEQUENCE_PATH = TEST_DATA_DIR / "test_sequence.fasta"

TXT_SEQUENCE = TXT_SEQUENCE_PATH.read_text().strip()
FASTA_SEQUENCE = ''.join(line.strip() for line in FASTA_SEQUENCE_PATH.read_text().splitlines() if not line.startswith('>'))

pytestmark = [
    pytest.mark.filterwarnings("ignore::sklearn.exceptions.InconsistentVersionWarning"),
]

if not MODEL_PATH.exists():  # pragma: no cover - guard for incomplete checkouts
    pytestmark.append(pytest.mark.skip(reason=f"Model file missing: {MODEL_PATH}"))


def _decode_image(image_b64: str) -> np.ndarray:
    """Decode a base64 PNG image into a NumPy array."""
    raw = base64.b64decode(image_b64)
    with Image.open(BytesIO(raw)) as img:
        return np.array(img.convert("RGBA"))


@pytest.fixture(scope="module")
def brickplotter(tmp_path_factory: pytest.TempPathFactory) -> BrickPlotter:
    output_dir = tmp_path_factory.mktemp("brickplots")
    return BrickPlotter(
        model=str(MODEL_PATH),
        output_folder=str(output_dir),
        is_plus_one=True,
        is_rc=False,
    )


def test_brickplot_produces_image_and_matrix(brickplotter: BrickPlotter) -> None:
    result = brickplotter.get_brickplot(TXT_SEQUENCE)

    assert result["sequence"] == TXT_SEQUENCE
    assert result["sequence_length"] == len(TXT_SEQUENCE)

    image = _decode_image(result["image_base64"])
    assert image.size > 0

    matrix = np.array(result["matrix"])
    assert matrix.ndim == 2
    assert matrix.shape[0] > 0 and matrix.shape[1] > 0




def test_brickplot_accepts_fasta_file(brickplotter: BrickPlotter) -> None:
    result = brickplotter.get_brickplot(str(FASTA_SEQUENCE_PATH))
    assert result["sequence"] == FASTA_SEQUENCE
    assert result["sequence_length"] == len(FASTA_SEQUENCE)

def test_brickplot_statistics_present(brickplotter: BrickPlotter) -> None:
    result = brickplotter.get_brickplot(TXT_SEQUENCE)
    stats = result.get("statistics", {})
    expected_keys = {"min_energy", "max_energy", "mean_energy", "best_position"}
    assert expected_keys.issubset(stats.keys())


def _enable_interactive_backend() -> None:
    """Switch to an interactive backend when available for manual demos."""
    try:
        plt.switch_backend("TkAgg")
    except Exception:  # pragma: no cover - backend availability depends on environment
        plt.switch_backend("Agg")


def run_demo() -> None:
    """Generate a brickplot and display it using matplotlib."""
    plotter = BrickPlotter(
        model=str(MODEL_PATH),
        output_folder=str(Path.cwd() / "demo_brickplots"),
        is_plus_one=True,
        is_rc=False,
    )
    result = plotter.get_brickplot(TXT_SEQUENCE)
    image = _decode_image(result["image_base64"])

    _enable_interactive_backend()
    plt.figure(figsize=(6, 4))
    plt.imshow(image)
    plt.title("BrickPlotter Demo")
    plt.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print("Running BrickPlotter demo...")
    run_demo()
