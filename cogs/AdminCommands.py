# cogs/AdminCommands.py - Contains commands for managing challeges, including challenege setup and shutdown.

import discord
from discord.ext import commands
from .utils import (
    save_challenge_data,
    load_challenge_data,
    load_config,
    save_config,
    display_leaderboard,
    end_challenge,
    calculate_average_rating,
)
import logging
import datetime
from discord.ui import Modal, TextInput
from discord import TextStyle

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)


# Modal Class to handle the setchallenge
class SetChallengeModal(discord.ui.Modal, title="Set a Challenge"):
    def __init__(self, bot, config):
        super().__init__()
        self.bot = bot
        self.config = config

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
        max_length=2000,
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
        try:
            day = self.day_input.value
            description = self.description_input.value
            answer = self.answer_input.value
            hints = self.hints_input.value
            writeup = self.writeup_input.value

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
            challenge_channel = self.bot.get_channel(int(self.config["channel_id"]))
            await challenge_channel.send(formatted_message)
            await interaction.response.send_message(
                f"Challenge set successfully for Day {day}!", ephemeral=True
            )
        except Exception as e:
            logging.error(f"Error in on_submit: {e}")
            await interaction.response.send_message(
                f"Failed to set challenge. Please check logs.", ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logging.error(f"Error in SetChallengeModal: {error}")
        await interaction.response.send_message(
            f"Failed to set challenge.\nError: {error}", ephemeral=True
        )


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.config = load_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")

    @discord.app_commands.command(
        name="setchallenge", description="Create a new challenge"
    )
    async def setchallenge(self, interaction: discord.Interaction) -> None:
        try:
            # Reload the configuration before performing any operation
            self.config = load_config()

            if (
                discord.utils.get(
                    interaction.guild.roles, id=self.config["ctf_creators"]
                )
                in interaction.user.roles
            ):
                modal = SetChallengeModal(self.bot, self.config)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message(
                    "You don't have permission to set a challenge!", ephemeral=True
                )
        except Exception as e:
            logging.error(f"Error in setchallenge: {e}")
            await interaction.response.send_message(
                "Failed to set challenge. Please check logs.", ephemeral=True
            )
        except Exception as e:
            logging.error(f"Error in setchallenge: {e}")
            await interaction.response.send_message(
                "Failed to set challenge. Please check logs.", ephemeral=True
            )

    @discord.app_commands.command(
        name="shutdown", description="Shutdowns active challenge"
    )
    async def shutdown(self, interaction: discord.Interaction) -> None:
        try:
            self.config = load_config()
            if (
                discord.utils.get(
                    interaction.guild.roles, id=int(self.config["ctf_creators"])
                )
                not in interaction.user.roles
            ):
                await interaction.response.send_message(
                    "You don't have permission to shutdown the challenge!",
                    ephemeral=True,
                )
                return

            challenge_data = load_challenge_data()
            if not challenge_data:
                await interaction.response.send_message(
                    "No active challenge to shut down.", ephemeral=True
                )
                return

            challenge_channel = self.bot.get_channel(
                int(self.config["leaderboard_channel_id"])
            )
            if challenge_data["leaderboard"]:
                await display_leaderboard(self.bot)
            else:
                await challenge_channel.send("No one has solved the challenge yet.")

            await challenge_channel.send(
                f"Correct answer for Day-{challenge_data['day']} was: ||`{challenge_data['answer']}`||"
            )
            if challenge_data['writeup']:
                await challenge_channel.send(
                    f"Official Writeup: {challenge_data['writeup']}"
                )
            else:
                await challenge_channel.send(
                    f"No official writeup for Day-{challenge_data['day']}"
                )
            avg = calculate_average_rating()
            if avg is not None:
                await challenge_channel.send(
                    f"The average rating for the challenge is: {avg:.2f}"
                )
            else:
                await challenge_channel.send("No ratings received for the challenge.")
            save_challenge_data({})
            await interaction.response.send_message(
                "Challenge has been shut down and leaderboard has been printed.",
                ephemeral=True,
            )
        except Exception as e:
            logging.error(f"Error in shutdown: {e}")
            await interaction.response.send_message(
                "Failed to shutdown challenge. Please check logs.", ephemeral=True
            )


async def setup(bot) -> None:
    await bot.add_cog(AdminCommands(bot))
