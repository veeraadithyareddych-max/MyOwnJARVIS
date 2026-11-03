
# MyOwnJARVIS - Application Tools
# Tools return structured results so the agent can detect success or failure.

import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import json
import math

# --------------------------------------------------
# 1. STRUCTURED RESULT FORMAT
# --------------------------------------------------


def tool_result(success, tool, data=None, error=None):
    """Create a structured tool result with an execution status."""

    if success:
        status = "accepted"
    else:
        status = "failed"

    return {
        "success": success,
        "tool": tool,
        "data": data,
        "error": error,
        "status": status,
    }



# --------------------------------------------------
# 2. APPROVED WINDOWS APPLICATIONS
# --------------------------------------------------

ALLOWED_APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
}


def open_application(app_name):
    """Open an approved Windows application."""

    if not isinstance(app_name, str) or not app_name.strip():
        return tool_result(
            False, "open_application",
            error="Please provide an application name."
        )

    app_name = app_name.lower().strip()

    if app_name not in ALLOWED_APPS:
        return tool_result(
            False,
            "open_application",
            error=(
                f"Cannot open '{app_name}'. "
                "Available applications: Notepad, Calculator, Paint."
            ),
        )

    try:
        subprocess.Popen(ALLOWED_APPS[app_name])

        return tool_result(
            True,
            "open_application",
            data=f"{app_name.title()} has been opened successfully.",
        )

    except OSError as error:
        return tool_result(
            False,
            "open_application",
            error=f"Could not open {app_name.title()}: {error}",
        )


# --------------------------------------------------
# 3. APPROVED WEBSITES
# --------------------------------------------------

ALLOWED_WEBSITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
}


def open_website(site_name):
    """Open an approved website in the default browser."""

    if not isinstance(site_name, str) or not site_name.strip():
        return tool_result(
            False, "open_website",
            error="Please provide a website name."
        )

    site_name = site_name.lower().strip()

    if site_name not in ALLOWED_WEBSITES:
        return tool_result(
            False,
            "open_website",
            error=(
                f"Cannot open '{site_name}'. "
                "Available websites: Google, YouTube, GitHub."
            ),
        )

    try:
        opened = webbrowser.open(ALLOWED_WEBSITES[site_name])

        if not opened:
            return tool_result(
                False,
                "open_website",
                error=f"Your browser did not confirm opening {site_name.title()}.",
            )

        return tool_result(
            True,
            "open_website",
            data=f"Opening {site_name.title()} in your browser.",
        )

    except Exception as error:
        return tool_result(
            False,
            "open_website",
            error=f"Could not open {site_name.title()}: {error}",
        )


# --------------------------------------------------
# 4. INTERNET CONNECTION CHECK
# --------------------------------------------------

def check_internet():
    """Check whether an internet connection is available."""

    url = "https://www.google.com"

    try:
        request = urllib.request.Request(url, method="HEAD")

        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status < 400:
                return tool_result(
                    True,
                    "check_internet",
                    data="Your internet connection is working.",
                )

            return tool_result(
                False,
                "check_internet",
                error=f"Internet check returned HTTP status {response.status}.",
            )

    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return tool_result(
            False,
            "check_internet",
            error=f"Could not reach the internet: {error}",
        )


# --------------------------------------------------
# 5. WEATHER DATA HELPER
# --------------------------------------------------

def fetch_json(url, attempts=2):
    """Fetch JSON data, retrying once after a temporary failure."""

    last_error = None

    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))

        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
        ) as error:
            last_error = error

            if attempt < attempts - 1:
                print("Weather request failed. Retrying once...")

    raise last_error


# --------------------------------------------------
# 6. CURRENT WEATHER
# --------------------------------------------------

def get_weather(city):
    """Retrieve current weather data with limited retries."""

    if not isinstance(city, str) or not city.strip():
        return tool_result(
            False,
            "get_weather",
            error="Please provide a city name.",
        )

    city = city.strip()

    try:
        # Find the city's geographic coordinates.
        city_query = urllib.parse.urlencode({"name": city})

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + city_query
            + "&count=1&language=en&format=json"
        )

        location_data = fetch_json(geo_url)
        results = location_data.get("results", [])

        if not results:
            return tool_result(
                False,
                "get_weather",
                error=f"Could not find the city '{city}'.",
            )

        location = results[0]
        latitude = location["latitude"]
        longitude = location["longitude"]
        city_name = location["name"]

        # Request current weather.
        weather_query = urllib.parse.urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "wind_speed_10m"
            ),
        })

        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + weather_query
        )


        weather_data = fetch_json(weather_url)

        if not isinstance(weather_data, dict):
            return tool_result(
                False,
                "get_weather",
                error="The weather service returned an invalid response.",
            )

        current = weather_data.get("current")

        if not isinstance(current, dict):
            return tool_result(
                False,
                "get_weather",
                error="The weather service did not return current conditions.",
            )

        required_fields = (
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
        )

        missing_fields = [
            field for field in required_fields
            if field not in current or current[field] is None
        ]

        if missing_fields:
            return tool_result(
                False,
                "get_weather",
                error=(
                    "The weather service returned incomplete data. "
                    f"Missing fields: {', '.join(missing_fields)}."
                ),
            )

        temperature = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        wind_speed = current["wind_speed_10m"]

        for field, value in (
            ("temperature_2m", temperature),
            ("relative_humidity_2m", humidity),
            ("wind_speed_10m", wind_speed),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                return tool_result(
                    False,
                    "get_weather",
                    error=(
                        "The weather service returned an invalid "
                        f"value for {field}."
                    ),
                )

        if not 0 <= humidity <= 100:
            return tool_result(
                False,
                "get_weather",
                error="The weather service returned invalid humidity.",
            )

        if wind_speed < 0:
            return tool_result(
                False,
                "get_weather",
                error="The weather service returned invalid wind speed.",
            )


        weather_message = (
            f"Current weather for {city_name}: "
            f"{temperature}°C, "
            f"humidity {humidity}%, "
            f"wind speed {wind_speed} km/h."
        )

        return tool_result(
            True,
            "get_weather",
            data={
                "city": city_name,
                "temperature_celsius": temperature,
                "humidity_percent": humidity,
                "wind_speed_kmh": wind_speed,
                "message": weather_message,
            },
        )

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
    ) as error:
        return tool_result(
            False,
            "get_weather",
            error=f"Could not retrieve weather after retrying: {error}",
        )


# --------------------------------------------------
# 7. DIRECT TEST
# --------------------------------------------------

if __name__ == "__main__":
    print("MyOwnJARVIS Tool Test")
    print("1. Check internet")
    print("2. Get weather")
    print("3. Open application")
    print("4. Open website")

    choice = input("Choose an option (1-4): ").strip()

    if choice == "1":
        result = check_internet()

    elif choice == "2":
        city = input("Enter a city: ")
        result = get_weather(city)

    elif choice == "3":
        app_name = input("Enter Notepad, Calculator, or Paint: ")
        result = open_application(app_name)

    elif choice == "4":
        site_name = input("Enter Google, YouTube, or GitHub: ")
        result = open_website(site_name)

    else:
        result = tool_result(
            False,
            "tool_test",
            error="Invalid option. Choose a number from 1 to 4.",
        )

    print("\nTool result:")
    print(json.dumps(result, indent=4))
