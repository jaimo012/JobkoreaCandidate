# JobkoreaCandidate - 프로젝트 규칙 문서

## 1. 프로젝트 개요

- **프로젝트명**: JobkoreaCandidate
- **목적**: 잡코리아 채용 후보자 관련 자동화 도구
- **배포 환경**: Cloudtype (클라우드 서버)
- **개발 언어**: Python 3.13
- **GitHub**: https://github.com/jaimo012/JobkoreaCandidate

## 2. 개발 환경

- **Python**: 3.13.2
- **패키지 관리**: pip + venv (가상환경)
- **버전 관리**: Git + GitHub
- **의존성 파일**: `requirements.txt` (버전 고정)

## 3. 프로젝트 구조 규칙

```
JobkoreaCandidate/
├── venv/                  # 가상환경 (git 미추적)
├── src/                   # 소스 코드 디렉토리
│   ├── __init__.py
│   ├── config.py          # 환경변수 기반 설정
│   ├── browser.py         # Chrome 드라이버 설정 + 로그인
│   ├── google_service.py  # Google Sheets / Drive / PDF
│   ├── ocr.py             # OCR 텍스트 추출
│   └── scraper.py         # 크롤링 + 시트 업데이트
├── main.py                # 진입점 (10분 간격 무한 루프)
├── Dockerfile             # Cloudtype 배포용
├── .env.example           # 환경변수 템플릿
├── .env                   # 실제 환경변수 (git 미추적)
├── .gitignore             # git 추적 제외 목록
├── requirements.txt       # 패키지 의존성 목록
├── rules.md               # 프로젝트 규칙 (이 파일)
└── README.md              # 프로젝트 설명서
```

## 4. 핵심 라이브러리 용도

| 라이브러리 | 용도 |
|---|---|
| `selenium` | 웹 브라우저 자동화 (크롤링, 자동 입력) |
| `webdriver-manager` | ChromeDriver 자동 설치 및 관리 |
| `beautifulsoup4` | HTML 파싱 및 데이터 추출 |
| `pandas` | 데이터 정리 및 분석 (DataFrame) |
| `gspread` | Google Sheets 읽기/쓰기 |
| `google-api-python-client` | Google API 통합 |
| `pytesseract` | OCR (이미지에서 텍스트 추출) |
| `Pillow` | 이미지 처리 |
| `pyperclip` | 클립보드 복사/붙여넣기 |

## 5. 코딩 컨벤션

- **네이밍**: snake_case (변수, 함수), PascalCase (클래스)
- **들여쓰기**: 스페이스 4칸
- **인코딩**: UTF-8
- **Docstring**: Google 스타일
- **최대 줄 길이**: 120자

## 6. Git 컨벤션

- **커밋 메시지 형식**: `[태그] 변경 내용 요약`
  - `[INIT]` 초기 설정
  - `[FEAT]` 새 기능 추가
  - `[FIX]` 버그 수정
  - `[REFACTOR]` 리팩토링
  - `[DOCS]` 문서 변경
  - `[STYLE]` 코드 스타일/포맷 변경
  - `[CHORE]` 기타 설정 변경
- **브랜치**: `main` (단일 브랜치)

## 7. 보안 규칙

- `.env` 파일에 API 키, 비밀번호 등 민감 정보 저장
- `credentials.json`, `token.json` 등 인증 파일은 절대 git에 올리지 않음
- `.gitignore`에 민감 파일 반드시 등록

## 8. 배포 (Cloudtype)

- Cloudtype에서 Python 런타임으로 배포 예정
- `requirements.txt`로 의존성 자동 설치
- 환경 변수는 Cloudtype 대시보드에서 별도 설정
