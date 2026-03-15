import datetime
import logging
import os
import re
import time
import random

import gspread
import pandas as pd
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait       # [수정 1] 똑똑한 대기를 위한 모듈
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from src.config import Config
from src.ocr import extract_text_from_base64
from src.google_service import (
    open_google_sheet,
    append_dataframe_to_gsheet,
    save_page_as_pdf,
    upload_file_to_drive,
)

logger = logging.getLogger(__name__)

TEMP_DIR = "temp_files"


# ──────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────
def _parse_soup(driver):
    return BeautifulSoup(driver.page_source, "html.parser")


def _human_delay(min_sec=2.0, max_sec=3.5):
    time.sleep(random.uniform(min_sec, max_sec))


def _safe_get(driver, url):
    try:
        driver.get(url)
    except TimeoutException:
        logger.warning("페이지 로딩 타임아웃 발생! 화면 로딩을 강제 중지하고 있는 데이터만 추출합니다.")
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass
    except Exception as e:
        logger.warning("페이지 이동 중 기타 오류: %s", e)


def _extract_portfolio_links(soup):
    """이력서 HTML에서 포트폴리오 첨부파일 링크를 최대 3개 추출한다."""
    links = []
    try:
        portfolio_box = soup.find("div", class_="base portfolio")
        if not portfolio_box:
            logger.info("등록된 포트폴리오가 없습니다.")
        else:
            for a_tag in portfolio_box.find_all("a"):
                href = a_tag.get("href", "").strip()
                if "file2.jobkorea" not in href:
                    continue
                links.append(href)
                if len(links) == 3:
                    break
    except Exception as e:
        logger.warning("포트폴리오 링크 추출 중 오류: %s", e)

    while len(links) < 3:
        links.append("")

    collected = 3 - links.count("")
    logger.info("포트폴리오 추출 완료 (수집된 링크 수: %d개)", collected)
    return links


# ──────────────────────────────────────────────
# Phase 1: 수락 후보자 목록 크롤링
# ──────────────────────────────────────────────
def _parse_candidate_row(row):
    """후보자 목록 테이블의 한 행(tr)에서 기본 정보를 추출한다."""
    name_tag = row.find("div", class_="name")
    name = name_tag.text.strip() if name_tag else "이름없음"

    gender, age = "", ""
    line_list = row.find("ul", class_="line-list")
    if line_list:
        li_tags = line_list.find_all("li")
        gender = li_tags[0].text.strip() if len(li_tags) > 0 else ""
        age = li_tags[1].text.strip() if len(li_tags) > 1 else ""

    td_tags = row.find_all("td")

    edu_tag = td_tags[3].find("div", class_="strong") if len(td_tags) > 3 else None
    education = edu_tag.text.strip() if edu_tag else ""

    exp_tag = td_tags[4].find("div", class_="strong") if len(td_tags) > 4 else None
    experience = exp_tag.text.strip() if exp_tag else ""

    mgr_tag = td_tags[5].find("div", class_="read") if len(td_tags) > 5 else None
    manager = mgr_tag.text.strip() if mgr_tag else ""

    r_no = row.get("data-r-no", "")
    co_pass_no = row.get("data-posg-no", "")
    resume_url = (
        f"https://www.jobkorea.co.kr/corp/person/resumedb"
        f"?R_No={r_no}&Pass_R_No=0&Co_Pass_No={co_pass_no}"
    )

    return {
        "이름": name,
        "성별": gender,
        "나이": age,
        "최종학력": education,
        "총경력": experience,
        "담당자": manager,
        "이력서URL": resume_url,
    }


