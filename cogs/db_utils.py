import logging
import sqlite3

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)


def db_init():
    try:
        con = sqlite3.connect("bot.db")
        logging.info("Connected to the database.")
        create_tables(con)
        return con
    except sqlite3.Error as e:
        logging.error("Error initializing database.")
        return None


def create_tables(con):
    try:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                ctf_creators INTEGER,
                leaderboard_channel_id INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS challenge_data (
                day INTEGER PRIMARY KEY AUTOINCREMENT,
                master_id INTEGER,
                description TEXT,
                answer TEXT,
                hints TEXT,
                writeup TEXT,
                start_time INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                user_id INTEGER PRIMARY KEY,
                submission TIMESTAMP
            )
        """)

        con.commit()

    except sqlite3.Error as e:
        logging.error(f"Error creating tables: {e}")

def update_config(con, key: str, value: int):
    try:
        cur = con.cursor()

        # Check if the record with id = 0 exists
        cur.execute("SELECT id FROM config WHERE id = 0")
        existing_record = cur.fetchone()

        if existing_record:
            # Update the existing record
            query = f"UPDATE config SET {key} = ? WHERE id = 0"
            cur.execute(query, (value,))
        else:
            # Insert a new record with id = 0
            query = f"INSERT INTO config (id, {key}) VALUES (0, ?)"
            cur.execute(query, (value,))

        con.commit()
        logging.info("Updated table config successfully.")
        return True
    except sqlite3.Error as e:
        logging.error(f"Error updating table config: {e}")
        return False

def insert_challenge(con, master_id: int, description: str, answer: str, hints: str, writeup: str):
    try:
        cur = con.cursor()

        cur.execute("DELETE FROM challenge_data")

        cur.execute("""INSERT INTO challenge_data (master_id, description, answer, hints, writeup, start_time) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                    master_id,
                    description,
                    answer,
                    hints,
                    writeup,
                    start_time)
        con.commit()
        logging.info("Inserted into table challenge_data successfully.")
        return True

    except sqlite3.Error as e:
        logging.error(f"Error inserting table challenge_data: {e}")
        return False


def insert_leaderboard(con, user_id: int, submission: int):
    try:
        cur = con.cursor()

        cur.execute(
            "INSERT INTO leaderboard (user_id, submission) VALUES (?, ?)", user_id, submission)
        con.commit()
        logging.info("Inserted into table leaderboard successfully.")
        return True

    except sqlite3.Error as e:
        logging.error(f"Error inserting table leaderboard: {e}")
        return False


def fetch_config(con):
    try:
        cur = con.cursor()

        cur.execute("SELECT * FROM config")
        row - cur.fetchone()
        return row
    except sqlite3.Error as e:
        logging.error(f"Error fetching table config: {e}")
