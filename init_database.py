import sqlite3

# Create connection and cursor
conn = sqlite3.connect('expenses.db')
c = conn.cursor()

# Delete all records from the expenses table
c.execute('''DELETE FROM expenses''')

# Commit changes and close connection
conn.commit()

# Create table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS expenses (
             id INTEGER PRIMARY KEY,
             user_id INTEGER,
             category TEXT,
             amount REAL,
             description TEXT,
             date DATE
             )''')

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized successfully.")
