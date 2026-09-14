#!/usr/bin/env python3
"""
Sample self-publishing platform — modeled on the shape of a site like Notion Press
rather than a bookstore: authors browse publishing packages, submit a manuscript into
one (claiming one of a limited number of monthly seats), track it on "My Submissions",
and can withdraw it. Separately, anyone can browse/search the catalog of books already
published through the platform — a showcase, not a storefront (no price, no checkout).
A real, server-rendered web app (no client-side JS needed) so kane-cli's browser
automation has an actual UI to assure. Started in-process locally rather than hosted
anywhere.

All packages, books, authors, and seat counts are synthetic.
requirements/book-publishing-website.md documents this app's behavior exactly — keep
both in sync if either changes.
"""

from __future__ import annotations

import itertools
import os
from datetime import date, timedelta

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("WEBSITE_SECRET_KEY", "dev-secret-change-me")

MANUSCRIPT_STATUSES = ["New Manuscript", "Revised Manuscript"]

# --- Publishing packages -----------------------------------------------------------
# "seats" model the platform's monthly onboarding capacity per package — a limited,
# shared, in-memory resource (like the reference demos' appointment slots / signed
# copies), so "fully booked this month" is a real, testable condition.
PACKAGES = [
    {"id": "starter", "name": "Starter", "code": "FP-PKG-01",
     "tagline": "Get your book listed online, fast and affordable.",
     "price": 499, "turnaround_days": 45,
     "features": ["Free ISBN assignment", "Paperback + eBook formats",
                  "Basic cover design", "Listing on our published-books catalog"],
     "seats": ["Seat 1", "Seat 2", "Seat 3", "Seat 4", "Seat 5", "Seat 6"]},
    {"id": "standard", "name": "Standard", "code": "FP-PKG-02",
     "tagline": "Professional editing and wider distribution.",
     "price": 999, "turnaround_days": 30,
     "features": ["Everything in Starter", "One round of professional editing",
                  "Custom cover design", "Distribution to major online retailers"],
     "seats": ["Seat 1", "Seat 2", "Seat 3", "Seat 4"]},
    {"id": "premium", "name": "Premium", "code": "FP-PKG-03",
     "tagline": "A dedicated team behind your launch.",
     "price": 1999, "turnaround_days": 21,
     "features": ["Everything in Standard", "Two rounds of professional editing",
                  "Dedicated publishing consultant", "Press release + marketing kit"],
     "seats": ["Seat 1", "Seat 2"]},
    {"id": "authors-choice", "name": "Author's Choice", "code": "FP-PKG-04",
     "tagline": "Our full-service imprint experience.",
     "price": 3499, "turnaround_days": 14,
     "features": ["Everything in Premium", "Hardcover edition",
                  "Book launch event support", "National bookstore placement"],
     "seats": ["Seat 1"]},
]
PACKAGES_BY_ID = {p["id"]: p for p in PACKAGES}

# Seats already claimed this month (by anyone) — shared, in-memory, resets when the
# process restarts. Key is (package_id, seat).
taken_seats: set[tuple[str, str]] = set()


def available_seats(package: dict) -> list[str]:
    return [s for s in package["seats"] if (package["id"], s) not in taken_seats]


def submissions() -> list[dict]:
    return session.setdefault("submissions", [])


_submission_counter = {"n": 1000}


def _next_submission_id() -> str:
    _submission_counter["n"] += 1
    return f"SUB-{_submission_counter['n']}"


