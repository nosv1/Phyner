''' IMPORTS '''

import discord
import asyncio
import mysql.connector
import re
from datetime import datetime
import traceback
import sys


import Database
import Logger
from Logger import log
import Support
from Support import simple_bot_response
from Support import quote
import Help
from Servers import TemplarLeagues



''' CONSTANTS '''

events_aliases = ["watch", "detect", "handle", "event"]
watching_aliases = ["watching", "events"]
watch_webhook_help = "'@Phyner#2797 watch webhook ?' for help"


''' CLASSES '''

## the below classes represent Event objects... Event.condition, Event.action, Event.object ##

class Condition:
    def __init__(self, condition=None, condition_id=None):
        self.condition = condition
        self.id = condition_id
# end Condition

class Action:
    def __init__(self, action=None, action_id=None):
        self.action = action
        self.id = action_id
# end Action


class Webhook:
    def __init__(self, obj_type="webhook", webhook_id=None):
        self.type = obj_type
        self.id = webhook_id
    # end __init__
# end Webhook

class Emoji:
    def __init__(self, obj_type="emoji", emoji_id=None):
        self.type = obj_type
        self.id = emoji_id # should be the unicode or the <:emoji_name:emoji_id>
    # end __init__
# end Emoji


class Event:
    """
        Event from Events table
        id - int, auto increment, primary key
        guild_id - varchar(20)
        obj - varchar(20) --  webhook, emoji
        obj_id - varchar(60)
        condition - varchar(20) -- None, message
        condition_id - varchar(20)
        event - varchar(20) -- message, reaction_add
        action - varchar(50) -- create_private_text_channel
        action_id - varchar(20)

    """

    def __init__(self, guild_id=None, obj=None, condition=Condition(), event=None, action=Action()):
        self.guild_id = guild_id
        self.object = obj
        self.condition = condition
        self.event = event
        self.action = action # TODO this may need to be a list ... event role_add multiple roles ??
    # end __init__


    def __eq__(self, other):
        if isinstance(other, Event):
            return (
                self.guild_id == other.guild_id and
                self.object.id == other.object.id and
                self.condition.id == other.condition.id and
                self.event == other.event and
                self.action.id == other.action.id and
                True
            )
    # end __eq__


    def edit_event(self, events):
        db = Database.connect_database()
        
        existing_event = False
        for event in events:
            if event == self:
                sql = "UPDATE Events SET "
                sql += "`condition` = %s, " % (quote(self.condition.condition) if self.condition else 'NULL ')
                sql += "`condition_id` = %s, " % (quote(self.condition.id) if self.condition else 'NULL ')
                sql += "`action` = %s, " % (quote(self.action.action) if self.action else 'NULL ')
                sql += "`action_id` = %s " % (quote(self.action.id) if self.action else 'NULL ')
                sql += " WHERE "
                sql += f"guild_id = '{self.guild_id}' AND "
                sql += f"object = '{self.object.type}' AND "
                sql += f"object_id = '{self.object.id}'"
                sql += ";"
                existing_event = True
                break

        if not existing_event:
            sql = "INSERT INTO Events ("
            sql += "`guild_id`, `object`, `object_id`, `condition`, `condition_id`, `event`, `action`, `action_id`"
            sql += " ) VALUES ( "
            sql += f"'{self.guild_id}', '{self.object.type}', '{self.object.id}', "
            sql += f"{quote(self.condition.condition) if self.condition.id else 'NULL'}, "
            sql += f"{quote(self.condition.id) if self.condition.id else 'NULL'}, "
            sql += f"'{self.event}', "
            sql += f"{quote(self.action.action) if self.action.id else 'NULL'}, "
            sql += f"{quote(self.action.id) if self.action.id else 'NULL'}"
            sql += f");"

        db.cursor.execute(sql)

        db.connection.commit()
        db.connection.close()
    # end edit_webhook


    def to_string(self):
        s = ""
        s += f"Guild ID: {self.guild_id}, "
        s += f"Object: {self.object.type} {self.object.id}, "
        s += f"Condition {self.condition.condition} {self.condition.id}, " if self.condition else ""
        s += f"Event: {self.event}, "
        s += f"Action: {self.action.action} {self.action.id}" if self.action else ""
        return s
    # end to_string
