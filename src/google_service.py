import json
import logging
import os
import time
import base64

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import Config

logger = logging.getLogger(__name__)

SHEETS_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_credentials(scopes):
    """환경변수 또는 파일에서 Google 서비스 계정 인증 정보를 생성한다."""
    if Config.GOOGLE_CREDENTIALS_JSON:
        info = json.loads(Config.GOOGLE_CREDENTIALS_JSON)
        return Credentials.from_service_account_info(info, scopes=scopes)
    if Config.GOOGLE_CREDENTIALS_FILE:
        return Credentials.from_service_account_file(Config.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
    raise ValueError(
        "Google 인증 정보가 설정되지 않았습니다. "
        "GOOGLE_CREDENTIALS_JSON 또는 GOOGLE_CREDENTIALS_FILE 환경변수를 확인하세요."
    )


# ──────────────────────────────────────────────
# Google Sheets
# ──────────────────────────────────────────────
def open_google_sheet():
    """구글 시트에 접근하여 (worksheet, DataFrame)을 반환한다."""
    logger.info("구글 시트 연동을 시도합니다...")
    try:
        creds = _get_credentials(SHEETS_SCOPES)
        gc = gspread.authorize(creds)

        doc = gc.open_by_url(Config.SPREADSHEET_URL)
        worksheet = doc.worksheet(Config.SHEET_NAME)

        records = worksheet.get_all_values()
        if not records:
            df_existing = pd.DataFrame()
        else:
            df_existing = pd.DataFrame(records[1:], columns=records[0])

        logger.info("구글 시트 데이터를 성공적으로 불러왔습니다.")
        return worksheet, df_existing
    except Exception as e:
        logger.error("구글 시트 접근 중 오류 발생: %s", e)
        return None, None


GSHEET_CHUNK_SIZE = 500


def append_dataframe_to_gsheet(worksheet, df):
    """DataFrame을 구글 시트 마지막 행 아래에 추가한다."""
    df = df.fillna("")
    data = df.values.tolist()

    logger.info("총 %d건의 데이터를 구글 시트에 업로드합니다...", len(data))
    for i in range(0, len(data), GSHEET_CHUNK_SIZE):
        chunk = data[i : i + GSHEET_CHUNK_SIZE]
        worksheet.append_rows(chunk)
        time.sleep(1)
        logger.info("  - %d건 업로드 완료...", i + len(chunk))

    logger.info("구글 시트 업로드가 완료되었습니다!")


# ──────────────────────────────────────────────
# Google Drive
# ──────────────────────────────────────────────
def upload_file_to_drive(local_file_path, file_name):
    """로컬 파일을 구글 드라이브 지정 폴더에 업로드하고 파일 ID를 반환한다."""
    try:
        creds = _get_credentials(DRIVE_SCOPES)
        drive_service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": file_name,
            "parents": [Config.DRIVE_FOLDER_ID],
        }
        media = MediaFileUpload(local_file_path, resumable=True)

        uploaded = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        return uploaded.get("id")
    except Exception as e:
        logger.error("드라이브 업로드 오류: %s", e)
        return None


# ──────────────────────────────────────────────
# PDF (Chrome CDP)
# ──────────────────────────────────────────────
def save_page_as_pdf(driver, local_save_path):
    """Chrome CDP를 이용하여 현재 페이지를 PDF로 저장한다."""
    try:
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": False,
            "paperWidth": 8.27,
            "paperHeight": 11.69,
            "marginTop": 0.4,
            "marginBottom": 0.4,
            "marginLeft": 0.4,
            "marginRight": 0.4,
        })
        with open(local_save_path, "wb") as f:
            f.write(base64.b64decode(pdf_data["data"]))
        return True
    except Exception as e:
        logger.error("PDF 생성 오류: %s", e)
        return False
