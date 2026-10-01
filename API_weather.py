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

# WMO 날씨 해석 코드 매핑 (Open-Meteo Weather interpretation codes)
WEATHER_CODES: Dict[int, str] = {
    0: "맑음",
    1: "주로 맑음",
    2: "구름 많음",
    3: "흐림",
    45: "안개",
    48: "착빙성 안개",
    51: "약한 이슬비",
    53: "보통 이슬비",
    55: "강한 이슬비",
    56: "약한 어는 이슬비",
    57: "강한 어는 이슬비",
    61: "약한 비",
    63: "보통 비",
    65: "강한 비",
    66: "약한 어는 비",
    67: "강한 어는 비",
    71: "약한 눈",
    73: "보통 눈",
    75: "강한 눈",
    77: "싸락눈",
    80: "약한 소나기",
    81: "보통 소나기",
    82: "강한 소나기",
    85: "약한 눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "약한 우박을 동반한 뇌우",
    99: "강한 우박을 동반한 뇌우",
}


def get_weather_desc(code: int) -> str:
    """WMO 날씨 코드를 한글 설명으로 변환합니다."""
    return WEATHER_CODES.get(code, "맑음")


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


def fetch_weather(lat: float, lon: float, days: int = 3) -> Optional[Dict[str, Any]]:
    """Open-Meteo API를 호출하여 날씨 예보 데이터를 가져옵니다."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "weather_code",
            "wind_speed_10m",
        ],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
        ],
        "wind_speed_unit": "ms",
        "timezone": "Asia/Seoul",
        "forecast_days": days,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"날씨 정보를 가져오는 중 오류 발생: {e}")
        return None


def display_weather_forecast(location: str, weather_data: Dict[str, Any]) -> None:
    """가져온 날씨 예보 데이터를 보기 쉬운 형식으로 터미널에 출력합니다."""
    hourly = weather_data.get("hourly", {})
    daily = weather_data.get("daily", {})

    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    precip_probs = hourly.get("precipitation_probability", [])
    codes = hourly.get("weather_code", [])
    wind_speeds = hourly.get("wind_speed_10m", [])

    daily_times = daily.get("time", [])
    daily_max = daily.get("temperature_2m_max", [])
    daily_min = daily.get("temperature_2m_min", [])

    day_labels = ["오늘", "내일", "모레"]

    print("\n" + "=" * 60)
    print(f"📍 {location} 날씨 예보 (오전 6시 / 오후 3시 기준)")
    print("=" * 60)

    # 3일간 예보 출력
    for day_idx in range(min(len(day_labels), len(daily_times))):
        date_str = daily_times[day_idx]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%m.%d.")
        label = day_labels[day_idx]

        print(f"\n📅 {label} ({formatted_date})")
        print("-" * 40)

        # 오전 06:00 및 오후 15:00 찾기
        target_morning = f"{date_str}T06:00"
        target_afternoon = f"{date_str}T15:00"

        # 오전 06:00 출력
        if target_morning in times:
            idx = times.index(target_morning)
            w_desc = get_weather_desc(codes[idx])
            t = round(temps[idx])
            pop = precip_probs[idx]
            rh = humidities[idx]
            ws = round(wind_speeds[idx])

            print("🌅 오전 06:00")
            print(f"  날씨: {w_desc}")
            print(f"  기온: {t} ℃")
            print(f"  강수확률: {pop}%")
            print(f"  습도: {rh}%")
            print(f"  풍속: {ws} m/s")

        print()

        # 오후 15:00 출력
        if target_afternoon in times:
            idx = times.index(target_afternoon)
            w_desc = get_weather_desc(codes[idx])
            t = round(temps[idx])
            pop = precip_probs[idx]
            rh = humidities[idx]
            ws = round(wind_speeds[idx])

            print("🌇 오후 15:00")
            print(f"  날씨: {w_desc}")
            print(f"  기온: {t} ℃")
            print(f"  강수확률: {pop}%")
            print(f"  습도: {rh}%")
            print(f"  풍속: {ws} m/s")

        # 일일 최저 / 최고 기온 출력
        d_min = round(daily_min[day_idx])
        d_max = round(daily_max[day_idx])
        print(f"\n🌡️ 일일 기온: 최저 {d_min} ℃ / 최고 {d_max} ℃")
        print("\n" + "=" * 60)


def save_weather_to_json(location: str, weather_data: Dict[str, Any]) -> str:
    """조회된 날씨 정보를 weather_{지역}_{YYYYMMDD_HHMMSS}.json 파일로 저장합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"weather_{location}_{timestamp}.json"

    export_data = {
        "location": location,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_weather_data": weather_data,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    return filename


if __name__ == "__main__":
    print("☀️ 날씨 예보 프로그램 (Open-Meteo API)")
    print("-" * 40)
    print("오전 6시, 오후 3시 기준으로 3일간 날씨를 제공합니다.\n")

    user_input = input("날씨를 확인할 지역을 입력하세요 (기본값: 서울): ").strip()
    location = user_input if user_input else "서울"

    coords = get_coordinates(location)
    if not coords:
        print(f"❌ '{location}' 지역을 찾을 수 없습니다. 프로그램을 종료합니다.")
        sys.exit(1)

    lat, lon = coords
    print(f"📍 {location} (위도: {lat}, 경도: {lon}) 의 날씨 정보를 가져옵니다...")

    weather_data = fetch_weather(lat, lon, days=3)
    if weather_data:
        display_weather_forecast(location, weather_data)

        # JSON 저장 여부 묻기
        save_choice = input("\n날씨 정보를 JSON 파일로 저장하시겠습니까? (y/n): ").strip().lower()
        if save_choice == "y":
            saved_file = save_weather_to_json(location, weather_data)
            print(f"💾 날씨 정보가 {saved_file} 파일로 저장되었습니다.")
    else:
        print("❌ 날씨 정보를 가져오는데 실패했습니다.")
