-- BACK UP THE DATABASE FIRST. Run this once against the app's MySQL database.
-- Existing users are set to staff to preserve access for current POS accounts.
ALTER TABLE users
  ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'staff';

-- Supported values are customer, staff, admin. Public registration creates customer only.
-- After reviewing accounts, manually demote any account that should not use the POS.
-- Example for one trusted administrator (replace username):
-- UPDATE users SET role = 'admin' WHERE username = 'your_trusted_admin_username';
