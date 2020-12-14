''' IMPORTS '''

import discord
import traceback

import Support
from Support import simple_bot_response
from Support import emojis
from Help import help_aliases
from Logger import log



''' CONSTANTS '''

delete_aliases = ["delete", "purge", "clear"]



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        figure out what we're trying to delete, deleting message is default
        messages, categories, ...
    """ 

    if args[2] == "category":
        # TODO @Phyner delete category
        pass

    else:
        await delete_messages(client, message, args[2:-1], author_perms)

# end main
        
    

async def delete_messages(cilent, message, args, author_perms):
    """
        Delete a count of messages, a group of messages, up to (and including) a certian message

        message.author must have manage_message

        @Phyner delete <count> [#channel]
        @Phyner delete <top_message_id> [#channel]
        @Phyner delete <top_message_id> <bottom_message_id> [#channel]
    """

    phyner = Support.get_phyner_from_channel(message.channel)


    ## HELP MESSAGE ##

    if not args or args[0] in help_aliases:
        title = "Deleting Messages in Bulk or Batches"

        description = "**Bulk Delete:**\n"
        description += f"`@{phyner} delete <count> [#channel]`\n"
        description += f"`@{phyner} delete <top_message_id> [#channel]`\n\n"

        description += "**Batch Delete:**\n"
        description += f"`@{phyner} delete <top_message_id> <bottom_message_id> [#channel]`\n\n"

        description += "**Notes:**\n"
        description += f"{emojis.bullet} {phyner.mention} cannot delete more than 100 messages at a time.\n"
        description += f"{emojis.bullet} The given Message IDs are deleted as well as everything between them.\n\n"

        description += "**Permissions Needed:** `Manage Messages`\n\n"

        description += f"**Extra Help:**\n"
        description += f"`@{phyner} ids` to learn how to get Message IDs."

        await simple_bot_response(message.channel,
            title=title,
            description=description,
            reply_message=message
        )

        log('delete messages', 'help sent')
        return


    ## CHECK FOR PERM ##

    if not author_perms.manage_messages:
        await simple_bot_response(message.channel,
            title="Permissions Needed",
            description=f"You need the `Manage Messages` permission to delete messages using {Support.get_phyner_from_channel(message.channel).mention}.",
            reply_message=message
        )
        log("delete message", "Memeber Permissions Needed")
        return


    ## GET TO WORK ##

    top_message_id = 0
    bottom_message_id = 0
    destination_channel = None
    try:
        destination_channel = message.channel_mentions[-1] if message.channel_mentions else message.channel
        if message.channel_mentions:
            del args[-1]

        top_message_id = int(args[0])
        bottom_message_id = int(args[-1])

    except:

        title = "Invalid Syntax"

        description = f"`@{phyner} delete <count> [#channel]` - deletes `count` messages above\n\n"
        description += f"`@{phyner} delete <top_message_id> [#channel]`- deletes all messages below and including `top_message_id`\n\n"
        description += f"`@{phyner} delete <top_message_id> <bottom_message_id> [#channel]`- deletes all messages including and between `top_message_id` and `bottom_message_id`\n\n"

        description += "`#channel` is the location where the messages will be deleted, if omitted, messages in the current channel are deleted\n"

        await simple_bot_response(message.channel, title=title, description=description, reply_message=message)
        log("delete error", f"Invalid Syntax\n{traceback.format_exc()}")
        return

    top_message = None
    bottom_message = None
    try:
        await message.channel.trigger_typing()
        
        top_message = await destination_channel.fetch_message(top_message_id)

        if (
            bottom_message_id != top_message_id or
            len(args) == 2
        ):
            bottom_message = await destination_channel.fetch_message(bottom_message_id)

    except discord.errors.NotFound:
        pass


    async def iter_delete_messages(messages, bot_only=False):
        [await m.delete() for m in messages if bot_only and m.author.id == Support.ids.phyner_id or not bot_only]
    # end iter_delete_messages

    async def log_delete_messages(messages):
        await simple_bot_response(message.channel,
            description=f"**Deleted:** {len(messages)-1}",
            delete_after=3
        )
        log("delete messages", f"Deleted Messages ({len(messages)})")
    # end log_delete_messages


    messages = []
    try:
        try:
            if not top_message: # likely not msg_id inputted, but instead a count
                count = top_message_id + 1 # + 1 to account for message
                messages = await destination_channel.history(limit=count).flatten()

            else:
                messages = await destination_channel.history(after=top_message, before=bottom_message).flatten()
                messages += [top_message] 
                messages += [bottom_message] if bottom_message and bottom_message_id != top_message_id else []
                messages += [message]
                
            messages = messages[-100:]
            await destination_channel.delete_messages(messages)
            await log_delete_messages(messages)

        except discord.errors.HTTPException: # messages too old, or message already in set
            
            msg = await simple_bot_response(message.channel,
                description="These messages are not in my cache. This could take a moment."
            )
            messages = messages[-99:] + [msg]
            await iter_delete_messages(messages)
            await log_delete_messages(messages)

        except AttributeError: # in dm
            msg = await simple_bot_response(message.channel,
                description="It looks like we're in a dm, so I will only delete my messages. This could take a moment."
            )
            messages = messages[-99:] + [msg]
            await iter_delete_messages(messages, bot_only=True)
            await log_delete_messages(messages)
    
    except discord.errors.Forbidden:
        await simple_bot_response(message.channel,
            title="Mising Permissions",
            description="I am missing permissions. I need the `Manage Message` permission to delete messages.",
            reply_message=message
        )
        log('delete error', f"Phyner Missing Permissions\n{traceback.format_exc()}")


# end delete_messages