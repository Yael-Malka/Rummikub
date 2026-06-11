"""List Roboflow project versions — useful for checking API access."""

import getpass
import sys
from roboflow import Roboflow

PROJECTS = [
    ("snips",                "rummikub-solver"),
    ("ahmet-aksnger",        "rummy-tiles-detector"),
    ("konstantin-elenik",    "rummy"),
    ("mahesha-itna-c-lhxlt", "rummy-6wacm"),
]

def main():
    api_key = getpass.getpass("Roboflow API key: ").strip()
    if not api_key:
        print("ERROR: no key entered")
        sys.exit(1)

    rf = Roboflow(api_key=api_key)

    for workspace, project_name in PROJECTS:
        print(f"\n{'='*50}")
        print(f"  {workspace}/{project_name}")
        print(f"{'='*50}")
        try:
            project  = rf.workspace(workspace).project(project_name)
            print(f"  Name    : {project.name}")
            print(f"  Type    : {project.type}")
            versions = project.versions()
            print(f"  Versions: {len(versions)}")
            for v in versions:
                print(f"    - v{v.version}  exports: {getattr(v, 'exports', 'unknown')}")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    main()
