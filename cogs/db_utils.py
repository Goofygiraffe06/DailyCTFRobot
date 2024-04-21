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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                ctf_creators INTEGER,
                leaderboard_channel_id INTEGER
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS challenge_data (
                day INTEGER PRIMARY KEY AUTOINCREMENT,
                master_id INTEGER,
                description TEXT,
                answer TEXT,
                attachment TEXT,
                hints TEXT,
                writeup TEXT,
                hints_released INTEGER DEFAULT 0,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS leaderboard (
                user_id INTEGER,
                submission TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                user_id INTEGER PRIMARY KEY,
                rating INTEGER
            )
        """
        )

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


def insert_challenge(con, values):
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM challenge_data")
        cur.execute("DELETE FROM leaderboard")
        cur.execute("DELETE FROM ratings")

        con.commit()

        cur.execute(
            """INSERT INTO challenge_data (master_id, description, answer, attachment, hints, writeup)
                        VALUES (?, ?, ?, ?, ?, ?)""",
            values,
        )
        con.commit()
        logging.info("Inserted into table challenge_data successfully.")
        return True
    except sqlite3.Error as e:
        logging.error(f"Error inserting table challenge_data: {e}")
        return False


def insert_leaderboard(con, user_id: int):
    try:
        cur = con.cursor()

        cur.execute("INSERT INTO leaderboard (user_id) VALUES (?)", (user_id,))
        con.commit()
        logging.info("Inserted into table leaderboard successfully.")
        return True

    except sqlite3.Error as e:
        logging.error(f"Error inserting table leaderboard: {e}")
        return False


def len_leaderboard(con):
    try:
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM leaderboard")
        rows = cur.fetchone()

        return rows[0]
    except sqlite3.Error as e:
        logging.error(f"Error counting table leaderboard: {e}")


def check_leaderboard(con, user_id: int):
    try:
        cur = con.cursor()

        cur.execute("SELECT * FROM leaderboard WHERE user_id = ?", (user_id,))
        existing_record = cur.fetchone()

        if existing_record:
            return True
        else:
            return False

    except sqlite3.Error as e:
        logging.error(f"Error checking table leaderboard: {e}")


def update_hint(con):
    try:
        cur = con.cursor()

        cur.execute("UPDATE leaderboard SET hints_released = 1")
    except sqlite3.Error as e:
        logging.error(f"Error updating hints_released table leaderboard: {e}")


def insert_rating(con, user_id: int, rating: int):
    try:
        cur = con.cursor()

        # Check if the user ID already exists in the table
        cur.execute("SELECT * FROM ratings WHERE user_id = ?", (user_id,))
        existing_rating = cur.fetchone()

        if existing_rating:
            # If the user ID exists, return False
            return False
        else:
            # If the user ID doesn't exist, insert a new row
            cur.execute(
                "INSERT INTO ratings (user_id, rating) VALUES (?, ?)", (user_id, rating)
            )
            con.commit()
            return True
    except sqlite3.Error as e:
        logging.error(f"Error inserting table rating: {e}")


def fetch_config(con):
    try:
        cur = con.cursor()

        cur.execute("SELECT * FROM config")
        row = cur.fetchone()
        if row:
            return {
                "channel_id": row[1],
                "ctf_creators": row[2],
                "leaderboard_channel_id": row[3],
            }
    except sqlite3.Error as e:
        logging.error(f"Error fetching table config: {e}")
        return None


def fetch_challenge_data(con):
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM challenge_data")
        row = cur.fetchone()
        if row:
            return {
                "day": row[0],
                "master_id": row[1],
                "description": row[2],
                "answer": row[3],
                "attachment": row[4],
                "hints": row[5],
                "writeup": row[6],
                "hints_released": row[7],
                "start_time": row[8],
            }
        else:
            return None
    except sqlite3.Error as e:
        logging.error(f"Error fetching challenge data: {e}")


def remove_challenge_data(con):
    try:
        cur = con.cursor()

        cur.execute("BEGIN TRANSACTION")

        cur.execute("DELETE FROM challenge_data")
        cur.execute("DELETE FROM leaderboard")
        cur.execute("DELETE FROM ratings")
        con.commit()
        logging.info("Deleted table challenge_data successfully.")

    except sqlite3.Error as e:
        logging.error(f"Error deleting table challenge_data: {e}")


def fetch_leaderboard_data(con):
    try:
        cur = con.cursor()

        cur.execute(
            "SELECT user_id, submission FROM leaderboard ORDER BY submission ASC"
        )
        leaderboard_data = cur.fetchall()
        return leaderboard_data

    except Exception as e:
        logging.error(f"Error fetching leaderboard data. Error: {e}")
        return None


def fetch_rating(con):
    try:
        cur = con.cursor()

        cur.execute("SELECT user_id, rating FROM ratings")
        ratings_data = cur.fetchall()
        return ratings_data

    except sqlite3.Error as e:
        logging.error(f"Error fetching table ratings: {e}")
