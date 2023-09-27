import discord
import json
import logging
from discord.ext import commands, tasks
import random
import datetime
import asyncio
import time
from discord import app_commands
from keep_alive import keep_alive
import os

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
# Stopping keep_alive log messages as they make hard to read and are useless
# Suppress Flask development server log
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)

# channel id for feedback
FEEDBACK_CHANNEL_ID = 914495197256228961

# Load bot configuration from JSON
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


# Load challenge data or return an empty data if file not found
def load_challenge_data():
    try:
        with open("challenge_data.txt", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.warning("Challenge data not found. Returning empty data.")
        return {}


# Save challenge data to a file
def save_challenge_data(data):
    with open("challenge_data.txt", "w") as file:
        json.dump(data, file)
    logging.info("Challenge data saved successfully.")


# Activities for bot presence
ACTIVITIES = [
    "Proving P = NP...",
    "Computing 6 x 9...",
    "Mining bitcoin...",
    "Dividing by 0...",
    "Initialising Skynet...",
    "[REDACTED]",
    "Downloading more RAM...",
    "Ordering 1s and 0s...",
    "Navigating neural network...",
    "Importing machine learning...",
    "Issuing Alice and Bob one-time pads...",
    "Mining bitcoin cash...",
    "Generating key material by trying to escape vim...",
    "for i in range(additional): Pylon()",
    "(creating unresolved tension...",
    "Symlinking emacs and vim to ed...",
    "Training branch predictor...",
    "Timing cache hits...",
    "Speculatively executing recipes...",
    "Adding LLM hallucinations...",
    "Cracking quantum encryption...",
    "Breaching mainframe...",
    "Accessing secret databases...",
    "Decompiling neural algorithms...",
    "Launching DDoS on Matrix...",
    "Rooting cyberspace...",
    "Bypassing firewall...",
    "Infiltrating digital fortress...",
    "Overriding security protocols...",
    "Decrypting alien communications...",
    "Running penetration tests...",
    "Compiling stealth trojans...",
    "Exploiting zero-day vulnerabilities...",
    "Activating VPN...",
    "Cloaking IP address...",
    "Hijacking satellite...",
    "Routing through proxies...",
    "Establishing darknet connection...",
    "Uploading virus to the Grid...",
    "Initializing worm propagation...",
]


# Task to change bot's activity every 30 minutes
@tasks.loop(minutes=30)
async def change_activity():
    activity = random.choice(ACTIVITIES)
    await bot.change_presence(activity=discord.Game(name=activity))
    logging.info(f"Activity set to: {activity}")


@bot.event
async def on_guild_join(guild):
    # Find a channel to send the welcome message to
    # Typically, this is the server's system channel or the first available text channel
    channel = guild.system_channel or next(
        (
            channel
            for channel in guild.channels
            if isinstance(channel, discord.TextChannel)
        ),
        None,
    )

    if channel is not None:
        # Introduction
        await channel.send(
            "Hello, thanks for adding DailyCTF Robot to your server! 🎉\nDailyCTF Robot is a bot designed to automate and enhance the experience of hosting Capture The Flag challenges, making it seamless for both organizers and participants."
        )

        # Prompt the admin to set up the bot
        await channel.send(
            "To get started, please use the `/setup` command to configure me for your server."
        )

        # Add a basic cheatsheet or instruction list for slash commands
        cheatsheet = """
        **Basic Commands Cheatsheet:**
        `/setup` - Configure the bot for your server.
        `/help` - Shows a list of available commands.
        `/setchallenge` - Create a new challenge.
        `/shutdown` - Shutdown the active CTF challenge.
        `/timeleft` - Shows the remaining time for hint and for the challenege to end.
        `/feedback` - Allows to submit feedback to bot creator.
        """
        await channel.send(cheatsheet)


@bot.event
async def on_ready():
    logging.info(f"We have logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} command(s)...")
    except Exception as e:
        logging.error(f"Error syncing commands!: {e}")
    try:
        bot.loop.create_task(release_hints())
    except Exception as e:
        logging.error(e)
    bot.loop.create_task(end_challenge())
    await change_activity.start()


def save_config():
    with open("config.json", "w") as config_file:
        json.dump(config, config_file)


# Create a select menu for roles
class RoleSelect(discord.ui.Select):
    def __init__(self, roles):
        options = [
            discord.SelectOption(label=role.name, value=str(role.id)) for role in roles
        ]
        super().__init__(placeholder="Select the CTF role...", options=options, row=0)

        async def on_timeout(self):
            if self.role_selected and self.channel_selected:
                save_config()

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.values[0]
        config["ctf_creators"] = int(self.values[0])
        save_config()  # Save the changes immediately
        await interaction.response.send_message(
            f"Selected Role: <@&{self.values[0]}>", ephemeral=True
        )


# Create a select menu for channels
class ChannelSelect(discord.ui.Select):
    def __init__(self, channels):
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in channels
            if isinstance(channel, discord.TextChannel)
        ]
        super().__init__(
            placeholder="Select the announcement channel...", options=options, row=1
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.values[0]
        config["channel_id"] = int(self.values[0])
        save_config()  # Save the changes immediately
        await interaction.response.send_message(
            f"Selected Channel: <#{self.values[0]}>", ephemeral=True
        )
class LeaderboardChannelSelect(discord.ui.Select):
    def __init__(self, channels):
        options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels if isinstance(channel, discord.TextChannel)]
        super().__init__(placeholder='Select the leaderboard channel...', options=options, row=2)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.values[0]
        config["leaderboard_channel_id"] = int(self.values[0])
        save_config()
        self.view.channel_selected = True
        await interaction.response.send_message(f"Selected Leaderboard Channel: <#{self.values[0]}>", ephemeral=True)

