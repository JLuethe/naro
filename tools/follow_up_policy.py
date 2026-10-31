"""Compatibility entry point; recompute recordings, never trust a supplied diff."""
from identity_review import classify


def deviation(tid, reference, candidate, differences):
    try:
        result = classify(reference, candidate, case_id=tid)
    except (KeyError, TypeError, ValueError, IndexError):
        return None
    if differences != result['differences']:
        return None
    return result['deviation_id'] if result['accepted'] and result['declared_deviation'] else None
