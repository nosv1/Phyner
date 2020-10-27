# Log functions
import asyncio
from datetime import datetime

mo_id = 405944496665133058

def log(connected, text):

  # open current log
  log_path = f"Logs\\{datetime.strftime(connected, '%Y-%b-%d %H%M')}"
  f = open(log_path, "a+")

  # log text
  log_string = f"{datetime.now()} - {text}"
  print(log_string)
  f.write(f"{log_string}\n")

  # close log
  f.close()
# end Log

async def logError(client, connected, error): # send error to mo and log error
  await client.get_user(mo_id).send(f"```{error}```")
  log(connected, error)
# end logError