def scrape_all_accepted_candidates(driver):
    """1~MAX_PAGES 페이지까지 순회하며 제안 수락 후보자 목록을 DataFrame으로 반환한다."""
    all_data = []
    page_num = 1

    logger.info("전체 페이지 데이터 자동 추출을 시작합니다...")

    while page_num <= Config.MAX_PAGES:
        target_url = Config.ACCEPT_URL.replace("PAGE_NUM", str(page_num))
        logger.info("%d페이지로 이동 중...", page_num)
        
        _safe_get(driver, target_url)
        
        # [수정 2] 무작정 기다리지 않고, 페이지 번호(span.now)가 뜰 때까지 최대 15초간 똑똑하게 대기!
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.now"))
            )
        except TimeoutException:
            logger.warning("15초가 지나도 후보자 목록(페이지 번호)이 화면에 나타나지 않습니다.")
            logger.info("👉 [원인분석용] 현재 URL: %s", driver.current_url)
            logger.info("👉 [원인분석용] 현재 제목: %s", driver.title)
            # 화면에 떠있는 텍스트의 앞부분 200자만 추출해서 로그로 출력
            soup_debug = _parse_soup(driver)
            text_preview = soup_debug.get_text(separator=' ', strip=True)[:200]
            logger.info("👉 [원인분석용] 화면 텍스트: %s...", text_preview)
        
        soup = _parse_soup(driver)

        current_page_tag = soup.find("span", class_="now")
        if current_page_tag:
            if current_page_tag.text.strip() != str(page_num):
                logger.info("더 이상 페이지가 없습니다. (마지막: %s)", current_page_tag.text.strip())
                break
        else:
            logger.info("페이지 번호를 찾을 수 없어 %d페이지에서 추출을 종료합니다.", page_num)
            break

        candidate_rows = soup.find_all("tr", class_="title-case")
        if not candidate_rows:
            logger.info("%d페이지에 추출할 데이터가 없어 종료합니다.", page_num)
            break

        logger.info("%d페이지에서 %d명 발견. 추출 중...", page_num, len(candidate_rows))

        for row in candidate_rows:
            try:
                all_data.append(_parse_candidate_row(row))
            except Exception as e:
                logger.warning("%d페이지 특정 지원자 데이터 추출 오류(스킵): %s", page_num, e)

        page_num += 1

    logger.info("전체 데이터 추출 완료! 총 %d명 수집.", len(all_data))
    return pd.DataFrame(all_data)


# ──────────────────────────────────────────────
# Phase 1-2: 중복 제거 후 구글 시트 업로드
# ──────────────────────────────────────────────
UPLOAD_COL_ORDER = ["수집일시", "담당자", "이름", "성별", "나이", "최종학력", "총경력", "이력서URL"]


