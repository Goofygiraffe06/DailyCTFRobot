# cogs/db_utils.py - It has functions to CRUD (CREATE, READ, UPDATE, DELETE) with the databae.

import logging
import sqlite3

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)


def db_init():
    """
    Creates a new database file if it doesn't exists and then runs the create_tables function.
    """
    try:
        con = sqlite3.connect("bot.db")
        logging.info("Connected to the database.")
        create_tables(con)
        return con
    except sqlite3.Error as e:
        logging.error("Error initializing database.")
        return None


def create_tables(con):
    """
    It is executed for every connection to the database to verify and repair any inconsitencies in the database,
    It creates a missing table if it doesn't exists.
    """
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
    """
    Updates the config table of the database, As this bot is made for single server use only,
    We use the id 0, to effectively update each attribute of the table independently.
    """
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
    """
    Inserts data into challenge_data table, first it goes by deleting few other tables because,
    When we are inserting a new challenge that means we also no longer want the old data in other tables
    and then finally inserts the supplied data.
    """
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
    """
    Simple function to insert a record to the leaderboard tables.
    """
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
    """
    A simple function which returns the length of the table, used for determining the position in submit command.
    """
    try:
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM leaderboard")
        rows = cur.fetchone()

        return rows[0]
    except sqlite3.Error as e:
        logging.error(f"Error counting table leaderboard: {e}")


def check_leaderboard(con, user_id: int):
    """
    A function to check if a specific user has already answered the challenge.
    """
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
    """
    Function which is used to set the hints_released coloumn to True (1).
    """
    try:
        cur = con.cursor()

        cur.execute("UPDATE leaderboard SET hints_released = 1")
    except sqlite3.Error as e:
        logging.error(f"Error updating hints_released table leaderboard: {e}")


def insert_rating(con, user_id: int, rating: int):
    """
    A Function which is responsible for inserting ratings, it firstly check if that user id has already
    rated the challenge or not, If yes, it returns False else True and inserts the data.
    """
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
    """
    A function which is used to return all the records and return it as dictionary,
    if their is no config then it returns False.
    """
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

def generate_title(con):
    try:
        cur = con.cursor()
        
        cur.execute("SELECT * FROM sqlite_sequence")
        day = cur.fetchone()
        
        if day:
            return f"Set a Challenge for Day {day[1] + 1}"
        else:
            return "Set a Challenge"
    
    except sqlite3.Error as e:
        logging.error(f"Error generating title: {e}")

