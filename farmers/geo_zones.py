"""Best-effort, offline classification of a Kenyan farm location into a county
and a recommended subset of farming activities.

DRAFT — not sourced from an official KALRO agro-ecological zone map or county
boundary data. County centroids below are approximate (decimal degrees,
hand-authored from general geography), used only for nearest-centroid
matching — this is a rough classification, not a point-in-polygon lookup
against real county boundaries. The ASAL (arid/semi-arid) and
fisheries-plausible county lists are drawn from general, publicly reported
knowledge of Kenya's geography and drought classifications, which themselves
vary by source (official counts range from 23 to 29 ASAL counties). Treat
every list and mapping in this module as a draft for MoFirms to verify or
correct — do not treat it as an authoritative agronomic source.

Deliberately offline: classifying from the pin's lat/long locally, rather
than calling a third-party reverse-geocoding API, avoids sending a farmer's
exact location to an outside service and keeps the WhatsApp webhook's
response fast and dependency-free.
"""

# (latitude, longitude) approximate centroids, decimal degrees.
COUNTY_CENTROIDS = {
    "Mombasa": (-4.05, 39.67),
    "Kwale": (-4.18, 39.45),
    "Kilifi": (-3.51, 39.85),
    "Tana River": (-1.65, 40.10),
    "Lamu": (-2.27, 40.90),
    "Taita-Taveta": (-3.40, 38.35),
    "Garissa": (-0.45, 39.65),
    "Wajir": (1.75, 40.05),
    "Mandera": (3.52, 40.97),
    "Marsabit": (2.33, 37.98),
    "Isiolo": (0.35, 38.20),
    "Meru": (0.05, 37.65),
    "Tharaka-Nithi": (-0.30, 37.80),
    "Embu": (-0.54, 37.45),
    "Kitui": (-1.37, 38.01),
    "Machakos": (-1.52, 37.27),
    "Makueni": (-1.80, 37.62),
    "Nyandarua": (-0.18, 36.52),
    "Nyeri": (-0.42, 36.95),
    "Kirinyaga": (-0.66, 37.28),
    "Murang'a": (-0.78, 37.05),
    "Kiambu": (-1.03, 36.83),
    "Turkana": (3.12, 35.60),
    "West Pokot": (1.62, 35.39),
    "Samburu": (1.17, 36.95),
    "Trans Nzoia": (1.02, 35.00),
    "Uasin Gishu": (0.55, 35.30),
    "Elgeyo-Marakwet": (0.80, 35.50),
    "Nandi": (0.18, 35.18),
    "Baringo": (0.60, 35.97),
    "Laikipia": (0.40, 36.78),
    "Nakuru": (-0.30, 36.07),
    "Narok": (-1.08, 35.87),
    "Kajiado": (-2.10, 36.78),
    "Kericho": (-0.37, 35.29),
    "Bomet": (-0.78, 35.34),
    "Kakamega": (0.28, 34.75),
    "Vihiga": (0.07, 34.72),
    "Bungoma": (0.56, 34.56),
    "Busia": (0.46, 34.11),
    "Siaya": (0.06, 34.29),
    "Kisumu": (-0.10, 34.75),
    "Homa Bay": (-0.53, 34.46),
    "Migori": (-1.06, 34.47),
    "Kisii": (-0.68, 34.77),
    "Nyamira": (-0.57, 34.94),
    "Nairobi City": (-1.29, 36.82),
}

# Predominantly arid/semi-arid, pastoral-dominant counties, per general NDMA/
# drought reporting (see module docstring: official ASAL lists vary 23-29
# counties; this is a conservative subset of the most unambiguously arid ones).
HARD_ASAL_COUNTIES = {
    "Turkana", "Marsabit", "Mandera", "Wajir", "Garissa",
    "Samburu", "West Pokot", "Isiolo", "Tana River",
}

# Coastal (Indian Ocean) or adjacent to a major lake, where fisheries is a
# realistic activity.
FISHERIES_COUNTIES = {
    "Mombasa", "Kwale", "Kilifi", "Lamu", "Tana River",  # coast
    "Kisumu", "Siaya", "Homa Bay", "Migori",  # Lake Victoria
    "Turkana",  # Lake Turkana
    "Baringo",  # Lake Baringo
    "Nakuru",  # Lake Naivasha / Nakuru
}

_ASAL_BASE_ACTIVITIES = ["livestock", "dairy", "poultry", "beekeeping", "other"]
_DEFAULT_BASE_ACTIVITIES = [
    "crops", "livestock", "dairy", "poultry", "horticulture",
    "beekeeping", "agroforestry", "other",
]


def nearest_county(latitude, longitude):
    """Return the county whose approximate centroid is closest to the given
    point. Simple nearest-neighbour over hand-authored centroids — a rough
    classification, not a precise boundary lookup."""
    best_county = None
    best_distance = None
    for county, (county_lat, county_lon) in COUNTY_CENTROIDS.items():
        distance = (latitude - county_lat) ** 2 + (longitude - county_lon) ** 2
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_county = county
    return best_county


def recommended_activities(county):
    """Return the subset of ACTIVITY_CHOICES keys considered plausible for
    this county, as a draft recommendation — always includes 'other'."""
    base = _ASAL_BASE_ACTIVITIES if county in HARD_ASAL_COUNTIES else _DEFAULT_BASE_ACTIVITIES
    activities = list(base)
    if county in FISHERIES_COUNTIES and "fisheries" not in activities:
        activities.append("fisheries")
    return activities
