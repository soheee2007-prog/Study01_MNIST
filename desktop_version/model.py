# -*- coding: utf-8 -*-
"""
MNIST 손글씨 숫자 인식을 위한 합성곱 신경망(CNN) 모델 정의
학습 코드(train.py)와 인식 프로그램(app.py)이 함께 사용합니다.
"""
import torch.nn as nn

# 학습된 가중치를 저장/불러올 파일 이름
가중치_파일 = "mnist_cnn.pt"

# MNIST 데이터셋의 평균과 표준편차 (입력 정규화에 사용)
평균 = 0.1307
표준편차 = 0.3081


class 숫자인식CNN(nn.Module):
    """입력: 1×28×28 흑백 이미지 → 출력: 숫자 0~9 각각의 점수(10개)"""

    def __init__(self):
        super().__init__()
        # 특징 추출부: 합성곱 → 배치정규화 → ReLU → 최대 풀링을 두 번 반복
        self.특징추출 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),   # 1×28×28 → 32×28×28
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),  # 32×28×28 유지
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),                              # → 32×14×14

            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # → 64×14×14
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),  # 64×14×14 유지
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),                              # → 64×7×7
        )
        # 분류부: 펼친 뒤 완전연결층으로 10개 클래스 점수 계산
        self.분류 = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.5),  # 과적합 방지
            nn.Linear(128, 10),
        )

    def forward(self, 입력):
        return self.분류(self.특징추출(입력))
