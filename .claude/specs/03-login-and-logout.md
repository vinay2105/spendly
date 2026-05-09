# Spec: Login and Logout

## Overview
Implement session-based authentication for Spendly. This step wires up the
existing `/login` route to accept credentials, verifies the password hash,
stores the user identity in Flask's signed session cookie, and redirects to a
new `/dashboard` page. The `/logout` route clears the session and redirects to
the landing page. It also updates the navbar to show contextual links depending
on whether the user is signed in. After this step the app has a complete
auth loop: register → login → dashboard → logout.

## Depends on
- Step 01 — Database Setup (`get_db()` and `users` table must exist)
- Step 02 — Registration (users must be able to create accounts to log in)

## Routes
- `GET  /login`     — render the login form — public
- `POST /login`     — validate credentials, set session, redirect to `/dashboard` — public
- `GET  /logout`    — clear session, redirect to `/` — logged-in
- `GET  /dashboard` — show the authenticated home page — logged-in

## Database changes
No database changes. The existing `users` table has all required fields.

## Templates
- **Modify:** `templates/login.html`
  - Replace the `{% if error %}` / `{{ error }}` block with the standard
    `get_flashed_messages` pattern already used in `base.html`
  - Keep the existing form fields (`email`, `password`) and layout unchanged
  - Repopulate the `email` field on re-render: `value="{{ request.form.get('email', '') }}"`

- **Modify:** `templates/base.html`
  - Update the `<div class="nav-links">` block to be session-aware:
    - If `session.user_id` is set: show "Hi, [name]" (non-link) and a
      "Sign out" link to `url_for('logout')`
    - If not logged in: keep existing "Sign in" and "Get started" links
  - No other changes to `base.html`

- **Create:** `templates/dashboard.html`
  - Extends `base.html`
  - Title: `Dashboard — Spendly`
  - Displays a greeting: "Welcome back, [session.user_name]!"
  - Contains placeholder cards/links for upcoming features
    (Add Expense, View Profile) styled with existing CSS classes
  - No data fetched from the database in this step — static content only

## Files to change
- `app.py`
  - Add `session` to the existing Flask import line
  - Add `check_password_hash` to the existing `werkzeug.security` import
  - Replace the GET-only `/login` stub with a `GET/POST` handler:
    1. Read `email` and `password` from `request.form` (strip whitespace)
    2. Validate both fields are non-empty; flash error and re-render if not
    3. Query: `SELECT id, name, password_hash FROM users WHERE email = ?`
    4. If no row found → flash "Invalid email or password." and re-render
       (do NOT reveal which field was wrong)
    5. `check_password_hash(row['password_hash'], password)` — if False →
       flash same generic message and re-render
    6. On success: set `session['user_id'] = row['id']` and
       `session['user_name'] = row['name']`
    7. Redirect to `url_for('dashboard')`
  - Replace the `/logout` stub with a real handler:
    1. `session.clear()`
    2. Flash "You've been signed out." with category `"success"`
    3. Redirect to `url_for('landing')`
  - Add a new `/dashboard` route:
    1. If `session.get('user_id')` is falsy → redirect to `url_for('login')`
    2. Otherwise render `dashboard.html`

- `templates/login.html` — see Templates section above
- `templates/base.html` — see Templates section above

## Files to create
- `templates/dashboard.html` — see Templates section above

## New dependencies
No new pip packages. `werkzeug.security.check_password_hash` is already
available as part of Flask's Werkzeug dependency.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never use f-strings or % formatting in SQL
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex colour values in templates
- All templates extend `base.html`
- Use `flash()` for all user-facing messages — no `{{ error }}` template vars
- Always use a generic "Invalid email or password." message — never reveal
  which field failed (prevents user enumeration)
- Close every database connection with try/finally
- Guard `/dashboard` and `/logout` with a session check; redirect to `/login`
  if the session is missing

## Definition of done
- [ ] Submitting `/login` with valid credentials sets the session and redirects
      to `/dashboard`
- [ ] `/dashboard` shows "Welcome back, [name]!" with the correct user's name
- [ ] `/dashboard` redirects to `/login` when visited without a session
- [ ] Submitting `/login` with a wrong password shows "Invalid email or
      password." and does not log the user in
- [ ] Submitting `/login` with an unregistered email shows the same generic
      error message
- [ ] Submitting `/login` with a blank email or password shows a validation
      error
- [ ] The email field is repopulated after a failed login attempt
- [ ] Visiting `/logout` clears the session and redirects to the landing page
      with a flash success message
- [ ] After logout, visiting `/dashboard` redirects to `/login`
- [ ] The navbar shows "Sign in" / "Get started" when logged out, and
      "Hi, [name]" / "Sign out" when logged in
- [ ] The demo user (`demo@spendly.com` / `demo123`) can log in successfully
