#!/usr/bin/env python3
"""Check whether a rootless namespace can run the distinct-UID backup actor."""
import json
import errno
import os
from pathlib import Path
import re
import sys

from parent_policy import InfrastructureError, PrerequisiteError, select_distinct_id


MISSING_PREFIX = "missing-prerequisite: distinct namespace actor: "
PREREQUISITE_ERRNOS = {errno.EPERM, errno.EACCES, errno.ENOENT,
                       errno.ENOSYS, errno.EOPNOTSUPP, errno.EINVAL}


def is_known_missing(status, output):
    return status == 1 and re.fullmatch(re.escape(MISSING_PREFIX) + r"[^\n]+\n?", output) is not None


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--is-missing-log":
        try:
            return 0 if is_known_missing(int(sys.argv[2]), Path(sys.argv[3]).read_text()) else 1
        except (OSError, ValueError):
            return 2
    if len(sys.argv) != 1:
        print("infrastructure-failure: invalid namespace probe arguments")
        return 2
    stage = "namespace maps"
    try:
        uid_map = Path("/proc/self/uid_map").read_text().strip()
        gid_map = Path("/proc/self/gid_map").read_text().strip()
        actor_id = select_distinct_id(uid_map, gid_map)
        stage = "supplementary groups"
        before = os.getgroups()
        os.setgroups([])
        stage = "primary GID"
        os.setgid(actor_id)
        stage = "primary UID"
        os.setuid(actor_id)
        if os.getgroups() or os.getegid() != actor_id or os.geteuid() != actor_id:
            raise PrerequisiteError("distinct actor credentials were not established")
    except PrerequisiteError as error:
        print(f"{MISSING_PREFIX}{error}")
        return 1
    except InfrastructureError as error:
        print(f"infrastructure-failure: distinct namespace actor {stage}: {error}")
        return 2
    except OSError as error:
        if error.errno in PREREQUISITE_ERRNOS:
            print(f"{MISSING_PREFIX}{stage}: {error}")
            return 1
        print(f"infrastructure-failure: distinct namespace actor {stage}: {error}")
        return 2
    print(json.dumps({"status": "pass", "actor_id": actor_id,
                      "initial_groups": before, "final_groups": os.getgroups(),
                      "uid_map": uid_map, "gid_map": gid_map}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
