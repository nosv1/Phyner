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

# general imports
import Secrets
import Logger
import Database

# specific imports
import Embed

mo_id = 405944496665133058
phyner_id = 770416211300188190

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
    Logger.log(connected, "Connected to Discord")

    global phyner_db
    phyner_db = Database.connectDatabase("Phyner")
    Logger.log(connected, "Connected to Database")

    await client.change_presence(
      activity=discord.Activity(
        type=discord.ActivityType.playing, name="Phyner is finer."
      )
    )
    
  except:
    error = traceback.format_exc()

  if error:
    await Logger.logError(client, connected, error)
# end on_ready



### ON_MESSAGE_EDIT and ON_MESSAGE ###

@client.event
async def on_raw_message_edit(payload):
  pd = payload.data

  # get the message object
  message = await client.get_channel(int(pd["channel_id"])).fetch_message(int(pd["id"]))
  
  if not message.author.bot and connected:
    try:
      pd["content"]
      await on_message(message)
    except KeyError: # when content was not updated
      pass
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
    args = mc.split(" ")


    if not message.author.bot: # not a bot
      if len(args) == 1: # no args, just @Phyner
        phyner = message.mentions[0]

        embed = discord.Embed()
        embed.description = f"{phyner.mention} help\n{phyner.mention} ? <search words>"

        try:
          embed.color = phyner.roles[-1].color
        except AttributeError: # when in DM
          embed.color = int("0x980B0D", 16) # red

        await message.channel.send(embed=embed)
        Logger.log(connected, "Sent help and search commands")
        
        
      ## CHECK FOR COMMANDS ##

      elif args[1] == "embed":
        await Embed.main(client, message, args)

    
  except:
    error = traceback.format_exc()

  if error:
    await Logger.logErrorMessage(client, connected, error, message)
# end on_message

client.run(Secrets.getToken("PhynerToken.txt"))