"""colony-counter: quantify colonies in crystal-violet-stained petri dishes."""

from .config import set_env_vars
from .detection import ColonyRecord, DetectionResult, detect
from .excel import ImageReport, write_workbook
from .params import DEFAULT_PARAMS, DetectionParams
from .visualization import save_mask_figure

__version__ = "0.1.0"

set_env_vars()

__all__ = [
    "DEFAULT_PARAMS",
    "ColonyRecord",
    "DetectionParams",
    "DetectionResult",
    "ImageReport",
    "__version__",
    "detect",
    "save_mask_figure",
    "write_workbook",
]
