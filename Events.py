''' IMPORTS '''

import discord
import asyncio
import mysql.connector
import re


import Database
from Logger import log
import Support
from Support import simple_bot_response
from Support import quote
import Help



''' CONSTANTS '''

events_aliases = ["watch", "detect", "handle"]
watching_aliases = ["watching", "events"]
watch_webhook_help = "'@Phyner#2797 watch webhook ?' for help"


''' CLASSES '''

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
        action - varchar(50) -- create_private_channel
        action_id - varchar(20)

    """

    def __init__(self, guild_id=None, obj=None, condition=None, event=None, action=None):
        self.guild_id = guild_id
        self.object = obj
        self.condition = condition
        self.event = event
        self.action = action
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
            sql += f"{quote(self.condition.condition) if self.condition else 'NULL'}, "
            sql += f"{quote(self.condition.id) if self.condition else 'NULL'}, "
            sql += f"'{self.event}', "
            sql += f"{quote(self.action.action) if self.action else 'NULL'}, "
            sql += f"{quote(self.action.id) if self.action else 'NULL'}"
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

''' the below classes represent Event objects... Event.condition, Event.action, Event.object '''

class Condition():
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



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        @Phyner watch webhook [webhook_id]
    """

    if author_perms.administrator:

        if args[1] in Help.help_aliases:
            log("Events", "help") # TODO help


        elif args[0] in events_aliases:

            if args[1] == "webhook":
                return await watch_webhook(client, message, args[1:])

            elif args[1] == "emoji":
                return await watch_emoji(client, message, args[1:])


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
        Returns [int(id), ...]
    """
    return [e.object.id for e in events if e.object.type == "type"]
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

            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=60)

            if str(reaction.emoji) == Support.emojis.tick_emoji:
                if poss_selection: # confirmed 
                    selected = poss_selection

                else:
                    embed = embed.to_dict()
                    field_footer = embed["fields"][-1]["value"]
                    embed["fields"][-1]["value"] = "\n".join(field_footer.split("\n")[:-2] + ["**Confirming Input...**"])
                    embed = discord.Embed().from_dict(embed)

                    await msg.edit(embed=embed)
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
                        lines = field_footer.split("\n")
                        lines[-2] = f"**{lines[-2]} {Support.emojis.exclamation_emoji}**"

                        embed = embed.to_dict()
                        embed["fields"][-1]["value"] = "\n".join(lines)
                        embed = discord.Embed().from_dict(embed)

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
    """

    phyner = Support.get_phyner_from_channel(message.channel)


    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in [Support.emojis.tick_emoji, Support.emojis.x_emoji]
        )
    # end reaction_check


    # identify emoji

    emoji = None
    msg = None
    while not emoji:

        emoji = re.findall(r"(\s?<a?:\S+:\d+>\s?)", message.content) # match ' <a:emoji_name:emoji_id> ' or ' <:emoji_name:emoji_id> '
        emoji = emoji[0].strip() if emoji and args[1] in emoji[0] else args[1] if len(args[1]) == 1 else None
        # if match use emoji else use args[1] if it's length is 1 else None

        embed = await simple_bot_response(message.channel,
            title="Confirm Emoji Identification",
            send=False
        )

        if emoji: # emoji matched, wait for confirmation
            embed.description = f"Is the emoji below the emoji you would like {phyner.mention} to watch?\n\n"
            
            embed.description += f"{emoji}\n\n"

        else: # emoji not found, user edit message, then tick to continue
            embed.description = f"There was not an emoji found in your message. Edit your [message above]({message.jump_url}) to match the syntax below, then click the {Support.emojis.tick_emoji}\n\n"
            
            embed.description += f"`@{phyner} watch emoji <:some_emoji:> [event] [message_id]`\n"
            embed.description += f"`@{phyner} watch emoji :partying_face:`\n\n"

            embed.description += f"If this is an error, and you believe your syntax is correct, use `{args[0]} bug help` to see options about reporting issues and getting help." # TODO @Phynber bug help

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
            msg = await msg.edit(embed=embed)


        # get user input

        try:
            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

            if str(reaction.emoji) == Support.emojis.x_emoji:
                embed.title += "\nCancelled"
                embed = Support.delete_last_field(embed)

                await Support.clear_reactions(msg)
                await msg.edit(embed=embed)

                log("watch emoji", "cancelled emoji identification confirmation")
                return

            else:
                await Support.clear_reactions(msg) if emoji else await Support.remove_reactions(msg, message.author, [Support.emojis.tick_emoji]) # clear reactions if emoji found else remove the tick

        except asyncio.TimeoutError:
            embed.title += "\nTimed Out"
            embed = Support.delete_last_field(embed)

            await Support.clear_reactions(msg)
            await msg.edit(embed=embed)

            log("watch emoji", "timed out waiting for emoji identificaiton confirmation")
            return

    # end while

    del args[0:2] # emoji and <emoji> args no longer needed
    embed.add_field(name="Watching Emoji", value=emoji)
    embed = Support.switch_last_two_fields(embed)
    await msg.edit(embed=embed)


    # identify event 

    embed.title = "Confirm Event Identification"
    event = None
    number_emojis_used = []
    while not event:

        possible_events = ["reaction_add", "reaction_remove"]
        if args[0] not in possible_events: # user provided event

            # build description
            embed.description = f"'{args[0]}' is not an event for emojis. Choose from the list below what {phyner.mention} needs to watch for with {emoji}\n\n"

            for i, possible_event in enumerate(possible_events):
                embed.description += f"{Support.emojis.number_emojis[i+1]} **{possible_event}\n**"
            embed.description += Support.emojis.space_char
            
            # build footer
            value = f"Number emoji then {Support.emojis.tick_emoji} to confirm\n"
            value += f"{Support.emojis.x_emoji} to cancel"

            embed = embed.to_dict()
            embed["fields"][-1]["value"] = value
            embed = discord.Embed().from_dict(embed)

            # send it
            await msg.edit(embed=embed)
            number_emojis_used = Support.emojis.number_emojis[1:len(possible_events)+1]
            [await msg.add_reaction(ne) for ne in number_emojis_used]

        else: # user did not provide event
            
            # build description
            embed.description = f"Is the event below the event you would like {phyner.mention} to watch with {emoji}?\n\n"

            embed.description += f"**{args[0]}**\n{Support.emojis.space_char}"

            # build footer
            value = f"{Support.emojis.tick_emoji} to confirm **|** {Support.emojis.x_emoji} to cancel"

            embed = embed.to_dict()
            embed["fields"][-1]["value"] = value
            embed = discord.Embed().from_dict(embed)
            await msg.edit(embed=embed)


        await msg.add_reaction(Support.emojis.tick_emoji)
        await msg.add_reaction(Support.emojis.x_emoji)


        # get user input

        event = await wait_for_tick_x_options(client, message, msg, embed, poss_selection=event, selection=possible_events)
        if event == "timed out":
            log("watch webhook", "timed out waiting for webhook identificaiton confirmation")
            return

        elif event == "cancelled":
            log("watch webhook", "cancelled during webhook identification confirmation") 
            return

    # end while

    embed.add_field(name="For Event", value=f"{event}")
    embed = Support.switch_last_two_fields(embed)

    event = Event(
        guild_id=message.guild.id, 
        obj=Emoji(emoji_id=emoji),
        event=event
    )

    await msg.edit(embed=embed) # todo get message id, 