# --- Published books catalog (showcase only — no price, no purchase) ---------------
BOOKS = [
    {"id": "willow-hour", "title": "The Willow Hour", "author": "Mireille Astor", "genre": "Fiction",
     "rating": 4.7, "format": "Paperback", "package_id": "premium",
     "blurb": "A quiet, aching novel about three sisters and the house that outlives them."},
    {"id": "glass-orchard", "title": "The Glass Orchard", "author": "Denis Faulk", "genre": "Fiction",
     "rating": 4.4, "format": "eBook", "package_id": "standard",
     "blurb": "A family saga spanning four decades of a failing apple farm in Vermont."},
    {"id": "harbor-light", "title": "Harbor Light", "author": "Adaeze Solomon", "genre": "Fiction",
     "rating": 4.6, "format": "Hardcover", "package_id": "authors-choice",
     "blurb": "A lighthouse keeper's family keeps the light burning long after the coast guard stops asking them to."},
    {"id": "cartographers-daughter", "title": "The Cartographer's Daughter", "author": "Noah Fennimore",
     "genre": "Fiction", "rating": 4.5, "format": "Paperback", "package_id": "starter",
     "blurb": "She inherits her father's unfinished atlas, and the border dispute that came with it."},
    {"id": "last-ledger", "title": "The Last Ledger", "author": "Priya Anand", "genre": "Mystery",
     "rating": 4.8, "format": "Paperback", "package_id": "premium",
     "blurb": "A forensic accountant uncovers a decades-old fraud with a body count."},
    {"id": "quiet-alibi", "title": "A Quiet Alibi", "author": "Owen Mercer", "genre": "Mystery",
     "rating": 4.3, "format": "eBook", "package_id": "standard",
     "blurb": "A small-town detective's best friend becomes her prime suspect."},
    {"id": "midnight-inventory", "title": "Midnight Inventory", "author": "Rosalind Kepler", "genre": "Mystery",
     "rating": 4.6, "format": "Paperback", "package_id": "starter",
     "blurb": "A shop owner closing up for the night finds a body between the shelves — and no sign of a break-in."},
    {"id": "vanishing-hour", "title": "The Vanishing Hour", "author": "Tomas Ekwueme", "genre": "Mystery",
     "rating": 4.4, "format": "Hardcover", "package_id": "authors-choice",
     "blurb": "Every witness agrees on what happened, except for the one hour nobody can account for."},
    {"id": "drift-engine", "title": "Drift Engine", "author": "Talia Voss", "genre": "Sci-Fi",
     "rating": 4.6, "format": "Paperback", "package_id": "standard",
     "blurb": "A salvage crew finds a derelict ship still running on a dead crew's orders."},
    {"id": "signal-noon", "title": "Signal at Noon", "author": "Kenji Warrick", "genre": "Sci-Fi",
     "rating": 4.5, "format": "eBook", "package_id": "starter",
     "blurb": "First contact told entirely through a rural radio operator's logbook."},
    {"id": "chrono-tide", "title": "Chrono Tide", "author": "Yusuf Bramwell", "genre": "Sci-Fi",
     "rating": 4.7, "format": "Paperback", "package_id": "premium",
     "blurb": "A colony ship arrives four hundred years early, and nobody on board has aged a day."},
    {"id": "last-uplink", "title": "The Last Uplink", "author": "Vera Ashcombe", "genre": "Sci-Fi",
     "rating": 4.5, "format": "Hardcover", "package_id": "authors-choice",
     "blurb": "A dead research station keeps transmitting — in a voice the crew swears they recognize."},
    {"id": "iron-court", "title": "The Iron Court", "author": "Branwen Oduya", "genre": "Fantasy",
     "rating": 4.9, "format": "Hardcover", "package_id": "authors-choice",
     "blurb": "A blacksmith's daughter is crowned regent of a kingdom that despises her."},
    {"id": "salt-and-crown", "title": "Salt and Crown", "author": "Idris Falk", "genre": "Fantasy",
     "rating": 4.5, "format": "Paperback", "package_id": "standard",
     "blurb": "Two rival pirate fleets are forced into an uneasy truce by a rising tide god."},
    {"id": "bonewood-throne", "title": "The Bonewood Throne", "author": "Isolde Marchetti", "genre": "Fantasy",
     "rating": 4.6, "format": "Paperback", "package_id": "premium",
     "blurb": "Every ruler who has taken this throne has been claimed by the forest within a year. She takes it anyway."},
    {"id": "ashes-ember-king", "title": "Ashes of the Ember King", "author": "Callan Okoro", "genre": "Fantasy",
     "rating": 4.4, "format": "eBook", "package_id": "starter",
     "blurb": "The war is over. Rebuilding a kingdom of ash turns out to be the harder story."},
    {"id": "unmade-map", "title": "The Unmade Map", "author": "Corinne Beswick", "genre": "Non-Fiction",
     "rating": 4.6, "format": "Paperback", "package_id": "standard",
     "blurb": "A cartographer's memoir of redrawing borders after twelve years of war."},
    {"id": "hunger-of-bees", "title": "The Hunger of Bees", "author": "Marcus Teller", "genre": "Non-Fiction",
     "rating": 4.4, "format": "eBook", "package_id": "starter",
     "blurb": "A beekeeper's field notes on colony collapse and quiet recovery."},
    {"id": "weight-small-things", "title": "The Weight of Small Things", "author": "Harriet Onwuka",
     "genre": "Non-Fiction", "rating": 4.5, "format": "Paperback", "package_id": "premium",
     "blurb": "Essays on what's left after you stop keeping most of what you own."},
    {"id": "concrete-and-coral", "title": "Concrete and Coral", "author": "Desmond Faulkner", "genre": "Non-Fiction",
     "rating": 4.7, "format": "Hardcover", "package_id": "authors-choice",
     "blurb": "A field account of rebuilding a dead reef under a working harbor, one frame at a time."},
    {"id": "paper-crown", "title": "Paper Crown", "author": "Selin Okafor", "genre": "Biography",
     "rating": 4.7, "format": "Hardcover", "package_id": "premium",
     "blurb": "The authorized life of a playwright who never once gave an interview."},
    {"id": "long-way-home", "title": "The Long Way Home", "author": "Frankie Ansah", "genre": "Biography",
     "rating": 4.3, "format": "Paperback", "package_id": "starter",
     "blurb": "A long-haul trucker's account of a life spent almost, but never quite, arriving."},
    {"id": "ordinary-weather", "title": "Ordinary Weather", "author": "Simone Achterberg", "genre": "Biography",
     "rating": 4.6, "format": "eBook", "package_id": "standard",
     "blurb": "A career meteorologist looks back on forty years of being wrong in public, gracefully."},
    {"id": "understudys-notebook", "title": "The Understudy's Notebook", "author": "Felix Aranzazu",
     "genre": "Biography", "rating": 4.4, "format": "Paperback", "package_id": "authors-choice",
     "blurb": "Thirty years backstage, three nights on stage, and everything he learned waiting in the wings."},
]
# --- Catalog extension: rounds every genre out to CATALOG_SIZE_PER_GENRE titles,
# generated deterministically from per-genre word banks (no randomness, so the
# catalog — and every id/isbn derived from it — is stable across restarts).
# The hand-written titles above stay as-is; this only fills in the rest.
CATALOG_SIZE_PER_GENRE = 20

