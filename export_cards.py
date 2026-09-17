#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Magic Arena collection extraction script from Untapped.gg.
Exports the complete list of cards line by line in the exact display order of Untapped.gg.

No need to download full HTML pages: simply provide your Untapped.gg collection URL.
"""

import os
import sys
import re
import glob
import json
import ssl
import argparse
import functools
import urllib.request

# SSL context and HTTP headers
SSL_CONTEXT = ssl.create_default_context()
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

CARDS_METADATA_URL = "https://mtgajson.untapped.gg/v1/latest/cards.json"
LOC_EN_URL = "https://mtgajson.untapped.gg/v1/latest/loc_en.json"
API_BASE_URL = "https://api.mtga.untapped.gg/api/v1/account/collections"
CONFIG_FILE = "config.json"


def get_cached_or_download(url, filepath, headers=None, verbose=True, force_download=False):
    """Downloads a resource or loads it from local cache."""
    if not force_download and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        if verbose:
            print(f"[Cache] Loading {os.path.basename(filepath)}...")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    if verbose:
        print(f"[Download] Fetching {url}...")
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def parse_url(url_string):
    """Extracts user_id and player_id from an Untapped.gg profile URL."""
    # Pattern: /profile/<user_id>/<player_id>
    match = re.search(r'/profile/([a-f0-9\-]+)/([A-Za-z0-9]+)', url_string)
    if match:
        return match.group(1), match.group(2)
    return None, None


def extract_info_from_html(html_path):
    """Extracts user_id, player_id, player_name, and cookie from a local HTML file."""
    if not os.path.exists(html_path):
        return None

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', content, re.DOTALL)
    if not match:
        return None

    try:
        next_data = json.loads(match.group(1))
        props = next_data.get("props", {})
        account = props.get("initialMtgaAccount", {})
        cookie = props.get("cookieHeader", "")

        user_id = account.get("id")
        mtga_players = account.get("mtga_players", [])
        if not mtga_players:
            return None

        player_id = mtga_players[0].get("player_id")
        player_name = mtga_players[0].get("player_name", "Player")

        return {
            "user_id": user_id,
            "player_id": player_id,
            "player_name": player_name,
            "cookie": cookie
        }
    except Exception:
        return None


def resolve_session_info(base_dir, args_target=None, args_url=None, args_html=None):
    """Resolves player identifiers from CLI args, config file, URL, or HTML file."""
    config_path = os.path.join(base_dir, CONFIG_FILE)
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    # 1. Check if an explicit URL or target URL was passed
    target = args_url or args_target
    if target and target.startswith("http"):
        user_id, player_id = parse_url(target)
        if user_id and player_id:
            config["user_id"] = user_id
            config["player_id"] = player_id
            config["url"] = target
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return {"user_id": user_id, "player_id": player_id, "cookie": "", "player_name": player_id}

    # 2. Check if an HTML file path was provided
    html_target = args_html or (args_target if args_target and args_target.endswith((".htm", ".html")) else None)
    if html_target:
        p = html_target if os.path.isabs(html_target) else os.path.join(base_dir, html_target)
        info = extract_info_from_html(p)
        if info:
            config["user_id"] = info["user_id"]
            config["player_id"] = info["player_id"]
            config["player_name"] = info["player_name"]
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return info

    # 3. Check if saved in config.json
    if config.get("user_id") and config.get("player_id"):
        return {
            "user_id": config["user_id"],
            "player_id": config["player_id"],
            "player_name": config.get("player_name", config["player_id"]),
            "cookie": config.get("cookie", "")
        }

    # 4. Search for any existing .htm file in the directory as fallback
    htm_candidates = glob.glob(os.path.join(base_dir, "*.htm")) + glob.glob(os.path.join(base_dir, "*.html"))
    for candidate in htm_candidates:
        info = extract_info_from_html(candidate)
        if info:
            config["user_id"] = info["user_id"]
            config["player_id"] = info["player_id"]
            config["player_name"] = info["player_name"]
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"[Auto-detected] Found HTML file: {os.path.basename(candidate)}")
            return info

    # 5. Interactive prompt: ask the user for their Untapped URL
    print("\nNo collection information found.")
    print("Example URL: https://mtga.untapped.gg/profile/<user_id>/<player_id>/collection")
    try:
        user_input = input("Please paste your Untapped.gg collection URL: ").strip()
    except (EOFError, KeyboardInterrupt):
        sys.exit(1)

    user_id, player_id = parse_url(user_input)
    if user_id and player_id:
        config["user_id"] = user_id
        config["player_id"] = player_id
        config["url"] = user_input
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return {"user_id": user_id, "player_id": player_id, "cookie": "", "player_name": player_id}

    print("[Error] Could not extract user_id and player_id from the provided input.")
    sys.exit(1)


def calculate_cmc(card):
    """Calculates converted mana cost (CMC)."""
    cmc = card.get("cmc")
    if cmc is not None:
        return cmc
    cost = card.get("castingcost")
    if not cost:
        return 0
    nums = re.findall(r'o(\d+)', cost)
    letters = re.findall(r'o([WUBRGXCY])', cost)
    return sum(int(n) for n in nums) + len(letters)


def parse_collection(session, cache_dir, include_basics=False, refresh=False):
    """
    Fetches the collection and card metadata, then filters and sorts them
    according to Untapped.gg's exact display logic.
    """
    print(f"[Profile] Player: {session['player_name']} (Player ID: {session['player_id']})")

    # 1. Fetch player collection
    coll_cache_path = os.path.join(cache_dir, "collection_cache.json")
    coll_url = f"{API_BASE_URL}/{session['player_id']}?user_id={session['user_id']}"
    headers = {"User-Agent": USER_AGENT}
    if session.get("cookie"):
        headers["Cookie"] = session["cookie"]

    collection_data = get_cached_or_download(
        coll_url, coll_cache_path, headers=headers, force_download=refresh
    )
    owned_cards = collection_data.get("cards", [])
    print(f"[Collection] Total owned print entries: {len(owned_cards)}")

    # 2. Fetch metadata for all MTGA cards
    cards_cache_path = os.path.join(cache_dir, "cards_meta_cache.json")
    loc_cache_path = os.path.join(cache_dir, "loc_en_cache.json")

    cards_meta = get_cached_or_download(CARDS_METADATA_URL, cards_cache_path)
    loc_en = get_cached_or_download(LOC_EN_URL, loc_cache_path)

    loc_map = {item["id"]: item["text"] for item in loc_en if "id" in item and "text" in item}
    cards_by_grpid = {c["grpid"]: c for c in cards_meta if "grpid" in c}

    # 3. Process and aggregate owned cards
    unique_cards = {}

    for entry in owned_cards:
        grpid = entry.get("grpid")
        qty = entry.get("quantity", 0)
        c = cards_by_grpid.get(grpid)
        if not c:
            continue

        name = c.get("name") or loc_map.get(c.get("titleId"), "")
        if not name:
            continue

        types = c.get("types") or []
        supertypes = c.get("supertypes") or []

        # Type 5 = Land
        is_direct_land = 5 in types
        # Basic lands: SuperType Basic (1 or "Basic") or standard basic land titleIds
        is_basic = is_direct_land and (
            1 in supertypes or "Basic" in supertypes or c.get("titleId") in [647, 648, 652, 653, 1250]
        )

        if not include_basics and is_basic:
            continue

        cmc = calculate_cmc(c)
        title_id = c.get("titleId", grpid)

        if title_id not in unique_cards:
            unique_cards[title_id] = {
                "titleId": title_id,
                "name": name,
                "cmc": cmc,
                "quantity": qty,
                "is_land": is_direct_land,
                "is_direct_land": is_direct_land,
                "is_basic": is_basic,
                "rarity": c.get("rarity"),
                "set": c.get("set")
            }
        else:
            unique_cards[title_id]["quantity"] += qty

    # 4. Untapped.gg sorting logic (ez.PF function)
    # Non-lands first (sorted by ascending CMC, then alphabetical by name)
    # Lands at the end (sorted by ascending CMC, then alphabetical by name)
    def compare_untapped(e, t):
        name_cmp = (e["name"] > t["name"]) - (e["name"] < t["name"])
        if e["is_land"] and t["is_land"]:
            if e["is_basic"] != t["is_basic"]:
                return 1 if e["is_basic"] else -1
            return (e["cmc"] - t["cmc"]) or name_cmp
        if e["is_land"] or t["is_land"]:
            return 1 if e["is_land"] else -1
        return (e["cmc"] - t["cmc"]) or name_cmp

    sorted_cards = sorted(unique_cards.values(), key=functools.cmp_to_key(compare_untapped))
    return sorted_cards


def main():
    parser = argparse.ArgumentParser(
        description="Export MTGA card collection from Untapped.gg data without needing to download HTML files."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Untapped.gg profile URL or path to HTML file (optional, auto-detected if omitted)"
    )
    parser.add_argument(
        "--url", "-u",
        default=None,
        help="Direct Untapped.gg collection/profile URL"
    )
    parser.add_argument(
        "--html",
        default=None,
        help="Path to a local Untapped.gg HTML file (optional)"
    )
    parser.add_argument(
        "--refresh", "-r",
        action="store_true",
        help="Force re-download of your collection from the API (bypasses cache)"
    )
    parser.add_argument(
        "--out", "-o",
        default="collection_cards.txt",
        help="Output text file for card names line by line (default: collection_cards.txt)"
    )
    parser.add_argument(
        "--out-qty",
        default="cards_with_quantity.txt",
        help="Output text file with quantities (default: cards_with_quantity.txt)"
    )
    parser.add_argument(
        "--include-basics",
        action="store_true",
        help="Include generic basic lands (Plains, Island, Swamp, Mountain, Forest, Wastes)"
    )

    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    out_file = args.out if os.path.isabs(args.out) else os.path.join(base_dir, args.out)
    out_qty_file = args.out_qty if os.path.isabs(args.out_qty) else os.path.join(base_dir, args.out_qty)
    cache_dir = os.path.join(base_dir, ".cache")

    print("=" * 60)
    print(" Untapped.gg -> Magic Arena Collection Exporter")
    print("=" * 60)

    session = resolve_session_info(
        base_dir=base_dir,
        args_target=args.target,
        args_url=args.url,
        args_html=args.html
    )

    cards = parse_collection(
        session=session,
        cache_dir=cache_dir,
        include_basics=args.include_basics,
        refresh=args.refresh
    )

    if not cards:
        print("[Error] No cards found.")
        return

    print(f"\n[Success] Found {len(cards)} unique cards in your collection!")
    print(f"  First card: {cards[0]['name']}")
    print(f"  Last card : {cards[-1]['name']}")

    # Write text file line by line (card names only)
    with open(out_file, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(c["name"] + "\n")
    print(f"\n[File Created] Line by line card list: {out_file}")

    # Write text file with quantities (standard Magic Arena format)
    with open(out_qty_file, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(f"{c['quantity']} {c['name']}\n")
    print(f"[File Created] Card list with quantity : {out_qty_file}")


if __name__ == "__main__":
    main()
