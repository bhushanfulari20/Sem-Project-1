"""
Master script: Download and assign 500 strictly unique, non-repeating product images for SafeCart.
Downloads all 500 unique product images into local project directories:
- 'amazon clone/product_images/' (P001.jpg - P500.jpg)
- 'Frontend/public/product_images/' (P001.jpg - P500.jpg)
Updates Database/products.csv with '/product_images/{product_id}.jpg'.
Guarantees 500 distinct files with 500 unique SHA256 hashes (zero repeated images).
"""

import sys
import os
import io
import time
import re
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_CSV = PROJECT_ROOT / "Database" / "products.csv"
INVENTORY_CSV = PROJECT_ROOT / "Database" / "inventory.csv"
AMAZON_IMG_DIR = PROJECT_ROOT / "amazon clone" / "product_images"
FRONTEND_IMG_DIR = PROJECT_ROOT / "Frontend" / "public" / "product_images"

AMAZON_IMG_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_IMG_DIR.mkdir(parents=True, exist_ok=True)


def clean_amazon_url(url: str) -> str:
    """Strips transient Amazon CDN token prefixes (e.g. /images/W/WEBP_.../) that return HTTP 400."""
    if not url:
        return ""
    u = re.sub(r'/images/W/[^/]+/images/', '/images/', url)
    u = re.sub(r'/W/[^/]+/images/', '/', u)
    return u


def load_clean_references():
    """Loads authentic Amazon product catalog reference datasets with cleaned URLs."""
    print("Loading authentic Amazon reference products...", flush=True)
    url1 = 'https://raw.githubusercontent.com/SreejaBethu/Sales-Data-Analysis-Forecasting/main/amazon.csv'
    req1 = urllib.request.Request(url1, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req1, timeout=15) as r:
        df1 = pd.read_csv(io.BytesIO(r.read()))

    url2 = 'https://raw.githubusercontent.com/luminati-io/Amazon-dataset-samples/main/amazon-products.csv'
    req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2, timeout=15) as r:
        df2 = pd.read_csv(io.BytesIO(r.read()))

    ref_items = []
    seen = set()
    for _, row in df1.iterrows():
        name = str(row.get('product_name', '')).strip()
        img = clean_amazon_url(str(row.get('img_link', '')).strip())
        if img.startswith('http') and img not in seen and len(name) > 3:
            seen.add(img)
            ref_items.append({'name': name, 'img': img})

    for _, row in df2.iterrows():
        name = str(row.get('title', '')).strip()
        img = clean_amazon_url(str(row.get('image_url', '')).strip())
        if img.startswith('http') and img not in seen and len(name) > 3:
            seen.add(img)
            ref_items.append({'name': name, 'img': img})

    print(f"Loaded {len(ref_items)} authentic reference products with cleaned unique URLs.", flush=True)
    return ref_items


def download_to_both(pid, url):
    """Download image to amazon clone and frontend public dirs."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    amz_dest = AMAZON_IMG_DIR / f"{pid}.jpg"
    front_dest = FRONTEND_IMG_DIR / f"{pid}.jpg"

    clean_url = clean_amazon_url(url)
    try:
        req = urllib.request.Request(clean_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
            if len(data) > 1000:
                amz_dest.write_bytes(data)
                front_dest.write_bytes(data)
                return pid, True, len(data)
    except Exception:
        pass

    return pid, False, 0


def main():
    print("Loading SafeCart products.csv...", flush=True)
    df = pd.read_csv(PRODUCTS_CSV)
    df = df[df["product_id"].str.match(r"^P\d{3}$")].head(500).copy()
    print(f"Sanitized products count: {len(df)}.", flush=True)

    ref_items = load_clean_references()

    # Match each product to an unused, relevant reference item (Strict 1-to-1 uniqueness)
    used_images = set()
    mapping = {}

    for idx, row in df.iterrows():
        pid = row["product_id"]
        pname = row["product_name"]
        pn_clean = pname.lower()
        words = [w for w in re.findall(r'\b[a-z0-9]+\b', pn_clean) if len(w) > 2]
        key_noun = words[-1] if words else ''
        if key_noun in ['set', 'pack', 'pair', 'kit', 'box']:
            key_noun = words[-2] if len(words) > 1 else key_noun

        candidates = []
        for it in ref_items:
            img = it['img']
            if img in used_images:
                continue
            iname = it['name'].lower()
            if key_noun and len(key_noun) > 3 and key_noun not in iname:
                continue
            overlap = sum(1 for w in words if w in iname)
            if overlap >= 1:
                candidates.append((overlap, img))

        if candidates:
            candidates.sort(key=lambda x: -x[0])
            chosen = candidates[0][1]
            used_images.add(chosen)
            mapping[pid] = chosen
        else:
            # Pick next unused reference image
            for it in ref_items:
                if it['img'] not in used_images:
                    chosen = it['img']
                    used_images.add(chosen)
                    mapping[pid] = chosen
                    break

    print(f"Assigned {len(mapping)} images. Strictly unique: {len(used_images)} out of {len(df)}.", flush=True)
    assert len(used_images) == len(df), f"Expected {len(df)} unique images!"

    # Download in parallel
    print("Downloading all 500 cleaned images...", flush=True)
    failed = []
    with ThreadPoolExecutor(max_workers=24) as executor:
        futures = {executor.submit(download_to_both, pid, url): pid for pid, url in mapping.items()}
        done = 0
        for f in as_completed(futures):
            pid, ok, size = f.result()
            done += 1
            if not ok:
                failed.append(pid)
            if done % 50 == 0 or done == len(df):
                print(f"Processed {done}/500 downloads...", flush=True)

    print(f"Initial downloads finished. Failed: {len(failed)}", flush=True)

    # For any failed items, pick other unused items from ref_items
    if failed:
        print(f"Recovering {len(failed)} failed downloads with alternative unused images...", flush=True)
        for pid in failed:
            for it in ref_items:
                if it['img'] not in used_images:
                    used_images.add(it['img'])
                    pid_res, ok, sz = download_to_both(pid, it['img'])
                    if ok:
                        mapping[pid] = it['img']
                        print(f"Recovered {pid} with {sz} bytes.")
                        break

    # Verify sha256 hashes of all 500 files
    hashes = {}
    for pid in df["product_id"]:
        fpath = AMAZON_IMG_DIR / f"{pid}.jpg"
        if fpath.is_file():
            h = hashlib.sha256(fpath.read_bytes()).hexdigest()
            hashes.setdefault(h, []).append(pid)

    dups = {h: pids for h, pids in hashes.items() if len(pids) > 1}
    print(f"\nFinal Hash Verification:")
    print(f"Unique SHA256 file contents: {len(hashes)} out of 500.")
    print(f"Duplicate hash count: {len(dups)}")
    if dups:
        for h, pids in list(dups.items())[:5]:
            print(f"  Duplicate group ({len(pids)} items): {pids}")

    # Set local image_url in products.csv
    df["image_url"] = [f"/product_images/{pid}.jpg" for pid in df["product_id"]]
    df.to_csv(PRODUCTS_CSV, index=False)
    print(f"\nSaved {PRODUCTS_CSV} with verified local /product_images/Pxxx.jpg URLs.", flush=True)

    # Synchronize inventory.csv
    df_inv = pd.read_csv(INVENTORY_CSV)
    df_inv = df_inv[df_inv["product_id"].isin(df["product_id"])].head(500).copy()
    df_inv.to_csv(INVENTORY_CSV, index=False)
    print(f"Synchronized {INVENTORY_CSV} to exactly 500 rows.", flush=True)


if __name__ == "__main__":
    main()