# end Event



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        @Phyner watch webhook [webhook_id]
    """

    if author_perms.administrator:

        if args[1] in Help.help_aliases:
            log("Events", "help") # TODO help


        elif args[0] in events_aliases and not message.edited_at:

            try:

                if args[1] == "webhook":
                    return await watch_webhook(client, message, args[2:])

                elif args[1] == "emoji":
                    return await watch_emoji(client, message, args[2:])

            except:
                phyner = Support.get_phyner_from_channel(message.channel)
                await simple_bot_response(message.channel,
                    description=f"**The previous action caused an error, and {phyner.mention} Support has been notified. Sorry for the inconvenience. See `@{phyner} bug help` for options about reporting issues and getting help.**"
                )
                await Logger.log_error(client, traceback.format_exc())


        elif args[0] in watching_aliases:
            log('events', 'display events') # TODO display events

    else:
        log("Events", "missig perms") # TODO missing perms
# end main


def get_event_from_entry(entry):

    # get object

    obj_id = entry[2]

    obj = None
    if entry[1] == "webhook":
        obj = Webhook(webhook_id=int(obj_id))

    elif entry[1] == "emoji":
        obj = Emoji(emoji_id=obj_id)


    # get condition

    condition = Condition(
        condition=entry[3],
        condition_id=int(entry[4]) if entry[4] else None
    )

    # get action

    action = Action(
        action=entry[6],
        action_id=int(entry[7])  if entry[7] else None
    )
        

    # get event

    return Event(
        guild_id=int(entry[0]),
        obj=obj,
        condition=condition,
        event=entry[5],
        action=action
    )
# end get_event_from_entry

def get_events():
    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT * FROM Events
    ;""")
    db.connection.close()
    return [get_event_from_entry(entry) for entry in db.cursor.fetchall()]
# end get_events


def get_object_ids(events, type):
    """
        Returns [id, ...] could be str or ints depending on object
    """
    return [e.object.id for e in events if e.object.type == "type"]
# end get_object_ids

def get_event_events(events, event):
    """
        Returns [Event, ...]
    """
    return [e for e in events if e.event == event]
# end get_object_ids


async def wait_for_tick_x_options(client, message, msg, embed, poss_selection=None, selection=[]):
    """
        selection should line up number emojis
    """

    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in [Support.emojis.tick_emoji, Support.emojis.x_emoji]
        )
    # end reaction_check


    # get user input

    number_emojis_used = Support.emojis.number_emojis[1:len(selection)+1]
    selected = None
    try:

        while not selected:

            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

            field_footer, embed = Support.confirm_input_last_field(embed)
            await msg.edit(embed=embed)

            if str(reaction.emoji) == Support.emojis.tick_emoji:
                if poss_selection: # confirmed 
                    selected = poss_selection
                    embed = Support.revert_confirm_input_last_field(field_footer, embed)
                    await Support.remove_reactions(msg, message.author, [Support.emojis.tick_emoji])

                else:
                    msg = await msg.channel.fetch_message(msg.id)

                    for reaction in msg.reactions:
                        if str(reaction.emoji) in number_emojis_used:
                            user_found = False

                            async for user in reaction.users():
                                if user.id == message.author.id:
                                    selected = selection[number_emojis_used.index(str(reaction.emoji))]
                                    user_found = True
                                    break

                            if user_found:
                                break

                    if not selected: # user did not click a number emoji before the tick
                        embed = Support.revert_confirm_input_last_field_exclamation(field_footer, embed)

                        await Support.remove_reactions(msg, message.author, msg.reactions)
                        await msg.edit(embed=embed)

            else:
                embed.title += "\nCancelled"
                embed = Support.delete_last_field(embed)

                await Support.clear_reactions(msg)
                await msg.edit(embed=embed)

                return "cancelled"

    except asyncio.TimeoutError:
        embed.title += "\nTimed Out"
        embed = Support.delete_last_field(embed)
        
        await Support.clear_reactions(msg)
        await msg.edit(embed=embed)
        return "timed out"

    return selected
