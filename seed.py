"""Seed catalog from Deezer public API (covers + tracklists). Falls back to iTunes Search API if Deezer is blocked."""
from __future__ import annotations

import argparse
import json
import random
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models import Product, User

USER_AGENT = "GarageVinylCollegeShop/1.0 (educational; +https://localhost)"
REQUEST_DELAY = 0.4

ARTIST_QUERIES: list[tuple[str, str]] = [
    ("jazz", "Miles Davis"),
    ("jazz", "John Coltrane"),
    ("jazz", "Alice Coltrane"),
    ("jazz", "Herbie Hancock"),
    ("rock", "Nirvana"),
    ("rock", "Pink Floyd"),
    ("rock", "Radiohead"),
    ("rock", "Arctic Monkeys"),
    ("hip-hop", "Nas"),
    ("hip-hop", "Kendrick Lamar"),
    ("hip-hop", "Wu-Tang Clan"),
    ("hip-hop", "Tyler, The Creator"),
    ("electronic", "Daft Punk"),
    ("electronic", "Aphex Twin"),
    ("electronic", "Portishead"),
    ("electronic", "Massive Attack"),
    ("electronic", "LCD Soundsystem"),
    ("soul", "Marvin Gaye"),
    ("soul", "Stevie Wonder"),
    ("soul", "Fela Kuti"),
    ("punk", "The Clash"),
    ("punk", "The Strokes"),
    ("punk", "Joy Division"),
    ("punk", "Bjork"),
]

CONDITIONS = [
    Product.CONDITION_NM,
    Product.CONDITION_VG_PLUS,
    Product.CONDITION_VG,
]

# Module flag: once Deezer 403s, skip further Deezer attempts
_deezer_blocked = False


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text or "record"


def unique_product_slug(artist: str, title: str) -> str:
    base = slugify(f"{artist}-{title}")
    slug = base
    n = 1
    while Product.query.filter_by(slug=slug).first() is not None:
        slug = f"{base}-{n}"
        n += 1
    return slug


def http_get_json(url: str) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"  ! HTTP {exc.code}: {url}")
        return {"__http_error__": exc.code}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"  ! request error ({url}): {exc}")
        return None
    finally:
        time.sleep(REQUEST_DELAY)


def deezer_get(url: str) -> dict | list | None:
    global _deezer_blocked
    if _deezer_blocked:
        return None
    data = http_get_json(url)
    if isinstance(data, dict) and data.get("__http_error__") in (403, 451):
        _deezer_blocked = True
        print("  ! Deezer blocked from this network — switching to iTunes Search API")
        return None
    if isinstance(data, dict) and "__http_error__" in data:
        return None
    return data


def search_deezer_albums(artist_name: str, limit: int = 3) -> list[dict]:
    q = urllib.parse.quote(artist_name)
    data = deezer_get(f"https://api.deezer.com/search/album?q={q}&limit=12")
    if not data or not isinstance(data, dict):
        return []
    items = data.get("data") or []
    artist_lower = artist_name.lower()
    matched = []
    for alb in items:
        name = ((alb.get("artist") or {}).get("name") or "").lower()
        if artist_lower in name or name in artist_lower:
            matched.append(alb)
    pool = matched or items
    seen, result = set(), []
    for alb in pool:
        aid = alb.get("id")
        if aid is None or aid in seen:
            continue
        # Prefer full albums over singles
        if (alb.get("record_type") or alb.get("type")) == "single":
            continue
        seen.add(aid)
        result.append(alb)
        if len(result) >= limit:
            break
    if len(result) < limit:
        for alb in pool:
            aid = alb.get("id")
            if aid is None or aid in seen:
                continue
            seen.add(aid)
            result.append(alb)
            if len(result) >= limit:
                break
    return result


def fetch_deezer_album(album_id) -> dict | None:
    data = deezer_get(f"https://api.deezer.com/album/{album_id}")
    if not data or not isinstance(data, dict) or data.get("error"):
        return None
    return data