class SetupView(discord.ui.View):
    def __init__(self, roles, channels):
        super().__init__(timeout=60)
        self.value = None
        self.add_item(RoleSelect(roles))
        self.add_item(ChannelSelect(channels))
        self.add_item(LeaderboardChannelSelect(channels))


@bot.tree.command(name="setup", description="Setup bot settings for the server.")
async def setup(interaction: discord.Interaction):
    
    # Check if the user has the "ctf_creators" role
    if discord.utils.get(interaction.guild.roles, id=int(1142485003264073869)) not in interaction.user.roles:
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        logging.warning(f"Unauthorized setup attempt by {interaction.user.name} (ID: {interaction.user.id}) in server: {interaction.guild.name} (ID: {interaction.guild.id})")
        return

    logging.info(
        f"Setup command invoked by {interaction.user.name} (ID: {interaction.user.id}) in server: {interaction.guild.name} (ID: {interaction.guild.id})"
    )
    roles = interaction.guild.roles
    channels = interaction.guild.channels
    view = SetupView(roles, channels)
    await interaction.response.send_message(
        "Please select the appropriate role and channel:", view=view, ephemeral=True
    )

class SetChallengeModal(discord.ui.Modal, title="Set a Challenge"):
    day_input = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Day",
        required=True,
        placeholder="Day number of the challenge",
    )

    description_input = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Description",
        required=True,
        max_length=500,
        placeholder="Description of the challenge",
    )

    answer_input = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Answer",
        required=True,
        placeholder="Answer to the challenge",
    )

    hints_input = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Hints",
        required=True,
        placeholder="Hints for the challenge",
    )
    writeup_input = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Write-up",
        required=False,  # Since it's optional
        max_length=1000,
        placeholder="Optional: Describe how to solve the challenge",
    )

    async def on_submit(self, interaction: discord.Interaction):
        day = self.day_input.value
        description = self.description_input.value
        answer = self.answer_input.value
        hints = self.hints_input.value
        writeup = self.writeup_input.value

        # Check if day input is numeric
        if not day.isdigit():
            await interaction.response.send_message(
                "Day input should only contain numbers.", ephemeral=True
            )
            return
        challenge_data = {
            "master_id": interaction.user.id,
            "day": day,
            "desc": description,
            "answer": answer,
            "hints": hints,
            "writeup": writeup,
            "leaderboard": {},
            "start_time": int(datetime.datetime.utcnow().timestamp()),
        }
        save_challenge_data(challenge_data)

        formatted_message = (
            f"@everyone\n**Day-{challenge_data['day']} Challenge by {interaction.user.name}:**\n"
            f"`{challenge_data['desc']}`"
        )
        challenge_channel = bot.get_channel(int(config["channel_id"]))
        await challenge_channel.send(formatted_message)
        await interaction.response.send_message(
            f"Challenge set successfully for Day {day}!"
        )
        await release_hints()
        await end_challenge()

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            f"Failed to set challenge.\nError: {error}", ephemeral=True
        )


