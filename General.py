''' IMPORTS '''

import discord
import traceback

import Logger
from Logger import log
import Support
from Support import simple_bot_response
from Help import help_aliases

say_aliases = ["say", "speak"]

''' FUNCTIONS '''

async def say(message, args, markdown=False):
    content = message.content[message.content.index(args[1])+len(args[1]):]
    content = f"```{content}```" if markdown else content
    await message.channel.send(content=content)
    log("say", 'say command')
# end say

async def send_ping(client, channel):
    """
        Send ping, host region, and client region
    """
    ping = int(client.latency*1000)
    description = f"**Ping:** {ping}ms\n"

    host_region = None
    try:
        host_region = client.get_guild(Support.ids.mobot_support).region
        client_region = channel.guild.region

        description += f"**Host:** {host_region}\n"
        description += f"**Client:** {client_region}"
    except AttributeError: # dm channel
        pass

    await simple_bot_response(channel, description=description)
    log("Connection", f"Ping: {ping}ms, Region: {host_region}")
# end send_ping