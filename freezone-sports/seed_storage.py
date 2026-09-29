"""Seed script for FreeZone Sports storage with initial preferences and sample tours."""

from app.storage import (
    FIRESTORE_PROJECT,
    save_user_preference,
    plan_tour,
    record_match_result,
    get_user_preferences,
    get_planned_tours,
    get_match_results,
    get_media_bucket_info,
)

print(f"--> Seeding Firestore database for project: {FIRESTORE_PROJECT}")

# Seed user preferences
print(save_user_preference("favorite_teams", "handball_club", "THW Kiel"))
print(save_user_preference("favorite_teams", "nfl_team", "Kansas City Chiefs"))
print(save_user_preference("motorbikes", "primary_ride", "Yamaha Tenere 700"))
print(save_user_preference("bicycles", "gravel_road", "Canyon Grizl CF SL"))
print(save_user_preference("hiking_preferences", "experience_level", "Alpine Advanced (T3/T4)"))

# Seed planned tours with metric values
print(plan_tour(
    title="Stelvio Pass Motorbike Traverse",
    activity_type="motorbike",
    location="Ortler Alps, Italy",
    distance_km=48.5,
    elevation_m=1870.0,
    notes="48 hairpin turns on the northeastern ramp. Bring thermal layers for summit at 2757 m."
))

print(plan_tour(
    title="Tre Cime di Lavaredo Circuit Hike",
    activity_type="hiking",
    location="Sexten Dolomites, Italy",
    distance_km=9.8,
    elevation_m=430.0,
    notes="Classic Alpine loop from Rifugio Auronzo. Spectacular limestone towers view."
))

print(plan_tour(
    title="Sella Ronda Cycling Loop",
    activity_type="cycling",
    location="Dolomites, Italy",
    distance_km=52.0,
    elevation_m=1650.0,
    notes="Clockwise route over Campolongo, Pordoi, Sella, and Gardena passes."
))

# Seed match results
print(record_match_result("Handball", "THW Kiel", "SG Flensburg-Handewitt", "28 - 27", "Nordderby thriller victory"))
print(record_match_result("NFL", "Kansas City Chiefs", "San Francisco 49ers", "28 - 18", "Regular season matchup"))

print("\n--- Current Seeded State ---")
print("Preferences:", get_user_preferences())
print(f"Total Planned Tours: {len(get_planned_tours())}")
print(f"Total Match Results: {len(get_match_results())}")
print(get_media_bucket_info())
print("Seeding completed successfully!")