@bot.tree.command(name="setchallenge", description="Create a new challenge")
async def setchallenge(interaction: discord.Interaction):
    if (
        discord.utils.get(interaction.guild.roles, id=config["ctf_creators"])
        in interaction.user.roles
    ):
        logging.info(
            f"Setchallenge command invoked by {interaction.user.name} (ID: {interaction.user.id}) in server: {interaction.guild.name} (ID: {interaction.guild.id})"
        )
        modal = SetChallengeModal()
        await interaction.response.send_modal(SetChallengeModal())
    else:
        await interaction.response.send_message(
            "You don't have permission to set a challenge!", ephemeral=True
        )
        return


async def display_leaderboard():
    challenge_data = load_challenge_data()
    position_emojis = ["🥇", "🥈", "🥉"]
    sorted_leaderboard = sorted(
        challenge_data["leaderboard"].items(), key=lambda x: x[1]
    )
    leaderboard_msg = "🏆 **The winners of today's CTF (Day-{day}) are:** 🏆\n"
    for i, (user_id, _) in enumerate(sorted_leaderboard[:3]):
        user = bot.get_user(int(user_id))
        leaderboard_msg += f"{position_emojis[i]} {user.mention}\n"
    challenge_channel = bot.get_channel(int(config["channel_id"]))
    await challenge_channel.send(leaderboard_msg.format(day=challenge_data["day"]))


async def end_challenge():
    challenge_data = load_challenge_data()
    if "start_time" in challenge_data:
        start_time = datetime.datetime.fromtimestamp(challenge_data["start_time"])
        elapsed_time = datetime.datetime.utcnow() - start_time
        remaining_time = 86400 - elapsed_time.total_seconds()

        # 24 hours minus elapsed time
        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
    else:
        await asyncio.sleep(86400)

    challenge_channel = bot.get_channel(int(config["channel_id"]))
    await challenge_channel.send(f"Day-{challenge_data['day']} Challenge has finished!")
    logging.info(f"Day-{challenge_data['day']}challenge has been finished...")
    await challenge_channel.send(
    f"The answer for Day-{challenge_data['day']} was: ||`{challenge_data['answer']}`||")

# Check if a write-up exists and then send the appropriate message
    if 'writeup' in challenge_data and challenge_data['writeup']:
      await challenge_channel.send(f"Writeup for Day-{challenge_data['day']}: {challenge_data['writeup']}")
    else:
      await challenge_channel.send("No writeup provided for Day-{challenge_data['day']}.")

    # reset challenge data
    save_challenge_data({})


