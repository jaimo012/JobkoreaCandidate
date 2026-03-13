# JobkoreaCandidate

잡코리아 제안 수락 후보자 자동화 파이프라인

## 프로젝트 정보

| 항목 | 내용 |
|---|---|
| **버전** | 0.2.0 |
| **Python** | 3.13.2 |
| **배포 환경** | Cloudtype (Docker) |
| **GitHub** | https://github.com/jaimo012/JobkoreaCandidate |

## 주요 기능

1. **자동 로그인**: 잡코리아 기업회원 계정으로 자동 로그인 (Headless Chrome)
2. **후보자 목록 크롤링**: 제안 수락 후보자 리스트를 1~5페이지까지 자동 수집
3. **이력서 상세 수집**: 개별 이력서에서 연락처(OCR), 포트폴리오 링크 추출
4. **제안 상세 수집**: 제안 포지션명, 발송일, 수행업무, 우대사항 추출
5. **이력서 PDF 백업**: Chrome CDP로 이력서를 PDF 변환 후 Google Drive 자동 업로드
6. **Google Sheets 동기화**: 수집 데이터를 구글 시트에 실시간 기록 (중복 제거 적용)
7. **반복 실행**: 한 사이클 완료 후 10분 대기, 무한 반복

## 기술 스택

| 라이브러리 | 버전 | 용도 |
|---|---|---|
| selenium | 4.41.0 | 웹 브라우저 자동화 (Headless Chrome) |
| webdriver-manager | 4.0.2 | ChromeDriver 자동 관리 |
| beautifulsoup4 | 4.14.3 | HTML 파싱 |
| pandas | 3.0.1 | 데이터 분석/처리 |
| gspread | 6.2.1 | Google Sheets 연동 |
| google-api-python-client | 2.192.0 | Google API 연동 |
| google-auth | 2.49.1 | Google 인증 |
| pytesseract | 0.3.13 | OCR (이미지→텍스트) |
| Pillow | 12.1.1 | 이미지 처리 |
| python-dotenv | 1.2.2 | 환경변수 관리 |

## 프로젝트 구조

```
JobkoreaCandidate/
├── src/
│   ├── __init__.py
│   ├── config.py           # 환경변수 기반 설정
│   ├── browser.py          # Chrome 드라이버 설정 + 로그인
│   ├── google_service.py   # Google Sheets / Drive / PDF
│   ├── ocr.py              # OCR 텍스트 추출
│   └── scraper.py          # 크롤링 + 시트 업데이트
├── main.py                 # 진입점 (10분 간격 무한 루프)
├── Dockerfile              # Cloudtype 배포용
├── .env.example            # 환경변수 템플릿
├── .env                    # 실제 환경변수 (git 미추적)
├── .gitignore
├── requirements.txt
├── rules.md
└── README.md
```

## 실행 흐름

```
[시작] → 크롬 열기 → 잡코리아 로그인
  ↓
[Phase 1] 수락 후보자 목록 크롤링 (1~5페이지)
  → 중복 제거 후 구글 시트에 기본정보 저장
  ↓
[Phase 2] 시트에서 연락처가 비어있는 행만 순회
  → 이력서 상세 (연락처 OCR, 포트폴리오)
  → 이력서 PDF → Google Drive 업로드
  → 제안 상세 (포지션명, 발송일, 수행업무, 우대사항)
  → 구글 시트 업데이트
  ↓
[완료] → 크롬 종료 → 10분 대기 → [시작]으로 반복
```

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

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 실제 값을 입력

# 5. 실행
python main.py
```

## Cloudtype 배포 방법

1. GitHub 저장소를 Cloudtype에 연결
2. **빌드 타입**: Dockerfile 선택
3. **환경변수** 설정 (Cloudtype 대시보드 → 환경변수):

| 환경변수 | 값 |
|---|---|
| `JOBKOREA_ID` | 잡코리아 기업회원 아이디 |
| `JOBKOREA_PW` | 잡코리아 기업회원 비밀번호 |
| `GOOGLE_CREDENTIALS_JSON` | 서비스 계정 JSON 파일 내용 전체 |
| `SPREADSHEET_URL` | 구글 스프레드시트 URL |
| `SHEET_NAME` | 시트 이름 (기본: RAW) |
| `DRIVE_FOLDER_ID` | 구글 드라이브 폴더 ID |
| `MAX_PAGES` | 최대 크롤링 페이지 수 (기본: 5) |
| `CYCLE_INTERVAL_SECONDS` | 사이클 간격 초 (기본: 600 = 10분) |

4. 배포 실행

## 변경 이력

| 날짜 | 버전 | 내용 |
|---|---|---|
| 2026-03-13 | 0.2.0 | 주피터 노트북 → 서버 자동화 스크립트 전환 (Headless Chrome, 환경변수 분리, Docker 지원, 10분 간격 반복 실행) |
| 2026-03-13 | 0.1.0 | 프로젝트 초기 설정 (Python 개발환경 구축, 라이브러리 설치) |
