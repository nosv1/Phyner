# Phyner is finer.
# Mo#9991
# Main File, handles events and runs bot, the controller

# python imports
import discord
import asyncio
from datetime import datetime, timedelta
import random
from pytz import timezone
import traceback
import gspread
import mysql.connector
from types import SimpleNamespace
import os
import re

from dotenv import load_dotenv
load_dotenv()

# general imports
import Secrets
import Logger
import Database

# specific imports
import Embed

mo_id = 405944496665133058
phyner_id = 770416211300188190
phyner_red = 0x980B0D

intents = discord.Intents.all()
client = discord.Client(intents = intents)

connected = None
phyner_db = None



### ON_READY ###

@client.event
async def on_ready():

  error = None
  try:
    global connected
    connected = datetime.now()
    log_path = f"Logs\\{datetime.strftime(connected, '%Y-%m-%d %H.%M.%S')}.txt"
    f = open(log_path, "a+")
    f.close()
    Logger.log("Connected to Discord")

    global phyner_db
    phyner_db = Database.connectDatabase("Phyner")
    Logger.log("Connected to Database")

    await client.change_presence(
      activity=discord.Activity(
        type=discord.ActivityType.watching, name="Phyner is finer. 🌹"
      )
    )
    
  except:
    error = traceback.format_exc()

  if error:
    await Logger.logError(client, error)
# end on_ready



### ON_MESSAGE_EDIT and ON_MESSAGE ###

@client.event
async def on_raw_message_edit(payload):
  if not connected: # we aint ready yet
    return

  error = False
  message = None
  try:

    pd = payload.data

    channel_id = int(pd["channel_id"])
    message_id = int(pd["id"])

    channel = client.get_channel(channel_id)
    channel = channel if channel else await client.fetch_channel(channel_id) # if DM, get_channel is none, i think

    message = await channel.fetch_message(message_id)

    if not message.author.bot and connected:
      try:
        pd["content"]
        await on_message(message)
      except KeyError: # when content was not updated
        pass

    
  except:
    error = traceback.format_exc()

  if error:
    await Logger.logErrorMessage(client, error, message)
  
# end on_raw_message_edit

@client.event
async def on_message(message):
  if not connected: # we aint ready yet
    return

  error = False
  try:
    # prep message content for use
    message.content = message.content.translate({ord(c) : '"' for c in ['“', '”']})
    mc = message.content.translate({ord(c) : " " for c in ["\n", "\t", "\r"]})
    while ("  " in mc):
      mc = mc.replace("  ", " ")
    args = mc.split(" ") + ["", ""]

    author_perms = dict(message.channel.permissions_for(message.author))
    is_mo = message.author.id == mo_id
    if is_mo:
      for permission  in author_perms:
        author_perms[permission] = True
      author_perms = SimpleNamespace(**author_perms)


    ## BEGIN CHECKS ##

    if not message.author.bot: # not a bot
      if (
        len(args[:-2]) == 1 and
        f"<@{phyner_id}>" == "".join(re.findall(r"[<@\d>]", message.content))
      ): # no args, just @Phyner
        phyner = message.mentions[0]

        embed = discord.Embed()
        embed.description = f"{phyner.mention} help\n{phyner.mention} ? <search words>"

        try:
          embed.color = phyner.roles[-1].color
        except AttributeError: # when in DM
          embed.color = phyner_red

        await message.channel.send(embed=embed)
        Logger.log("Sent help and search commands")
        
        
      ## COMMAND CHECKS ##

      elif args[1] == "test" and is_mo:
        embed = discord.Embed()
        embed.set_footer(text="Yeet", icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)
        await message.channel.send("done", delete_after=3)

      elif args[1] == "embed":
        await Embed.main(client, message, args, author_perms)
    
  except:
    error = traceback.format_exc()

  if error:
    await Logger.logErrorMessage(client, error, message)
# end on_message

client.run(os.getenv("DISCORD_TOKEN"))