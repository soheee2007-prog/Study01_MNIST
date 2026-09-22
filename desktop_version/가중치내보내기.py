# -*- coding: utf-8 -*-
"""
학습된 가중치(mnist_cnn.pt)를 웹 버전이 읽을 수 있는 파일 2개로 내보냅니다.
  - ../web_version/가중치.bin        : float32 little-endian 숫자를 이어 붙인 데이터
  - ../web_version/가중치정보.json   : 텐서 이름·형상·위치와 정규화 상수
BatchNorm은 앞의 합성곱에 미리 합쳐서, 웹은 합성곱·ReLU·풀링·완전연결만 계산하면 됩니다.
실행 방법: desktop_version 폴더에서 python 가중치내보내기.py
"""
import json
import os
import sys

import numpy as np
import torch

from model import 숫자인식CNN, 가중치_파일, 평균, 표준편차

웹_폴더 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web_version")
허용_오차 = 1e-4


def 배치정규화_합치기(합성곱, 배치정규화):
    """합성곱 뒤의 BatchNorm을 합성곱 가중치·편향에 합쳐 (가중치, 편향) numpy 배열로 돌려줍니다."""
    배율 = 배치정규화.weight / torch.sqrt(배치정규화.running_var + 배치정규화.eps)
    가중치 = 합성곱.weight * 배율.reshape(-1, 1, 1, 1)
    편향 = (합성곱.bias - 배치정규화.running_mean) * 배율 + 배치정규화.bias
    return 가중치.detach().numpy().astype(np.float32), 편향.detach().numpy().astype(np.float32)


def 텐서_목록_만들기(모델):
    """(이름, numpy 배열) 12개를 웹이 읽을 순서대로 돌려줍니다."""
    특징 = 모델.특징추출
    목록 = []
    for 번호, (합성곱_위치, 정규화_위치) in enumerate([(0, 1), (3, 4), (7, 8), (10, 11)], start=1):
        가중치, 편향 = 배치정규화_합치기(특징[합성곱_위치], 특징[정규화_위치])
        목록 += [(f"합성곱{번호}.가중치", 가중치), (f"합성곱{번호}.편향", 편향)]
    for 번호, 위치 in enumerate([1, 4], start=1):
        층 = 모델.분류[위치]
        목록 += [(f"완전연결{번호}.가중치", 층.weight.detach().numpy().astype(np.float32)),
                 (f"완전연결{번호}.편향", 층.bias.detach().numpy().astype(np.float32))]
    return 목록


def 넘파이_순전파(텐서, 입력):
    """합친 가중치만으로 웹과 같은 순서의 계산을 합니다. 입력: (N,1,28,28) → 출력: (N,10) 점수"""
    값 = dict(텐서)
    x = torch.from_numpy(입력)
    for 번호 in range(1, 5):
        x = torch.nn.functional.conv2d(x, torch.from_numpy(값[f"합성곱{번호}.가중치"]),
                                       torch.from_numpy(값[f"합성곱{번호}.편향"]), padding=1).clamp_min(0)
        if 번호 in (2, 4):
            x = torch.nn.functional.max_pool2d(x, 2)
    x = x.flatten(1)
    x = (x @ torch.from_numpy(값["완전연결1.가중치"]).T + torch.from_numpy(값["완전연결1.편향"])).clamp_min(0)
    x = x @ torch.from_numpy(값["완전연결2.가중치"]).T + torch.from_numpy(값["완전연결2.편향"])
    return x.numpy()


def 메인():
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치_파일, map_location="cpu", weights_only=True))
    모델.eval()
    텐서 = 텐서_목록_만들기(모델)

    # 저장하기 전에 합친 가중치가 원래 모델과 같은 답을 내는지 확인합니다.
    생성기 = torch.Generator().manual_seed(0)
    시험_입력 = torch.randn(8, 1, 28, 28, generator=생성기)
    with torch.no_grad():
        기대 = 모델(시험_입력).numpy()
    실제 = 넘파이_순전파(텐서, 시험_입력.numpy())
    최대_차이 = float(np.abs(기대 - 실제).max())
    print(f"합친 모델과 원래 모델의 최대 차이: {최대_차이:.3e}")
    if 최대_차이 > 허용_오차:
        print(f"차이가 허용 오차 {허용_오차}를 넘어 저장하지 않습니다.")
        sys.exit(1)

    os.makedirs(웹_폴더, exist_ok=True)
    정보 = {"형식": "float32-le", "평균": 평균, "표준편차": 표준편차, "텐서": []}
    시작 = 0
    with open(os.path.join(웹_폴더, "가중치.bin"), "wb") as 파일:
        for 이름, 배열 in 텐서:
            파일.write(배열.astype("<f4").tobytes())
            정보["텐서"].append({"이름": 이름, "형상": list(배열.shape), "시작": 시작, "개수": int(배열.size)})
            시작 += int(배열.size)
    with open(os.path.join(웹_폴더, "가중치정보.json"), "w", encoding="utf-8") as 파일:
        json.dump(정보, 파일, ensure_ascii=False, indent=2)
    print(f"저장 완료 → 가중치.bin ({시작 * 4:,}바이트, 파라미터 {시작:,}개), 가중치정보.json (텐서 {len(텐서)}개)")


if __name__ == "__main__":
    메인()