def process_and_upload_candidates(df_new):
    if df_new.empty:
        logger.info("크롤링된 새로운 데이터가 없어 업로드를 건너뜁니다.")
        return

    worksheet, df_existing = open_google_sheet()
    if worksheet is None:
        return

    df_upload = df_new.copy()
    df_upload["수집일시"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for col in UPLOAD_COL_ORDER:
        if col not in df_upload.columns:
            df_upload[col] = ""
    df_upload = df_upload[UPLOAD_COL_ORDER]

    if not df_existing.empty and "이력서URL" in df_existing.columns:
        existing_urls = set(df_existing["이력서URL"].tolist())
        df_final = df_upload[~df_upload["이력서URL"].isin(existing_urls)]
        dup_count = len(df_upload) - len(df_final)
        logger.info("기존 시트와 비교하여 %d건 중복 제외.", dup_count)
    else:
        df_final = df_upload

    if df_final.empty:
        logger.info("새로 추가할 지원자가 없습니다. (모두 기존 데이터)")
        return

    append_dataframe_to_gsheet(worksheet, df_final)
    logger.info("%d건의 새로운 지원자 정보가 구글 시트에 저장되었습니다!", len(df_final))


# ──────────────────────────────────────────────
# Phase 2: 이력서 상세정보 + PDF + 제안정보
# ──────────────────────────────────────────────
def _extract_resume_details(driver, resume_url, candidate_name):
    _safe_get(driver, resume_url)
    time.sleep(random.uniform(2.5, 3.5))
    soup = _parse_soup(driver)

    phone, email = "비공개", "비공개"
    info_box = soup.find("div", class_="info-detail")
    if info_box:
        for item in info_box.find_all("div", class_="item"):
            label_tag = item.find("div", class_="label")
            value_tag = item.find("div", class_="value")
            if not label_tag or not value_tag:
                continue
            label = label_tag.text.strip()
            img_tag = value_tag.find("img")
            if not img_tag or "src" not in img_tag.attrs:
                continue
            base64_src = img_tag["src"]
            if label == "휴대폰":
                phone = extract_text_from_base64(base64_src)
            elif label == "Email":
                email = extract_text_from_base64(base64_src)

    portfolio_links = _extract_portfolio_links(soup)

    accepted_link = ""
    history_detail = soup.find("div", class_="history-detail")
    if history_detail and history_detail.get("data-href"):
        accepted_link = "https://www.jobkorea.co.kr" + history_detail["data-href"]

    safe_phone = phone.replace("-", "").replace(" ", "") if phone else "번호없음"
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M")
    pdf_filename = f"{now_str}_{candidate_name}_{safe_phone}.pdf"

    logger.info("[%s] 이력서 및 첨부파일 드라이브 백업을 시작합니다...", candidate_name)

    os.makedirs(TEMP_DIR, exist_ok=True)
    local_pdf_path = os.path.join(TEMP_DIR, pdf_filename)
    pdf_drive_url = ""

    if save_page_as_pdf(driver, local_pdf_path):
        drive_file_id = upload_file_to_drive(local_pdf_path, pdf_filename)
        if drive_file_id:
            logger.info("  이력서 PDF 드라이브 저장 완료! (%s)", pdf_filename)
            pdf_drive_url = f"https://drive.google.com/file/d/{drive_file_id}/view"
            os.remove(local_pdf_path)

    return {
        "휴대전화번호": phone,
        "이메일": email,
        "첨부파일1": portfolio_links[0],
        "첨부파일2": portfolio_links[1],
        "첨부파일3": portfolio_links[2],
        "제안URL": accepted_link,
        "이력서파일URL": pdf_drive_url,
    }


def _extract_offer_details(driver, offer_url):
    result = {"제안포지션": "", "제안일자": "", "수행업무": "", "우대사항": ""}
    if not offer_url:
        return result

    logger.info("  제안 상세 페이지 추가 정보를 추출합니다...")
    _safe_get(driver, offer_url)
    time.sleep(random.uniform(1.5, 2.5))
    soup = _parse_soup(driver)

    try:
        title_tag = soup.find("p", class_="plea-send-title-sub")
        if title_tag:
            result["제안포지션"] = title_tag.text.strip()

        day_dl = soup.find("dl", class_="plea-send-txt-day")
        if day_dl:
            dd_tag = day_dl.find("dd")
            if dd_tag:
                match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", dd_tag.text.strip())
                if match:
                    result["제안일자"] = (
                        f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    )

        info_div = soup.find("div", class_="plea-send-txt-info preLine")
        if info_div:
            for dl in info_div.find_all("dl"):
                dt = dl.find("dt")
                dd = dl.find("dd")
                if not dt or not dd:
                    continue
                label = dt.text.strip()
                value = dd.get_text(separator="\n").strip()
                if "수행업무" in label:
                    result["수행업무"] = value
                elif "우대사항" in label:
                    result["우대사항"] = value
    except Exception as e:
        logger.warning("제안 상세 정보 일부 추출 실패: %s", e)

    return result


# ──────────────────────────────────────────────
# Phase 2 메인: 빈 데이터 순회 및 구글 시트 업데이트
# ──────────────────────────────────────────────
REQUIRED_COLUMNS = [
    "이름", "이력서URL", "휴대전화번호", "이메일",
    "첨부파일1", "첨부파일2", "첨부파일3", "제안URL",
    "제안포지션", "제안일자", "이력서파일URL", "수행업무", "우대사항",
]

def update_empty_resumes_in_sheet(driver):
    logger.info("구글 시트에서 업데이트 대상을 탐색합니다...")
    worksheet, _ = open_google_sheet()
    if not worksheet:
        return

    all_values = worksheet.get_all_values()
    if len(all_values) < 2:
        logger.info("시트에 데이터가 없습니다.")
        return

    headers = all_values[0]

    try:
        col_idx = {col: headers.index(col) + 1 for col in REQUIRED_COLUMNS}
    except ValueError as e:
        logger.error("시트에 필요한 컬럼이 존재하지 않습니다: %s", e)
        return

    update_count = 0

    for i in range(1, len(all_values)):
        row_data = all_values[i]
        sheet_row_num = i + 1

        def _cell_value(col_name):
            idx = col_idx[col_name] - 1
            return row_data[idx].strip() if len(row_data) > idx else ""

        name = _cell_value("이름")
        phone = _cell_value("휴대전화번호")
        resume_url = _cell_value("이력서URL")

        if not name or phone or not resume_url:
            continue

        try:
            details = _extract_resume_details(driver, resume_url, name)
            offer_details = {"제안포지션": "", "제안일자": "", "수행업무": "", "우대사항": ""}
            if details["제안URL"]:
                offer_details = _extract_offer_details(driver, details["제안URL"])

            cells_to_update = [
                gspread.Cell(row=sheet_row_num, col=col_idx["휴대전화번호"], value=details["휴대전화번호"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["이메일"], value=details["이메일"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["첨부파일1"], value=details["첨부파일1"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["첨부파일2"], value=details["첨부파일2"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["첨부파일3"], value=details["첨부파일3"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["제안URL"], value=details["제안URL"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["제안포지션"], value=offer_details["제안포지션"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["제안일자"], value=offer_details["제안일자"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["수행업무"], value=offer_details["수행업무"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["우대사항"], value=offer_details["우대사항"]),
                gspread.Cell(row=sheet_row_num, col=col_idx["이력서파일URL"], value=details["이력서파일URL"]),
            ]

            worksheet.update_cells(cells_to_update)
            logger.info("  [%s] 시트 기록 완료!", name)

            update_count += 1
            time.sleep(1.5)
        except Exception as e:
            logger.error("  [%s] 정보 처리 중 오류 발생: %s", name, e)

    logger.info("총 %d명의 데이터 수집 및 시트 동기화가 종료되었습니다.", update_count)
