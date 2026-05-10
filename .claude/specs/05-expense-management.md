# Spec: Expense Management

## Overview
Implement the core expense tracking functionality for Spendly. This step
replaces the four stub routes (`/expenses/add`, `/expenses/<id>/edit`,
`/expenses/<id>/delete`, and the bare-bones `/dashboard`) with working
implementations. After this step, a logged-in user can log new expenses,
view all their expenses in a summary dashboard, edit any entry, and delete
any entry. The `expenses` table already exists in the schema — no migrations
are required.

## Depends on
- Step 01 — Database Setup (`get_db()`, `expenses` table must exist)
- Step 02 — Registration (user accounts must exist)
- Step 03 — Login and Logout (session must be set for guards to work)

## Routes

- `GET  /dashboard`              — redesigned: query and display all user expenses with summary stats — logged-in
- `GET  /expenses/add`           — render the add-expense form — logged-in
- `POST /expenses/add`           — validate and insert a new expense row — logged-in
- `GET  /expenses/<int:id>/edit` — render the edit form pre-populated with the expense — logged-in + owner
- `POST /expenses/<int:id>/edit` — validate and update the expense row — logged-in + owner
- `POST /expenses/<int:id>/delete` — delete the expense row — logged-in + owner

## Database changes
No database changes. The `expenses` table already exists:

```sql
expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    date        TEXT    NOT NULL,       -- stored as YYYY-MM-DD
    description TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
)
```

## Templates

- **Modify:** `templates/dashboard.html`
  - Replace the two quick-link cards with a full expense dashboard:
    - Top row: 3 summary stat cards — Total Expenses (count), Total Spent
      (sum of amount), Biggest Category (category with highest total)
    - "Add Expense" button (links to `/expenses/add`) anchored top-right of
      the expense section
    - Expense table: columns Date, Description, Category, Amount, Actions
      (Edit | Delete). Right-align the Amount column with tabular-nums.
      Show an empty-state message if the user has no expenses yet.
    - Table rows ordered by date DESC, then created_at DESC

- **Create:** `templates/expenses/add.html`
  - Extends `base.html`
  - Title: `Add Expense — Spendly`
  - Single card form with four fields (see Rules section for field spec)
  - Primary action "Add expense"; cancel link back to `/dashboard`

- **Create:** `templates/expenses/edit.html`
  - Extends `base.html`
  - Title: `Edit Expense — Spendly`
  - Same card layout as add form, all fields pre-populated from DB row
  - Primary action "Save changes"; cancel link back to `/dashboard`

## Files to change

- `app.py`
  - `/dashboard` route: query all expenses for `session['user_id']` ordered
    by date DESC; compute total count, total amount, and biggest category;
    pass all to `dashboard.html`
  - `/expenses/add` route: change to `methods=["GET", "POST"]`; implement
    validation and INSERT
  - `/expenses/<int:id>/edit` route: change to `methods=["GET", "POST"]`;
    fetch row, verify ownership, implement validation and UPDATE
  - `/expenses/<int:id>/delete` route: add `methods=["POST"]`; verify
    ownership; DELETE row

- `static/css/style.css`
  - Add dashboard summary card styles (`.summary-cards`, `.summary-card`,
    `.summary-card-value`, `.summary-card-label`)
  - Add expense table styles (`.expense-table`, row hover, right-aligned
    amount column, `.expense-table-empty`)
  - Add expense form card styles — reuse `.auth-card` or add
    `.expense-form-section` wrapper if needed
  - Add category badge styles (`.cat-badge` with per-category colour via
    data attribute or modifier class)

## Files to create

- `templates/expenses/add.html`
- `templates/expenses/edit.html`

## New dependencies
No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never use f-strings or `%` in SQL
- Use CSS variables — never hardcode hex colour values
- All templates extend `base.html`
- Use `flash()` for all user-facing messages
- Close every database connection with `try/finally`
- Guard every expense route with a session check; redirect to `/login` if missing
- **Ownership check:** before editing or deleting, verify
  `expense['user_id'] == session['user_id']`; if not, flash an error and
  redirect to `/dashboard` (do not 404, do not expose whether the row exists)
- **Form fields for add and edit:**
  - `amount` — required; must be a positive number (`float(amount) > 0`);
    store as REAL
  - `category` — required; must be one of the fixed list:
    Food, Transport, Bills, Health, Entertainment, Shopping, Other
  - `date` — required; must be a valid `YYYY-MM-DD` string; default to
    today's date on the GET form
  - `description` — optional; strip whitespace; store empty string as `""`
    if blank (not NULL)
- **Delete** uses a `<form method="POST">` button — no GET, no JS confirm
- **Empty state:** if the user has no expenses, show a friendly message in
  the table area with a link to add their first expense
- After a successful add → redirect to `/dashboard` with flash "Expense added."
- After a successful edit → redirect to `/dashboard` with flash "Expense updated."
- After a successful delete → redirect to `/dashboard` with flash "Expense deleted."
- On validation failure → flash error(s) and redirect back to the form
  (GET re-renders the form; on POST failure redirect to the same GET URL)

## Definition of done

- [ ] `/dashboard` shows the expense table for the logged-in user, ordered
      by date descending
- [ ] The 3 summary stat cards display correct values (count, total amount,
      biggest category)
- [ ] Visiting `/dashboard` with no expenses shows the empty-state message
- [ ] Clicking "Add Expense" navigates to `/expenses/add`
- [ ] The add form pre-fills today's date
- [ ] Submitting the add form with valid data inserts a row and redirects to
      `/dashboard` with flash "Expense added."
- [ ] Submitting the add form with a missing or zero amount flashes a
      validation error and does not insert
- [ ] Submitting the add form with an invalid category flashes an error
- [ ] Clicking Edit on a row navigates to `/expenses/<id>/edit` with all
      fields pre-populated
- [ ] Submitting the edit form with valid data updates the row and redirects
      to `/dashboard` with flash "Expense updated."
- [ ] Attempting to edit or delete another user's expense redirects to
      `/dashboard` with an error flash — it does not update or delete the row
- [ ] Clicking Delete on a row removes it from the DB and redirects to
      `/dashboard` with flash "Expense deleted."
- [ ] The demo user (`demo@spendly.com` / `demo123`) sees their 8 seeded
      expenses on the dashboard immediately after login
- [ ] All pages are responsive — table scrolls horizontally below ~768px,
      form cards stack or remain single-column cleanly on mobile