# end watch_emoji



## WEBHOOKS ##

async def watch_webhook(client, message, args):
    """
        Figure out what the user wants to watch for upon webhook message
    """

    phyner = Support.get_phyner_from_channel(message.channel)

    # find matching webhooks

    webhook_id = args[1]
    webhook = None

    guild_webhooks = [wh for wh in await message.guild.webhooks() if wh.type == discord.WebhookType.incoming] if message.guild else []
    for wh in guild_webhooks:
        if str(wh.id) == webhook_id or wh.url in webhook_id: # in url cause cba to replace <> from input
            webhook = wh

    embed = await simple_bot_response(message.channel,
        title="Confirm Webhook Identification",
        send=False
    )

    # list webhooks to choose from

    msg = None
    number_emojis_used = []
    if not webhook:

        if guild_webhooks:

            embed.description = f"A webhook with the given id/url, `{webhook_id}`, was not found.\n"
            embed.description += f"Choose the webhook you would like {phyner.mention} to watch from the list below.\n\n"

            for i, wh in enumerate(guild_webhooks):
                embed.description += f"{Support.emojis.number_emojis[i+1]} **{wh.name} - {wh.id}**\n"

            embed.description += f"\nNumber emoji then {Support.emojis.tick_emoji} to confirm\n"
            embed.description += f"{Support.emojis.x_emoji} to cancel"

            msg = await message.channel.send(embed=embed)
            number_emojis_used = Support.emojis.number_emojis[1:len(guild_webhooks)+1]
            [await msg.add_reaction(ne) for ne in number_emojis_used]
            
        else:

            await simple_bot_response(message.channel,
                description="**There were no webhooks found in this server.**",
                reply_message=message
            )
            log("watch webhook", "no webhooks found")
            return


    else:
        embed.description = f"Is the webhook below the webhook you would like {phyner.mention} to watch?\n\n"

        embed.description += f"**{webhook.name} - {webhook.id}**\n\n"

        embed.description += f"{Support.emojis.tick_emoji} to confirm **|** {Support.emojis.x_emoji} to cancel"

        msg = await message.channel.send(embed=embed)


    await msg.add_reaction(Support.emojis.tick_emoji)
    await msg.add_reaction(Support.emojis.x_emoji)


    # get user input

    webhook = await wait_for_tick_x_options(client, message, msg, embed, poss_selection=webhook, selection=guild_webhooks)
    if webhook == "timed out":
        log("watch webhook", "timed out waiting for webhook identificaiton confirmation")
        return

    elif webhook == "cancelled":
        log("watch webhook", "cancelled during webhook identification confirmation") 
        return

    
    # create event

    embed.title=discord.Embed().Empty
    embed.description=f"**Now treating messages from <@{webhook.id}> as user messages.**"
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