@bot.tree.command(name="submit", description="Used to Submit flag.")
@app_commands.describe(flag="Enter your flag here.")
async def submit(interaction: discord.Interaction, flag: str):
    challenge_data = load_challenge_data()

    if not challenge_data:
        await interaction.response.send_message(
            "There's no active challenge right now!", ephemeral=True
        )
        return

    if (
        "answer" in challenge_data
        and str(interaction.user.id) in challenge_data["leaderboard"]
    ):
        await interaction.response.send_message(
            "You've already submitted the correct answer!", ephemeral=True
        )
        return

    if "answer" in challenge_data and challenge_data["answer"] == flag:
        leaderboard_length = len(challenge_data["leaderboard"])

        if str(interaction.user.id) not in challenge_data["leaderboard"]:
            challenge_data["leaderboard"][
                str(interaction.user.id)
            ] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
            save_challenge_data(challenge_data)

            master = bot.get_user(challenge_data["master_id"])
            if master:
                await master.send(f"{interaction.user.name} just solved the challenge!")

            challenge_channel = bot.get_channel(int(config["leaderboard_channel_id"]))

            if leaderboard_length == 0:
                await challenge_channel.send(
                    f"🚩 First Blood! {interaction.user.mention} just conquered today's challenge! 🔥 Only two top spots left. Who's claiming the next one? 🚀"
                )
                await interaction.response.send_message(
                    "Incredible! You've stormed through the challenge and secured the top spot!",
                    ephemeral=True,
                )

            elif leaderboard_length == 1:
                await challenge_channel.send(
                    f"🎉 Bravo! {interaction.user.mention} secures the second spot! Only one more top spot remaining. Who's taking it? 🌟"
                )
                await interaction.response.send_message(
                    "Fantastic! You've secured the second top spot! Let's see who claims the last!",
                    ephemeral=True,
                )

            elif leaderboard_length == 2:
                await challenge_channel.send(
                    f"🔥 {interaction.user.mention} clinches the third spot! Top spots are taken but the game's still on! ⚡ Push your limits!"
                )
                await interaction.response.send_message(
                    "Great job grabbing the third spot! Keep this energy up for the next challenges!",
                    ephemeral=True,
                )
                await display_leaderboard()

            else:
                await interaction.response.send_message(
                    f"Correct answer! You're in position {leaderboard_length + 1}. Push harder next time to claim a top spot!",
                    ephemeral=True,
                )

        else:
            await interaction.response.send_message(
                "You've already submitted!", ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "Wrong answer! Try again.", ephemeral=True
        )


@bot.tree.command(name="shutdown", description="Shutdowns active challenge")
async def shutdown(interaction: discord.Interaction):

    # Check for permissions
    if (
        discord.utils.get(interaction.guild.roles, id=int(config["ctf_creators"]))
        not in interaction.user.roles
    ):
        await interaction.response.send_message(
            "You don't have permission to shutdown the challenge!", ephemeral=True
        )
        logging.warning(
            f"Unauthorized challenge shutdown attempt by {interaction.user.name} (ID: {interaction.user.id}) in server: {interaction.guild.name} (ID: {interaction.guild.id})"
        )
        return

    challenge_data = load_challenge_data()

    # If there's no challenge data
    if not challenge_data:
        await interaction.response.send_message(
            "No active challenge to shut down.", ephemeral=True
        )
        return

    position_emojis = ["🥇", "🥈", "🥉"]
    challenge_channel = bot.get_channel(int(config["leaderboard_channel_id"]))

    # Print leaderboard
    if challenge_data["leaderboard"]:
        await display_leaderboard()
    else:
        await challenge_channel.send("No one has solved the challenge yet.")

    # Print the correct answer
    await challenge_channel.send(
        f"Correct answer for Day-{challenge_data['day']} was: `{challenge_data['answer']}`")
    await challenge_channel.send(
        f"Official Writeup: `{challenge_data['writeup']}`")

    # Reset challenge data
    save_challenge_data({})
    await challenge_channel.send(
        "Challenge has been shut down and leaderboard has been printed."
    )

async def release_hints():
    logging.info("Function release_hints started.")

    challenge_data = load_challenge_data()

    if not challenge_data:
        logging.warning("No challenge data available. Exiting release_hints.")
        return

    if "start_time" in challenge_data:
        start_time = datetime.datetime.fromtimestamp(challenge_data["start_time"])
        elapsed_time = datetime.datetime.utcnow() - start_time
        remaining_time = 21600 - elapsed_time.total_seconds()  # 6 hours minus elapsed time

        logging.info(
            f"Start time found. Elapsed time: {elapsed_time.total_seconds()} seconds. Remaining time: {remaining_time} seconds."
        )

        if remaining_time > 0:
            logging.info(f"Sleeping for {remaining_time} seconds.")
            await asyncio.sleep(remaining_time)
        else:
            logging.warning("Time already passed for hint release.")
    else:
        logging.error("start_time not found in challenge_data. Unable to determine hint release time.")

    if (
        not challenge_data.get("hints_revealed", False)
        and not challenge_data.get("leaderboard", {})
    ):
        challenge_channel = bot.get_channel(int(config["channel_id"]))
        await challenge_channel.send(
            f"Hint for Day-{challenge_data['day']}: `{challenge_data['hints']}`"
        )
        logging.info(f"Hint for Day-{challenge_data['day']} released.")

        challenge_data["hints_revealed"] = True
        save_challenge_data(challenge_data)
    else:
        logging.warning(
            "Hints were either already revealed or there is an active leaderboard. No hint was released."
        )

