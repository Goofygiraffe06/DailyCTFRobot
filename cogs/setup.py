# cogs/setup.py - Handles server specific configuration for the bot including role selection and channel selection.

import discord
from .utils import load_config, save_config
from discord.ext import commands
import logging
from discord.ext.commands import has_permissions, CheckFailure

# Initialize logging
logging.basicConfig(level=logging.INFO,
										format="%(asctime)s | %(levelname)s | %(message)s")

logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)


# Shared Configuration Object to hold our configuration
class Config:
	def __init__(self):
		self.data = load_config()

	def get(self, key, default=None):
		return self.data.get(key, default)

	def set(self, key, value):
		self.data[key] = value

	def save(self):
		save_config(self.data)

# Create a select menu for roles


class RoleSelect(discord.ui.Select):
	def __init__(self, roles, config):
		options = [
				discord.SelectOption(label=role.name, value=str(role.id))
				for role in roles
		]
		super().__init__(placeholder="Select the CTF role...", options=options, row=0)
		self.config = config

	async def callback(self, interaction: discord.Interaction):
		self.config.set("ctf_creators", int(self.values[0]))
		self.config.save()
		await interaction.response.send_message(
				f"Selected Role: <@&{self.values[0]}>", ephemeral=True
		)


# Create a select menu for channels
class ChannelSelect(discord.ui.Select):
	def __init__(self, channels, config):
		options = [
				discord.SelectOption(label=channel.name, value=str(channel.id))
				for channel in channels if isinstance(channel, discord.TextChannel)
		]
		super().__init__(placeholder="Select the announcement channel...",
										 options=options, row=1)
		self.config = config

	async def callback(self, interaction: discord.Interaction):
		self.config.set("channel_id", int(self.values[0]))
		self.config.save()
		await interaction.response.send_message(
				f"Selected Channel: <#{self.values[0]}>", ephemeral=True
		)


class LeaderboardChannelSelect(discord.ui.Select):
	def __init__(self, channels, config):
		options = [
				discord.SelectOption(label=channel.name, value=str(channel.id))
				for channel in channels if isinstance(channel, discord.TextChannel)
		]
		super().__init__(placeholder='Select the leaderboard channel...',
										 options=options, row=2)
		self.config = config

	async def callback(self, interaction: discord.Interaction):
		self.config.set("leaderboard_channel_id", int(self.values[0]))
		self.config.save()
		await interaction.response.send_message(
				f"Selected Leaderboard Channel: <#{self.values[0]}>", ephemeral=True
		)

# Add individual drop-down menu into a single modal


class SetupView(discord.ui.View):
	def __init__(self, roles, channels, config):
		super().__init__(timeout=60)
		self.add_item(RoleSelect(roles, config))
		self.add_item(ChannelSelect(channels, config))
		self.add_item(LeaderboardChannelSelect(channels, config))


class Setup(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = Config()
		self.config = Config()
		# Only initialize the configuration if it's empty or doesn't exist
		if self.config.data is None:
			self.config.data = save_config({})

	@discord.app_commands.command(name="setup", description="Setup bot settings for the server.")
	@has_permissions(administrator=True)
	async def setup(self, interaction: discord.Interaction) -> None:
		logging.info(
				f"Setup command invoked by {interaction.user.name} (ID: {interaction.user.id}) in server: {interaction.guild.name} (ID: {interaction.guild.id})")
		roles = interaction.guild.roles
		channels = interaction.guild.channels
		view = SetupView(roles, channels, self.config)
		await interaction.response.send_message(
				"Please select the appropriate role and channel:",
				view=view, ephemeral=True
		)

	@setup.error
	async def setup_error(self, interaction, error):
		if isinstance(error, CheckFailure):
			await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
			logging.warning(
					f"Unauthorized setup attempt by {interaction.user.name} (ID: {interaction.user.id}) in server: {interaction.guild.name} (ID: {interaction.guild.id})"
			)
			return


async def setup(bot) -> None:
	await bot.add_cog(Setup(bot))