_FIRST_NAMES_POOL = [
    "Elena", "Marcus", "Priya", "Owen", "Talia", "Kenji", "Branwen", "Idris", "Corinne", "Selin",
    "Frankie", "Yusuf", "Vera", "Isolde", "Callan", "Harriet", "Desmond", "Simone", "Felix", "Rosalind",
    "Tomas", "Adaeze", "Noah", "Mireille", "Denis", "Junot", "Aisling", "Rafael", "Wren", "Odalys",
    "Casimir", "Leandra", "Bram", "Nkechi", "Soren", "Delphine", "Kwame", "Ottilie", "Rian", "Zuri",
]
_LAST_NAMES_POOL = [
    "Cruz", "Webb", "Anand", "Mercer", "Voss", "Warrick", "Oduya", "Falk", "Beswick", "Okafor",
    "Ansah", "Bramwell", "Ashcombe", "Marchetti", "Okoro", "Onwuka", "Faulkner", "Achterberg", "Aranzazu", "Kepler",
    "Ekwueme", "Solomon", "Fennimore", "Astor", "Faulk", "Delacroix", "Whitfield", "Nakamura", "Osei", "Bellweather",
    "Callahan", "Ivanova", "Okonjo", "Pruitt", "Rasmussen", "Tavares", "Ueda", "Vance", "Winslow", "Zhukov",
]

