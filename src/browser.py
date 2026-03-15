import logging
import subprocess
import time
import random
import tempfile # 임시 폴더 생성을 위한 모듈 추가

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from src.config import Config

logger = logging.getLogger(__name__)

HUMAN_LIKE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _log_chromium_version():
    """Chromium과 ChromeDriver 버전을 로그에 출력한다 (진단용)."""
    try:
        result = subprocess.run(
            ["/usr/bin/chromium", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        logger.info("Chromium: %s", result.stdout.strip())
    except Exception as e:
        logger.warning("Chromium 버전 확인 실패: %s", e)

    try:
        result = subprocess.run(
            ["/usr/bin/chromedriver", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        logger.info("ChromeDriver: %s", result.stdout.strip())
    except Exception as e:
        logger.warning("ChromeDriver 버전 확인 실패: %s", e)


def setup_chrome_driver():
    """Chrome WebDriver를 생성하여 반환한다.

    - 서버(Docker): Headless 모드 + 시스템 Chromium 사용
    - 로컬(Windows): GUI 모드 + webdriver_manager 자동 설치
    """
    logger.info("크롬 브라우저를 준비합니다...")

    options = Options()
    options.add_argument(f"--user-agent={HUMAN_LIKE_USER_AGENT}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if Config.RUNNING_IN_DOCKER:
        _log_chromium_version()

        # [핵심 변경점] 현재 권한으로 확실하게 쓸 수 있는 임시 폴더를 파이썬이 직접 생성합니다.
        chrome_data_dir = tempfile.mkdtemp(prefix="chrome-data-")
        chrome_crash_dir = tempfile.mkdtemp(prefix="chrome-crash-")

        options.binary_location = "/usr/bin/chromium"
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--user-data-dir=/tmp/chrome-data")
        options.add_argument("--crash-dumps-dir=/tmp/chrome-crashes")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--lang=ko_KR")
        service = Service("/usr/bin/chromedriver")
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)

    logger.info("크롬 브라우저가 준비되었습니다.")
    return driver


def _human_delay(min_sec=0.5, max_sec=0.6):
    time.sleep(random.uniform(min_sec, max_sec))


def login_to_jobkorea(driver):
    """잡코리아 기업회원 계정으로 로그인한다."""
    logger.info("잡코리아 로그인을 시작합니다...")
    
    try:
        driver.get(Config.LOGIN_URL)
        _human_delay()

        corp_tab = driver.find_element(By.CSS_SELECTOR, 'a[data-m-type="Co"]')
        corp_tab.click()
        _human_delay()

        tag_id = driver.find_element(By.NAME, "M_ID")
        tag_id.click()
        tag_id.clear()
        tag_id.send_keys(Config.JOBKOREA_ID)
        _human_delay()

        tag_pw = driver.find_element(By.NAME, "M_PWD")
        tag_pw.click()
        tag_pw.clear()
        tag_pw.send_keys(Config.JOBKOREA_PW)
        _human_delay()

        login_btn = driver.find_element(By.CLASS_NAME, "login-button")
        
        # [수정포인트 1] 셀레니움의 기본 click() 대신 자바스크립트를 이용해 강제 클릭! (무한 로딩 방지)
        driver.execute_script("arguments[0].click();", login_btn)
        logger.info("로그인 버튼 클릭 완료! 응답을 기다립니다...")

        # [수정포인트 2] 브라우저가 기절했는지 우리가 직접 1초마다 확인 (최대 15초까지만 대기)
        login_success = False
        for i in range(15):
            time.sleep(1)
            # URL에 더 이상 'Login'이 없으면 무사히 넘어간 것으로 간주
            if "Login" not in driver.current_url:
                login_success = True
                break
        
        if not login_success:
            raise Exception("15초가 지나도 로그인 페이지를 벗어나지 못했습니다. 봇 탐지(캡차)에 걸렸거나 메모리가 부족할 수 있습니다.")
            
        logger.info("로그인이 완료되었습니다. 다음 단계로 넘어갑니다.")
        
    except Exception as e:
        logger.error("로그인 과정 중 오류 발생: %s", e)
        raise
