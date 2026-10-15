import re

from flask import Flask, render_template, request
import requests

app = Flask(__name__)

SAN_JOSE_LAT = 37.3382
SAN_JOSE_LON = -121.8863
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ZIP_URL = "https://api.zippopotam.us/us/{zip}"

# WMO weather interpretation codes used by Open-Meteo
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_current_weather(lat=SAN_JOSE_LAT, lon=SAN_JOSE_LON):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "temperature_unit": "fahrenheit",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=10)
    response.raise_for_status()
    current = response.json()["current"]
    return {
        "temperature": round(current["temperature_2m"]),
        "description": WEATHER_CODES.get(current["weather_code"], "Unknown"),
    }


def lookup_zip(zip_code):
    """Return the place name and coordinates for a US zip code, or None if it does not exist."""
    response = requests.get(ZIP_URL.format(zip=zip_code), timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    place = response.json()["places"][0]
    return {
        "name": f"{place['place name']}, {place['state']}",
        "lat": float(place["latitude"]),
        "lon": float(place["longitude"]),
    }


@app.route("/")
def index():
    try:
        weather = get_current_weather()
        error = None
    except (requests.RequestException, KeyError, ValueError):
        weather = None
        error = "Could not load the weather right now. Please try again later."
    return render_template("index.html", weather=weather, error=error)


@app.route("/zip")
def zip_weather():
    zip_code = request.args.get("zip", "").strip()
    place = weather = error = None
    if zip_code:
        if not re.fullmatch(r"\d{5}", zip_code):
            error = "Please enter a 5-digit US zip code."
        else:
            try:
                place = lookup_zip(zip_code)
                if place is None:
                    error = f"Zip code {zip_code} does not exist."
                else:
                    weather = get_current_weather(place["lat"], place["lon"])
            except (requests.RequestException, KeyError, IndexError, ValueError):
                place = None
                error = "Could not load the weather right now. Please try again later."
    return render_template(
        "zip.html", zip_code=zip_code, place=place, weather=weather, error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
