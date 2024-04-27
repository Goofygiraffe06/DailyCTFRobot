import unittest
import sqlite3
import sys
import os
sys.path.append(os.path.abspath('..'))

from cogs.db_utils import *

class TestDatabaseFunctions(unittest.TestCase):
    def setUp(self):
        """
        Initialize a test database in memory and create tables before each test case.
        """
        self.con = sqlite3.connect(":memory:")
        create_tables(self.con)

    def tearDown(self):
        """
        Close the database connection after each test case.
        """
        self.con.close()

    def test_fetch_challenge_data(self):
        """
        Test the fetch_challenge_data function.
        """
        # Test fetching challenge data when no data is present
        self.assertIsNone(fetch_challenge_data(self.con), "Expected None when no challenge data is present.")

        # Insert test data
        test_data = (1, 123, "Test description", "Test answer", "", "Test hints", "Test writeup", 0, "2024-04-25 12:00:00")
        cur = self.con.cursor()
        cur.execute("INSERT INTO challenge_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", test_data)
        self.con.commit()

        # Test fetching challenge data when data is present
        fetched_data = fetch_challenge_data(self.con)
        self.assertIsNotNone(fetched_data, "Expected challenge data when inserted.")
        self.assertEqual(fetched_data['description'], "Test description")

    def test_fetch_leaderboard_data(self):
        """
        Test the fetch_leaderboard_data function.
        """
        # Test fetching leaderboard data when no data is present
        self.assertEqual(fetch_leaderboard_data(self.con), [], "Expected empty list when no leaderboard data is present.")

        # Insert test data
        cur = self.con.cursor()
        cur.execute("INSERT INTO leaderboard (user_id, submission) VALUES (?, ?)", (123, "2024-04-25 12:00:00"))
        self.con.commit()

        # Test fetching leaderboard data when data is present
        fetched_data = fetch_leaderboard_data(self.con)
        self.assertIsNotNone(fetched_data, "Expected leaderboard data when inserted.")
        self.assertEqual(len(fetched_data), 1)

    def test_fetch_rating(self):
        """
        Test the fetch_rating function.
        """
        # Test fetching ratings data when no data is present
        self.assertEqual(fetch_rating(self.con), [], "Expected empty list when no ratings data is present.")

        # Insert test data
        cur = self.con.cursor()
        cur.execute("INSERT INTO ratings (user_id, rating) VALUES (?, ?)", (123, 5))
        self.con.commit()

        # Test fetching ratings data when data is present
        fetched_data = fetch_rating(self.con)
        self.assertIsNotNone(fetched_data, "Expected ratings data when inserted.")
        self.assertEqual(len(fetched_data), 1)

    def test_remove_challenge_data(self):
        """
        Test the remove_challenge_data function.
        """
        # Insert test data
        test_data = (1, 123, "Test description", "Test answer", "", "Test hints", "Test writeup", 0, "2024-04-25 12:00:00")
        cur = self.con.cursor()
        cur.execute("INSERT INTO challenge_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", test_data)
        self.con.commit()

        # Test removing challenge data
        remove_challenge_data(self.con)
        fetched_data = fetch_challenge_data(self.con)
        self.assertIsNone(fetched_data, "Expected None after challenge data is removed.")

    def test_insert_challenge(self):
        """
        Test the insert_challenge function.
        """
        # Test inserting challenge data
        values = (123, "Test description", "Test answer", "", "Test hints", "Test writeup")
        result = insert_challenge(self.con, values)
        self.assertTrue(result, "Expected True when challenge data is inserted.")

        # Add assertions for inserted data
        fetched_data = fetch_challenge_data(self.con)
        self.assertIsNotNone(fetched_data, "Expected challenge data when inserted.")
        self.assertEqual(fetched_data['description'], "Test description")

    def test_insert_leaderboard(self):
        """
        Test the insert_leaderboard function.
        """
        # Test inserting leaderboard data
        user_id = 123
        result = insert_leaderboard(self.con, user_id)
        self.assertTrue(result, "Expected True when leaderboard data is inserted.")

        # Add assertions for inserted data
        fetched_data = fetch_leaderboard_data(self.con)
        self.assertIsNotNone(fetched_data, "Expected leaderboard data when inserted.")
        self.assertEqual(len(fetched_data), 1)

    def test_insert_rating(self):
        """
        Test the insert_rating function.
        """
        # Test inserting ratings data
        user_id = 123
        rating = 5
        result = insert_rating(self.con, user_id, rating)
        self.assertTrue(result, "Expected True when ratings data is inserted.")

        # Add assertions for inserted data
        fetched_data = fetch_rating(self.con)
        self.assertIsNotNone(fetched_data, "Expected ratings data when inserted.")
        self.assertEqual(len(fetched_data), 1)

    def test_update_config(self):
        """
        Test the update_config function.
        """
        # Test updating config
        key = 'channel_id'
        value = 12345
        result = update_config(self.con, key, value)
        self.assertTrue(result, "Expected True when config is updated.")

        # Add assertions for updated config
        cur = self.con.cursor()
        cur.execute("SELECT channel_id FROM config WHERE id = 0")
        fetched_data = cur.fetchone()
        self.assertIsNotNone(fetched_data, "Expected config data when updated.")
        self.assertEqual(fetched_data[0], value)

    def test_fetch_challenge_data_not_exist(self):
        """
        Test fetching challenge data when no data exists.
        """
        fetched_data = fetch_challenge_data(self.con)
        self.assertIsNone(fetched_data, "Expected None when no challenge data exists.")

    def test_update_config_invalid_key(self):
        """
        Test updating config with an invalid key.
        """
        # Test updating config with an invalid key
        key = 'invalid_key'
        value = 12345
        result = update_config(self.con, key, value)
        self.assertFalse(result, "Expected False when updating config with an invalid key.")

if __name__ == '__main__':
    unittest.main()

