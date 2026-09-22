# -*- coding: utf-8 -*-
"""
바로가기와 앱 창에 쓸 아이콘(icon.ico)을 만듭니다.
실행 방법: python make_icon.py
"""
from PIL import Image, ImageDraw, ImageFont

아이콘_파일 = "icon.ico"
기준_크기 = 256  # 가장 큰 크기로 그린 뒤 작은 크기들은 자동으로 줄여서 만듭니다.


def 글꼴_불러오기(크기):
    """윈도우 기본 굵은 글꼴을 쓰고, 없으면 PIL 기본 글꼴을 씁니다."""
    for 경로 in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/malgunbd.ttf"):
        try:
            return ImageFont.truetype(경로, 크기)
        except OSError:
            pass
    return ImageFont.load_default(크기)


def 아이콘_그리기():
    그림 = Image.new("RGBA", (기준_크기, 기준_크기), (0, 0, 0, 0))
    붓 = ImageDraw.Draw(그림)

    # 파란색 둥근 사각형 바탕
    붓.rounded_rectangle([8, 8, 248, 248], radius=48, fill=(25, 118, 210, 255))

    # 가운데에 흰색 숫자 "7"
    글꼴 = 글꼴_불러오기(190)
    붓.text((128, 136), "7", font=글꼴, fill="white", anchor="mm")

    # 오른쪽 아래에 연필 모양 (손글씨 느낌)
    붓.line([(172, 222), (232, 162)], fill=(255, 193, 7, 255), width=22)  # 연필 몸통
    붓.polygon([(164, 230), (160, 214), (178, 228)], fill=(60, 60, 60, 255))  # 연필 심
    return 그림


if __name__ == "__main__":
    아이콘_그리기().save(아이콘_파일, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"아이콘 저장 완료 → {아이콘_파일}")
