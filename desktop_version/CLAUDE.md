# CLAUDE.md (desktop_version)

이 폴더는 PyTorch CNN으로 MNIST를 학습하고, tkinter 창에서 마우스로 그린 숫자를 인식하는 윈도우용 프로그램입니다. 루트의 `CLAUDE.md`(두 버전 공통 규칙)를 먼저 읽으세요.

**이 폴더 안에서 실행해야 합니다.** 모든 명령은 `desktop_version/`으로 이동한 뒤 실행하세요(`가중치_파일`과 `./data`가 현재 작업 디렉터리 기준 상대 경로이기 때문입니다).

## 명령어

```bash
cd desktop_version

# 의존성 (Python 3.10+, CPU 버전 PyTorch)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install pillow numpy

python train.py            # 5에폭 학습, 최고 정확도 가중치를 mnist_cnn.pt로 저장 (CPU 에폭당 약 3분)
python app.py              # 손글씨 인식 앱 실행 (mnist_cnn.pt 필요)
python make_icon.py        # icon.ico 다시 만들기
python 가중치내보내기.py    # mnist_cnn.pt → ../web_version/가중치.bin, 가중치정보.json
python 검증데이터만들기.py  # ../web_version/검증데이터.json 생성 (웹 버전 검증용, 약 27MB, 깃에 없음)
```

바탕 화면 바로가기는 `pythonw.exe`로 `app.py`를 실행해 콘솔 창 없이 앱을 띄웁니다.

- 대상: `pythonw.exe "C:\study01_MNIST\desktop_version\app.py"`
- 시작 위치: `C:\study01_MNIST\desktop_version`
- 아이콘: `C:\study01_MNIST\desktop_version\icon.ico`

## 구조와 주의점

- **`model.py`가 학습과 추론의 공통 계약입니다.** CNN 정의(`숫자인식CNN`), 가중치 파일 이름(`가중치_파일`), 정규화 상수(`평균`, `표준편차`)를 `train.py`와 `app.py`가 함께 가져다 씁니다. 모델 구조를 바꾸면 기존 `mnist_cnn.pt`는 `load_state_dict`에서 실패하므로 `train.py`로 다시 학습해야 합니다.
- **`app.py`의 `전처리()`는 그림판 이미지를 MNIST 분포에 맞추는 핵심 로직입니다.** 색 반전 → bbox 잘라내기 → 비율 유지 20×20 축소 → 28×28 가운데 배치 → 무게중심을 (14,14)로 이동 → 학습과 같은 평균·표준편차로 정규화. 이 단계나 `train.py`의 변환(정규화·데이터 증강)을 바꿀 때는 양쪽이 계속 일치하는지 확인하세요.
- **`전처리()`를 바꾸면 `web_version/전처리.js`도 함께 바꿔야 합니다.** `전처리.js`는 이 함수를 단계와 반올림 방식까지 그대로 재현한 것이라, 한쪽만 바꾸면 두 버전이 다른 답을 냅니다(루트 `CLAUDE.md`의 공통 계약 참고).
- 앱은 tkinter 캔버스(화면 표시)와 PIL 이미지(인식 입력)에 **같은 획을 동시에 그립니다**. 그리기 관련 코드를 수정할 때는 두 곳을 함께 바꿔야 합니다.
- `가중치_파일`과 `./data`는 **현재 작업 디렉터리 기준 상대 경로**입니다(아이콘만 `__file__` 기준). 스크립트는 이 폴더(`desktop_version/`)에서 실행해야 합니다.
- `data/`(MNIST, 학습 시 자동 다운로드)와 `mnist_cnn.pt`는 생성물입니다.

## 웹 버전용 스크립트 2개

- **`가중치내보내기.py`**: `mnist_cnn.pt`를 읽어 BatchNorm을 앞 합성곱에 합친 뒤, 텐서 12개를 float32로 이어 붙인 `../web_version/가중치.bin`과 텐서 이름·형상·정규화 상수를 담은 `../web_version/가중치정보.json`을 씁니다. 저장 전에 합친 모델의 출력이 원본과 1e-4 이내로 같은지 확인하고, 다르면 저장하지 않습니다.
- **`검증데이터만들기.py`**: MNIST 시험 이미지 200장과 `app.py`의 그리기 방식으로 그린 표본 30장 등을 파이썬 전처리·예측 결과와 함께 `../web_version/검증데이터.json`에 씁니다. 이 파일로 `web_version/검증.html`이 JS 결과와 파이썬 결과를 대조합니다.
- 두 스크립트 모두 `desktop_version/`에서 실행하고, 출력은 스크립트 파일 기준 `../web_version/`에 씁니다.

## 코드 스타일

- 변수·함수·클래스 이름과 주석, 출력 메시지를 모두 **한국어**로 씁니다(예: `모델`, `한_에폭_학습`, `손글씨_앱`). 새 코드도 같은 방식을 따르세요.
- 각 파일 맨 위에 `# -*- coding: utf-8 -*-`와 실행 방법을 적은 모듈 docstring이 있습니다.
- `README.md`는 한국어 사용자 문서로, 학습 결과표와 모델 구조 설명을 담고 있습니다. 학습 설정이나 구조가 바뀌면 함께 갱신하세요.
