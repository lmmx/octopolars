"""Retrieve a GitHub auth token from `gh`."""

import os
import subprocess


ENV_GH_TOKEN = os.getenv("GH_TOKEN")
if ENV_GH_TOKEN is None:
    try:
        tokproc = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
        )
        ENV_GH_TOKEN = tokproc.stdout.strip()
    except Exception:
        print("No token, file listings not available and repo listings rate limited")
