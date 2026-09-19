"""Implementations for the wrsrcli subcommands."""

import datetime
import sys
from pathlib import Path

from . import config, scan, steam, steamapi, steamcmd, table
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

# Verbatim per SPEC.md 3 — do not reword.
STEAMCMD_PROMPT = """Press ENTER to automatically download and install steamcmd from Valve. If you prefer to download and install yourself, please open this link:
   https://developer.valvesoftware.com/wiki/SteamCMD
"""


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


def _enrich(key, entries):
    """Fetch Web API metadata. Returns (details, authors, api_mode).

    A failure here degrades to the local-only table rather than aborting a
    run that can still produce useful output (decision D-007).
    """
    item_ids = [e["item_id"] for e in entries if e.get("item_id")]
    owner_ids = sorted({e["owner_id"] for e in entries if e.get("owner_id")})

    try:
        details = steamapi.published_file_details(item_ids)
        authors = steamapi.player_names(key, owner_ids)
    except WrsrcliError as exc:
        print(f"warning: {exc}", file=sys.stderr)
        print(
            "warning: falling back to local data only — the table will omit "
            "author name, posted date and file size.",
            file=sys.stderr,
        )
        return None, None, False

    print(
        f"Retrieved Steam Web API metadata for {len(details)} item(s) and "
        f"{len(authors)} author(s)."
    )
    return details, authors, True


def cmd_output_table(args):
    key = config.get(config.API_KEY)
    if not key:
        print(NO_API_KEY_MESSAGE)
        print()

    entries = table.load_manifest()

    details, authors, api_mode = (None, None, False)
    if key:
        details, authors, api_mode = _enrich(key, entries)

    rows = table.build_rows(entries, resolve_workshop_path(), details, authors)

    destination = _resolve_output(_prompt_save_folder())
    try:
        destination.write_text(table.render(rows, api_mode), encoding="utf-8")
    except OSError as exc:
        raise WrsrcliError(f"could not write {destination}: {exc}") from exc

    print(f"Wrote {len(rows)} row(s) to {destination}")
    return 0


def cmd_steamcmd(args):
    if not args.install:
        if args.path:
            raise WrsrcliError("`--path` only applies with `--install`.")
        print("wrsrcli steamcmd: nothing to do — pass -i/--install.", file=sys.stderr)
        return 1

    install_path = (
        Path(args.path).expanduser() if args.path else steam.steam_path() / "steamcmd"
    )

    if steamcmd.is_installed(install_path):
        print(f"SteamCMD is already installed at {install_path}")
        return 0

    print(STEAMCMD_PROMPT)
    # Only an empty line proceeds; anything else cancels (decision D-008).
    if input().strip():
        print("Cancelled — nothing was downloaded.")
        return 0

    print(f"Downloading SteamCMD from Valve to {install_path} ...")
    size = steamcmd.install(install_path)
    print(f"Downloaded and extracted {size:,} bytes.")

    print("Running steamcmd.exe once to let it self-update (this can take a while) ...")
    result = steamcmd.bootstrap(install_path)
    if result.returncode not in (0, 7):
        # 7 is SteamCMD's normal exit after a bare bootstrap on some builds.
        print(
            f"warning: steamcmd.exe exited with code {result.returncode} during "
            "its first run.",
            file=sys.stderr,
        )

    print(f"SteamCMD ready at {steamcmd.executable(install_path)}")
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
