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
        ..p say [#channel] [markdown] content
        ..p edit <msg_id> [#channel] [markdown] content
    """
    
    # get the channel
    channel = Support.get_id_from_str(args[1 if is_edit else 0]) if "#" in args[1 if is_edit else 0] else []
    channel = int(channel[0]) if channel and len(channel) == 1 else message.channel
    if channel != message.channel: # channel may be given

        channel = [c for c in message.guild.channels if c.id == channel]
        if channel: # channel given
            channel = channel[0]
            del args[1 if is_edit else 0]

        else: # channel not given, or not found
            await Support.previous_action_error(client, message)
            log("say/edit error", "given channel not found")
            return


    # find a msg to edit
    msg = None
    if is_edit:
        msg_id = Support.get_id_from_str(args[0])
        msg_id = int(msg_id[0]) if msg_id else None
        del args[0]

        try:
            msg = await channel.fetch_message(msg_id)

        except discord.errors.NotFound:
            await Support.previous_action_error(client, message)
            log("edit msg error", "msg not found")
            return


    # markdown?
    markdown = "markdown" in args[0]
    if markdown:
        del args[0]


    # send it
    if args[0].strip(): # content left over
        content = message.content[message.content.index(args[0]):]
        content = content[len(channel.mention):] if args[0] == channel.mention else content
        content = f"```{content}```" if markdown else content

        await msg.edit(content=content) if msg else await channel.send(content=content)
        if is_edit:
            await Support.process_complete_reaction(message)
        log("edit", "edit command") if msg else log("say", 'say command')

    else: # we aint tryna edit a blank message
        await Support.process_complete_reaction(message, rejected=True)
        log("edit", "edit command rejected") if msg else log("say", 'say command rejected')

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