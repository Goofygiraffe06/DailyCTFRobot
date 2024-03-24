# cogs/GeneralCommands,py -  Contains general-use commands such as submit, feedback and rating mechanism.

import discord
from discord.ext import commands
from .utils import load_config, load_challenge_data, save_challenge_data, display_leaderboard, release_hints, end_challenge, calculate_average_rating, check_rating
import logging
import datetime
from .utils import RateView

# Initialize logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
# Stopping keep_alive log messages as they make hard to read and are useless
# Suppress Flask development server log
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)

# Class to handle the feedback forms


class FeedbackModal(discord.ui.Modal, title="Send us your feedback"):
  fb_title = discord.ui.TextInput(
      style=discord.TextStyle.short,
      label="Title",
      required=False,
      placeholder="Give your feedback a title",
  )

  message = discord.ui.TextInput(
      style=discord.TextStyle.long,
      label="Message",
      required=True,  # made this required since this is the actual feedback
      max_length=500,
      placeholder="Give your message",
  )

  async def on_submit(self, interaction: discord.Interaction):
    channel = interaction.client.get_guild(914495197256228954).get_channel(
        914495197256228961)

    embed = discord.Embed(
        title=f"New Feedback: {self.fb_title.value}",
        description=self.message.value,
        color=discord.Color.yellow(),
    )
    embed.set_author(name=interaction.user.name,
                     icon_url=interaction.user.avatar.url)

    # Send the feedback to the feedback channel
    await channel.send(embed=embed)
    await interaction.response.send_message(
        "Thank you for your feedback! Join the Official bot server to check the status of your feedback here: https://discord.gg/CTWQm7KjCn",
        ephemeral=True,
    )

  async def on_error(self, interaction: discord.Interaction, error: Exception):
    await interaction.response.send_message(
        "Failed to send feedback. [Contact Creator](https://discordapp.com/users/749572519106838560)",
        ephemeral=True,
    )

# Class that handles the behaviour of rate button


