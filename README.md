# Untapped.gg MTGA Collection Exporter

This Python script exports your entire **Magic: The Gathering Arena** card collection directly from **Untapped.gg**.

It generates clean text files listing all your cards **line by line**, sorted in the exact same order as displayed on Untapped.gg (by mana value / CMC, then lands at the end, excluding generic basic lands).

---

## Key Improvements

- **No HTML file download required!** You can now simply pass your public Untapped.gg collection URL (or let the script ask for it once).
- **Auto-Config**: Once run with your URL, your settings are saved in `config.json`—future runs only require typing `python export_cards.py`.
- **One-Command Refresh (`--refresh` / `-r`)**: Fetches your latest collection updates directly from Untapped.gg's API at any time.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [How to Find Your Collection URL](#how-to-find-your-collection-url)
- [Command-Line Options](#command-line-options)
- [Generated Output Files](#generated-output-files)
- [Cache & How It Works](#cache--how-it-works)

---

## Features

- **Zero External Dependencies**: Works out-of-the-box using only Python's standard library (`urllib`, `json`, `re`, etc.).
- **URL or HTML Support**:
  - **Recommended**: Provide your Untapped profile URL directly.
  - **Alternative**: Works with saved `.htm` files if preferred.
- **Complete Collection Export**: Bypasses browser virtual DOM limitations (the web browser only renders ~50 visible cards at a time, whereas this script accesses all 3,500+ cards).
- **Exact Untapped.gg Ordering**:
  - Non-land cards first (sorted by ascending mana value / CMC, then alphabetically).
  - Lands at the end (sorted alphabetically).
  - Starts with the very first card (*Accorder's Shield*) and ends with the very last (*Zanarkand, Ancient Metropolis*).
- **Dual Export Formats**:
  - Line-by-line card names (`collection_cards.txt`).
  - Standard Magic Arena deck import format with quantities (`cards_with_quantity.txt`).

---

## Quick Start

### 1. First Run: Pass Your Collection URL

Run the script with your Untapped.gg collection URL:

```powershell
python export_cards.py "https://mtga.untapped.gg/profile/<user_id>/<player_id>/collection"
```

The script extracts your identifiers and saves them in `config.json`.

### 2. Subsequent Runs

Once configured, simply run:

```powershell
python export_cards.py
```

### 3. Updating With Newly Acquired Cards

Whenever you get new cards on MTGA and Untapped has synced:

```powershell
python export_cards.py --refresh
```

This bypasses the local collection cache and retrieves your latest cards immediately.

---

## How to Find Your Collection URL

1. Open your browser and log in to [Untapped.gg](https://mtga.untapped.gg/).
2. Click your avatar/profile in the top right > **Collection**.
3. Copy the URL from your browser's address bar. It looks like:
   ```
   https://mtga.untapped.gg/profile/63f2f410-706e-43f7-8791-0ae7857cd0d7/ABDZQJC4VVCZPEAW4GIAWW3S6Y/collection
   ```

---

## Command-Line Options

| Option | Shorthand | Description |
| :--- | :--- | :--- |
| `[target]` | - | Direct URL or path to an HTML file. Optional. |
| `--url <url>` | `-u` | Specific Untapped.gg collection/profile URL. |
| `--refresh` | `-r` | Force refresh collection data from the API (bypasses cache). |
| `--out <path>` | `-o` | Output file path for card names line by line (default: `collection_cards.txt`). |
| `--out-qty <path>` | - | Output file path with card quantities (default: `cards_with_quantity.txt`). |
| `--include-basics` | - | Include generic basic lands (*Plains*, *Island*, *Swamp*, *Mountain*, *Forest*, *Wastes*). |
| `--html <path>` | - | Path to a local Untapped.gg HTML file (fallback). |
| `--help` | `-h` | Show help and options. |

### Examples

- **Fetch latest cards with fresh API call**:
  ```powershell
  python export_cards.py -r
  ```

- **Include basic lands**:
  ```powershell
  python export_cards.py --include-basics
  ```

- **Custom output filenames**:
  ```powershell
  python export_cards.py -o "my_cards.txt" --out-qty "my_cards_quantities.txt"
  ```

---

## Generated Output Files

### 1. `collection_cards.txt` (Line by line)
```text
Accorder's Shield
Bone Saw
Mishra's Bauble
Mox Amber
Mox Opal
...
Yavimaya Coast
Zanarkand, Ancient Metropolis
```

### 2. `cards_with_quantity.txt` (Magic Arena format)
```text
1 Accorder's Shield
1 Bone Saw
1 Mishra's Bauble
4 Aegis Turtle
...
```

---

## Cache & How It Works

The script manages a `.cache/` folder:
- `collection_cache.json`: Cached copy of your owned card IDs.
- `cards_meta_cache.json`: Untapped's MTGA card database (mana costs, types, IDs).
- `loc_en_cache.json`: English localization table.

The metadata files (~18 MB) are downloaded only once and reused across all subsequent exports for near-instant execution.