_GENRE_WORDBANKS = {
    "Fiction": {
        "adjectives": ["Quiet", "Unfinished", "Distant", "Gentle", "Autumn", "Tender", "Fading", "Patient",
                       "Restless", "Ordinary", "Scattered", "Lingering", "Unspoken", "Borrowed", "Faint", "Slow"],
        "nouns": ["House", "Garden", "Letter", "Season", "Harbor", "River", "Attic", "Orchard", "Kitchen",
                  "Porch", "Field", "Coastline", "Chapter", "Photograph", "Recipe", "Windowsill"],
        "blurbs": [
            "A novel about the {n} that outlasts everyone who ever lived in it.",
            "Three siblings return to the {n} their mother never spoke of.",
            "A quiet story about what a {n} remembers and what it forgets.",
            "A family spends one last summer deciding what to do with the {n}.",
        ],
    },
    "Mystery": {
        "adjectives": ["Silent", "Hidden", "Final", "Missing", "Locked", "Cold", "Untold", "Last", "Buried",
                       "Quiet", "Forgotten", "Crooked", "Uneasy", "Vanished", "Whispered", "Narrow"],
        "nouns": ["Witness", "Alibi", "Clue", "Inventory", "Ledger", "Confession", "Verdict", "Suspect",
                  "Inquest", "Testimony", "Evidence", "Motive", "Detective", "Case", "Shadow", "Register"],
        "blurbs": [
            "A detective reopens a case built entirely on a {n} nobody can explain.",
            "The only lead is a {n} that shouldn't exist.",
            "Everyone in town has a theory about the {n} — and an alibi to match.",
            "A cold case turns hot the moment the {n} resurfaces.",
        ],
    },
    "Sci-Fi": {
        "adjectives": ["Distant", "Silent", "Frozen", "Orbital", "Synthetic", "Last", "Quantum", "Derelict",
                       "Hollow", "Stellar", "Fractured", "Dormant", "Drifting", "Unmapped", "Recursive", "Dead"],
        "nouns": ["Station", "Colony", "Transmission", "Horizon", "Engine", "Protocol", "Anomaly", "Vessel",
                  "Frontier", "Array", "Uplink", "Nebula", "Circuit", "Passage", "Relay", "Signal"],
        "blurbs": [
            "A crew discovers a {n} that has been running long after it should have failed.",
            "First contact arrives as a {n} nobody on the ship can decode.",
            "A colony ship's {n} starts making decisions nobody authorized.",
            "The last transmission from a dead station is just a {n}, repeating.",
        ],
    },
    "Fantasy": {
        "adjectives": ["Iron", "Bonewood", "Ember", "Silver", "Gilded", "Forgotten", "Thorned", "Ashen",
                       "Wintered", "Sunken", "Broken", "Wandering", "Crowned", "Shattered", "Veiled", "Hollow"],
        "nouns": ["Throne", "Court", "Kingdom", "Crown", "Blade", "Oracle", "Citadel", "Grove", "Prophecy",
                  "Forge", "Realm", "Tower", "Legion", "Covenant", "Wyrm", "Regent"],
        "blurbs": [
            "A kingdom undone by a {n}, and the one heir willing to face it.",
            "Every ruler who claims the {n} is gone within a year. She takes it anyway.",
            "A war fought over a {n} nobody living has actually seen.",
            "The last {n} in the realm chooses the least likely champion.",
        ],
    },
    "Non-Fiction": {
        "adjectives": ["Working", "Small", "Quiet", "Lasting", "Ordinary", "Forgotten", "Practical", "Patient",
                       "Living", "Plain", "Long", "Local", "Public", "Private", "Common", "Unfinished"],
        "nouns": ["Weight", "Language", "Geography", "Architecture", "Economy", "Ecology", "Anatomy", "Memory",
                  "Politics", "Patience", "Silence", "Discipline", "Craft", "Practice", "Arithmetic", "Repair"],
        "blurbs": [
            "An essay collection on the {n} of ordinary life, and what it costs to keep it.",
            "A field account of {n}, written from the ground up.",
            "A reporter spends a decade inside the {n} nobody else was covering.",
            "A clear-eyed history of {n}, told through the people who did the work.",
        ],
    },
    "Biography": {
        "adjectives": ["Ordinary", "Unfinished", "Quiet", "Borrowed", "Restless", "Undelivered", "Private",
                       "Unwritten", "Working", "Wandering", "Remembered", "Unsigned", "Late", "Early", "Plain", "Long"],
        "nouns": ["Weather", "Notebook", "Letters", "Apprentice", "Correspondence", "Portrait", "Rehearsal",
                  "Interview", "Manuscript", "Recollection", "Inheritance", "Career", "Apology", "Diary", "Season", "Record"],
        "blurbs": [
            "The authorized life of a figure best known for the {n} they left behind.",
            "A memoir built from a lifetime of {n}, most of it never meant to be read.",
            "An intimate portrait of a career defined by one long {n}.",
            "Drawn from decades of {n}, this is the story nobody asked her to tell.",
        ],
    },
}

