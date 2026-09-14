from typing import Dict, Any
from src.profiles.lab_profile import get_canonical_lab_profile
from src.profiles.university_practical_profile import get_university_practical_profile


def get_profile_by_name(name: str) -> Dict[str, Any]:
    """Retrieves a profile dictionary by name or selection key."""
    if "UNIVERSITY" in name.upper() or "PRACTICAL" in name.upper() or "CIC" in name.upper():
        return get_university_practical_profile()
    return get_canonical_lab_profile()


__all__ = ["get_canonical_lab_profile", "get_university_practical_profile", "get_profile_by_name"]
