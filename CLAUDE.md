# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

손글씨 숫자(0~9) 인식 프로그램을 **데스크톱 버전**과 **웹 버전** 두 가지로 제공하는 저장소입니다. 두 버전은 같은 PyTorch CNN 모델(`desktop_version/model.py`의 `숫자인식CNN`)에서 나온 같은 가중치를 쓰며, 같은 그림에 같은 답을 내도록 만들어져 있습니다.

- `desktop_version/`: 기존 PyTorch + tkinter 프로그램. `python train.py`로 학습하고 `python app.py`로 실행합니다.
- `web_version/`: 외부 라이브러리 없는 순수 자바스크립트로 같은 모델을 추론하는 정적 사이트. GitHub Pages에 배포합니다.

각 폴더에는 그 폴더 전용 규칙을 담은 `CLAUDE.md`가 따로 있습니다. 작업 전에 해당 폴더의 `CLAUDE.md`를 먼저 읽으세요.

- [`desktop_version/CLAUDE.md`](desktop_version/CLAUDE.md)
- [`web_version/CLAUDE.md`](web_version/CLAUDE.md)

## 공통 규칙

- 모든 변수·함수·클래스 이름, 주석, 화면·출력 메시지는 **한국어**로 씁니다.
- 파이썬 파일 맨 위에는 `# -*- coding: utf-8 -*-`와 실행 방법을 적은 모듈 docstring을 둡니다. JS 파일 맨 위에는 역할을 적은 한국어 주석을 둡니다.

## 두 버전의 공통 계약

두 버전은 완전히 독립된 코드지만, 다음 값들은 **데스크톱 쪽이 원본이고 웹 버전은 그 결과물을 받아 쓰는** 관계입니다.

- 웹이 쓰는 가중치(`web_version/가중치.bin`, `web_version/가중치정보.json`)와 검증용 정답 데이터(`web_version/검증데이터.json`)는 `desktop_version/`의 스크립트 두 개가 파이썬(PyTorch)으로 만듭니다. 웹 버전 코드는 이 파일들을 읽기만 하고 만들지 않습니다.
- 정규화 상수(평균 0.1307, 표준편차 0.3081)는 `desktop_version/model.py` 한 곳에서만 정의되고, `가중치정보.json`을 거쳐 웹으로 전달됩니다. JS 코드에 이 숫자를 직접 적지 않습니다.
- **모델 구조, 정규화 상수, 또는 `app.py`의 `전처리()`를 바꾸면** 다음 순서로 다시 실행해야 두 버전이 계속 일치합니다.
  1. `desktop_version/`에서 `python train.py` (모델 구조를 바꾼 경우)
  2. `desktop_version/`에서 `python 가중치내보내기.py`
  3. `desktop_version/`에서 `python 검증데이터만들기.py`
  4. `web_version/`을 로컬 서버로 열고 `검증.html`을 실행해 통과 여부 확인

## 작업 폴더 규칙

두 버전 모두 **각자의 폴더 안에서** 스크립트를 실행해야 합니다. `desktop_version/`의 파이썬 스크립트는 작업 폴더 기준 상대 경로(`mnist_cnn.pt`, `./data`)를 쓰고, `web_version/`은 정적 서버(`python -m http.server`)로 그 폴더를 루트 삼아 열어야 합니다. 자세한 내용은 각 폴더의 `CLAUDE.md`를 보세요.

## 배포 요약

`main` 브랜치에 push되면 `.github/workflows/pages.yml`이 `web_version/` 폴더만 GitHub Pages에 배포합니다(GitHub Actions 방식, 저장소 Settings → Pages → Source를 "GitHub Actions"로 설정해야 동작). `desktop_version/`은 배포 대상이 아닙니다. 자세한 절차는 루트 `README.md`와 `web_version/CLAUDE.md`를 보세요.
