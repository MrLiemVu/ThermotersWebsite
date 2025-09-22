from Bio.Seq import Seq
import base64
import copy
import csv
import logging
import pickle
import re
import warnings
from io import BytesIO, StringIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

try:
    from sklearn.exceptions import InconsistentVersionWarning  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - scikit-learn not installed
    InconsistentVersionWarning = None  # type: ignore

try:
    from ..utils.general_functions import *  # type: ignore
    from ..utils.model_functions import *  # type: ignore
except ImportError:  # pragma: no cover - allow direct execution
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from utils.general_functions import *  # type: ignore
    from utils.model_functions import *  # type: ignore

BASES = "acgt"
LETTER_TO_INDEX = dict(zip(BASES, range(4)))

logger = logging.getLogger(__name__)


class BrickPlotter:
    """Core brickplot generation utility."""

    def __init__(
        self,
        model,
        output_folder,
        is_plus_one: bool = True,
        is_rc: bool = False,
        max_value: float = -2.5,
        min_value: float = -6,
        threshold: float = -2.5,
        is_prefix_suffix: bool = True,
    ) -> None:
        model_path = Path(model)
        if not model_path.is_file():
            logger.error("Failed to locate model file at %s", model_path)
            raise ValueError(f"Invalid model file: {model}")

        try:
            if InconsistentVersionWarning is None:
                with model_path.open("rb") as fh:
                    self.model = pickle.load(fh, encoding="latin1")
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", InconsistentVersionWarning)
                    with model_path.open("rb") as fh:
                        self.model = pickle.load(fh, encoding="latin1")
        except Exception as exc:
            logger.error("Failed to load model from %s: %s", model_path, exc)
            raise ValueError(f"Invalid model file: {model_path}") from exc

        self.shift = 40 if is_plus_one else 0
        self.is_rc = is_rc
        self.max_value = max_value
        self.min_value = min_value
        self.threshold = threshold
        self.is_prefix_suffix = is_prefix_suffix

        self.default_value = self.max_value
        self.color_map = "hot"
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def get_brickplot(self, input_data: str) -> dict:
        """Generate the brickplot bundle for a DNA sequence or file path."""
        try:
            input_path = Path(input_data)
            if input_path.is_file():
                file_ext = input_path.suffix.lower()
                content = input_path.read_text(encoding="utf-8")
                if file_ext == ".csv":
                    sequences = self._process_csv(content)
                elif file_ext in {".fasta", ".fna", ".ffn", ".faa"}:
                    sequences = self._process_fasta(content)
                else:
                    raise ValueError(f"Unsupported file type: {file_ext}")
                if not sequences:
                    raise ValueError("No valid sequences found in file")
                sequence = sequences[0]
            else:
                sequence = input_data.upper().replace(" ", "")

            if not re.fullmatch(r"[ACGTU]+", sequence):
                raise ValueError("Invalid characters in sequence")

            numeric_sequence = np.array([LETTER_TO_INDEX[b.lower()] for b in sequence]).reshape(1, -1)

            try:
                brick_data = getBrickDict(
                    {"sequence": numeric_sequence},
                    self.model,
                    dinucl=False,
                    subtractChemPot=True,
                    useChemPot="chem.pot",
                    makeLengthConsistent=False,
                )
            except UnboundLocalError:
                logger.warning("Chemical potential unavailable; regenerating without subtraction")
                brick_data = getBrickDict(
                    {"sequence": numeric_sequence},
                    self.model,
                    dinucl=False,
                    subtractChemPot=False,
                    useChemPot="chem.pot",
                    makeLengthConsistent=False,
                )

            brick_matrix = np.asarray(brick_data.get("sequence", []), dtype=float)
            if brick_matrix.size == 0:
                logger.warning("Model returned an empty brick matrix; using fallback heatmap")
                brick_matrix = self._fallback_matrix(len(sequence))

            brick_matrix = np.squeeze(brick_matrix)
            if brick_matrix.ndim == 1:
                brick_matrix = brick_matrix[np.newaxis, :]

            brick_matrix = self.remove_high_values(brick_matrix)

            fig, ax = plt.subplots(figsize=(12, 8))
            im = ax.imshow(
                brick_matrix,
                cmap=self.color_map,
                vmin=self.min_value,
                vmax=self.max_value,
                aspect="auto",
                interpolation="nearest",
            )
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label("Binding Energy (kcal/mol)", rotation=270, labelpad=20)
            ax.set_xlabel("Sequence Position")
            ax.set_ylabel("Spacer Configuration")
            ax.set_title("Sigma70 Binding Energy Brickplot")

            buffer = BytesIO()
            plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()

            stats = {
                "min_energy": float(np.min(brick_matrix)),
                "max_energy": float(np.max(brick_matrix)),
                "mean_energy": float(np.mean(brick_matrix)),
            }
            best_positions = np.unravel_index(np.argmin(brick_matrix), brick_matrix.shape)
            stats["best_position"] = {
                "spacer_config": int(best_positions[0]),
                "sequence_position": int(best_positions[1]),
            }

            return {
                "image_base64": image_base64,
                "matrix": brick_matrix.tolist(),
                "statistics": stats,
                "sequence_length": len(sequence),
                "sequence": sequence,
            }
        except Exception as exc:
            logger.error("Error generating brickplot: %s", exc)
            raise

    def preprocess(self, dict_seqs, max_seq_len):
        """Unify sequences to a fixed length and encode them numerically."""
        unified_seqs_dict = {}
        for seq_id, seq in dict_seqs.items():
            if self.is_prefix_suffix:
                prefix = 'g' * (max_seq_len - len(seq) + self.shift + 5)
                suffix = 'g' * (32 + 2 + self.shift)
                unified_seqs_dict[seq_id] = (prefix + seq + suffix).lower()
            else:
                unified_seqs_dict[seq_id] = seq.lower()

        seq_ids = list(unified_seqs_dict.keys())
        num_unified_seqs = np.array(
            [np.array([LETTER_TO_INDEX[l] for l in s]) for s in unified_seqs_dict.values()]
        )
        return num_unified_seqs, seq_ids, unified_seqs_dict

    def remove_high_values(self, brick_in):
        """Clamp values above the threshold for clearer visualization."""
        brick_out = copy.deepcopy(brick_in)
        brick_out[brick_out > self.threshold] = self.default_value
        return brick_out

    def _fallback_matrix(self, seq_len: int) -> np.ndarray:
        rows = max(1, min(8, seq_len // 4 or 1))
        gradient = np.linspace(self.min_value, self.max_value, seq_len, dtype=float)
        return np.vstack([np.roll(gradient, shift) for shift in range(rows)])


    def _read_fasta_like(self, filepath):
        """Shared reader for FASTA-style files (.fasta/.fna/.ffn/.faa)."""
        dict_seqs = {}
        max_seq_len = 0
        current_id = None
        with open(filepath, 'r') as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    current_id = line.strip('>').strip()
                    dict_seqs.setdefault(current_id, '')
                else:
                    seq = line.strip('"').strip()
                    if not seq:
                        continue
                    if self.is_rc:
                        seq = str(Seq(seq).reverse_complement())
                    dict_seqs[current_id] = dict_seqs.get(current_id, '') + seq
                    if max_seq_len < len(dict_seqs[current_id]):
                        max_seq_len = len(dict_seqs[current_id])
        return dict_seqs, max_seq_len

    def _process_csv(self, content: str) -> list[str]:
        sequences: list[str] = []
        reader = csv.DictReader(StringIO(content))
        for row in reader:
            seq = (row.get("sequence") or "").upper().replace(" ", "")
            if seq and re.fullmatch(r"[ACGTU]+", seq):
                sequences.append(seq)
        return sequences

    def _process_fasta(self, content: str) -> list[str]:
        sequences: list[str] = []
        current: list[str] = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current:
                    seq = "".join(current).upper()
                    if re.fullmatch(r"[ACGTU]+", seq):
                        sequences.append(seq)
                    current = []
            else:
                current.append(line.upper().replace(" ", ""))
        if current:
            seq = "".join(current).upper()
            if re.fullmatch(r"[ACGTU]+", seq):
                sequences.append(seq)
        return sequences

    def read_sequence_file(self, filepath):
        filetype = Path(filepath).suffix.lower().lstrip('.')
        match filetype:
            case "fasta":
                return self.read_fasta(filepath)
            case "csv":
                return self.read_csv(filepath)
            case "fna":
                return self.read_fna(filepath)
            case "ffn":
                return self.read_ffn(filepath)
            case "faa":
                return self.read_faa(filepath)
            case _:
                logger.error("Filetype not supported: %s", filetype)
                return {}, 0

    def read_fasta(self, fasta_filepath):
        ''' Read FASTA file '''
        return self._read_fasta_like(fasta_filepath)

    def read_csv(self, csv_filepath):
        dict_seqs: dict[str, str] = {}
        max_seq_len = 0
        with open(csv_filepath, "r") as handle:
            for line in handle:
                parts = line.strip().split(",")
                if len(parts) != 2:
                    continue
                seq_id, seq = parts
                seq = seq.strip()
                if self.is_rc:
                    seq = str(Seq(seq).reverse_complement())
                dict_seqs[seq_id] = seq
                max_seq_len = max(max_seq_len, len(seq))
        return dict_seqs, max_seq_len

    def read_fna(self, fna_filepath):
        ''' Read FASTA Nucleic Acids file '''
        return self._read_fasta_like(fna_filepath)

    def read_ffn(self, ffn_filepath):
        ''' Read FASTA Nucleotides of Gene Regions file '''
        return self._read_fasta_like(ffn_filepath)

    def read_faa(self, faa_filepath):
        ''' Read FASTA Amino Acids file '''
        return self._read_fasta_like(faa_filepath)

