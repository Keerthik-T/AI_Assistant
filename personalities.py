# personalities.py

PERSONALITIES = {
    "furina": {
        "name": "Furina",
        "voice_id": "af_bella",  # High quality female voice profile matching Furina's theatrical style
        "description": "Lady Furina, the dramatic and theatrical former Hydro Archon of Fontaine."
    }
}

def get_personality(name: str) -> dict:
    """
    Retrieves the personality metadata for a given character name.
    Defaults to Furina's voice profile if not found.
    """
    key = name.lower().strip()
    return PERSONALITIES.get(key, {
        "name": name.capitalize(),
        "voice_id": "af_bella",
        "description": f"Custom profile for {name}."
    })
