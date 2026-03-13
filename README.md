# JobkoreaCandidate

잡코리아 채용 후보자 관련 자동화 도구

## 프로젝트 정보

| 항목 | 내용 |
|---|---|
| **버전** | 0.1.0 (초기 설정) |
| **Python** | 3.13.2 |
| **배포 환경** | Cloudtype |
| **GitHub** | https://github.com/jaimo012/JobkoreaCandidate |

## 기술 스택

| 라이브러리 | 버전 | 용도 |
|---|---|---|
| selenium | 4.41.0 | 웹 브라우저 자동화 |
| webdriver-manager | 4.0.2 | ChromeDriver 자동 관리 |
| beautifulsoup4 | 4.14.3 | HTML 파싱 |
| pandas | 3.0.1 | 데이터 분석/처리 |
| gspread | 6.2.1 | Google Sheets 연동 |
| google-api-python-client | 2.192.0 | Google API 연동 |
| pytesseract | 0.3.13 | OCR (이미지→텍스트) |
| Pillow | 12.1.1 | 이미지 처리 |
| pyperclip | 1.11.0 | 클립보드 제어 |

## 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/jaimo012/JobkoreaCandidate.git
cd JobkoreaCandidate

# 2. 가상환경 생성 및 활성화
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 패키지 설치
pip install -r requirements.txt
```

## 프로젝트 구조

```
JobkoreaCandidate/
├── src/                   # 소스 코드
│   ├── handlers/          # 기능별 핸들러
│   └── utils/             # 유틸리티 함수
├── .env                   # 환경 변수 (git 미추적)
├── .gitignore             # git 추적 제외 목록
├── requirements.txt       # 패키지 의존성
├── rules.md               # 프로젝트 규칙
├── README.md              # 이 파일
└── main.py                # 진입점
```

## 변경 이력

| 날짜 | 버전 | 내용 |
|---|---|---|
| 2026-03-13 | 0.1.0 | 프로젝트 초기 설정 (Python 개발환경 구축, 라이브러리 설치) |
