# 손글씨 숫자 인식 (MNIST CNN)

마우스나 손가락으로 숫자(0~9)를 그리면 PyTorch로 학습한 합성곱 신경망(CNN)이 어떤 숫자인지 알려주는 프로젝트입니다. 같은 모델을 **데스크톱 버전**과 **웹 버전** 두 가지로 씁니다.

## 두 버전 비교

| | [`desktop_version/`](desktop_version) | [`web_version/`](web_version) |
|---|---|---|
| 실행 환경 | 윈도우, Python + tkinter | 브라우저(정적 사이트) |
| 추론 | PyTorch | 외부 라이브러리 없는 순수 자바스크립트 |
| 학습 | 가능 (`train.py`) | 불가능 (데스크톱에서 학습한 가중치를 가져다 씀) |
| 입력 | 마우스로 그림 | 마우스·터치·펜으로 그림 |
| 실행 방법 | `python app.py` 또는 바탕 화면 바로가기 | 정적 서버로 `index.html` 열기 |
| 배포 | 없음(로컬 실행) | GitHub Pages |

두 버전은 같은 가중치에서 나왔고 같은 전처리를 거치므로 같은 그림에 같은 답을 냅니다. 자세한 구조는 각 폴더의 `CLAUDE.md`와 `README.md`를 보세요.

## 빠른 시작

### 데스크톱 버전

```bash
cd desktop_version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install pillow numpy
python app.py
```

자세한 설치·사용법은 [`desktop_version/README.md`](desktop_version/README.md)를 보세요.

### 웹 버전 (로컬에서 열기)

```bash
cd web_version
python -m http.server 8000
```

브라우저로 `http://localhost:8000` 에 접속합니다. `file://`로 직접 열면 동작하지 않으니 반드시 로컬 서버를 거쳐야 합니다.

## 배포 (GitHub Pages)

`main` 브랜치에 push하면 `.github/workflows/pages.yml`이 `web_version/` 폴더만 GitHub Pages에 자동으로 배포합니다.

1. 저장소 **Settings → Pages → Source**를 **"GitHub Actions"**로 한 번 설정합니다(사용자가 직접 해야 함).
2. 이후 `web_version/`을 바꾸고 `main`에 push할 때마다 자동으로 다시 배포됩니다(`workflow_dispatch`로 수동 실행도 가능).
3. 배포 주소는 `https://<사용자명>.github.io/<저장소 이름>/` 형태입니다(예: `https://soheee2007-prog.github.io/Study01_MNIST/`). 모든 경로가 상대 경로라 이런 하위 경로에서도 그대로 동작합니다.
4. 배포는 `web_version/` 폴더 전체를 올리므로 `검증.html`도 함께 게시되지만, 검증용 정답 데이터(`검증데이터.json`)는 `.gitignore`에 들어 있어 깃에 없으므로 Pages에서는 "검증데이터.json이 없습니다"만 보이고 실제 검증은 로컬에서만 할 수 있습니다.

## 검증 결과

웹 버전의 순수 JS 추론·전처리가 파이썬(PyTorch) 결과와 같은지 `web_version/검증.html`로 검사합니다(로컬 전용, 검증용 정답 데이터는 `desktop_version/검증데이터만들기.py`로 따로 만들어야 합니다).

| 항목 | 기준 | 실측 |
|---|---|---|
| 순전파 일치 | 같은 28×28 입력에 대한 확률 최대 절대차 ≤ 1e-4 | 2.8e-7 (200장) |
| 전체 정확도 | 280×280 그림 → JS 전처리 → JS 모델 경로로 200장 중 97% 이상 정답 | JS 100.0%(200/200), 파이썬 100.0% |
| 데스크톱 회귀 | 터미널 실행과 바탕 화면 바로가기 더블클릭 정상 | 정상 |
| 웹 앱 동작 | 그린 숫자를 인식하고 상위 3개 후보 표시 | 정상(합성 포인터로 그린 7 인식 확인, 실제 터치 기기는 미확인) |

검증 페이지(`검증.html`)는 위 4가지 외에 가중치 파일 형식, 전처리 단독 비교, 빈 그림, 경계 표본, 그린 표본 30장 등 보조 검사를 포함해 총 14개 항목을 검사하며, 모두 통과하면 `검증 통과 14/14`를 표시합니다.

## 모델 구조

```
입력 (1×28×28)
 → [합성곱 3×3, 32] → 배치정규화 → ReLU
 → [합성곱 3×3, 32] → 배치정규화 → ReLU → 최대풀링  (32×14×14)
 → [합성곱 3×3, 64] → 배치정규화 → ReLU
 → [합성곱 3×3, 64] → 배치정규화 → ReLU → 최대풀링  (64×7×7)
 → 펼치기 → 완전연결 128 → ReLU → 드롭아웃 0.5
 → 완전연결 10 (숫자 0~9)
```

웹 버전은 추론 시 불필요한 배치정규화(BatchNorm)를 앞 합성곱에 미리 합치고 드롭아웃을 뺀 같은 구조를 씁니다. 학습 결과와 전처리 설명은 [`desktop_version/README.md`](desktop_version/README.md)를 보세요.