_FORMATS = ["Paperback", "eBook", "Hardcover"]
_PACKAGE_CYCLE = ["starter", "standard", "premium", "authors-choice"]


def _slugify(text: str) -> str:
    out: list[str] = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    slug = "".join(out).strip("-")
    return slug[4:] if slug.startswith("the-") else slug


def _extend_catalog(target_per_genre: int) -> list[dict]:
    generated: list[dict] = []
    used_titles = {b["title"] for b in BOOKS}
    used_ids = {b["id"] for b in BOOKS}

    for genre, bank in _GENRE_WORDBANKS.items():
        need = target_per_genre - len([b for b in BOOKS if b["genre"] == genre])
        if need <= 0:
            continue

        adjectives, nouns, blurbs = bank["adjectives"], bank["nouns"], bank["blurbs"]
        name_offset = sum(ord(c) for c in genre)  # spreads author pairing differently per genre
        made = 0

        for idx, (adj, noun) in enumerate(itertools.product(adjectives, nouns)):
            if made >= need:
                break

            pattern = idx % 3
            if pattern == 0:
                title = f"The {adj} {noun}"
            elif pattern == 1:
                title = f"{adj} {noun}"
            else:
                noun2 = nouns[(idx + 5) % len(nouns)]
                title = f"The {noun}'s {noun2}"
            if title in used_titles:
                continue

            author = (f"{_FIRST_NAMES_POOL[(name_offset + idx) % len(_FIRST_NAMES_POOL)]} "
                      f"{_LAST_NAMES_POOL[(name_offset + idx * 3) % len(_LAST_NAMES_POOL)]}")

            book_id = _slugify(title)
            if book_id in used_ids:
                book_id = f"{book_id}-{idx}"
            used_ids.add(book_id)
            used_titles.add(title)

            generated.append({
                "id": book_id,
                "title": title,
                "author": author,
                "genre": genre,
                "rating": round(4.1 + (idx % 8) * 0.1, 1),
                "format": _FORMATS[idx % len(_FORMATS)],
                "package_id": _PACKAGE_CYCLE[idx % len(_PACKAGE_CYCLE)],
                "blurb": blurbs[idx % len(blurbs)].format(n=noun.lower()),
            })
            made += 1

    return generated


BOOKS.extend(_extend_catalog(CATALOG_SIZE_PER_GENRE))
BOOKS_BY_ID = {b["id"]: b for b in BOOKS}
GENRES = sorted({b["genre"] for b in BOOKS})


def _isbn13(prefix: str) -> str:
    """Compute a valid ISBN-13 check digit for a 12-digit prefix."""
    digits = [int(d) for d in prefix]
    total = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    check = (10 - total % 10) % 10
    return f"{prefix[0:3]}-{prefix[3]}-{prefix[4:9]}-{prefix[9:12]}-{check}"


