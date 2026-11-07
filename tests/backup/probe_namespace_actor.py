#!/usr/bin/env python3
"""Check whether a rootless namespace can run the distinct-UID backup actor."""
import json
import os
from pathlib import Path
import sys

from parent_policy import PrerequisiteError, mapped_distinct_id


def main():
    try:
        actor_id = mapped_distinct_id()
        uid_map = Path("/proc/self/uid_map").read_text().strip()
        gid_map = Path("/proc/self/gid_map").read_text().strip()
        before = os.getgroups()
        os.setgroups([])
        os.setgid(actor_id)
        os.setuid(actor_id)
        if os.getgroups() or os.getegid() != actor_id or os.geteuid() != actor_id:
            raise PrerequisiteError("distinct actor credentials were not established")
    except (OSError, PrerequisiteError) as error:
        print(f"missing-prerequisite: distinct namespace actor: {error}")
        return 1
    print(json.dumps({"status": "pass", "actor_id": actor_id,
                      "initial_groups": before, "final_groups": os.getgroups(),
                      "uid_map": uid_map, "gid_map": gid_map}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
