import sqlite3

conn = sqlite3.connect("matches.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS matches;")
conn.commit()
conn.close()

print("✅ Ο πίνακας 'matches' διαγράφηκε με επιτυχία.")
