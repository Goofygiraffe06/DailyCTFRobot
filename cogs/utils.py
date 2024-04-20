import logging
import asyncio
import datetime
import json
import discord
from discord.ext import commands
from .db_utils import db_init, fetch_config, update_config, fetch_challenge_data, remove_challenge_data, len_leaderboard, update_hint, fetch_rating, insert_rating

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)

def load_challenge_data():
    try:
        with open("challenge_data.txt", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.warning("Challenge data not found. Returning empty data.")
        return {}
    except json.JSONDecodeError:
        logging.warning("Challenge data corrupted. Returning empty data.")
        return {}


def save_challenge_data(data):
    try:
        with open("challenge_data.txt", "w") as file:
            json.dump(data, file, indent=4)
        logging.info("Challenge data saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save challenge data. Error: {e}")


def load_config():
    try:
        with open("config.json", "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.warning("Config not found. Returning empty data.")
        return {}
    except json.JSONDecodeError:
        logging.warning("Config corrupted. Returning empty data.")
        return {}


def save_config(config_data):
    try:
        with open("config.json", "w") as config_file:
            json.dump(config_data, config_file, indent=4)
        return config_data
    except Exception as e:
        logging.error(f"Failed to save config data. Error: {e}")
        return {}

con = db_init()

async def end_challenge(bot):
    config = fetch_config(con)
    challenge_data = fetch_challenge_data(con)
    
    if challenge_data is None:
        return 

    if challenge_data["start_time"] != "":
        start_time = datetime.datetime.strptime(challenge_data["start_time"], '%Y-%m-%d %H:%M:%S')
        elapsed_time = datetime.datetime.utcnow() - start_time
        remaining_time = 86400 - elapsed_time.total_seconds()

        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
    else:
        await asyncio.sleep(86400)

    challenge_channel = bot.get_channel(config["challenge_channel"])

    if challenge_channel:
        await display_leaderboard(bot)
        await challenge_channel.send(
            f"Day-{challenge_data['day']} Challenge has finished!"
        )
        logging.info(
            f"Day-{challenge_data['day']} challenge has been finished..."
        )

        if 'writeup' in challenge_data and challenge_data['writeup']:
            await challenge_channel.send(
                f"Writeup for Day-{challenge_data['day']}: {challenge_data['writeup']}"
            )
        else:
            await challenge_channel.send(
                f"No writeup provided for Day-{challenge_data['day']}."
            )

        avg = calculate_average_rating()
        if avg is not None:
            await challenge_channel.send(
                f"The average rating for the challenge is: {avg:.2f}"
            )
        else:
            await challenge_channel.send("No ratings received for the challenge.")
        remove_challenge_data(con)

async def display_leaderboard(bot):
    config = fetch_config(con)
    leaderboard_data = fetch_leaderboard(con)

    if not leaderboard_data:
        logging.warning("No leaderboard data available.")
        return

    leaderboard_msg = f"🏆 **The winners of today's CTF are:** 🏆\n"
    position_emojis = ["🥇", "🥈", "🥉"]

    for i, (user_id, timestamp) in enumerate(leaderboard_data[:3]):
        user = bot.get_user(int(user_id))
        if user:
            leaderboard_msg += f"{position_emojis[i]} {user.mention}\n"

    challenge_channel = bot.get_channel(config['leaderboard_channel_id'])
    if challenge_channel:
        await challenge_channel.send(leaderboard_msg)

def calculate_average_rating():
    challenge_data = fetch_challenge_data(con)
    ratings_data = fetch_rating(con)
    
    if challenge_data and ratings_data:
        total_ratings = sum(rating[1] for rating in ratings_data)
        num_ratings = len(ratings_data)
        
        if num_ratings > 0:
            average_rating = total_ratings / num_ratings
            return average_rating
        else:
            return None
    else:
        logging.warning("No challenge data or ratings data available. Unable to calculate average rating.")
        return None

class RateView(discord.ui.View):

    def __init__(self):
        super().__init__()

        for i in range(1, 6):
            self.add_item(RateButton(rating=i))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

class RateButton(discord.ui.Button):

    def __init__(self, rating: int):
        super().__init__(label=str(rating), custom_id=f'rate_{rating}')
        self.rating = rating

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        rating_inserted = insert_rating(con, user_id, self.rating)
        if rating_inserted:
            await interaction.response.send_message(
                f'You rated the challenge {self.rating} stars!', ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f'You already rated the challenge.'
            )

async def release_hints(bot):
    logging.info("Function release_hints started.")

    challenge_data = fetch_challenge_data(con)
    if not challenge_data:
        logging.warning("No challenge data available. Exiting release_hints.")
        return

    if "start_time" in challenge_data:
        start_time = datetime.datetime.strptime(challenge_data["start_time"], '%Y-%m-%d %H:%M:%S')
        elapsed_time = datetime.datetime.utcnow() - start_time
        remaining_time = 21600 - elapsed_time.total_seconds()

        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
    else:
        logging.error(
            "start_time not found in challenge_data. Unable to determine hint release time."
        )

    config = fetch_config(con)

    if challenge_data["hints"] != "" and len_leaderboard(con) == 0:
        challenge_channel = bot.get_channel(config["challenge_channel"])
        if challenge_channel:
            await challenge_channel.send(
                f"Hint for Day-{challenge_data['day']}: `{challenge_data['hints']}`"
            )
            logging.info(f"Hint for Day-{challenge_data['day']} released.")

        update_hint(con)
    else:
        logging.warning(
            "Hints were either already revealed or there is an active leaderboard. No hint was released."
        )

async def check_rating(interaction):
    challenge_data = fetch_challenge_data(con)
    if challenge_data:
        ratings = fetch_rating(con)
        for rating in ratings:
            if (rating[0] == interaction.user.id): 
                await interaction.followup.send("You've already submitted!", ephemeral=True)
                return

        view = RateView()
        await interaction.followup.send(
            "Rate today's challenge:", view=view, ephemeral=True
        )

    else:
        logging.warning("No challenge data available. Unable to check rating.")

