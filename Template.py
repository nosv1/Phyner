import asyncio
import traceback

async def main(client, message, args):

  if len(args) == 2 or args[2] == "help": # @Phyner <command> or @Phyner command help
    await message.channel.send("send help")

# end main