# Deterministic, genuine-looking ISBN + publication date per title — assigned by
# catalog order so they stay stable across app restarts (no randomness to seed).
_CATALOG_START = date(2022, 1, 10)
for _i, _book in enumerate(BOOKS, start=1):
    _book["isbn"] = _isbn13(f"978163971{_i:03d}")
    _book["published"] = (_CATALOG_START + timedelta(days=_i * 11)).strftime("%B %Y")


@app.context_processor
def inject_globals():
    return {"genres": GENRES, "submission_count": len(submissions())}


@app.get("/")
def home():
    featured = sorted(BOOKS, key=lambda b: -b["rating"])[:4]
    return render_template("home.html", packages=PACKAGES, featured=featured, book_count=len(BOOKS))


@app.get("/publish")
def publish_packages():
    return render_template(
        "packages.html",
        packages=[{**p, "seats_left": len(available_seats(p))} for p in PACKAGES],
    )


@app.get("/publish/<package_id>")
def package_detail(package_id: str):
    package = PACKAGES_BY_ID.get(package_id)
    if not package:
        return "Package not found", 404
    return render_template(
        "package_detail.html",
        package=package,
        seats=available_seats(package),
        genres=GENRES,
        statuses=MANUSCRIPT_STATUSES,
        error=request.args.get("error"),
    )


@app.post("/publish/<package_id>/submit")
def submit_manuscript(package_id: str):
    package = PACKAGES_BY_ID.get(package_id)
    if not package:
        return "Package not found", 404

    book_title = request.form.get("book_title", "").strip()
    author_name = request.form.get("author_name", "").strip()
    email = request.form.get("email", "").strip()
    genre = request.form.get("genre", "").strip()
    manuscript_status = request.form.get("manuscript_status", "")
    seat = request.form.get("seat", "")

    if not (book_title and author_name and email and genre):
        return redirect(url_for("package_detail", package_id=package_id,
                                 error="Please fill in the book title, author name, email, and genre."))
    if not manuscript_status:
        return redirect(url_for("package_detail", package_id=package_id,
                                 error="Please select whether this is a new or revised manuscript."))
    if not seat or (package_id, seat) in taken_seats or seat not in package["seats"]:
        return redirect(url_for("package_detail", package_id=package_id,
                                 error="That seat is no longer available this month. Please choose another."))

    taken_seats.add((package_id, seat))
    entry = {
        "submission_id": _next_submission_id(),
        "package_id": package_id,
        "package_name": package["name"],
        "seat": seat,
        "manuscript_status": manuscript_status,
        "book_title": book_title,
        "author_name": author_name,
        "email": email,
        "genre": genre,
        "status": "Under Review",
    }
    subs = submissions()
    subs.append(entry)
    session["submissions"] = subs
    session["last_submission"] = entry
    return redirect(url_for("package_detail", package_id=package_id))


@app.get("/my-submissions")
def my_submissions():
    return render_template("submissions.html", items=submissions())


@app.post("/my-submissions/withdraw/<int:index>")
def withdraw_submission(index: int):
    items = submissions()
    if 0 <= index < len(items):
        entry = items.pop(index)
        taken_seats.discard((entry["package_id"], entry["seat"]))
        session["submissions"] = items
    return redirect(url_for("my_submissions"))


@app.get("/books")
def books_overview():
    counts = {g: len([b for b in BOOKS if b["genre"] == g]) for g in GENRES}
    return render_template("books_overview.html", counts=counts, total=len(BOOKS))


@app.get("/search")
def search():
    q = (request.args.get("q") or "").strip().lower()
    results = [
        b for b in BOOKS
        if q and (q in b["title"].lower() or q in b["author"].lower() or q in b["genre"].lower())
    ]
    return render_template("search_results.html", query=request.args.get("q", ""), results=results)


