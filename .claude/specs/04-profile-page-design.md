# Spec: Profile Page Design

## Overview
Implement the user profile page for Spendly. This step replaces the stub
`/profile` route with a fully functional page where authenticated users can
view their account details (name, email, member-since date), update their
name and email address, and change their password. The page is split into
two independent forms so that each action is self-contained and flashes
contextual success or error messages. This is the last auth-adjacent step
before the app moves on to expense management.

## Depends on
- Step 01 — Database Setup (`get_db()` and `users` table must exist)
- Step 02 — Registration (user accounts must exist)
- Step 03 — Login and Logout (session must be set for the guard to work)

## Routes
- `GET  /profile`          — render profile page with current user data — logged-in
- `POST /profile`          — update name and email — logged-in
- `POST /profile/password` — change password — logged-in

## Database changes
No database changes. The existing `users` table has all required fields
(`id`, `name`, `email`, `password_hash`, `created_at`).

## Templates
- **Create:** `templates/profile.html`
  - Extends `base.html`
  - Title: `Profile — Spendly`
  - Two distinct card sections side by side (or stacked on mobile):
    1. **Account Details** — form with Name and Email fields, "Save changes" button
    2. **Change Password** — form with Current Password, New Password, Confirm New
       Password fields, "Update password" button
  - Below the cards, a read-only "Member since" line showing `created_at`
  - All form inputs use `.form-input`, labels use `.form-group label`
  - Buttons use `.btn-submit` (or `.btn-primary` where full-width is not needed)
  - Use CSS variables only — never hardcode hex values
  - Flash messages are handled by `base.html`; no inline error template vars

## Files to change
- `app.py`
  - Replace the GET-only `/profile` stub with a `GET` handler:
    1. Guard: if `session.get('user_id')` is falsy → redirect to `url_for('login')`
    2. Query: `SELECT id, name, email, created_at FROM users WHERE id = ?`
       using `session['user_id']`
    3. Render `profile.html` passing the `user` row
  - Add a `POST /profile` handler (same route, method `["GET","POST"]`):
    1. Guard session as above
    2. Read `name` and `email` from `request.form` (strip whitespace)
    3. Validate: both fields required; email must contain `@`
    4. Check no other user owns the new email:
       `SELECT id FROM users WHERE email = ? AND id != ?`
    5. If validation fails → flash error(s) and redirect to `url_for('profile')`
    6. `UPDATE users SET name = ?, email = ? WHERE id = ?`
    7. Update `session['user_name']` to the new name
    8. Flash "Profile updated successfully." with category `"success"`
    9. Redirect to `url_for('profile')`
  - Add a `POST /profile/password` route:
    1. Guard session
    2. Read `current_password`, `new_password`, `confirm_password` from `request.form`
    3. Validate: all three fields required; new password ≥ 8 characters;
       new and confirm must match
    4. Fetch `password_hash` from DB: `SELECT password_hash FROM users WHERE id = ?`
    5. `check_password_hash(row['password_hash'], current_password)` — if False →
       flash "Current password is incorrect." and redirect to `url_for('profile')`
    6. `UPDATE users SET password_hash = ? WHERE id = ?` with
       `generate_password_hash(new_password)`
    7. Flash "Password updated successfully." with category `"success"`
    8. Redirect to `url_for('profile')`

## Files to create
- `templates/profile.html` — see Templates section above

## New dependencies
No new dependencies. `werkzeug.security` functions are already available.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never use f-strings or `%` formatting in SQL
- Passwords verified/hashed with `werkzeug.security` (`check_password_hash`,
  `generate_password_hash`)
- Use CSS variables — never hardcode hex colour values
- All templates extend `base.html`
- Use `flash()` for all user-facing messages — no `{{ error }}` template vars
- Close every database connection with `try/finally`
- Guard both `/profile` (GET+POST) and `/profile/password` (POST) with a
  session check; redirect to `/login` if the session is missing
- Never reveal the stored hash or whether an email exists to a different account
  via timing — keep error messages generic where possible
- Pre-populate the Name and Email fields with the current user values on GET
  and after a failed update redirect (use `request.form` fallback pattern via
  query re-fetch)

## Definition of done
- [ ] Visiting `/profile` without a session redirects to `/login`
- [ ] `/profile` renders correctly for a logged-in user, showing their name,
      email, and member-since date
- [ ] Name and Email fields are pre-populated with the user's current values
- [ ] Submitting the Account Details form with valid data updates the DB and
      flashes "Profile updated successfully."
- [ ] After a name update, the navbar greeting ("Hi, [name]") reflects the new name
- [ ] Submitting the Account Details form with a blank name or email flashes
      a validation error and does not update the DB
- [ ] Attempting to change the email to one already used by another account
      flashes an error and does not update the DB
- [ ] Submitting the Change Password form with the correct current password and
      matching new passwords (≥ 8 chars) updates the hash and flashes success
- [ ] Submitting the Change Password form with the wrong current password flashes
      "Current password is incorrect." and does not update the hash
- [ ] Submitting the Change Password form with mismatched new/confirm passwords
      flashes an error
- [ ] Submitting the Change Password form with a new password shorter than 8
      characters flashes a validation error
- [ ] After a successful password change, the user can log in with the new password
- [ ] The demo user (`demo@spendly.com` / `demo123`) can view and update their profile