def tracks_from_deezer(album: dict) -> list[dict]:
    tracks = []
    for t in (album.get("tracks") or {}).get("data") or []:
        tracks.append(
            {
                "position": t.get("track_position") or len(tracks) + 1,
                "title": t.get("title") or "Untitled",
                "duration_sec": t.get("duration") or 0,
            }
        )
    return tracks


def itunes_artwork(url: str | None) -> str | None:
    if not url:
        return None
    # Upgrade 100x100 -> 1000x1000
    return re.sub(r"/\d+x\d+bb\.", "/1000x1000bb.", url)


def search_itunes_albums(artist_name: str, limit: int = 3) -> list[dict]:
    q = urllib.parse.quote(f"{artist_name}")
    data = http_get_json(
        f"https://itunes.apple.com/search?term={q}&entity=album&limit=10&media=music"
    )
    if not data or not isinstance(data, dict) or data.get("__http_error__"):
        return []
    items = data.get("results") or []
    artist_lower = artist_name.lower().replace(",", "")
    matched = []
    for alb in items:
        name = (alb.get("artistName") or "").lower().replace(",", "")
        if artist_lower in name or name in artist_lower:
            if alb.get("collectionType") == "Album" or alb.get("wrapperType") == "collection":
                matched.append(alb)
    pool = matched or [
        a for a in items if a.get("wrapperType") == "collection"
    ]
    seen, result = set(), []
    for alb in pool:
        cid = alb.get("collectionId")
        if not cid or cid in seen:
            continue
        # skip singles (few tracks)
        tc = alb.get("trackCount") or 0
        if tc and tc < 4:
            continue
        seen.add(cid)
        result.append(alb)
        if len(result) >= limit:
            break
    return result


def fetch_itunes_tracks(collection_id) -> list[dict]:
    data = http_get_json(
        f"https://itunes.apple.com/lookup?id={collection_id}&entity=song&limit=200"
    )
    if not data or not isinstance(data, dict) or data.get("__http_error__"):
        return []
    tracks = []
    for item in data.get("results") or []:
        if item.get("wrapperType") != "track":
            continue
        ms = item.get("trackTimeMillis") or 0
        tracks.append(
            {
                "position": item.get("trackNumber") or len(tracks) + 1,
                "title": item.get("trackName") or "Untitled",
                "duration_sec": int(ms / 1000) if ms else 0,
            }
        )
    tracks.sort(key=lambda t: t["position"])
    return tracks


def parse_year(value) -> int:
    if not value:
        return 1990
    s = str(value)
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:4])
    return 1990


def make_description(title: str, artist: str, genre: str, year: int) -> str:
    genre_ru = {
        "jazz": "джаз",
        "rock": "рок",
        "hip-hop": "хип-хоп",
        "electronic": "электроника",
        "soul": "соул",
        "punk": "панк / инди",
    }.get(genre, genre)
    return random.choice(
        [
            f"Оригинальный пресс «{title}» — {artist} ({year}). Проверенное состояние, готов к прослушиванию.",
            f"{artist} — «{title}». Классика {genre_ru}, тёплый аналоговый звук.",
            f"Пластинка «{title}» ({artist}, {year}). Состояние проверено в магазине, конверт целый.",
            f"«{title}» от {artist}. Хороший экземпляр для коллекции и домашнего прослушивания.",
        ]
    )


def ensure_admin():
    user = User.query.filter_by(username="admin").first()
    if user:
        user.is_staff = True
        print("Admin already exists")
        return user
    user = User(username="admin", email="admin@garage.local", is_staff=True)
    user.set_password("admin12345")
    db.session.add(user)
    db.session.commit()
    print("Created staff user: admin / admin12345")
    return user