class RateButton(discord.ui.Button):

  def __init__(self, rating: int):
    super().__init__(label=str(rating), custom_id=f'rate_{rating}')
    self.rating = rating

  async def callback(self, interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    challenge_data = load_challenge_data()

    challenge_data.setdefault('ratings', []).append({
        'user': user_id,
        'rating': self.rating
    })
    save_challenge_data(challenge_data)

    await interaction.response.send_message(
        f'You rated the challenge {self.rating} stars!', ephemeral=True)


class GeneralCommands(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    # Overriding default discord help message for our very own embeded one.
    self.bot.remove_command("help")
    self.config = load_config()

  @discord.app_commands.command(name="submit",
                                description="Used to Submit flag.")
  async def submit(self, interaction: discord.Interaction, flag: str) -> None:
    self.config = load_config()
    challenge_data = load_challenge_data()

    if not challenge_data:
      await interaction.response.send_message(
          "There's no active challenge right now!", ephemeral=True)
      return

    if "answer" in challenge_data and str(
            interaction.user.id) in challenge_data["leaderboard"]:
      await interaction.response.send_message(
          "You've already submitted the correct answer!", ephemeral=True)
      return

    if "answer" in challenge_data and challenge_data["answer"] == flag:
      leaderboard_length = len(challenge_data["leaderboard"])
      if str(interaction.user.id) not in challenge_data["leaderboard"]:
        challenge_data["leaderboard"][str(
            interaction.user.id)] = datetime.datetime.utcnow().strftime(
                "%Y-%m-%d %H:%M:%S.%f")
        save_challenge_data(challenge_data)

        master = self.bot.get_user(challenge_data["master_id"])
        if master:
          await master.send(
              f"{interaction.user.name} just solved the challenge!")

          challenge_channel = self.bot.get_channel(
              int(self.config["leaderboard_channel_id"]))
          # Logic for the leaderboard messages
          if leaderboard_length == 0:
            await challenge_channel.send(
                f"🚩 First Blood! {interaction.user.mention} just conquered today's challenge! 🔥 Only two top spots left. Who's claiming the next one? 🚀"
            )
            await interaction.response.send_message(
                "Incredible! You've stormed through the challenge and secured the top spot!",
                ephemeral=True)
            await check_rating(interaction)
          elif leaderboard_length == 1:
            await challenge_channel.send(
                f"🎉 Bravo! {interaction.user.mention} secures the second spot! Only one more top spot remaining. Who's taking it? 🌟"
            )
            await interaction.response.send_message(
                "Fantastic! You've secured the second top spot! Let's see who claims the last!",
                ephemeral=True)
            await check_rating(interaction)
          elif leaderboard_length == 2:
            await challenge_channel.send(
                f"🔥 {interaction.user.mention} clinches the third spot! Top spots are taken but the game's still on! ⚡ Push your limits!"
            )
            await interaction.response.send_message(
                "Great job grabbing the third spot! Keep this energy up for the next challenges!",
                ephemeral=True)
            await check_rating(interaction)
            display_leaderboard(self.bot)
          else:
            await interaction.response.send_message(
                f"Correct answer! You're in position {leaderboard_length + 1}. Push harder next time to claim a top spot!",
                ephemeral=True)
            await check_rating(interaction)
        else:
          await interaction.response.send_message("You've already submitted!",
                                                  ephemeral=True)
    else:
      await interaction.response.send_message("Wrong answer! Try again.",
                                              ephemeral=True)

  @discord.app_commands.command(
      name="timeleft",
      description="Tells the time left for the hint and the challenge end.")
  async def timeleft(self, interaction: discord.Interaction) -> None:
    self.config = load_config()
    challenge_data = load_challenge_data()

    if not challenge_data:
      await interaction.response.send_message("No active challenge currently!",
                                              ephemeral=True)
      return

    # The start time is stores as an unix timestamp allowing us easily perform arithemetic operations on it.
    start_time = datetime.datetime.fromtimestamp(challenge_data["start_time"])
    current_time = datetime.datetime.utcnow()

    hint_time = start_time + datetime.timedelta(hours=6)
    end_time = start_time + datetime.timedelta(hours=24)

    time_to_hint = hint_time - current_time
    time_to_end = end_time - current_time

    if current_time > end_time:
      await interaction.response.send_message(
          "The challenge has already ended.", ephemeral=True)
      return

    if challenge_data.get(
            "leaderboard", {}) and not challenge_data.get("hints_revealed", False):
      hint_msg = "Hint will no longer be printed since someone has already solved the challenge."
    elif current_time < hint_time:
      hours_hint, remainder_hint = divmod(time_to_hint.total_seconds(), 3600)
      minutes_hint, seconds_hint = divmod(remainder_hint, 60)
      hint_msg = f"Time left for hint: {int(hours_hint)}:{int(minutes_hint):02}:{int(seconds_hint):02}"
    else:
      hint_msg = "Hint has been released!"

    hours_end, remainder_end = divmod(time_to_end.total_seconds(), 3600)
    minutes_end, seconds_end = divmod(remainder_end, 60)
    end_msg = f"Time left for challenge end: {int(hours_end)}:{int(minutes_end):02}:{int(seconds_end):02}"

    await interaction.response.send_message(f"{hint_msg}\n{end_msg}",
                                            ephemeral=True)

  @discord.app_commands.command(
      name="feedback", description="Submit feedback, bugs, or suggestions.")
  async def _feedback(self, interaction: discord.Interaction) -> None:
    self.config = load_config()
    logging.info(
        f"Feedback command invoked by {interaction.user.name} (ID: {interaction.user.id})"
    )
    modal = FeedbackModal()
    await interaction.response.send_modal(modal)

  @discord.app_commands.command(name="rate",
                                description="Rate the challenge out of 5.")
  async def rate_challenge(self, interaction: discord.Interaction):
    challenge_data = load_challenge_data()
    if not challenge_data:
      await interaction.response.send_message("No active challenge currently!",
                                              ephemeral=True)
      return
    # Check if user has already rated
    for rate in challenge_data.get('ratings', []):
      if rate.get('user') == str(interaction.user.id):
        await interaction.response.send_message(
            'You have already rated this challenge!', ephemeral=True)
        return

    view = RateView()

    await interaction.response.send_message("Rate today's challenge:",
                                            view=view,
                                            ephemeral=True)


async def setup(bot) -> None:
  await bot.add_cog(GeneralCommands(bot))


# Thanks man, people like you mean a lot to me going through my code and this is an easter egg, send me a screenshot with this message at @Goofygiraffe06 on twitter or anywhere else. :D