@bot.tree.command(
    name="timeleft",
    description="Tells the time left for the hint and the challenge end.",
)
async def timeleft(interaction: discord.Interaction):
    challenge_data = load_challenge_data()

    if not challenge_data:
        await interaction.response.send_message(
            "No active challenge currently!", ephemeral=True
        )
        return

    start_time = datetime.datetime.fromtimestamp(challenge_data["start_time"])
    current_time = datetime.datetime.utcnow()

    hint_time = start_time + datetime.timedelta(hours=6)
    end_time = start_time + datetime.timedelta(hours=24)

    time_to_hint = hint_time - current_time
    time_to_end = end_time - current_time

    if current_time > end_time:
        await interaction.response.send_message(
            "The challenge has already ended.", ephemeral=True
        )
        return

    if challenge_data.get("leaderboard", {}) and not challenge_data.get("hints_revealed", False):
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

    await interaction.response.send_message(
        f"{hint_msg}\n{end_msg}", ephemeral=True
    )


@bot.tree.command(name="ping", description="Check if the bot is alive or not.")
async def _ping(interaction: discord.Interaction):
    message = await interaction.response.send_message("Pong!")


@bot.command(pass_context=True)
async def ping(ctx):
    """ Pong! """
    before = time.monotonic()
    message = await ctx.send("Pong!")
    ping = (time.monotonic() - before) * 1000
    await message.edit(content=f"Pong!  `{int(ping)}ms`")
    print(f"Ping {int(ping)}ms")


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
        channel = interaction.guild.get_channel(FEEDBACK_CHANNEL_ID)

        embed = discord.Embed(
            title=f"New Feedback: {self.fb_title.value}",
            description=self.message.value,
            color=discord.Color.yellow(),
        )
        embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.avatar.url
        )

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


@bot.tree.command(name="feedback", description="Submit feedback, bugs, or suggestions.")
async def _feedback(interaction: discord.Interaction):
    logging.info(
        f"Feedback command invoked by {interaction.user.name} (ID: {interaction.user.id})"
    )
    modal = FeedbackModal()
    await interaction.response.send_modal(modal)


# Overriding default discord help messsage for our very own embeded one.
bot.remove_command("help")


# Custom help command
@bot.tree.command(
    name="help", description="Displays the list of commands and their descriptions."
)
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="DailyCTF Robot Help",
        description="List of available commands. DailyCTF Robot is a bot to automate ...",
        color=0x55A7F7,
    )

    # General Commands
    general_commands = """
    `/ping` - Check if the bot is alive.
    `/submit <flag>` - Submit the CTF flag.
    `/timeleft` - Tells the time left for the hint and the challenge end.
    `/feedback` - Submit feedback, bugs, or suggestions.
    """
    embed.add_field(name="General Commands", value=general_commands, inline=False)

    # Admin Commands
    admin_commands = """
    `/setchallenge` - Create a new challenge.
    `/shutdown` - Shutdown the active challenge.
    `/setup` - Setup bot settings for the server.
    """
    embed.add_field(
        name="Admin Commands (for CTF creators)", value=admin_commands, inline=False
    )

    # Send the help embed
    await interaction.response.send_message(embed=embed)


keep_alive()
try:
    bot.run(os.getenv("token"))
except discord.errors.HTTPException or discord.app_commands.errors.CommandInvokeError:
    logging.error("Being Rate Limited!")
    os.system("kill 1")
    os.system("python restart.py")
