# Fernwood Press — Release Requirements

**Product:** Fernwood Press online bookstore (sample)
**Environment under test:** the bundled sample website (`website/server.py`), run locally
at `http://localhost:5050`
**Release:** demo / pipeline validation
**Owner:** Solutions Engineering

> This document is the single source of truth `kane-cli context ingest`/`design tests`
> work from. It's written to match `website/server.py` exactly (verified by hand), so
> scenarios kane-cli designs from it are ones the sample site can actually pass or
> meaningfully fail — keep the two in sync if either changes. All data is synthetic;
> never point this pipeline at a real storefront without redoing this doc for the real
> thing.

---

## REQ-01 — Book search

Readers must be able to find a book by title, author, or genre from any page.

Acceptance criteria:
- The search box is present in the header on every page.
- Searching a term that matches a book's title, author, or genre (e.g. "Fantasy") returns
  a results grid with at least one book tile, and each tile shows the book's title,
  author, and price.
- Searching a term with no matches shows an explicit "No books match your search" message
  rather than an empty page or an error.
- Search results are reachable via a shareable URL (the search term appears as a `q`
  query parameter in the address bar).

## REQ-02 — Genre browse and refinement

Readers must be able to browse a genre and change how results are presented.

Acceptance criteria:
- Opening a genre from the home page or nav opens a listing page showing a book count
  and a grid of book tiles.
- The listing offers a sort control (title A-Z, price low-to-high, rating high-to-low)
  and the first book shown changes when the sort order changes.
- The listing offers a "show N per page" control, and choosing a smaller value reduces
  the number of tiles rendered.
- Switching between grid and list view keeps the same books on screen.

## REQ-03 — Book detail and purchase

The book detail page must give a reader enough to decide, and must sell the correct copy.

Acceptance criteria:
- Opening a book from a listing or search result shows the book's title, author, genre,
  price, rating, a short blurb, a cover image, and its SKU/ISBN.
- Every book tile in search results and genre listings shows a cover image and a SKU.
- Purchasing without selecting an edition is rejected with a message telling the reader
  to select one; no item is added to the cart.
- Purchasing a valid, currently-available copy with an edition succeeds, shows a
  confirmation naming the book, copy, and edition, and updates the header's "My Cart"
  count.
- Attempting to purchase a copy that has already been sold (to this reader or anyone
  else) is rejected with a message that the copy is no longer available; no second sale
  is created for that copy.
- A book with no copies left shows an explicit "sold out" message instead of a purchase
  form.

## REQ-04 — Cart integrity

The cart must reflect exactly what the reader purchased, and must survive removals.

Acceptance criteria:
- The "My Cart" page lists every purchased item with title, author, copy, edition, and
  price.
- The total shown equals the sum of the listed prices.
- Removing an item from the cart takes it off the list, updates the total, and makes
  that copy purchasable again from the book's page.
- With zero items, the page shows an explicit "cart is empty" message.

## REQ-05 — Store disclosures

Acceptance criteria:
- A shipping banner ("Free shipping on orders over $35...") is visible on every page.
- Every book detail page shows a disclaimer distinguishing signed-edition final sale
  terms from standard-edition return terms.
- The contact page shows support hours, a phone number, and a shipping note.

---

Add REQ-NN sections here — and matching logic in `website/server.py` — before pointing
this pipeline at a different or more capable site.
