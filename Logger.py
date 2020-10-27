# Log functions
import asyncio
from datetime import datetime

mo_id = 405944496665133058

def log(connected, text):

  # open current log
  log_path = f"Logs\\{datetime.strftime(connected, '%Y-%m-%d %H.%M.%S')}.txt"
  f = open(log_path, "a+")

  # log text
  log_string = f"{datetime.strftime(datetime.now(), '%Y-%m-%d %H.%M.%S')} - {text}"
  print(log_string)
  f.write(f"{log_string}\n")

  # close log
  f.close()
# end Log

async def logError(client, connected, error): # general errors
  await client.get_user(mo_id).send(f"```{error}```")
  log(connected, error)
# end logError

async def logErrorMessage(client, connected, error, message): # error after user message
  await client.get_user(mo_id).send(
    f"**Message**\n{message.content}\n\n**Error**```{error}```"
  )
  log(connected, message.content)
  log(connected, error)
# end logErrorMessage