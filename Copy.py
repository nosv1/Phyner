''' IMPORTS '''

import discord
import re


import Database
from Logger import log
import Support
from Support import simple_bot_response



''' CONSTANTS '''

copy_aliases = ["copy", "duplicate"]
replace_aliases = ["replace"]



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        @Phyner copy <message_id> [#message_location] [#destination]
        @Phyner copy <role_id/@role> [new_role_name]
        @Phyenr copy <channel_id/#channel> [#destination] [new_channel_name] 
        @Phyner copy <category_id> [new_category_name]
        @Phyner replace <message_id> [#message_location] <replacement_message_id> [#replacement_message_location]
    """

    if args[0] in copy_aliases:
        # TODO copy help
        source = await get_copy_source(client, message, args[1:-1])
        if source:
            await create_copy(client, *source, author_perms)

    elif args[0] in replace_aliases:
        await replace(client, message, args[1:], author_perms)

# end main


## REPLACE ##

async def replace(client, message, args, author_perms):

    mesge_id = Support.get_id_from_str(args[0])
    mesge_id = int(mesge_id[0]) if mesge_id else None
    try:
        mesge_channel = message.channel_mentions[0] if "#" in args[1] else message.channel

    except IndexError:
        await Support.previous_action_error(client, message)
        log("replace error", "no message ids") # TODO replace error
        return

    replacement_mesge_id = Support.get_id_from_str(args[2 if "#" in args[1] else 1])
    replacement_mesge_id = int(replacement_mesge_id[0]) if replacement_mesge_id else None
    replacement_mesge_channel = message.channel_mentions[-1] if "#" in args[-1] else message.channel


    if mesge_id and replacement_mesge_id:
        try:
            mesge = await mesge_channel.fetch_message(mesge_id)
            try:
                replacement_mesge = await replacement_mesge_channel.fetch_message(replacement_mesge_id)
            except discord.errors.NotFound:
                replacement_mesge = None
        except discord.errors.NotFound:
            mesge = None

    if mesge and replacement_mesge:
        await mesge.edit(
            content=replacement_mesge.content,
            embed=replacement_mesge.embeds[0] if replacement_mesge else None
        )
        await Support.process_complete_reaction(message)

    elif not mesge:
        await Support.previous_action_error(client, message)
        log("replace error", "no mesge") # TODO replace error
        return

    elif not replacement_mesge:
        await Support.previous_action_error(client, message)
        log("replace erorr", "no replacement_mesge") # TODO replace error
        return
# end replace


## COPY ##

async def get_copy_source(client, message, args):
    """
        returns source, destination, new_name
    """

    source = None

    source_id = Support.get_id_from_str(args[0])
    source_id = int(source_id[0]) if source_id else None


    if not source_id:
        await Support.previous_action_error(client, message)
        log("copy error", "no source id") # TODO copy error
        return


    source = [r for r in message.guild.roles if r.id == source_id] # find a role
    source = [c for c in message.guild.categories if c.id == source_id] if not source else source # if not find a category
    source = [c for c in message.guild.channels if c.id == source_id] if not source else source # if not find a channel


    destination_channel = None
    if not source: # if not, find a channel to look for the message_id

        if len(message.channel_mentions) > 1: # both source, and desitnation mentioned
            source_channel = message.channel_mentions[0]
            destination_channel = message.channel_mentions[-1]

        elif len(message.channel_mentions) == 1:
            if "#" in " ".join(args[:-2]): # channel is mentioned before last arg
                source_channel = message.channel_mentions[0]
                destination_channel = message.channel

            elif "#" in args[-1]: # channel is mentioned in last arg
                source_channel = message.channel
                destination_channel = message.channel_mentions[0]
        
        else:
            source_channel = message.channel
            destination_channel = message.channel


        source_ids = [
            int(Support.get_id_from_str(arg)[0]) for arg in args[:
                -1 if str(destination_channel.id) in message.content else len(args)
            ]
        ] # get all message ids from message
        try:
            # the above got all the ids before destination channel, 
            del source_ids[source_ids.index(source_channel.id)] 
            # need to remove the source channel id from that list, if it's there

        except ValueError: # source channel not mentioned in message
            pass

        
        try:
            source = [await source_channel.fetch_message(source_id) for source_id in source_ids]

        except discord.errors.NotFound:
            await Support.previous_action_error(client, message)
            log("copy error", "no mesge found in current channel if no channel_id given") # TODO copy error
            return

    new_name = message.content.split(args[0])[1].strip()

    return (message, source, destination_channel, new_name) 
# end get_copy_source

async def create_copy(client, message, sources, destination, new_name, author_perms):

    guild = message.guild

    if type(sources[0]) == discord.role.Role: # copy role
        source = sources[0]
        if author_perms.manage_roles:
            try:
                source_copy = await guild.create_role(
                    name=(new_name if new_name else f"{source.name} copy"),
                    permissions=source.permissions,
                    color=source.color,
                    mentionable=source.mentionable
                )

                await simple_bot_response(message.channel,
                    description=f"**Source:** {source.mention}\n**Copy: **{source_copy.mention}"
                )

            except discord.errors.Forbidden:
                await Support.previous_action_error(client, message)
                log("copy role error", "phyner missing perms") # TODO copy role error
                return

            except discord.errors.HTTPException:
                await Support.previous_action_error(client, message)
                log("copy role error", "failed to create role, possible max role count") # TODO copy role error
                return


        else:
            await Support.previous_action_error(client, message)    
            log("copy role error", "missing perms") # TODO copy role error
            return


    elif type(sources[0]) in [discord.channel.CategoryChannel, discord.channel.TextChannel, discord.channel.VoiceChannel]: # copy channel
        source = sources[0]
        if author_perms.manage_channels:

            try:

                name = new_name if new_name else f"{source.name} copy"
                source_copy = await source.clone(name=name)

                await simple_bot_response(message.channel,
                    description=f"**Source:** {source.mention}\n**Copy: **{source_copy.mention}"
                )

            except discord.errors.Forbidden:
                await Support.previous_action_error(client, message)
                log("copy channel error", "phyner missing perms") # TODO copy channel error
                return

            except discord.errors.HTTPException:
                await Support.previous_action_error(client, message)
                log("copy channel error", "failed to create role, possible max role count") # TODO copy channel error
                return


        else:
            await Support.previous_action_error(client, message)
            log("copy channel error", "missing perms") # TODO copy channel error
            return

    
    elif type(sources[0]) == discord.message.Message:
        if author_perms.manage_messages:
            
            description = ""

            for source in sources:
                try:

                    embed = source.embeds[0] if source.embeds else None
                    content = source.content if source.content else None

                    source_copy = await destination.send(content=content, embed=embed)
                    description += f"**Source:** [message]({source.jump_url})\n"
                    description += f"**Copy: **[message]({source_copy.jump_url})\n\n"

                except discord.errors.Forbidden:
                    await Support.previous_action_error(client, message)
                    log("copy message error", "phyner missing perms") # TODO copy message error

            if new_name != "copy_event": # from event
                await simple_bot_response(message.channel, description=description)


        else:
            await Support.previous_action_error(client, message)
            log("copy message error", "missing perms") # TODO copy message error
            return
# end create_copy