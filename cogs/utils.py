import logging
import asyncio
import datetime
import json
import discord
from discord.ext import commands

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


async def end_challenge(bot):
    config = load_config()
    challenge_data = load_challenge_data()

    if "start_time" in challenge_data:
        start_time = datetime.datetime.fromtimestamp(challenge_data["start_time"])
        elapsed_time = datetime.datetime.utcnow() - start_time
        remaining_time = 86400 - elapsed_time.total_seconds()

        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
    else:
        await asyncio.sleep(86400)

    challenge_channel = bot.get_channel(int(config.get("channel_id", 0)))

    if challenge_channel:
        await display_leaderboard(bot)
        await challenge_channel.send(
            f"Day-{challenge_data.get('day', 'N/A')} Challenge has finished!"
        )
        logging.info(
            f"Day-{challenge_data.get('day', 'N/A')} challenge has been finished..."
        )

        if 'writeup' in challenge_data and challenge_data['writeup']:
            await challenge_channel.send(
                f"Writeup for Day-{challenge_data.get('day', 'N/A')}: {challenge_data['writeup']}"
            )
        else:
            await challenge_channel.send(
                f"No writeup provided for Day-{challenge_data.get('day', 'N/A')}."
            )

        avg = calculate_average_rating()
        if avg is not None:
            await challenge_channel.send(
                f"The average rating for the challenge is: {avg:.2f}"
            )
        else:
            await challenge_channel.send("No ratings received for the challenge.")
        save_challenge_data({})


async def display_leaderboard(bot):
    config = load_config()
    challenge_data = load_challenge_data()
    if not challenge_data:
        return

    sorted_leaderboard = sorted(
        challenge_data.get("leaderboard", {}).items(), key=lambda x: x[1]
    )

    leaderboard_msg = f"🏆 **The winners of today's CTF (Day-{challenge_data.get('day', 'N/A')}) are:** 🏆\n"
    position_emojis = ["🥇", "🥈", "🥉"]
    for i, (user_id, _) in enumerate(sorted_leaderboard[:3]):
        user = bot.get_user(int(user_id))
        if user:
            leaderboard_msg += f"{position_emojis[i]} {user.mention}\n"

    challenge_channel = bot.get_channel(int(config.get("channel_id", 0)))
    if challenge_channel:
        await challenge_channel.send(leaderboard_msg)


def calculate_average_rating():
    challenge_data = load_challenge_data()
    if not challenge_data or "ratings" not in challenge_data:
        return None

    total_ratings = sum(rate["rating"] for rate in challenge_data["ratings"])
    if not total_ratings or not challenge_data["ratings"]:
        return None

    average_rating = total_ratings / len(challenge_data["ratings"])
    return average_rating


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
        challenge_data = load_challenge_data()

        challenge_data.setdefault('ratings', []).append(
            {'user': user_id, 'rating': self.rating}
        )
        save_challenge_data(challenge_data)

        await interaction.response.send_message(
            f'You rated the challenge {self.rating} stars!', ephemeral=True
        )


async def release_hints(bot):
    logging.info("Function release_hints started.")

    challenge_data = load_challenge_data()
    if not challenge_data:
        logging.warning("No challenge data available. Exiting release_hints.")
        return

    if "start_time" in challenge_data:
        start_time = datetime.datetime.fromtimestamp(challenge_data["start_time"])
        elapsed_time = datetime.datetime.utcnow() - start_time
        remaining_time = 21600 - elapsed_time.total_seconds()

        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
    else:
        logging.error(
            "start_time not found in challenge_data. Unable to determine hint release time."
        )

    config = load_config()

    if not challenge_data.get("hints_revealed", False) and not challenge_data.get(
        "leaderboard", {}
    ):
        challenge_channel = bot.get_channel(int(config.get("channel_id", 0)))
        if challenge_channel:
            await challenge_channel.send(
                f"Hint for Day-{challenge_data.get('day', 'N/A')}: `{challenge_data.get('hints', 'No hints available')}`"
            )
            logging.info(f"Hint for Day-{challenge_data.get('day', 'N/A')} released.")

        challenge_data["hints_revealed"] = True
        save_challenge_data(challenge_data)
    else:
        logging.warning(
            "Hints were either already revealed or there is an active leaderboard. No hint was released."
        )


async def check_rating(interaction):
    challenge_data = load_challenge_data()
    user_ratings = [rating['user'] for rating in challenge_data.get('ratings', [])]
    if str(interaction.user.id) not in user_ratings:
        view = RateView()
        await interaction.followup.send(
            "Rate today's challenge:", view=view, ephemeral=True
        )
    else:
        await interaction.followup.send("You've already submitted!", ephemeral=True)
