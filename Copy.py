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

async def main(message, args, author_perms):
    """
        @Phyner copy <message_id> [#message_location] [#destination]
        @Phyner copy <role_id/@role> [new_role_name]
        @Phyenr copy <channel_id/#channel> [#destination] [new_channel_name] 
        @Phyner copy <category_id> [new_category_name]
    """

    # TODO copy help
    source = await get_copy_source(message, args[2:])
    if source:
        await create_copy(*source, author_perms)

# end main


async def get_copy_source(message, args):
    """
        returns source, destination, new_name
    """

    msg = None
    source = None
    while not source:

        source_id = Support.get_id_from_str(args[0])
        source_id = int(source_id[0]) if source_id else None

        if not source_id:
            log("copy", "no source id") # TODO copy error
            return

        source = [r for r in message.guild.roles if r.id == source_id] # find a role
        source = [c for c in message.guild.categories if c.id == source_id] if not source else source # if not find a category
        source = [c for c in message.guild.channels if c.id == source_id] if not source else source # if not find a channel

        if not source: # if not, find a channel to look for the message_id

            if len(message.channel_mentions) > 1:
                channel = message.channel_mentions[0]
            
            else: # we get destination channel later, but we assume user is in source channel so [-1] is the destination channel if given at all
                channel = message.channel
            
            try:
                source = await channel.fetch_message(source_id)

            except discord.errors.NotFound:
                log("copy", "no mesge found in current channel if no channel_id given") # TODO copy error
                return

        else:
            source = source[0]

        destination = message.channel_mentions[-1] if message.channel_mentions else message.channel
        new_name = message.content.split(args[0])[1].strip()

        return (msg if msg else message, source, destination, new_name) # TODO this should be outside of while, and use .wait_for
# end get_copy_source

async def create_copy(msg, source, destination, new_name, author_perms):

    embed, message, msg = Support.messageOrMsg(msg)
    guild = msg.guild if msg else message.guild

    if type(source) == discord.role.Role: # copy role
        if author_perms.manage_roles:
            try:
                source_copy = await guild.create_role(
                    name=(new_name if new_name else f"{source.name} copy"),
                    permissions=source.permissions,
                    color=source.color,
                    mentionable=source.mentionable
                )

                embed = await simple_bot_response(msg.channel if msg else message.channel,
                    description=f"**Source:** {source.mention}\n**Copy: **{source_copy.mention}",
                    send=False
                )

                await msg.edit(embed=embed) if msg else await message.channel.send(embed=embed)

            except discord.errors.Forbidden:
                log("copy role", "phyner missing perms") # TODO copy role error
                return

            except discord.errors.HTTPException:
                log("copy role", "failed to create role, possible max role count") # TODO copy role error
                return


        else:
            log("copy role", "missing perms") # TODO copy role error
            return


    elif type(source) in [discord.channel.CategoryChannel, discord.channel.TextChannel, discord.channel.VoiceChannel]: # copy channel
        if author_perms.manage_channels:

            try:

                name = new_name if new_name else f"{source.name} copy"
                source_copy = await source.clone(name=name)

                embed = await simple_bot_response(msg.channel if msg else message.channel,
                    description=f"**Source:** {source.mention}\n**Copy: **{source_copy.mention}",
                    send=False
                )

                await msg.edit(embed=embed) if msg else await message.channel.send(embed=embed)

            except discord.errors.Forbidden:
                log("copy role", "phyner missing perms") # TODO copy channel error
                return

            except discord.errors.HTTPException:
                log("copy role", "failed to create role, possible max role count") # TODO copy channel error
                return


        else:
            log("copy role", "missing perms") # TODO copy channel error
            return

    
    elif type(source) == discord.message.Message:
        if author_perms.manage_messages:

            try:

                embed = source.embeds[0] if source.embeds else None
                content = source.content if source.content else None

                source_copy = await destination.send(content=content, embed=embed)
                embed = await simple_bot_response(msg.channel if msg else message.channel,
                    description=f"**Source:** [message]({source.jump_url})\n**Copy: **[message]({source_copy.jump_url})",
                    send=False
                )

                await msg.edit(embed=embed) if msg else await message.channel.send(embed=embed)

            except discord.errors.Forbidden:
                log("copy role", "phyner missing perms") # TODO copy message error
                return

            except discord.errors.HTTPException:
                log("copy role", "failed to create role, possible max role count") # TODO copy message error
                return


        else:
            log("copy role", "missing perms") # TODO copy message error
            return
# end create_copy