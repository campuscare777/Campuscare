"""
HostelCare – Hostel location master config and complaint category list.
Used by API and frontend dropdowns.
"""

# Three hostel types supported
HOSTEL_TYPES = [
    "Boys Hostel",
    "Girls Hostel",
    "NRI Hostel",
]

# Per-hostel location structure: blocks with their floors and common areas
HOSTEL_LOCATIONS = {
    "Boys Hostel": {
        "blocks": ["Block A", "Block B", "Block C", "Block D"],
        "floors": ["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor"],
        "areas": ["Lobby", "Corridor", "Washroom", "Common Room", "Dining Area", "Gym", "Study Room"],
        "common_areas": ["Lobby", "Corridor", "Washroom", "Common Room", "Dining Area", "Gym", "Study Room"],
    },
    "Girls Hostel": {
        "blocks": ["Block E", "Block F", "Block G"],
        "floors": ["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor"],
        "areas": ["Lobby", "Corridor", "Washroom", "Common Room", "Dining Area", "Study Room"],
        "common_areas": ["Lobby", "Corridor", "Washroom", "Common Room", "Dining Area", "Study Room"],
    },
    "NRI Hostel": {
        "blocks": ["NRI Wing A", "NRI Wing B"],
        "floors": ["Ground Floor", "1st Floor", "2nd Floor"],
        "areas": ["Lobby", "Corridor", "Washroom", "Common Room", "Dining Area"],
        "common_areas": ["Lobby", "Corridor", "Washroom", "Common Room", "Dining Area"],
    },
}

# Complaint categories as defined in HOSTELCARE-F001
COMPLAINT_CATEGORIES = [
    "Electrical",
    "Plumbing",
    "Cleanliness",
    "Food/Mess",
    "Internet/Network",
    "Furniture",
    "Pest Control",
    "Water Supply",
    "Other",
]

# Backward-compat alias (used by the /locations endpoint if still referenced)
CAMPUS_LOCATIONS = [
    {"id": h.lower().replace(" ", "_"), "name": h, "building": h, "zone": "Residential Zone"}
    for h in HOSTEL_TYPES
]