@app.get("/genre/<name>")
def genre(name: str):
    books = [b for b in BOOKS if b["genre"].lower() == name.lower()]
    if not books:
        return render_template("listing.html", genre_name=name, books=[], view="grid", sort="title"), 404

    sort_key = request.args.get("sort", "title")
    if sort_key == "rating":
        books = sorted(books, key=lambda b: -b["rating"])
    elif sort_key == "published":
        books = sorted(books, key=lambda b: b["title"])  # stable order; date differences are cosmetic
    else:
        sort_key = "title"
        books = sorted(books, key=lambda b: b["title"])

    try:
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        per_page = 20
    view = request.args.get("view", "grid")
    if view not in ("grid", "list"):
        view = "grid"

    return render_template(
        "listing.html",
        genre_name=books[0]["genre"],
        books=books[:per_page],
        total=len(books),
        sort=sort_key,
        per_page=per_page,
        view=view,
    )


@app.get("/book/<book_id>")
def book_detail(book_id: str):
    book = BOOKS_BY_ID.get(book_id)
    if not book:
        return "Book not found", 404
    return render_template(
        "book_detail.html",
        book=book,
        package=PACKAGES_BY_ID.get(book["package_id"]),
    )


@app.get("/success-stories")
def success_stories():
    testimonials = [
        {"quote": "Fernwood Press took a manuscript I'd rewritten four times and made it a real, "
                   "ISBN-registered book in three weeks.",
         "author": "Mireille Astor", "book_id": "willow-hour", "package_id": "premium"},
        {"quote": "The editing team caught plot holes my writing group missed for two years.",
         "author": "Priya Anand", "book_id": "last-ledger", "package_id": "premium"},
        {"quote": "I only needed the Starter package — free ISBN and a bookstore listing was exactly it.",
         "author": "Kenji Warrick", "book_id": "signal-noon", "package_id": "starter"},
        {"quote": "Author's Choice got me a hardcover run and an actual launch event. Worth every seat.",
         "author": "Branwen Oduya", "book_id": "iron-court", "package_id": "authors-choice"},
        {"quote": "Distribution was the part I dreaded most, and Standard handled it without me lifting a finger.",
         "author": "Corinne Beswick", "book_id": "unmade-map", "package_id": "standard"},
        {"quote": "They found the version of my memoir I'd been too close to see.",
         "author": "Selin Okafor", "book_id": "paper-crown", "package_id": "premium"},
    ]
    for t in testimonials:
        t["package_name"] = PACKAGES_BY_ID[t["package_id"]]["name"]
        t["book_title"] = BOOKS_BY_ID[t["book_id"]]["title"]
    return render_template("success_stories.html", testimonials=testimonials)


@app.get("/contact")
def contact():
    return render_template("contact.html")


# Test-fixture seeding only — not part of the product surface. Submits one or more
# manuscripts into the CALLING browser's own session (same cookie jar) before
# redirecting, so a kane-cli scenario can arrive at a page with pre-existing
# submissions by navigating here first, instead of being told to "submit this
# yourself" in prose.
# `submit` repeats as package_id:seat:manuscript_status:book_title:author_name:email:genre
# (colon-separated).
@app.get("/dev/seed")
def dev_seed():
    for entry in request.args.getlist("submit"):
        parts = entry.split(":", 6)
        if len(parts) != 7:
            continue
        package_id, seat, manuscript_status, book_title, author_name, email, genre_name = parts
        package = PACKAGES_BY_ID.get(package_id)
        if not package or (package_id, seat) in taken_seats:
            continue
        taken_seats.add((package_id, seat))
        subs = submissions()
        subs.append({
            "submission_id": _next_submission_id(),
            "package_id": package_id,
            "package_name": package["name"],
            "seat": seat,
            "manuscript_status": manuscript_status,
            "book_title": book_title,
            "author_name": author_name,
            "email": email,
            "genre": genre_name,
            "status": "Under Review",
        })
        session["submissions"] = subs
    return redirect(request.args.get("next", "/"))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0", port=port)
