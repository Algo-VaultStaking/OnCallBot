import configparser
import json
import re
from tabulate import tabulate

import discord
from discord import app_commands
from discord.ext import commands, tasks
from web3 import Web3

import database

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
ADMIN_ROLES = c["DISCORD"]["admin_roles"]
ephemeral = bool(True if str(c["DISCORD"]["ephemeral"]) == "True" else False)
guilds = json.loads(c["DISCORD"]["guilds"])
e_channel = int(c["DISCORD"]["error_channel"])
intents = discord.Intents.default()
intents.messages = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")
    #synced = await bot.tree.sync()
    #print(f"Synced {len(synced)} commands")


@bot.tree.command(name="add-to-schedule", description="Add a user and on-call time to the schedule.")
@app_commands.describe(user="The on-call user.", day_of_week="The day of the week", start="The start time in UTC [0000 - 2358].", end="The end time in UTC [0001 - 2359].")
async def add_user(interaction: discord.Interaction, user: str, day_of_week: str, start: str, end: str):
    db_connection = database.get_db_connection()
    time_pattern = re.compile("^([0-1][0-9]|2[0-3])[0-5][0-9]$")

    if user[:2] != "<@" or user[-1:] != ">":
        await interaction.response.send_message(f"Please tag a specific user.", ephemeral=ephemeral)
        db_connection.close()
        return

    if not time_pattern.match(start):
        await interaction.response.send_message(f"Please enter a start UTC time in the range 0000 - 2358.", ephemeral=ephemeral)
        db_connection.close()
        return

    if not time_pattern.match(end):
        await interaction.response.send_message(f"Please enter an end UTC time in the range 0001 - 2359.", ephemeral=ephemeral)
        db_connection.close()
        return

    if int(start) > int(end):
        await interaction.response.send_message(f"The end time should be later than the start time.", ephemeral=ephemeral)
        db_connection.close()
        return

    if day_of_week[:3].lower() not in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        await interaction.response.send_message(f"Please use the full name (Monday) or abbreviation (Mon) for the Day of the Week.", ephemeral=ephemeral)
        db_connection.close()
        return

    success = database.add_to_schedule(db_connection, user, day_of_week[:3].lower(), start, end, interaction.guild_id)
    db_connection.close()

    if success:
        await interaction.response.send_message(f"{user} was added to the schedule.", ephemeral=ephemeral)

    if not success:
        await interaction.response.send_message(f"The user wasn't saved in the database. cc: <@712863455467667526>", ephemeral=ephemeral)


@bot.tree.command(name="remove-from-schedule", description="Remove a user's on-call time from the schedule.")
@app_commands.describe(schedule_id="Schedule ID to remove.")
async def remove_user(interaction: discord.Interaction, schedule_id: int):
    db_connection = database.get_db_connection()

    success = database.remove_from_schedule(db_connection, schedule_id, interaction.guild_id)
    db_connection.close()

    if success:
        await interaction.response.send_message(f"Schedule ID {schedule_id} was removed from the schedule.", ephemeral=ephemeral)

    if not success:
        await interaction.response.send_message(f"There was an issue. cc: <@712863455467667526>", ephemeral=ephemeral)


@bot.tree.command(name="show-schedule", description="Show the current schedule.")
@app_commands.describe()
async def get_schedule(interaction: discord.Interaction):
    db_connection = database.get_db_connection()
    response = database.list_schedule(db_connection)

    await interaction.response.send_message(tabulate(response), ephemeral=ephemeral)


bot.run(discord_token)
