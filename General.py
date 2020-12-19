''' IMPORTS '''

import discord
import traceback

import Logger
from Logger import log
import Support
from Support import simple_bot_response
from Help import help_aliases



''' CONSTANTS '''

say_aliases = ["say", "speak"]
edit_aliases = ["edit"]



''' FUNCTIONS '''

async def say(client, message, args, is_edit=False):
    """
        say and edit command
    """
    
    markdown = "markdown" in args[1]

    msg = None
    if is_edit:
        del args[0] # deletes the edit bit in ..p edit msg_id <content>

        msg_id = Support.get_id_from_str(args[0])
        msg_id = int(msg_id[0]) if msg_id else None

        try:
            msg = await message.channel.fetch_message(msg_id)

        except discord.errors.NotFound:
            await Support.previous_action_error(client, message.channel)
            log("edit msg error", "msg not found")

    content = message.content[message.content.index(args[0])+len(args[0]):]
    content = content if len(content.strip()) > 0 else Support.emojis.space_char
    content = f"```{content}```" if markdown else content

    await msg.edit(content=content) if msg else await message.channel.send(content=content)
    log("edit", "edit command") if msg else log("say", 'say command')
# end say


async def send_ping(client, channel):
    """
        Send ping, host region, and client region
    """
    ping = int(client.latency*1000)
    description = f"**Ping:** {ping}ms\n"

    host_region = None
    try:
        host_region = client.get_guild(Support.ids.mobot_support_id).region
        client_region = channel.guild.region

        description += f"**Host:** {host_region}\n"
        description += f"**Client:** {client_region}"
    except AttributeError: # dm channel
        pass

    await simple_bot_response(channel, description=description)
    log("Connection", f"Ping: {ping}ms, Region: {host_region}")
# end send_ping