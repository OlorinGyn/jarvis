"""Pass the Waiting views older versions left behind through the 40-view rule, once (backlog 28).

Usage: uv run python tools/settle_waiting.py [--dry-run]

Each waiting view, oldest first, enters Chosen while there is room, or in
place of the chosen view with the closest twin when it is more different
than that pair; every other one is deleted with its photo, and the queues
end empty. --dry-run writes nothing and prints what would happen. A real
run copies faces/ and dogs/ to backups/ first, and refuses while this
folder's J.A.R.V.I.S. is running: it writes the same files.
"""

import shutil
import sys
from datetime import datetime

from dotenv import dotenv_values

from jarvis import ROOT, dogs, faces, web

BACKUP_DIR = ROOT / "backups"


def galleries():
    return [("People", faces.Gallery()), ("Dogs", dogs.DogGallery())]


def backup(found):
    """Copy every gallery's folder to backups/waiting_<date-time>/ and return where."""
    target = BACKUP_DIR / f"waiting_{datetime.now():%Y%m%d-%H%M%S}"
    for _, gallery in found:
        folder = gallery.path.parent
        if folder.exists():
            shutil.copytree(folder, target / folder.name)
    return target


def report(title, rows):
    print(f"{title}:")
    if not rows:
        print("  nothing waiting")
    for row in rows:
        print(f"  {row['name'] or row['id']:24} {row['waiting']:3} waiting: {row['entered']:3} enter Chosen,"
              f" {row['discarded']:3} deleted; {row['pushed_out']:3} chosen views deleted to make room")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    dry_run = "--dry-run" in argv
    port = int(dotenv_values(ROOT / ".env").get("WEB_PORT") or web.PORT)
    if not dry_run and web.already_running(port):
        print(f"J.A.R.V.I.S. is running on port {port}: stop it first, or use --dry-run.")
        return 1
    migrated = None if dry_run else faces.migrate_gallery(backup_dir=BACKUP_DIR)
    if migrated:
        print(f"Face gallery rebuilt for {faces.EMBEDDING_MODEL} first: {migrated}")
    migrated = None if dry_run else dogs.migrate_gallery(backup_dir=BACKUP_DIR)
    if migrated:
        print(f"Dog gallery rebuilt for {dogs.EMBEDDING_MODEL} first: {migrated}")
    found = galleries()
    if dry_run:
        print("Dry run: nothing is written or deleted.")
    else:
        print(f"Copied to {backup(found)}")
    for title, gallery in found:
        report(title, gallery.settle_waiting(dry_run=dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
