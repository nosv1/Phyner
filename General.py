''' IMPORTS '''

import discord
import traceback

import Logger
from Logger import log
import Support
from Support import simple_bot_response
from Help import help_aliases



''' FUNCTIONS '''

async def send_ping(client, channel):
    """
        Send ping, host region, and client region
    """
    ping = int(client.latency*1000)
    description = f"**Ping:** {ping}ms\n"
    description += f"**Host:** {client.get_guild(Support.ids.mobot_support).region}\n"
    description += f"**Client:** {channel.guild.region}"

    await simple_bot_response(channel, description=description)
    log("Connection", f"Ping: {ping}ms, Region: {channel.guild.region}")
# end send_ping