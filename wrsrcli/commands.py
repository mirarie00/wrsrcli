"""Implementations for the wrsrcli subcommands."""

import datetime
import sys
from pathlib import Path

from . import config, scan, steam, table
from .errors import WrsrcliError

# Verbatim per SPEC.md 4.2 — do not reword.
NO_API_KEY_MESSAGE = """Steam Web API key has not been set. To retrieve metadata from Steam, please obtain an API key from:
   https://steamcommunity.com/dev/apikey

wrsrcli will now build an HTML table of your assets using workshopconfig.ini."""

SAVE_PROMPT = (
    "Please enter path to save folder, or press ENTER to use Documents. "
    "The filename will be WRSR Assets.html: "
)

COLLISION_PROMPT = """WRSR Assets.html found. Do you want to:
   1. Overwrite the current file
   2. Append a timestamp to the new file

Please select: """

OUTPUT_NAME = "WRSR Assets.html"


def _store_path(key, raw, label):
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise WrsrcliError(f"{path} is not an existing directory.")
    resolved = path.resolve()
    config.set_value(key, str(resolved))
    print(f"{label} path set to: {resolved}")


def resolve_path(key, detector):
    """A configured path if set, else autodetect and store it.

    SPEC.md 3: autodetection is attempted automatically the first time
    paths are needed if none are set; explicit values always win.
    """
    stored = config.get(key)
    if stored:
        return Path(stored)
    detected = detector()
    config.set_value(key, str(detected))
    return detected


def resolve_game_path():
    return resolve_path(config.GAME_PATH, steam.game_path)


def resolve_workshop_path():
    return resolve_path(config.WORKSHOP_PATH, steam.workshop_path)


def cmd_api(args):
    if args.remove:
        if args.key:
            raise WrsrcliError("`api --remove` does not take a key.")
        if config.remove(config.API_KEY):
            print("Steam Web API key removed.")
        else:
            print("No Steam Web API key was stored.")
        return 0

    if args.key:
        config.set_value(config.API_KEY, args.key)
        print(f"Steam Web API key stored in {config.config_path()}")
        return 0

    # No key and no --remove: report whether one is stored. The key itself
    # is never echoed back.
    if config.get(config.API_KEY):
        print("A Steam Web API key is stored.")
    else:
        print("No Steam Web API key is stored.")
    return 0


def cmd_scan(args):
    workshop_path = resolve_workshop_path()
    acf_path = steam.workshop_acf()
    if not acf_path.exists():
        raise WrsrcliError(f"{acf_path} not found — no workshop data to scan.")

    entries, warnings = scan.build(workshop_path, acf_path)

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    path = scan.write_manifest(entries)
    print(f"Scanned {len(entries)} installed item(s) from {workshop_path}")
    print(f"Manifest written to {path}")
    return 0


def _prompt_save_folder():
    raw = input(SAVE_PROMPT).strip().strip('"')
    folder = Path(raw).expanduser() if raw else Path.home() / "Documents"
    if not folder.is_dir():
        raise WrsrcliError(f"{folder} is not an existing directory.")
    return folder


def _resolve_output(folder):
    """The file to write, applying SPEC.md 4.2's collision prompt."""
    target = folder / OUTPUT_NAME
    if not target.exists():
        return target

    while True:
        choice = input(COLLISION_PROMPT).strip()
        if choice == "1":
            return target
        if choice == "2":
            stamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M")
            return folder / f"WRSR Assets {stamp}.html"
        print("Please enter 1 or 2.")


def cmd_output_table(args):
    if not config.get(config.API_KEY):
        print(NO_API_KEY_MESSAGE)
        print()
    else:
        # Phase 5 adds Web API enrichment; until then a stored key changes
        # nothing about the output, and saying so beats implying otherwise.
        print(
            "A Steam Web API key is stored, but Steam Web API enrichment is not "
            "implemented yet — building from local data only."
        )
        print()

    entries = table.load_manifest()
    rows = table.build_rows(entries, resolve_workshop_path())

    destination = _resolve_output(_prompt_save_folder())
    try:
        destination.write_text(table.render(rows), encoding="utf-8")
    except OSError as exc:
        raise WrsrcliError(f"could not write {destination}: {exc}") from exc

    print(f"Wrote {len(rows)} row(s) to {destination}")
    return 0


def cmd_path(args):
    acted = False

    if args.auto_detect:
        # Detect first, so that an explicit -g/-w in the same invocation
        # overrides the detected value (SPEC.md 3).
        steam_root = steam.steam_path()
        print(f"Steam install: {steam_root}")

        detected_game = steam.game_path()
        config.set_value(config.GAME_PATH, str(detected_game))
        print(f"Game path detected: {detected_game}")

        detected_workshop = steam.workshop_path()
        config.set_value(config.WORKSHOP_PATH, str(detected_workshop))
        print(f"Workshop path detected: {detected_workshop}")
        acted = True

    if args.game:
        _store_path(config.GAME_PATH, args.game, "Game")
        acted = True

    if args.workshop:
        _store_path(config.WORKSHOP_PATH, args.workshop, "Workshop")
        acted = True

    if not acted:
        data = config.load()
        print(f"Game path:     {data.get(config.GAME_PATH) or '(not set)'}")
        print(f"Workshop path: {data.get(config.WORKSHOP_PATH) or '(not set)'}")

    return 0