# end wait_for_tick_x



## EMOJIS ##

async def watch_emoji(client, message, args):
    """
        Figure out what the user wants to watch for upon emoji add or remove
        @Phyner watch emoji <emoji> <mesge_id> [#channel] <action_id>
    """

    phyner = Support.get_phyner_from_channel(message.channel)


    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in [Support.emojis.tick_emoji, Support.emojis.x_emoji]
        )
    # end reaction_check

    def message_check(before, after):
        return before.id == after.id
    # end message_check


    # identify emoji

    embed = None
    emoji = None
    msg = None
    while not emoji:

        emoji = re.findall(r"(<a?:\S+:\d{17,}>)", message.content) # match ' <a:emoji_name:emoji_id> ' or ' <:emoji_name:emoji_id> '
        emoji = emoji[0].strip() if emoji and args[0] in emoji[0] else args[1] if len(args[0]) == 1 else None
        # if match use emoji else use args[1] if it's length is 1 else None

        embed = await simple_bot_response(message.channel,
            title="Emoji Identification Confirmation",
            footer="There may be delays during setup - apologies. - Mo#9991",
            send=False
        ) if not embed else embed

        if emoji: # emoji matched, wait for confirmation
            embed.description = f"Is the emoji below the emoji you would like {phyner.mention} to watch?\n\n"
            
            embed.description += f"{emoji}"

        else: # emoji not found, user edit message, then tick to continue
            embed.description = f"There was not an emoji found in your message. Edit your [message above]({message.jump_url}) to match the syntax below, then click the {Support.emojis.tick_emoji}\n\n"
            
            embed.description += f"`@{phyner} watch emoji <:some_emoji:> [message_id] [action_id]`\n"
            embed.description += f"`@{phyner} watch emoji :partying_face:`\n\n"

            embed.description += f"If this is an error, and you believe your syntax is correct, use `@{phyner} bug help` to see options about reporting issues and getting help." # TODO @Phynber bug help

        if not msg:
            embed.add_field(
                name=Support.emojis.space_char, 
                value=f"{Support.emojis.tick_emoji} to confirm **|** {Support.emojis.x_emoji} to cancel", 
                inline=False
            )
            msg = await message.channel.send(embed=embed)
            await msg.add_reaction(Support.emojis.tick_emoji)
            await msg.add_reaction(Support.emojis.x_emoji)

        else:
            await msg.edit(embed=embed)


        # get user input

        try:
            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

            field_footer, embed = Support.confirm_input_last_field(embed)
            await msg.edit(embed=embed)

            if str(reaction.emoji) == Support.emojis.x_emoji:
                embed.title += "\nCancelled"
                embed = Support.delete_last_field(embed)

                await Support.clear_reactions(msg)
                await msg.edit(embed=embed)

                log("watch emoji", "cancelled emoji identification confirmation")
                return

            else:
                embed = Support.revert_confirm_input_last_field(field_footer, embed)
                await Support.remove_reactions(msg, message.author, [Support.emojis.tick_emoji])

                if not emoji:
                    args, _ = Support.get_args_from_content(message.content)
                    args = args[3:]

        except asyncio.TimeoutError:
            embed.title += "\nTimed Out"
            embed = Support.delete_last_field(embed)

            await Support.clear_reactions(msg)
            await msg.edit(embed=embed)

            log("watch emoji", "timed out waiting for emoji identificaiton confirmation")
            return

    # end while

    emoji_event = Event(guild_id=message.guild.id, obj=Emoji(emoji_id=emoji))

    del args[0] # <emoji> arg no longer needed
    embed.add_field(name=Support.emojis.space_char, value=f"**When** {emoji} **on** ...")
    embed = Support.switch_last_two_fields(embed)
    embed.title = "Message Identification Confirmation"


    # identify message id

    channel = message.channel_mentions[0] if message.channel_mentions else message.channel # BUG
    mesge_id = None
    mesge = None
    while not mesge:

        mesge_id = re.findall(r"(\d{17,})", args[0])
        mesge_id = int(mesge_id[0]) if mesge_id else None

        try:
            if mesge_id:
                mesge = await channel.fetch_message(mesge_id)

        except discord.errors.NotFound:
            pass

        if mesge: # user message found
            embed.description = f"Is the message below the message you would like {phyner.mention} to watch for when {emoji} is added or removed?\n\n"

            embed.description += f"[click to go to message]({mesge.jump_url})"

        elif mesge_id and not mesge: # no user message found, but possible message id found
            embed.description = f"A message with the given ID, `{mesge_id}`, was not found in {'this channel' if not message.channel_mentions else 'the given channel, '}{channel.mention if message.channel_mentions else ''}. Edit your [message above]({message.jump_url}) to match the syntax below, then click the {Support.emojis.tick_emoji}\n\n"

        elif not mesge_id: # no message id found
            embed.description = f"There was not a message ID found in your message. Edit your [message above]({message.jump_url}) to match the syntax below, then click the {Support.emojis.tick_emoji}\n\n"

        if not mesge:
            embed.description += f"`... `{emoji}` <message_id> [#channel] [action_id]`\n"
            embed.description += f"`... `{emoji}` {message.id} `{channel.mention}"

        await msg.edit(embed=embed)


        # get user input

        try:
            
            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

            field_footer, embed = Support.confirm_input_last_field(embed)
            await msg.edit(embed=embed)

            if str(reaction.emoji) == Support.emojis.x_emoji:
                embed.title += "\nCancelled"
                embed = Support.delete_last_field(embed)

                await Support.clear_reactions(msg)
                await msg.edit(embed=embed)

                log("watch emoji", "cancelled message identification confirmation")
                return

            else:
                embed = Support.revert_confirm_input_last_field(field_footer, embed)
                await Support.remove_reactions(msg, message.author, [Support.emojis.tick_emoji])

                if not mesge:
                    args, _ = Support.get_args_from_content(message.content)
                    args = args[4:]
                    channel = message.channel_mentions[0] if message.channel_mentions else message.channel

        except asyncio.TimeoutError:
            embed.title += "\nTimed Out"
            embed = Support.delete_last_field(embed)

            await Support.clear_reactions(msg)
            await msg.edit(embed=embed)

            log("watch emoji", "timed out waiting for message identificaiton confirmation")
            return

    # end while


    emoji_event.condition = Condition(condition="message", condition_id=mesge.id)

    del args[0] # <message_id> arg no longer needed
    if str(mesge.channel.id) in args[0] and message.channel.id != mesge.channel.id: # remove channel mention as well
        del args[0]

    embed = Support.delete_last_field(embed)
    embed.add_field(name=Support.emojis.space_char, value=f"**When** {emoji} **on** [message]({mesge.jump_url}) **is** ...", inline=False)
    embed = Support.switch_last_two_fields(embed)
    embed.title = "Event Identification Confirmation"


    # identify event 

    number_emojis_used = []
    event = None

    possible_events = ["reaction_add", "reaction_remove"]

    # build description
    embed.description = f"Choose from the list below what {phyner.mention} needs to watch for with {emoji}\n\n"

    for i, possible_event in enumerate(possible_events):
        embed.description += f"{Support.emojis.number_emojis[i+1]} **{possible_event}\n**"
    
    # build footer
    value = f"Number emoji then {Support.emojis.tick_emoji} to confirm\n"
    value += f"{Support.emojis.x_emoji} to cancel"

    embed = embed.to_dict()
    embed["fields"][-1]["value"] = value
    embed = discord.Embed().from_dict(embed)

    # send it
    await Support.clear_reactions(msg)
    await msg.edit(embed=embed)

    number_emojis_used = Support.emojis.number_emojis[1:len(possible_events)+1]
    [await msg.add_reaction(ne) for ne in number_emojis_used]

    await msg.add_reaction(Support.emojis.tick_emoji)
    await msg.add_reaction(Support.emojis.x_emoji)


    # get user input

    event = await wait_for_tick_x_options(client, message, msg, embed, poss_selection=event, selection=possible_events)
    if event == "timed out":
        log("watch webhook", "timed out waiting for event identificaiton confirmation")
        return

    elif event == "cancelled":
        log("watch webhook", "cancelled during event identification confirmation") 
        return


    emoji_event.event = event

    embed = Support.delete_last_field(embed)
    embed.add_field(name=Support.emojis.space_char, value=f"**When** {emoji} **on** [message]({mesge.jump_url}) **is** {event}ed, **do** ... ", inline=False)
    embed = Support.switch_last_two_fields(embed)
    embed.title = "Action Identification Confirmation"


    # identify event 

    number_emojis_used = []
    action = None

    possible_actions = ["create_private_text_channel", ] # "role_add (wip)", "role_remove (wip)"]

    # build description
    embed.description = f"Choose from the list below what {phyner.mention} needs to do when {emoji} is {'added to' if event == 'reaction_add' else 'removed from'} this [message]({message.jump_url}).\n\n"

    for i, possible_action in enumerate(possible_actions):
        embed.description += f"{Support.emojis.number_emojis[i+1]} **{possible_action}\n**"
    
    # build footer
    value = f"Number emoji then {Support.emojis.tick_emoji} to confirm\n"
    value += f"{Support.emojis.x_emoji} to cancel"

    embed = embed.to_dict()
    embed["fields"][-1]["value"] = value
    embed = discord.Embed().from_dict(embed)

    # send it
    await Support.clear_reactions(msg)
    await msg.edit(embed=embed)

    number_emojis_used = Support.emojis.number_emojis[1:len(possible_actions)+1]
    [await msg.add_reaction(ne) for ne in number_emojis_used]

    await msg.add_reaction(Support.emojis.tick_emoji)
    await msg.add_reaction(Support.emojis.x_emoji)


    # get user input

    action = await wait_for_tick_x_options(client, message, msg, embed, poss_selection=action, selection=possible_actions)
    if action == "timed out":
        log("watch webhook", "timed out waiting for action identificaiton confirmation")
        return

    elif action == "cancelled":
        log("watch webhook", "cancelled during action identification confirmation") 
        return


    emoji_event.action = Action(action=action)

    embed = Support.delete_last_field(embed)
    embed.add_field(name=Support.emojis.space_char, value=f"**When** {emoji} **on** [message]({mesge.jump_url}) **is** {event}ed, **do** {action} **using** ...", inline=False)
    embed = Support.delete_last_field(Support.switch_last_two_fields(embed))
    embed.title = "Action ID Identification Confirmation"

    await Support.clear_reactions(msg)

    await msg.add_reaction(Support.emojis.tick_emoji)
    await msg.add_reaction(Support.emojis.x_emoji)

    # build footer
    value = f"{Support.emojis.tick_emoji} to confirm **|** {Support.emojis.x_emoji} to cancel"
    embed.add_field(
        name=Support.emojis.space_char, 
        value=value, 
        inline=False
    )

    # identify action id

    action_id = None
    action_source = None
    while not action_source:

        action_id = re.findall(r"\d{17,}", args[0])
        action_id = int(action_id[0]) if action_id else None

        try:
            if action_id and not action_source:
                if action == "create_private_text_channel":
                    categories = message.guild.categories # check categories
                    action_source = [category_channel for category_channel in categories if category_channel.id == action_id]
                    
                    if not action_source: # check channels
                        channels = message.guild.channels
                        action_source = [chnnl for chnnl in channels if chnnl.id == action_id]

        except: # this may not be needed, but same template as while not mesge: seen above
            pass

        action_source_types = []
        if action in ["create_private_text_channel"]:
            action_source_types = ["text channels", "categories"]

        if action_source:
            action_source = action_source[0]

            action_source_type = ""
            
            # categories and text channels
            action_source_type = 'category' if str(action_source.type) == "category" else 'text channel' if str(action_source.type) == 'text' else None # unlikely this is ends up being none

            # action_source_type = ... if role or something

            embed.description = f"Is the below {action_source_type} the {action_source_type} you would like {phyner.mention} to use for {action}?\n\n"

            embed.description += f"{action_source.mention}"

        elif action_id and not action_source: # no action_source found based on action_id
            embed.description = f"There were no {' or '.join(action_source_types)} found with the given action ID, {action_id}, in this server. Edit your [message above]({message.jump_url}) to match the syntax below, then click the {Support.emojis.tick_emoji}\n\n"

        elif not action_id: # no action id provided
            embed.description = f"There was not an action ID found in your message. Edit your [message above]({message.jump_url}) to match the syntax below, then click the {Support.emojis.tick_emoji}\n\n"

        if not action_source:
            embed.description += f"`... <message_id> [#channel] <action_id/action_mention>`\n"
            embed.description += f"`... {mesge.id} {mesge.channel.mention} 593896370700550154`"

        await msg.edit(embed=embed)


        # get user input

        try:
            
            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

            field_footer, embed = Support.confirm_input_last_field(embed)
            await msg.edit(embed=embed)

            if str(reaction.emoji) == Support.emojis.x_emoji:
                embed.title += "\nCancelled"
                embed = Support.delete_last_field(embed)

                await Support.clear_reactions(msg)
                await msg.edit(embed=embed)

                log("watch emoji", "cancelled action id identification confirmation")
                return

            else:
                embed = Support.revert_confirm_input_last_field(field_footer, embed)
                await Support.remove_reactions(msg, message.author, [Support.emojis.tick_emoji])

                if not action_source:
                    args, _ = Support.get_args_from_content(message.content)
                    args = args[-2:]

        except asyncio.TimeoutError:
            embed.title += "\nTimed Out"
            embed = Support.delete_last_field(embed)

            await Support.clear_reactions(msg)
            await msg.edit(embed=embed)

            log("watch emoji", "timed out waiting for action id identificaiton confirmation")
            return

    # end while

    emoji_event.action.id = action_source.id

    embed = Support.delete_last_field(embed)
    embed.add_field(name=Support.emojis.space_char, value=f"**When** {emoji} **on** [message]({mesge.jump_url}) **is** {event}ed, **do** {action} **using** {action_source.mention}.", inline=False) # may need to make action_source a list
    embed = Support.delete_last_field(Support.switch_last_two_fields(embed))
    embed.title = "Event Confirmation"
    embed.description = discord.Embed().Empty

    # build footer
    value = f"{Support.emojis.tick_emoji} to confirm **|** {Support.emojis.x_emoji} to cancel"
    embed.add_field(
        name=Support.emojis.space_char, 
        value=value, 
        inline=False
    )

    await msg.edit(embed=embed)

    try:
            
        reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

        field_footer, embed = Support.confirm_input_last_field(embed)
        await msg.edit(embed=embed)

        if str(reaction.emoji) == Support.emojis.x_emoji:
            embed.title += "\nCancelled"
            embed = Support.delete_last_field(embed)

            await Support.clear_reactions(msg)
            await msg.edit(embed=embed)

            log("watch emoji", "cancelled event confirmation")
            return

    except asyncio.TimeoutError:
        embed.title += "\nTimed Out"
        embed = Support.delete_last_field(embed)

        await Support.clear_reactions(msg)
        await msg.edit(embed=embed)

        log("watch emoji", "timed out waiting for event confirmation")
        return


    ## all done

    await mesge.add_reaction(emoji)

    embed.title = "Event Confirmed"
    embed = Support.delete_last_field(embed)

    await Support.clear_reactions(msg)
    await msg.edit(embed=embed)

    emoji_event.edit_event(get_events())

    log("watch emoji", emoji_event.to_string())
    return emoji_event