def albums_for_artist(artist_query: str) -> list[dict]:
    """Return normalized album dicts: title, artist, year, cover_url, tracks, deezer_id."""
    normalized = []

    stubs = search_deezer_albums(artist_query, limit=2)
    for stub in stubs:
        album = fetch_deezer_album(stub.get("id"))
        if not album:
            continue
        title = (album.get("title") or stub.get("title") or "Untitled").strip()
        artist_name = (
            (album.get("artist") or {}).get("name")
            or (stub.get("artist") or {}).get("name")
            or artist_query
        ).strip()
        normalized.append(
            {
                "title": title,
                "artist": artist_name,
                "year": parse_year(album.get("release_date")),
                "cover_url": album.get("cover_xl")
                or album.get("cover_big")
                or stub.get("cover_xl"),
                "tracks": tracks_from_deezer(album),
                "deezer_id": str(album.get("id") or stub.get("id")),
            }
        )

    if normalized:
        return normalized

    # iTunes fallback
    print(f"  (iTunes fallback for {artist_query})")
    for stub in search_itunes_albums(artist_query, limit=2):
        cid = stub.get("collectionId")
        tracks = fetch_itunes_tracks(cid)
        normalized.append(
            {
                "title": (stub.get("collectionName") or "Untitled").strip(),
                "artist": (stub.get("artistName") or artist_query).strip(),
                "year": parse_year(stub.get("releaseDate")),
                "cover_url": itunes_artwork(stub.get("artworkUrl100")),
                "tracks": tracks,
                "deezer_id": None,  # not from Deezer
            }
        )
    return normalized


def run_seed(clear: bool = True):
    app = create_app()
    with app.app_context():
        db_path = Path(app.root_path).parent / "garage_vinyl.db"
        if clear and db_path.exists():
            # Recreate schema for new columns (college SQLite)
            db.drop_all()
            print("Dropped tables")
        db.create_all()
        ensure_admin()

        if clear:
            n = Product.query.count()
            if n:
                Product.query.delete()
                db.session.commit()
                print(f"Deleted {n} products")

        created = 0
        featured_budget = 10
        condition_idx = 0

        for genre, artist_query in ARTIST_QUERIES:
            print(f"\n→ {artist_query} [{genre}]")
            albums = albums_for_artist(artist_query)
            if not albums:
                print("  (no albums)")
                continue

            for album in albums:
                deezer_id = album.get("deezer_id")
                if deezer_id and Product.query.filter_by(deezer_id=deezer_id).first():
                    print(f"  skip deezer_id={deezer_id}")
                    continue

                title = album["title"]
                artist_name = album["artist"]
                artist_slug = slugify(artist_name)
                slug = unique_product_slug(artist_name, title)
                year = album["year"]
                tracks = album["tracks"]

                price = Decimal(str(int(round(random.uniform(15.0, 45.0), 2) * 100)))
                condition = CONDITIONS[condition_idx % len(CONDITIONS)]
                condition_idx += 1
                stock = random.randint(1, 8)
                is_featured = featured_budget > 0 and random.random() < 0.35
                if is_featured:
                    featured_budget -= 1

                product = Product(
                    title=title,
                    artist=artist_name,
                    artist_slug=artist_slug,
                    slug=slug,
                    genre=genre,
                    year=year,
                    price=price,
                    condition=condition,
                    stock=stock,
                    description=make_description(title, artist_name, genre, year),
                    cover=None,
                    cover_url=album.get("cover_url"),
                    deezer_id=deezer_id,
                    tracklist=json.dumps(tracks, ensure_ascii=False),
                    is_featured=is_featured,
                )
                db.session.add(product)
                created += 1
                print(f"  + {artist_name} — {title} ({len(tracks)} tracks)")

                if created >= 50:
                    break
            if created >= 50:
                break

        db.session.commit()
        print(f"\nDone. Created {created} products. Total: {Product.query.count()}")
        artists = (
            db.session.query(Product.artist_slug, Product.artist)
            .distinct()
            .order_by(Product.artist)
            .limit(8)
            .all()
        )
        for a_slug, a_name in artists:
            cnt = Product.query.filter_by(artist_slug=a_slug).count()
            print(f"  sample artist: /artist/{a_slug}/  ({a_name}, {cnt})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Garage Vinyl from Deezer / iTunes")
    parser.add_argument("--clear", dest="clear", action="store_true", default=True)
    parser.add_argument("--no-clear", dest="clear", action="store_false")
    args = parser.parse_args()
    run_seed(clear=args.clear)
