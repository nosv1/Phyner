''' IMPORTS '''

import discord
import random
import re

import Logger
from Logger import log
import Support
from Support import edit_aliases
from Support import simple_bot_response
import Help



''' CONSTANTS '''

say_aliases = ["say", "speak", "create"]
randomize_aliases = ["randomize", "shuffle", "choose"]  # edit randomize() if u change this, shuffle on the left, choose on the right
feedback_aliases = ["request", "issue", "bug", "report"] # make sure u change feedback_type in feedback() if you edit this, bugs on the right, requests on the left



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
    markdown = args[0] in ["markdown", "md"]
    if markdown:
        del args[0]


    # send it
    if args[0].strip(): # content left over
        content = message.content[message.content.index(args[0]):]
        content = content[len(channel.mention):] if args[0] == channel.mention else content
        content = f"```{content}```" if markdown else content
        content = content.replace("\\s", Support.emojis.space_char).replace("\\b", Support.emojis.bullet)

        await msg.edit(content=content) if msg else await channel.send(content=content)
        if is_edit:
            await Support.process_complete_reaction(message)
        log("edit", "edit command") if msg else log("say", 'say command')

    else: # we aint tryna edit a blank message
        await Support.process_complete_reaction(message, rejected=True)
        log("edit", "edit command rejected") if msg else log("say", 'say command rejected')
# end say


async def send_ping(client, message):
    """
        Send ping, host region, and client region
    """

    phyner = Support.get_phyner_from_channel(message.channel)

    pong = await message.channel.send('pong')

    ping = int((pong.created_at - (message.edited_at if message.edited_at else message.created_at)).total_seconds() * 1000)
    description = f"**Ping to Discord:** {int(client.latency * 1000)}ms\n"
    description += f"**Ping to {message.author.display_name}:** {ping}ms\n\n"

    host_region = None
    try:
        host_region = client.get_guild(Support.ids.mobot_support_id).region
        client_region = message.guild.region

        description += f"**{phyner.display_name}:** {host_region}\n"
        description += f"**{message.guild}:** {client_region}"
    except AttributeError: # dm channel
        pass

    await simple_bot_response(message.channel, description=description)
    await pong.delete()
    log("Connection", f"Ping: {ping}ms, Region: {host_region}")
# end send_ping


async def feedback(client, message, args):
    phyner = Support.get_phyner_from_channel(message.channel)

    feedback_type = "issue" if args[0] in feedback_aliases[-3:] else "request"

    if not args[1] or args[1] in Help.help_aliases: # no feedback provided
        await Help.send_help_embed(
            client, 
            message, 
            Help.help_links if feedback_type == "issue" else Help.help_links, # FIXME set these links
            default_footer=False
        )
        return


    channel = client.get_guild(Support.ids.phyner_support_id).get_channel(
        Support.ids.reported_issues if feedback_type == "issue" else Support.ids.requested_features
    )


    description = "**Status:** TBD\n\n"

    description += f"**User:** <@{message.author.id}>\n"
    description += f"**Guild:** {message.guild.id}"

    embed = await simple_bot_response(channel,
        title=feedback_type.title(),
        description=description,
        footer=f"..p {feedback_type} <your_{feedback_type}>",
        send=False
    )

    feedback = message.content[message.content.index(args[0]) + len(args[0]):]
    embed.add_field(name=Support.emojis.space_char, value=feedback)


    msg = await channel.send(embed=embed)
    for r in [Support.emojis.pushpin_emoji, Support.emojis.wrench_emoji, Support.emojis.tick_emoji, Support.emojis.wastebasket_emoji]:
        await msg.add_reaction(r)


    description = f"Thank you! Join the [Phyner Support Server]({Support.invite_links.reported_issues if feedback_type == 'issue' else Support.invite_links.requested_features}) to stay up-to-date on [this {feedback_type}]({msg.jump_url}).\n\n"

    if feedback_type == "request":
        description += f"If {phyner.mention} has made your life in Discord a bit easier, please consider showing your support in the form of a [donation](https://paypal.me/moshots). The gesture alone goes a long way to keeping features in development. -Mo#9991 :)"

    await simple_bot_response(message.channel,
        title=f"{feedback_type.title()} {'Submitted' if feedback_type == 'request' else 'Reported'}",
        description=description
    )
# end feedback


async def reaction(message, args):
    '''
        ..p reaction add/remove reaction ... message_id [#channel] [all] # all is used when using remove
    '''

    reactions = [r for r in args[2:]]

    channel = message.channel_mentions[0] if message.channel_mentions else message.channel

    try:
        msg_id = re.findall(r"\s\d{18}\s", " ".join(args))[0].strip()
        msg = await channel.fetch_message(int(msg_id))

    except IndexError:
        await simple_bot_response(message.channel,
            description=f"**There was not a Message ID included in your [message]({message.jump_url}).**\n\n`@Phyner#2797 reaction {args[2]} <reaction> ... <MESSAGE_ID> [#channel] all (if removing reaction)`"
        )
        return

    except discord.errors.NotFound:
        await simple_bot_response(message.channel,
            description=f"**The given Message ID was not a message in {channel.mention}. If the message is in a different channel, type the channel mention after the message id.**\n\n`..p reaction ... <message_id> #channel`"
        )
        return

    for r in reactions:
        
        if args[2] == "add":

            try:
                await msg.add_reaction(r)

                log("reaction", f"added reaction {r}")

            except: # couldn't add emoji to message, likely was one of the args after the last reaction
                pass

        elif args[2] == "remove":
            
            if args[-2] == "all":

                for ur in msg.reactions:

                    if str(ur.emoji) == r:
                        
                        async for user in ur.users():
                            await Support.remove_reactions(msg, user, ur.emoji)
                
                log("reaction", f"removed all reactions")

            else:
                await Support.remove_reactions(msg, Support.get_phyner_from_channel, r)
                
                log("reaction", f"removed reaction {r}")

    await Support.process_complete_reaction(message)
# end reaction


async def randomize(message, args):
    choices = [c.replace(',', '') for c in args[2:]]

    if choices:
        if args[1] in randomize_aliases[0:2]:  # shuffle
            random.shuffle(choices)
            await message.channel.send(f"**Shuffled:**{', '.join(choices)}")
        
        elif args[1] in randomize_aliases[2:]:  # choose
            await message.channel.send(f"**Chosen:** {random.choice(choices)}")

    else:
        await Support.simple_bot_response(
            message.channel,
            description=f"**There were no choices provided.**\n\n`{args[0]} <randomize/choose> <choice>, <choice>, ...`"
        )
# end randomize