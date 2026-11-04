from pathlib import Path
import os
APP_NAME="SAI AI Recruiter"
BASE_DIR=Path(__file__).resolve().parent.parent
DATA_DIR=Path(os.getenv("SAI_DATA_DIR",BASE_DIR/"data"))
DATA_DIR.mkdir(parents=True,exist_ok=True)
DB_PATH=Path(os.getenv("SAI_DB_PATH",DATA_DIR/"sai_recruiter.db"))
UPLOAD_DIR=Path(os.getenv("SAI_UPLOAD_DIR",DATA_DIR/"uploads"))
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
DEFAULT_ORGANIZATION="Demo Staffing"
