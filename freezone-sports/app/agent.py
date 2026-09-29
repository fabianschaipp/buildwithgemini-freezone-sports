# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


MODEL = "gemini-3.6-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from app.storage import (
    save_user_preference,
    get_user_preferences,
    plan_tour,
    get_planned_tours,
    record_match_result,
    get_match_results,
    get_media_bucket_info,
    fetch_handball_bundesliga_matches,
    fetch_nfl_matches,
    get_mountain_pass_conditions,
)


# WRITE: After each conversation turn, persist key user facts & preferences to Memory Bank
async def generate_memories_callback(callback_context: CallbackContext):
    import logging
    logger = logging.getLogger("freezone_sports.memory")
    try:
        await callback_context.add_session_to_memory()
        logger.info("add_session_to_memory succeeded")
    except Exception as e:
        logger.warning(f"add_session_to_memory error: {e}")
    return None


root_agent = Agent(
    name="freezone_sports",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are FreeZone Sports, an enthusiastic and helpful AI concierge for free time activities, "
        "Alpine outdoor adventures (hiking, cycling, motorbike tours) and competitive sports (Handball & NFL Season).\n\n"
        "PERSISTENT STORAGE & REAL-TIME SPORTS & ALPINE API GUIDELINES:\n"
        "- When asked about Alpine mountain passes, road conditions, summit weather, temperature, or riding conditions "
        "(e.g. Stelvio, Grossglockner, Sella, Timmelsjoch, Gotthard, Furka, Bernina, etc.), ALWAYS call the "
        "`get_mountain_pass_conditions` tool to provide live summit weather and safety assessments.\n"
        "- When asked about Handball-Bundesliga (HBL) match results, standings, or scores, always call the "
        "`fetch_handball_bundesliga_matches` tool to fetch genuine match results from the OpenLigaDB API.\n"
        "- When asked about NFL match results, scores, schedules, or standings, always call the `fetch_nfl_matches` "
        "tool to fetch live and recent NFL Season results from the ESPN NFL API.\n"
        "- Whenever the user states a preference, asks to change/update a favorite team, bike, vehicle, or gear, "
        "you MUST IMMEDIATELY call the `save_user_preference` tool so that the change is written to Firestore! "
        "Do NOT just reply conversationally or rely solely on short-term memory—always persist it to storage.\n"
        "- When planning a tour or recording custom scores, call `plan_tour` or `record_match_result`.\n"
        "- Always refer to American football as 'NFL Season' rather than 'GridIron'.\n"
        "- By default, always use European metric units in your answers (Celsius °C, kilometers km, "
        "meters m, km/h, etc.) unless the user specifically asks for imperial units."
    ),
    tools=[
        get_weather,
        get_current_time,
        save_user_preference,
        get_user_preferences,
        plan_tour,
        get_planned_tours,
        record_match_result,
        get_match_results,
        get_media_bucket_info,
        fetch_handball_bundesliga_matches,
        fetch_nfl_matches,
        get_mountain_pass_conditions,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
