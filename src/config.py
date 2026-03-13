import os
import platform

from dotenv import load_dotenv

load_dotenv()


class Config:
    JOBKOREA_ID = os.getenv("JOBKOREA_ID", "")
    JOBKOREA_PW = os.getenv("JOBKOREA_PW", "")
    LOGIN_URL = "https://www.jobkorea.co.kr/Login"
    ACCEPT_URL = (
        "https://www.jobkorea.co.kr/corp/person/position"
        "?rPageCode=PO&Period=1&Page=PAGE_NUM"
    )

    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "")
    GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
    SPREADSHEET_URL = os.getenv("SPREADSHEET_URL", "")
    SHEET_NAME = os.getenv("SHEET_NAME", "RAW")
    DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")

    MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))
    CYCLE_INTERVAL_SECONDS = int(os.getenv("CYCLE_INTERVAL_SECONDS", "600"))

    RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"

    @staticmethod
    def get_tesseract_cmd():
        env_path = os.getenv("TESSERACT_CMD", "")
        if env_path:
            return env_path
        if platform.system() == "Windows":
            return r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        return "/usr/bin/tesseract"