# end watch_emoji



## WEBHOOKS ##

async def watch_webhook(client, message, args):
    """
        Figure out what the user wants to watch for upon webhook message
    """

    phyner = Support.get_phyner_from_channel(message.channel)

    # find matching webhooks

    webhook_id = args[0]
    webhook = None

    guild_webhooks = [wh for wh in await message.guild.webhooks() if wh.type == discord.WebhookType.incoming] if message.guild else []
    for wh in guild_webhooks:
        if str(wh.id) == webhook_id or wh.url in webhook_id: # in url cause cba to replace <> from input
            webhook = wh

    embed = await simple_bot_response(message.channel,
        title="Webhook Identification Confirmation",
        send=False
    )

    # list webhooks to choose from

    msg = None
    number_emojis_used = []
    confirmed_webhook = None
    while not confirmed_webhook:

        if not webhook:
            if guild_webhooks: # check given webhook_id against guild_webhook

                embed.description = f"A webhook with the given ID/URL, `{webhook_id}`, was not found.\n"
                embed.description += f"Choose the webhook you would like {phyner.mention} to watch from the list below.\n\n"

                for i, wh in enumerate(guild_webhooks):
                    embed.description += f"{Support.emojis.number_emojis[i+1]} **{wh.name} - {wh.id}**\n"

                # build footer
                value = f"\nNumber emoji then {Support.emojis.tick_emoji} to confirm\n"
                value += f"{Support.emojis.x_emoji} to cancel"

                if not msg:
                    embed.add_field(
                        name=Support.emojis.space_char, 
                        value=f"{Support.emojis.tick_emoji} to confirm **|** {Support.emojis.x_emoji} to cancel", 
                        inline=False
                    )

                    msg = await message.channel.send(embed=embed)
                number_emojis_used = Support.emojis.number_emojis[1:len(guild_webhooks)+1]
                [await msg.add_reaction(ne) for ne in number_emojis_used]
                
            else: # no guild webhooks to check

                await simple_bot_response(message.channel,
                    description="**There were no webhooks found in this server.**",
                    reply_message=message
                )
                log("watch webhook", "no webhooks found")
                return

        else: # webhook id given and found, confirm
            embed.description = f"Is the webhook below the webhook you would like {phyner.mention} to watch?\n\n"

            embed.description += f"**{webhook.name} - {webhook.id}**\n\n"

            value = f"{Support.emojis.tick_emoji} to confirm **|** {Support.emojis.x_emoji} to cancel"

            if not msg:
                embed.add_field(
                    name=Support.emojis.space_char, 
                    value=value, 
                    inline=False
                )

                msg = await message.channel.send(embed=embed)   
                
        await msg.add_reaction(Support.emojis.tick_emoji)
        await msg.add_reaction(Support.emojis.x_emoji)

        # get user input

        confirmed_webhook = await wait_for_tick_x_options(client, message, msg, embed, poss_selection=webhook, selection=guild_webhooks)
        if webhook == "timed out":
            log("watch webhook", "timed out waiting for webhook identificaiton confirmation")
            return

        elif webhook == "cancelled":
            log("watch webhook", "cancelled during webhook identification confirmation") 
            return

    # end while

    webhook = confirmed_webhook
    del confirmed_webhook
    
    # create event

    embed.title=discord.Embed().Empty
    embed.description=f"**Now treating messages from <@{webhook.id}> as user messages.**"
    embed = Support.delete_last_field(embed)

    await Support.clear_reactions(msg)
    await msg.edit(embed=embed)

    event = Event(
        guild_id=message.guild.id, 
        obj=Webhook(webhook_id=webhook.id),
        event="on_message"
    )
    event.edit_event(get_events())

    log("watch webhook", event.to_string())
    return event
# end watch_webhook



## ACTIONS ##

async def perform_action(client, message, user, event):

    if event.action.action == "create_private_text_channel":
        channel = await create_private_text_channel(client, message, user, event)

        if event.guild_id == TemplarLeagues.templar_leagues_id:
            if event.condition.id == "some_message_id":
                if event.object.id == "some_emoji":
                    await TemplarLeagues.series_report(channel, user)

    
# end perform_action


async def create_private_text_channel(client, message, user, event):

    source = [c for c in message.guild.channels if c.id == event.action.id]
    source = [c for c in message.guild.categories if c.id == event.action.id] if not source else source

    if not source:
        log('event', f"source does not exist for CREATE_PRIVATE_TEXT_CHANNEL\n{event.to_string()}")
        return
    else:
        source = source[0]

    overwrites = source.overwrites
    overwrites[user] = discord.PermissionOverwrite(
        read_messages=True,
        send_messages=True
    )

    channel = await message.guild.create_text_channel(
        name=f"{user.display_name} {user.discriminator}",
        overwrites=overwrites,
        category=source.category if type(source) == type(message.channel) else source,
        position=sys.maxsize,
    )

    log("reaction_add event", f"private text channel created {event.to_string()}")
    return channel
# end create_private_text_channel