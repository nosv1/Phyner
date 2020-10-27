# Phyner is finer.
# Mo#9991
# Main File, handles events and runs bot, the controller

import discord
import asyncio
from datetime import datetime, timedelta
import random
from pytz import timezone
import traceback
import gspread
import mysql.connector

import Secrets
import Logger
import Database

intents = discord.Intents.all()
client = discord.Client(intents = intents)

connected = None
phyner_db = None

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

client.run(Secrets.getToken("PhynerToken.txt"))