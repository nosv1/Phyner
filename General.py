''' IMPORTS '''

import discord
import traceback

import Logger
from Logger import log
import Support
from Support import simple_bot_response



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


async def delete_messages(client, message, args, author_perms):
    """
        Delete a count of messages, a group of messages, up to (and including) a certian message

        message.author must have manage_message
    """
    args = args[:-1]
        
    if not author_perms.manage_messages:
        await simple_bot_response(message.channel,
            title="Permissions Needed",
            description=f"You need the `Manage Messages` permission to delete messages using {Support.get_phyner_from_channel(message.channel).mention}.",
            reply_message=message
        )
        log("delete message", "Memeber Permissions Needed")
        return


    top_message_id = 0
    bottom_message_id = 0
    destination_channel = None
    try:
        destination_channel = message.channel_mentions[-1] if message.channel_mentions else message.channel
        if message.channel_mentions:
            del args[-1]

        top_message_id = int(args[2])
        bottom_message_id = int(args[-1])

    except:
        phyner = Support.get_phyner_from_channel(message.channel)

        title = "Invalid Syntax"

        description = f"`@{phyner} delete <count> [#channel]` - deletes `count` messages above\n"
        description = f"`@{phyner} delete <top_message_id> [#channel]`- deletes all messages below and including `top_message_id`\n"
        description = f"`@{phyner} delete <top_message_id> <bottom_message_id> [#channel]`- deletes all messages including and between `top_message_id` and `bottom_message_id`\n\n"

        description += "`#channel` is the location where the messages will be deleted, if omitted, messages in the current channel are deleted\n"

        await simple_bot_response(message.channel, title=title, description=description, reply_message=message)
        log("delete error", f"Invalid Syntax\n{traceback.format_exc()}")
        return

    top_message = None
    bottom_message = None
    try:
        await message.channel.trigger_typing()
        top_message = await destination_channel.fetch_message(top_message_id)
        bottom_message = await destination_channel.fetch_message(bottom_message_id) if bottom_message_id != top_message_id else None

    except discord.errors.NotFound:
        pass


    messages = []
    try:
        if not top_message: # likely not msg_id inputted, but instead a count
            count = top_message_id
            messages = await destination_channel.history(limit=count).flatten()

        else:
            messages = await destination_channel.history(after=top_message, before=bottom_message).flatten()
            messages += [top_message] + ([bottom_message] if bottom_message else [])
            messages += [message]
            

        await destination_channel.delete_messages(messages)
        await simple_bot_response(message.channel,
            description=f"**Deleted:** {len(messages)}",
            delete_after=3
        )
        log("delete messages", f"Deleted Messages ({len(messages)})")
    
    except discord.errors.Forbidden:
        await simple_bot_response(message.channel,
            title="Mising Permissions",
            description="I am missing permissions. I need the `Manage Message` permission to delete messages.",
            reply_message=message
        )
        log('delete error', f"Phyner Missing Permissions\n{traceback.format_exc()}")

    except discord.errors.HTTPException:
        for delete_message in messages:
            await delete_message.delete()

        await simple_bot_response(message.channel,
            description=f"**Deleted:** {len(messages)}",
            delete_after=3
        )
        log("delete messages", f"Deleted Messages ({len(messages)})")
    

# end delete_messages