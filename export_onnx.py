"""Export XGBoost model PRATYAKSA ke format ONNX.

Jalankan: python export_onnx.py
Output: artifacts/artifact_xgb_model.onnx
"""
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

sys.path.insert(0, str(PROJECT_ROOT))

# basicConfig sebelum pemakaian logger (aturan docs.python.org logging HOWTO)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

import joblib
import xgboost as xgb

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


def main() -> None:
    logger.info("Memuat XGBoost model...")
    model = xgb.XGBClassifier()
    model.load_model(str(ARTIFACTS_DIR / "artifact_xgb_model.json"))

    logger.info("Memuat scaler...")
    scaler = joblib.load(str(ARTIFACTS_DIR / "artifact_scaler.pkl"))
    n_features = scaler.n_features_in_
    logger.info("Jumlah fitur: %d", n_features)

    try:
        import onnxmltools
        from onnxmltools.convert.common.data_types import FloatTensorType

        initial_type = [("float_input", FloatTensorType([None, n_features]))]
        onnx_model = onnxmltools.convert_xgboost(model, initial_types=initial_type)
        output_path = ARTIFACTS_DIR / "artifact_xgb_model.onnx"
        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        logger.info("ONNX model berhasil disimpan di %s", output_path)
    except ImportError:
        logger.warning("onnxmltools tidak tersedia, skip export ONNX")
    except Exception:
        logger.exception("Gagal export ONNX")


if __name__ == "__main__":
    main()
