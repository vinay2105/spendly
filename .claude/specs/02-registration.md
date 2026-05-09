# Spec: Registration

## Overview
Implement user account creation for Spendly. This step wires up the existing
`/register` route to accept form submissions, validates all input server-side,
hashes the password, persists the new user to the database, and redirects to
the login page on success. It is the first step that makes the application
interactive — until now every route was read-only or a placeholder.

## Depends on
- Step 01 — Database Setup (users table and `get_db()` must exist)

## Routes
- `GET  /register` — render the empty registration form — public
- `POST /register` — validate input, create user, redirect to `/login` — public

## Database changes
No new tables or columns. The existing `users` table already has all required
fields (`name`, `email`, `password_hash`, `created_at`).

## Templates
- **Modify:** `templates/register.html`
  - Add `<form method="POST" action="/register">` wrapping all inputs
  - Fields: `name` (text), `email` (email), `password` (password),
    `confirm_password` (password)
  - Display flashed error messages above the form
  - Display a success flash message when redirected back from a failed state
  - All field names must match what `request.form` reads in `app.py`

## Files to change
- `app.py`
  - Add `from flask import request, redirect, url_for, flash, session`
  - Set `app.secret_key` (required for `flash()` to work)
  - Replace the `GET`-only `/register` route with a `GET/POST` handler
  - POST handler logic:
    1. Read `name`, `email`, `password`, `confirm_password` from `request.form`
    2. Strip whitespace from all fields
    3. Validate — collect all errors before returning:
       - `name` must not be empty
       - `email` must not be empty
       - `password` must be at least 8 characters
       - `password` and `confirm_password` must match
    4. If validation errors exist → flash each error and re-render the form
    5. Check email uniqueness: `SELECT id FROM users WHERE email = ?`
    6. If email taken → flash "Email already registered." and re-render
    7. Hash password: `generate_password_hash(password)`
    8. Insert: `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)`
    9. `conn.commit()` then `conn.close()`
    10. Flash "Account created! Please log in." and `redirect(url_for('login'))`

## Files to create
None.

## New dependencies
None. `werkzeug.security` is already installed as part of Flask.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never use f-strings or % formatting in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex colour values in templates
- All templates extend `base.html`
- Use `flash()` for all user-facing messages — never put error text in the URL
- Validate server-side even if the HTML form has `required` attributes
- Close every database connection (use try/finally or check that all paths close)
- `app.secret_key` must be set before any route uses `flash()` or `session`

## Definition of done
- [ ] Submitting the form with all valid, unique data creates a row in `users`
- [ ] The stored password is a werkzeug hash, not plain text
- [ ] Successful registration redirects to `/login` with a flash success message
- [ ] Submitting with an already-registered email shows an error on the form
- [ ] Submitting with mismatched passwords shows an error on the form
- [ ] Submitting with a password shorter than 8 characters shows an error
- [ ] Submitting with any blank field shows an error
- [ ] The form re-renders with an error message — user does not lose their input
  (name and email fields should stay populated on re-render)
- [ ] App starts without errors after changes to `app.py`
