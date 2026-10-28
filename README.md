# JWT 인증 게시판

웹서비스설계 개인 과제로 제작한 게시판이다. React로 화면을 구성하고 FastAPI에서 게시글 API와 JWT 인증을 처리하며, 게시글은 SQLite 파일에 저장한다. 게시글 목록과 상세 내용은 로그인하지 않아도 볼 수 있지만, 글 작성은 로그인한 사용자만 가능하다. 수정과 삭제는 게시글 작성자 본인에게만 허용된다.

작성자: 이주은

## 사용 기술

프론트엔드는 React 19.3.0과 Vite 8.3.4, 백엔드는 Python FastAPI 0.143.0을 사용했다. JWT 발급과 검증에는 PyJWT 2.15.1을 사용하고, 게시글 데이터는 Python의 `sqlite3` 모듈로 SQLite에 저장한다. 작업 및 검증 환경은 Windows PowerShell이며, Node.js 20.19 이상과 Python 3.10 이상이 필요하다.

## 프로젝트 구성

```text
JWT-Assignment/
├── README.md
├── .gitignore
├── backend-fastapi/
│   ├── .env.example
│   ├── app.py
│   ├── auth.py
│   ├── errors.py
│   ├── store.py
│   ├── users.py
│   └── requirements.txt
├── frontend-react/
│   ├── src/
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── tools/
│   └── check_api.py
└── docs/
    ├── report.pdf       # 최종 보고서 제출 시 추가
    └── evidence/        # 별도 증거 파일이 있을 때 추가
```

`app.py`에는 API 경로와 입력 검사가, `auth.py`에는 JWT 발급·검증과 작성자 권한 검사가 구현되어 있다. `store.py`는 게시글의 SQLite 저장과 조회를 처리하며, `users.py`에는 과제에서 제공한 Alice와 Bob의 계정 및 비밀번호 검증 기능이 있다. 프론트엔드의 `src/api.js`는 API 호출과 로그인 세션을 관리하고, `src/main.jsx`는 게시판 화면과 사용자 동작을 담당한다.

## 설치 및 실행

다음 명령은 Windows PowerShell을 기준으로 작성했다. 저장소를 복제한 후 백엔드와 프론트엔드를 각각 다른 터미널에서 실행한다.

```powershell
git clone https://github.com/Lee-jueun1/jwt-board-assignment.git
cd jwt-board-assignment
```

### 백엔드 실행

프로젝트 루트에서 다음 명령을 실행한다.

```powershell
cd backend-fastapi
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` 파일의 `JWT_SECRET`에는 직접 생성한 64자리 16진수 키를 설정해야 한다. 다음 명령으로 새 키를 생성할 수 있다.

```powershell
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

출력된 값을 `.env`의 `JWT_SECRET=...` 부분에 넣는다. 나머지 설정은 아래 값을 사용한다.

```dotenv
JWT_ISSUER=webservice-class
JWT_AUDIENCE=board-api
TOKEN_TTL=90
DB_FILE=data/board.sqlite
PORT=8000
```

설정을 마친 뒤 서버를 실행한다.

```powershell
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

서버가 실행되면 `http://127.0.0.1:8000/api/health`에서 `status`가 `ok`인 응답을 확인할 수 있다. API 문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있다.

### 프론트엔드 실행

백엔드 서버를 실행한 상태에서 새 PowerShell 터미널을 열고 프로젝트 루트에서 다음 명령을 실행한다.

```powershell
cd frontend-react
npm ci
npm run build
npm run preview
```

브라우저에서 `http://127.0.0.1:4173`에 접속한다. 개발 중에는 `npm run dev`로 실행하고 `http://127.0.0.1:5173`에 접속할 수 있다. Vite 프록시가 `/api` 요청을 `http://127.0.0.1:8000`으로 전달하므로 백엔드 서버가 함께 실행 중이어야 한다. 소스를 수정한 후 빌드 결과를 확인하려면 `npm run build`를 다시 실행한다. 서버 종료는 각 터미널에서 `Ctrl+C`를 누르면 된다.

## 테스트 계정

| 사용자 | 이메일 | 비밀번호 |
| --- | --- | --- |
| Alice | `alice@class.test` | `Classroom!2026` |
| Bob | `bob@class.test` | `Classroom!2026` |

두 계정은 과제용으로 제공된 테스트 계정이다. 회원가입 기능은 구현 범위에 포함되지 않는다.

## 구현 내용

로그인에 성공하면 서버는 HS256 방식으로 서명한 JWT와 사용자 공개 정보를 반환한다. JWT에는 사용자 ID(`sub`), 만료 시각(`exp`), 발급자(`iss`), 사용 대상(`aud`)이 포함된다. 프론트엔드는 발급된 토큰을 JavaScript 메모리에만 보관하고, `/api/me`와 게시글 등록·수정·삭제 요청에 `Authorization: Bearer <TOKEN>` 헤더를 첨부한다. `localStorage`나 `sessionStorage`에는 토큰을 저장하지 않는다.

