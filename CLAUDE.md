# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyTorch CNN으로 MNIST를 학습하고, tkinter 창에서 마우스로 그린 숫자를 인식하는 윈도우용 학습 프로젝트입니다. git 저장소가 아니며, 테스트·린트·빌드 설정은 없습니다.

## 명령어

```bash
# 의존성 (Python 3.10+, CPU 버전 PyTorch)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install pillow numpy

python train.py      # 5에폭 학습, 최고 정확도 가중치를 mnist_cnn.pt로 저장 (CPU 에폭당 약 3분)
python app.py        # 손글씨 인식 앱 실행 (mnist_cnn.pt 필요)
python make_icon.py  # icon.ico 다시 만들기
```

바탕 화면 바로가기는 `pythonw.exe`로 `app.py`를 실행해 콘솔 창 없이 앱을 띄웁니다.

## 구조와 주의점

- **`model.py`가 학습과 추론의 공통 계약입니다.** CNN 정의(`숫자인식CNN`), 가중치 파일 이름(`가중치_파일`), 정규화 상수(`평균`, `표준편차`)를 `train.py`와 `app.py`가 함께 가져다 씁니다. 모델 구조를 바꾸면 기존 `mnist_cnn.pt`는 `load_state_dict`에서 실패하므로 `train.py`로 다시 학습해야 합니다.
- **`app.py`의 `전처리()`는 그림판 이미지를 MNIST 분포에 맞추는 핵심 로직입니다.** 색 반전 → bbox 잘라내기 → 비율 유지 20×20 축소 → 28×28 가운데 배치 → 무게중심을 (14,14)로 이동 → 학습과 같은 평균·표준편차로 정규화. 이 단계나 `train.py`의 변환(정규화·데이터 증강)을 바꿀 때는 양쪽이 계속 일치하는지 확인하세요.
- 앱은 tkinter 캔버스(화면 표시)와 PIL 이미지(인식 입력)에 **같은 획을 동시에 그립니다**. 그리기 관련 코드를 수정할 때는 두 곳을 함께 바꿔야 합니다.
- `가중치_파일`과 `./data`는 **현재 작업 디렉터리 기준 상대 경로**입니다(아이콘만 `__file__` 기준). 스크립트는 프로젝트 폴더에서 실행해야 합니다.
- `data/`(MNIST, 학습 시 자동 다운로드)와 `mnist_cnn.pt`는 생성물입니다.

## 코드 스타일

- 변수·함수·클래스 이름과 주석, 출력 메시지를 모두 **한국어**로 씁니다(예: `모델`, `한_에폭_학습`, `손글씨_앱`). 새 코드도 같은 방식을 따르세요.
- 각 파일 맨 위에 `# -*- coding: utf-8 -*-`와 실행 방법을 적은 모듈 docstring이 있습니다.
- `README.md`는 한국어 사용자 문서로, 학습 결과표와 모델 구조 설명을 담고 있습니다. 학습 설정이나 구조가 바뀌면 함께 갱신하세요.
