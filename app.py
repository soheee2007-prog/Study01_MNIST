# -*- coding: utf-8 -*-
"""
마우스로 숫자를 그리면 학습된 CNN(mnist_cnn.pt)이 어떤 숫자인지 알려주는 프로그램
실행 방법: python app.py   (먼저 train.py 로 가중치를 만들어 두어야 합니다)

조작법
  - 왼쪽 마우스 버튼을 누른 채 끌어서 숫자를 그립니다.
  - 마우스를 떼면 자동으로 인식합니다.
  - [지우기] 버튼 또는 오른쪽 클릭 / Delete 키로 화면을 지웁니다.
"""
import os
import sys
import tkinter as tk

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageOps

from model import 숫자인식CNN, 가중치_파일, 평균, 표준편차

캔버스_크기 = 280   # 그림판 크기(픽셀). 28×28의 10배
붓_두께 = 20        # 선 굵기


def 모델_불러오기():
    """저장된 가중치 파일을 읽어 평가 모드의 모델을 돌려줍니다."""
    if not os.path.exists(가중치_파일):
        print(f"'{가중치_파일}' 파일이 없습니다. 먼저 'python train.py'를 실행해 주세요.")
        sys.exit(1)
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치_파일, map_location="cpu", weights_only=True))
    모델.eval()
    return 모델