서버는 보호 API 요청마다 JWT의 서명, 만료 시간, 필수 클레임과 사용자 존재 여부를 검증한다. 글을 등록할 때는 요청 본문의 작성자 ID를 사용하지 않고 검증된 로그인 사용자 ID를 저장한다. 수정과 삭제에서는 저장된 게시글의 `authorId`와 현재 사용자 ID를 비교하며, 서로 다르면 403 `FORBIDDEN`을 반환하고 데이터를 변경하지 않는다. 프론트엔드에서도 본인 글에만 수정·삭제 버튼을 표시하지만, 실제 권한 검사는 서버에서 수행한다.

게시글 제목은 1~100자, 내용은 1~5000자로 제한하며 공백만 입력하거나 `authorId`, `userId`, `id`와 같은 추가 필드를 전달하면 400 `BAD_INPUT`으로 처리한다. 게시글 목록과 상세 조회는 로그인 없이 사용할 수 있다.

로그아웃하거나 페이지를 새로고침하면 메모리에 저장된 로그인 상태가 해제된다. 만료되거나 유효하지 않은 토큰으로 보호 API를 호출해 401 응답을 받아도 프론트엔드 세션을 비운다. 반면 게시글은 SQLite에 저장되므로 새로고침이나 서버 재시작 후에도 유지된다. 로그아웃만으로 이미 발급된 JWT가 서버에서 즉시 폐기되는 것은 아니다.

## HTTP 응답과 테스트

정상적인 조회·로그인·수정은 200, 게시글 생성은 201과 `Location` 헤더, 삭제는 본문이 없는 204를 반환한다. 잘못된 입력은 400 `BAD_INPUT`, 잘못된 로그인 정보는 401 `INVALID_CREDENTIALS`, 토큰 누락은 401 `TOKEN_REQUIRED`, 변조되거나 유효하지 않은 토큰은 401 `INVALID_TOKEN`, 만료된 토큰은 401 `TOKEN_EXPIRED`로 처리한다. 다른 작성자의 글 변경은 403 `FORBIDDEN`, 존재하지 않는 게시글 조회는 404 `NOT_FOUND`로 처리한다. 보호 API의 401 응답에는 `WWW-Authenticate: Bearer` 헤더를 포함한다.

백엔드 서버를 실행한 상태에서 프로젝트 루트로 이동하여 다음 명령으로 API 자동 검사를 실행할 수 있다.

```powershell
py tools/check_api.py --mode final
```

만료 검사는 `backend-fastapi/.env`의 `TOKEN_TTL`을 `3`으로 변경하고 백엔드를 재시작한 다음 아래 명령을 실행한다.

```powershell
py tools/check_api.py --mode final --expiry
```

만료 검사를 마친 뒤에는 `TOKEN_TTL=90`으로 되돌리고 서버를 재시작한다. 자동 검사 외에도 Alice와 Bob의 작성자 권한 구분, 401과 403의 차이, 204의 빈 응답 본문, 서버 재시작 후 게시글 유지, React 빌드 및 4173번 포트에서의 동작을 확인했다. 개별 테스트의 조건과 증거는 보고서에 정리한다.

SQLite 데이터베이스는 백엔드를 처음 실행할 때 `backend-fastapi/data/board.sqlite`에 생성된다. 데이터를 초기화하려면 백엔드를 종료한 후 해당 파일을 삭제하고 서버를 다시 실행하면 된다. 이 경우 기존 게시글은 모두 삭제된다.

## 보고서와 증거

최종 제출 시 구현 보고서는 [`docs/report.pdf`](docs/report.pdf)에, 별도 테스트 화면은 `docs/evidence/`에 정리해야 하지만, 워드 문서를 pdf로 변환하려 하자 아무 이유 없이 약 50%가 전사되지 않는 문제가 발생해 부득이하게 doxs 파일로 제출하였다. 보고서에는 인증·권한 검사 구현 과정, HTTP 응답 검증, T01~T17 테스트 결과와 직접 확인한 화면을 포함한다. 

## AI 활용 및 참고 자료

JWT 인증 구현과 React API 연동, 오류 원인 분석, 테스트 방법 검토 및 보고서 문장 정리에 ChatGPT를 사용했다. 제안된 내용을 프로젝트 코드에 적용한 후 서버 실행, API 자동 검사, 수동 요청과 브라우저 화면을 통해 동작을 확인했다. AI 활용 사례별 요청 내용, 반영 위치와 검증 결과는 보고서에 별도로 기록한다.

기본 프로젝트 구조와 API 명세, 테스트 계정 및 검사 도구는 웹서비스설계 과목에서 제공한 시작 템플릿과 과제 자료를 바탕으로 했다.

## 제출 시 주의 사항

실제 `.env` 파일, JWT 비밀 키, 발급된 토큰, SQLite 데이터베이스, `.venv`, `node_modules`, 빌드 결과물은 저장소에 포함하지 않는다. GitHub에는 실행에 필요한 소스 코드와 의존성 목록, 설정 예시, 최종 보고서 및 테스트 증거만 올린다. 최종 파일을 모두 업로드한 후 커밋 SHA를 확인하여 저장소 URL과 함께 LMS에 제출한다.
