from pathlib import Path

ENCODING = "utf-8"

ROOT_DIRPATH = Path(__file__).parent
DATA_DIRPATH = ROOT_DIRPATH / "data"
LOGS_DIRPATH = ROOT_DIRPATH / "logs"

DATA_FILEPATH = DATA_DIRPATH / "star_gifts.json"
LOG_FILEPATH = LOGS_DIRPATH / "main.log"

DATA_DIRPATH.mkdir(exist_ok=True)
LOGS_DIRPATH.mkdir(exist_ok=True)