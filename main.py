import logging
import time
import traceback

from src.config import Config
from src.browser import setup_chrome_driver, login_to_jobkorea
from src.scraper import (
    scrape_all_accepted_candidates,
    process_and_upload_candidates,
    update_empty_resumes_in_sheet,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_cycle():
    """한 사이클: 드라이버 생성 → 로그인 → 크롤링 → 상세수집 → 드라이버 종료"""
    driver = setup_chrome_driver()

    try:
        login_to_jobkorea(driver)

        logger.info("===== Phase 1: 수락 후보자 목록 크롤링 =====")
        df_new = scrape_all_accepted_candidates(driver)
        process_and_upload_candidates(df_new)

        logger.info("===== Phase 2: 상세정보 수집 및 시트 업데이트 =====")
        update_empty_resumes_in_sheet(driver)

        logger.info("===== 사이클 정상 완료 =====")
    finally:
        driver.quit()
        logger.info("크롬 브라우저를 종료했습니다.")


def main():
    logger.info("JobkoreaCandidate 자동화 서비스를 시작합니다.")
    logger.info("사이클 간격: %d초 (%d분)", Config.CYCLE_INTERVAL_SECONDS, Config.CYCLE_INTERVAL_SECONDS // 60)

    while True:
        try:
            run_cycle()
        except Exception:
            logger.error("사이클 실행 중 오류 발생:\n%s", traceback.format_exc())

        logger.info("%d초 후 다음 사이클을 시작합니다...", Config.CYCLE_INTERVAL_SECONDS)
        time.sleep(Config.CYCLE_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
