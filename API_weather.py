"""
Open-Meteo API를 활용한 날씨 예보 프로그램
- 사용자에게 지역을 입력받음 (기본값: 서울)
- 오늘, 내일, 모레까지 3일간의 날씨를 오전 6시, 오후 3시 기준으로 표시
- Open-Meteo API 사용 (인증키 불필요, 무료)
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any, Tuple

# Windows 콘솔 환경에서 한글 및 이모지 출력 안정화
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 한국 주요 도시 기본 좌표 (위도, 경도)
DEFAULT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "서울": (37.5665, 126.9780),
    "천안": (36.8151, 127.1139),
    "부산": (35.1796, 129.0756),
    "인천": (37.4563, 126.7052),
    "대구": (35.8714, 128.6014),
    "대전": (36.3504, 127.3845),
    "광주": (35.1595, 126.8526),
    "울산": (35.5384, 129.3114),
    "수원": (37.2636, 127.0286),
    "세종": (36.4800, 127.2890),
    "청주": (36.6424, 127.4890),
    "전주": (35.8242, 127.1480),
    "포항": (36.0190, 129.3435),
    "창원": (35.2281, 128.6811),
    "제주": (33.4996, 126.5312),
    "춘천": (37.8813, 127.7298),
    "강릉": (37.7519, 128.8761),
}


def get_coordinates(location_name: str) -> Optional[Tuple[float, float]]:
    """입력받은 지역명의 위도와 경도를 반환합니다.
    기본 딕셔너리에 없으면 Open-Meteo Geocoding API를 사용하여 검색합니다.
    """
    clean_name = location_name.strip()
    if not clean_name:
        clean_name = "서울"

    # 1. 사전 정의된 주요 도시 확인
    for city, coords in DEFAULT_COORDINATES.items():
        if clean_name == city or clean_name in city or city in clean_name:
            return coords

    # 2. Open-Meteo Geocoding API 호출
    geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": clean_name,
        "count": 5,
        "language": "ko",
        "format": "json"
    }

    try:
        response = requests.get(geocoding_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        # 대한민국(KR) 우선 검색
        for item in results:
            if item.get("country_code") == "KR":
                return round(item["latitude"], 4), round(item["longitude"], 4)

        # 첫 번째 결과 사용
        first = results[0]
        return round(first["latitude"], 4), round(first["longitude"], 4)
    except Exception as e:
        print(f"좌표 검색 중 오류 발생: {e}")
        return None


if __name__ == "__main__":
    loc = input("날씨를 확인할 지역을 입력하세요 (기본값: 서울): ").strip() or "서울"
    coords = get_coordinates(loc)
    if coords:
        print(f"📍 {loc} (위도: {coords[0]}, 경도: {coords[1]}) 의 날씨 정보를 가져옵니다...")
    else:
        print(f"❌ '{loc}' 지역의 좌표를 찾을 수 없습니다.")
