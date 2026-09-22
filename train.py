# -*- coding: utf-8 -*-
"""
MNIST 데이터셋으로 CNN을 학습하고, 가중치를 mnist_cnn.pt로 저장합니다.
실행 방법: python train.py
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import 숫자인식CNN, 가중치_파일, 평균, 표준편차

# ===== 학습 설정 =====
에폭_수 = 5
배치_크기 = 128
학습률 = 1e-3
장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def 데이터_준비():
    """학습용/시험용 데이터 로더를 만듭니다. (처음 실행 시 ./data 폴더에 자동 다운로드)"""
    # 학습 데이터에는 약간의 회전·이동·확대를 주어 실제 손글씨에 더 강하게 만듭니다.
    학습_변환 = transforms.Compose([
        transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ])
    시험_변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ])
    학습_데이터 = datasets.MNIST("./data", train=True, download=True, transform=학습_변환)
    시험_데이터 = datasets.MNIST("./data", train=False, download=True, transform=시험_변환)
    학습_로더 = DataLoader(학습_데이터, batch_size=배치_크기, shuffle=True)
    시험_로더 = DataLoader(시험_데이터, batch_size=1000, shuffle=False)
    return 학습_로더, 시험_로더


def 한_에폭_학습(모델, 로더, 최적화기, 에폭):
    """데이터 전체를 한 번 돌며 모델을 학습합니다."""
    모델.train()
    for 번호, (이미지, 정답) in enumerate(로더):
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        최적화기.zero_grad()
        손실 = F.cross_entropy(모델(이미지), 정답)
        손실.backward()
        최적화기.step()
        if 번호 % 100 == 0:
            print(f"[에폭 {에폭}] {번호 * len(이미지):>5}/{len(로더.dataset)}  손실: {손실.item():.4f}")


@torch.no_grad()
def 평가(모델, 로더):
    """시험 데이터에 대한 평균 손실과 정확도(%)를 계산합니다."""
    모델.eval()
    전체_손실, 맞춘_개수 = 0.0, 0
    for 이미지, 정답 in 로더:
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        출력 = 모델(이미지)
        전체_손실 += F.cross_entropy(출력, 정답, reduction="sum").item()
        맞춘_개수 += (출력.argmax(dim=1) == 정답).sum().item()
    개수 = len(로더.dataset)
    return 전체_손실 / 개수, 100.0 * 맞춘_개수 / 개수


def 메인():
    print(f"사용 장치: {장치}")
    학습_로더, 시험_로더 = 데이터_준비()

    모델 = 숫자인식CNN().to(장치)
    최적화기 = torch.optim.Adam(모델.parameters(), lr=학습률)
    # 에폭마다 학습률을 조금씩 줄여 안정적으로 수렴하게 합니다.
    스케줄러 = torch.optim.lr_scheduler.StepLR(최적화기, step_size=1, gamma=0.7)

    최고_정확도 = 0.0
    for 에폭 in range(1, 에폭_수 + 1):
        한_에폭_학습(모델, 학습_로더, 최적화기, 에폭)
        시험_손실, 정확도 = 평가(모델, 시험_로더)
        print(f"==> 에폭 {에폭} 시험 결과: 평균 손실 {시험_손실:.4f}, 정확도 {정확도:.2f}%")
        스케줄러.step()

        # 가장 성능이 좋은 가중치를 저장합니다.
        if 정확도 > 최고_정확도:
            최고_정확도 = 정확도
            torch.save(모델.state_dict(), 가중치_파일)
            print(f"    가중치 저장 완료 → {가중치_파일}")

    print(f"학습 완료! 최고 시험 정확도: {최고_정확도:.2f}%")


if __name__ == "__main__":
    메인()
