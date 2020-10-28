# Log functions
import discord
import asyncio
from datetime import datetime
import pathlib

mo_id = 405944496665133058
phyner_id = 770416211300188190
phyner_red = int("0x980B0D", 16)


def log(text):

  # open current log
  logs_folder = pathlib.Path("Logs")
  log_path = list(logs_folder.iterdir())[-1]
  f = open(log_path, "a+")

  # log text
  log_string = f"{datetime.strftime(datetime.now(), '%Y-%m-%d %H.%M.%S')} - {text}"
  print(log_string)
  f.write(f"{log_string}\n")

  # close log
  f.close()
# end Log

async def logError(client, error): # general errors
  await client.get_user(mo_id).send(f"```{error}```")
  log(error)
# end logError

async def logErrorMessage(client, error, message): # error after user message
  await client.get_user(mo_id).send(
    f"**Message**\n{message.content}\n\n**Error**```{error}```"
  )
  log(message.content)
  log(error)
# end logErrorMessage

async def botResponse(message, response): # response to user command error
  in_dm = False
  try:
    phyner = [member for member in message.channel.members if member.id == phyner_id][0]
  except AttributeError:
    in_dm = True

  embed = discord.Embed()
  embed.description = response
  embed.color = phyner_red if in_dm else phyner.roles[-1].color

  await message.channel.send(embed=embed)
  log(message.content)
  log(response)
# end botResponse