def 전처리(그림: Image.Image):
    """
    그림판 이미지를 MNIST와 같은 형식(28×28, 검은 배경에 흰 글씨, 가운데 정렬)으로 바꿉니다.
    MNIST는 숫자를 20×20 상자에 맞춘 뒤 무게중심이 28×28의 가운데에 오도록 배치했으므로 똑같이 따라 합니다.
    그린 것이 없으면 None을 돌려줍니다.
    """
    반전 = ImageOps.invert(그림)            # 흰 배경/검은 글씨 → 검은 배경/흰 글씨
    영역 = 반전.getbbox()                   # 글씨가 있는 영역만 찾기
    if 영역 is None:
        return None
    글씨 = 반전.crop(영역)

    # 가로세로 비율을 유지하며 긴 쪽을 20픽셀로 줄입니다.
    가로, 세로 = 글씨.size
    배율 = 20.0 / max(가로, 세로)
    새_크기 = (max(1, round(가로 * 배율)), max(1, round(세로 * 배율)))
    글씨 = 글씨.resize(새_크기, Image.LANCZOS)

    # 28×28 검은 바탕 가운데에 붙입니다.
    바탕 = Image.new("L", (28, 28), 0)
    바탕.paste(글씨, ((28 - 새_크기[0]) // 2, (28 - 새_크기[1]) // 2))

    # 무게중심이 정중앙(14, 14)에 오도록 이동합니다.
    배열 = np.asarray(바탕, dtype=np.float32)
    세로좌표, 가로좌표 = np.indices(배열.shape)
    총합 = 배열.sum()
    중심_y = (세로좌표 * 배열).sum() / 총합
    중심_x = (가로좌표 * 배열).sum() / 총합
    이동_x, 이동_y = round(14 - 중심_x), round(14 - 중심_y)
    바탕 = 바탕.transform((28, 28), Image.AFFINE, (1, 0, -이동_x, 0, 1, -이동_y))

    # 0~1 범위로 바꾸고 학습 때와 같은 방식으로 정규화합니다.
    텐서 = torch.from_numpy(np.asarray(바탕, dtype=np.float32) / 255.0)
    텐서 = (텐서 - 평균) / 표준편차
    return 텐서.unsqueeze(0).unsqueeze(0)   # 모양: (1, 1, 28, 28)


class 손글씨_앱:
    """tkinter로 만든 손글씨 입력 창"""

    def __init__(self, 창: tk.Tk, 모델):
        self.창 = 창
        self.모델 = 모델
        self.이전_좌표 = None
        창.title("손글씨 숫자 인식 (MNIST CNN)")
        창.resizable(False, False)
        # 창 제목 표시줄과 작업 표시줄에 보일 아이콘 (파일이 없으면 기본 아이콘 사용)
        아이콘_경로 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(아이콘_경로):
            창.iconbitmap(default=아이콘_경로)

        # 왼쪽: 그림판
        self.캔버스 = tk.Canvas(창, width=캔버스_크기, height=캔버스_크기,
                              bg="white", cursor="pencil", highlightthickness=1)
        self.캔버스.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        # 화면에 보이는 그림과 똑같은 그림을 PIL 이미지에도 함께 그립니다(인식에 사용).
        self.그림 = Image.new("L", (캔버스_크기, 캔버스_크기), 255)
        self.붓 = ImageDraw.Draw(self.그림)

        # 오른쪽: 결과 표시
        오른쪽 = tk.Frame(창)
        오른쪽.grid(row=0, column=1, sticky="n", padx=10, pady=10)
        tk.Label(오른쪽, text="인식 결과", font=("맑은 고딕", 12)).pack()
        self.결과_글자 = tk.Label(오른쪽, text="?", font=("맑은 고딕", 64, "bold"), width=3)
        self.결과_글자.pack()
        self.확신도_글자 = tk.Label(오른쪽, text="숫자를 그려 보세요", font=("맑은 고딕", 10))
        self.확신도_글자.pack(pady=(0, 8))

        # 0~9 각각의 확률 막대
        self.막대들 = []
        for 숫자 in range(10):
            줄 = tk.Frame(오른쪽)
            줄.pack(fill="x", pady=1)
            tk.Label(줄, text=str(숫자), width=2, font=("Consolas", 10)).pack(side="left")
            막대 = tk.Canvas(줄, width=150, height=14, bg="#eeeeee", highlightthickness=0)
            막대.pack(side="left")
            self.막대들.append(막대)

        tk.Button(창, text="지우기", command=self.지우기, width=12).grid(row=1, column=1, pady=10)

        # 마우스·키보드 이벤트 연결
        self.캔버스.bind("<Button-1>", self.그리기_시작)
        self.캔버스.bind("<B1-Motion>", self.그리기)
        self.캔버스.bind("<ButtonRelease-1>", self.그리기_끝)
        self.캔버스.bind("<Button-3>", lambda 이벤트: self.지우기())
        창.bind("<Delete>", lambda 이벤트: self.지우기())

    def 점_찍기(self, x, y):
        반지름 = 붓_두께 / 2
        self.캔버스.create_oval(x - 반지름, y - 반지름, x + 반지름, y + 반지름, fill="black", outline="black")
        self.붓.ellipse([x - 반지름, y - 반지름, x + 반지름, y + 반지름], fill=0)

    def 그리기_시작(self, 이벤트):
        self.이전_좌표 = (이벤트.x, 이벤트.y)
        self.점_찍기(이벤트.x, 이벤트.y)

    def 그리기(self, 이벤트):
        x, y = 이벤트.x, 이벤트.y
        if self.이전_좌표:
            이전_x, 이전_y = self.이전_좌표
            self.캔버스.create_line(이전_x, 이전_y, x, y, width=붓_두께, capstyle=tk.ROUND, smooth=True)
            self.붓.line([이전_x, 이전_y, x, y], fill=0, width=붓_두께)
        self.점_찍기(x, y)   # 선 끝을 둥글게
        self.이전_좌표 = (x, y)

    def 그리기_끝(self, 이벤트):
        self.이전_좌표 = None
        self.인식하기()

    def 지우기(self):
        self.캔버스.delete("all")
        self.붓.rectangle([0, 0, 캔버스_크기, 캔버스_크기], fill=255)
        self.결과_글자.config(text="?")
        self.확신도_글자.config(text="숫자를 그려 보세요")
        for 막대 in self.막대들:
            막대.delete("all")

    @torch.no_grad()
    def 인식하기(self):
        입력 = 전처리(self.그림)
        if 입력 is None:
            return
        확률 = F.softmax(self.모델(입력), dim=1)[0]
        예측 = int(확률.argmax())
        self.결과_글자.config(text=str(예측))
        self.확신도_글자.config(text=f"확신도 {확률[예측] * 100:.1f}%")
        for 숫자, 막대 in enumerate(self.막대들):
            막대.delete("all")
            색 = "#2e7d32" if 숫자 == 예측 else "#1976d2"
            막대.create_rectangle(0, 0, 150 * float(확률[숫자]), 14, fill=색, width=0)


def 메인():
    모델 = 모델_불러오기()
    창 = tk.Tk()
    손글씨_앱(창, 모델)
    창.mainloop()


if __name__ == "__main__":
    메인()
