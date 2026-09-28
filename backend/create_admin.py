"""
Run once to create the default admin user in the SQLite database.
Usage: python create_admin.py
"""
import sys, uuid, sqlite3

sys.path.insert(0, ".")
from app.core.auth import hash_password

EMAIL    = "admin@knowsphere.ai"
NAME     = "Admin"
PASSWORD = "admin123"

hashed  = hash_password(PASSWORD)
user_id = str(uuid.uuid4())

conn = sqlite3.connect("data/knowsphere.db")
cur  = conn.cursor()

cur.execute(
    "INSERT OR IGNORE INTO users (id, email, name, password_hash) VALUES (?, ?, ?, ?)",
    (user_id, EMAIL, NAME, hashed),
)
conn.commit()

cur.execute("SELECT id, email, name FROM users")
print("Users in DB:", cur.fetchall())
conn.close()

print(f"\n✅  Done! Log in with:\n   Email   : {EMAIL}\n   Password: {PASSWORD}")
