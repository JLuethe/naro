"""Named legacy differences; identity review stays separate from raw matching."""
from identity_review import legacy_deviation


def deviation(tid, reference, candidate, differences):
    return legacy_deviation(tid, reference, candidate, differences)
