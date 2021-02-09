''' IMPORTS '''

import asyncio
import copy
import discord
import re


import Database
import Embeds
from Embeds import get_saved_embeds
import Guilds
from Logger import log
import Help
import Role
from Servers import TemplarLeagues
from Servers import COTM
import Support
from Support import simple_bot_response
from Support import quote



''' CONSTANTS '''

events_aliases = ["watch", "detect", "handle", "event"]
watching_aliases = ["watching", "events"]
watch_webhook_help = "'@Phyner#2797 watch webhook ?' for help"


''' CLASSES '''

## the below classes represent Event objects... Event.condition, Event.action, Event.object ##

class Condition:
    """
        "message"
    """
    def __init__(self, condition=None, condition_id=None):
        self.condition = condition
        self.id = condition_id
# end Condition

class Action:
    """
        action extra is like a channel name or something, like for create_private_text_channel
    """
    def __init__(self, action=None, action_id=None, extra=None):
        self.action = action
        self.id = action_id
        self.extra = extra
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
                sql += "`action_id` = %s, " % (quote(self.action.id) if self.action else 'NULL ')
                sql += "`action_extra` = %s " % (quote(self.action.extra) if self.action else 'NULL ')
                sql += " WHERE "
                sql += f"guild_id = '{self.guild_id}' AND "
                sql += f"object_id = '{self.object.id}' AND "
                sql += f"condition_id = '{self.condition.id}' AND "
                sql += f"action_id = '{self.action.id}'"
                sql += ";"
                existing_event = True
                break

        if not existing_event:
            sql = "INSERT INTO Events ("
            sql += "`guild_id`, `object`, `object_id`, `condition`, `condition_id`, `event`, `action`, `action_id`, `action_extra`"
            sql += " ) VALUES ( "
            sql += f"'{self.guild_id}', '{self.object.type}', '{self.object.id}', "
            sql += f"{quote(self.condition.condition) if self.condition.id else 'NULL'}, "
            sql += f"{quote(self.condition.id) if self.condition.id else 'NULL'}, "
            sql += f"'{self.event}', "
            sql += f"{quote(self.action.action) if self.action.id else 'NULL'}, "
            sql += f"{quote(self.action.id) if self.action.id else 'NULL'}, "
            sql += f"{quote(self.action.extra) if self.action.extra else 'NULL'}"
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
        s += f"Action: {self.action.action} {self.action.id} {self.action.extra}" if self.action else ""
        return s
    # end to_string
# end Event



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        @Phyner watch webhook [webhook_id]
        @Phyner watch emoji <emoji> <message_id> [#channel] add/remove_role <role_id/@Role ...>
        @Phyner watch emoji <emoji> <message_id> [#channel] create_private_text_channel <channel/category_id/#channel> [name template]
    """

    if author_perms.administrator:

        if args[1] in Help.help_aliases:
            await send_event_help(client, message)


        elif args[0] in events_aliases and not message.edited_at:

            try:

                if args[1] == "webhook":
                    return await watch_webhook(client, message, args[2:])

                elif args[1] == "emoji":
                    return await watch_emoji(client, message)

            except:
                await Support.previous_action_error(client, message)


        elif args[0] in watching_aliases:
            log('events', 'display events') # TODO display events

    else:
        await Support.previous_action_error(client, message)
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
        action_id=(int(entry[7]) if entry[7] else None),
        extra=(entry[8] if entry[8] else None)
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
    """
        returns all events
    """

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
        Returns [Event, ...] based on event given
    """
    return [e for e in events if e.event == event]
# end get_object_ids


async def wait_for_tick_x_options(client, message, msg, embed, poss_selection=None, selection=[]):
    """
        selection should line up number emojis
    """

    number_emojis_used = Support.emojis.number_emojis[1:len(selection)+1]

    def reaction_check_1(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in [Support.emojis.tick_emoji, Support.emojis.x_emoji]
        )
    # end reaction_check_1

    def reaction_check_2(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in number_emojis_used
        )
    # end reaction_check_2


    # get user input
    selected = None
    poss_selcted = None

    while not selected:

        done, pending = await asyncio.wait([
            client.wait_for('reaction_add', check=reaction_check_1), # tick or x
            client.wait_for('reaction_add', check=reaction_check_2), # number emoji
            ],
            timeout=120,
            return_when=asyncio.FIRST_COMPLETED # still going to check if number emoji was clicked
        )


        if done: # something finished

            for task in done:
                reaction, user = task.result()

                if str(reaction.emoji) == Support.emojis.x_emoji: # cancel 
                    embed.title += "\nCancelled"
                    embed = Support.delete_last_field(embed)

                    await Support.clear_reactions(msg)
                    await msg.edit(embed=embed)

                    for future in pending:
                        future.cancel()

                    return "cancelled"


                if str(reaction.emoji) in number_emojis_used: # number emoji clicked first, poss selected
                    poss_selcted = selection[number_emojis_used.index(str(reaction.emoji))]

                
                if str(reaction.emoji) == Support.emojis.tick_emoji: # tryna confirm

                    if poss_selcted: # can confirm
                        selected = poss_selcted
                        break

                    else: # has not clicked a number emoji yet
                        field_footer = embed.to_dict()["fields"][-1]["value"]
                        embed = Support.revert_confirm_input_last_field_exclamation(field_footer, embed)

                        await Support.remove_reactions(msg, message.author, msg.reactions)
                        await msg.edit(embed=embed)


        else: # nothing finished, so timed out

            embed.title += "\nTimed Out"
            embed = Support.delete_last_field(embed)
            
            await Support.clear_reactions(msg)
            await msg.edit(embed=embed)

            for future in pending:
                future.cancel()

            return "timed out"

    # end while

    return selected
# end wait_for_tick_x



## EMOJIS ##

async def watch_emoji(client, message):

    def message_edit_check(before, after):
        return after.id == message.id
    # end message_edit_check


    args, content = Support.get_args_from_content(message.content)

    phyner = Support.get_phyner_from_channel(message.channel)
    guild_prefix = Guilds.get_guild_prefix(message.guild.id)

    actions = [
        "add_role", 
        "remove_role",
        "create_private_text_channel" # stuff regarding channels go at the bottom, using this logic to check channel mentions
    ]


    # syntax examples
    basic_syntax = f"`{guild_prefix} watch emoji <emoji> <message_id> [#channel] <action> <action_id/mention ...> [action_extra]`"

    examples = {
        "add_role" : f"`{guild_prefix} watch emoji emoji_event_object_id 791701974809968640 #role-selection add_role @role1 @role2`",

        "remove_role" : f"`{guild_prefix} watch emoji emoji_event_object_id 791701974809968640 #role-selection add_role @role1 @role2`",
        
        "create_private_text_channel" : f"`{guild_prefix} watch emoji emoji_event_object_id 791701974809968640 #open-channels create_private_text_channel 789182513633427507 .user`",
    }


    missing_arg_embed = await simple_bot_response(message.channel,
        title="**Missing Argument**",
        description="",
        footer=f"{guild_prefix} watch help",
        send=False
    )


    # get emoji
    emoji_event = Event(
        guild_id=message.guild.id, 
        obj=Emoji(emoji_id=args[3]),
        event="reaction_add",
        condition=Condition(condition="message"),
        action=Action()
    )


    # get action
    msg = None
    while not emoji_event.action.action: # while no given action

        args, content = Support.get_args_from_content(message.content)
        action = [a for a in actions if a in args]
    
        if action: # action exists in message
            emoji_event.action.action = action[0]

        else: # wait for edit

            missing_arg_embed.description = f"Your command message is missing an action. Add an action to your message from the list below.\n\n"

            missing_arg_embed.description += "**Available Actions:**\n"
            missing_arg_embed.description += "`add_role`\n"
            missing_arg_embed.description += "`remove_role`\n"
            missing_arg_embed.description += "`create_private_text_channel`\n\n"

            missing_arg_embed.description += "**Syntax:**\n"
            missing_arg_embed.description += f"{basic_syntax.replace('<action>', '<ACTION>')}\n\n"

            missing_arg_embed.description += f"{examples['add_role'].replace('emoji_event_object_id', emoji_event.object.id)}\n\n"

            missing_arg_embed.description += f"**Edit your [message above]({message.jump_url}) to continue.**"


            # prompt user
            if msg:
                await msg.edit(embed=missing_arg_embed)

            else:
                msg = await message.reply(embed=missing_arg_embed)
            await message.add_reaction(Support.emojis.x_emoji)


            # wait
            try:
                before, after = await client.wait_for("message_edit", check=message_edit_check, timeout=300)
                await Support.remove_reactions(message, client.user, [Support.emojis.x_emoji])
                message = after

            except asyncio.TimeoutError:
                missing_arg_embed.title += "\nTimed Out"
                await msg.edit(embed=missing_arg_embed)
                return

    # end while


    # get action souces
    action_sources = []
    while not action_sources:

        args, content = Support.get_args_from_content(message.content)
        action_ids = [Support.get_id_from_str(a) for a in args[args.index(emoji_event.action.action)+1:]]
        action_ids = [a_id[0] for a_id in action_ids if a_id] # the above returns [[id, ...], ...] need to convert that to [id, ...]


        missing_arg_embed.description = ""
        action_source_str = "If you want to add/remove roles, the action_ids/mentions should be role IDs or @role mentions; if you want to create a private channel, the action ID/mention should be a category/channel ID or a channel mention, etc."


        if action_ids: # action_ids given

            if emoji_event.action.action in actions[:2]: # is add_role or remove_role
                guild_roles = message.guild.roles
                action_sources = [r for r in guild_roles if r.id in action_ids]

            elif emoji_event.action.action == actions[2]: # is create_private_text_channel
                guild_categories = message.guild.categories
                guild_channels = message.guild.channels

                action_sources = [cat for cat in guild_categories if cat.id == action_ids[0]] # get category if exists

                if not action_sources:
                    action_sources = [ch for ch in guild_channels if ch.id == action_ids[0]] # get channel if exists


            if not action_sources: # no action sources from the given ids

                missing_arg_embed.description += f"None of the given action IDs/mentions match the action type. {action_source_str}\n\n"

                missing_arg_embed.description += "**Syntax:**\n"
                missing_arg_embed.description += f"{basic_syntax}\n\n"


        else: # no action ids given

            missing_arg_embed.description += f"There were no action IDs/mentions found in your message. {action_source_str}\n\n"

            missing_arg_embed.description += "**Syntax:**\n"
            missing_arg_embed.description += f"{basic_syntax.replace('<action_id/mention ...>', '<ACTION_ID/MENTION ...>')}\n\n"


        if not action_sources: # no action sources

            missing_arg_embed.description += f"{examples[emoji_event.action.action].replace('emoji_event_object_id', emoji_event.object.id)}\n\n"

            missing_arg_embed.description += f"**Edit your [message above]({message.jump_url}) to continue.**"


            # prompt user
            if msg:
                await msg.edit(embed=missing_arg_embed)

            else:
                msg = await message.reply(embed=missing_arg_embed)
            await message.add_reaction(Support.emojis.x_emoji)

            # wait
            try:
                before, after = await client.wait_for("message_edit", check=message_edit_check, timeout=300)
                await Support.remove_reactions(message, client.user, [Support.emojis.x_emoji])
                message = after

            except asyncio.TimeoutError:
                missing_arg_embed.title += "\nTimed Out"
                await msg.edit(embed=missing_arg_embed)
                return

    # end while


    # get message
    mesge = None
    while not mesge:

        args, content = Support.get_args_from_content(message.content)

        mesge_id = Support.get_id_from_str(args[4])
        mesge_id = int(mesge_id[0]) if mesge_id else None


        if emoji_event.action.action in actions[:2]: # not a channel related action
            channel = message.channel_mentions[0] if message.channel_mentions else message.channel
        
        else:
            if "#" in args[5]:
                channel = message.channel_mentions[0] if message.channel_mentions else message.channel # i agree if there is # in arg surely it's a channel mention, just gotta make sure

            else: # message should be in current channel
                channel = message.channel


        missing_arg_embed.description = ""
        if mesge_id: # msg id given
            try:
                mesge = await channel.fetch_message(mesge_id) # mesge got got
                emoji_event.condition.id = mesge.id

            except discord.errors.NotFound:

                missing_arg_embed.description += f"The given message ID is not in this channel. Double check your message ID, and if the message is not in this channel, add the channel mention right after the message ID.\n\n"

                missing_arg_embed.description += "**Syntax:**\n"
                missing_arg_embed.description += f"{basic_syntax.replace('[#channel]', '[#CHANNEL]')}\n\n"

        else: # msg id not given

            missing_arg_embed.description += f"Your command message is missing a message ID. This is the message {phyner.mention} watches to know when a {emoji_event.object.id} is added or removed.\n\n"

            missing_arg_embed.description += "**Syntax:**\n"
            missing_arg_embed.description += f"{basic_syntax.replace('<message_id>', '<MESSAGE_ID>')}\n\n"


        if not mesge: # still no message

            missing_arg_embed.description += f"{examples[emoji_event.action.action].replace('emoji_event_object_id', emoji_event.object.id)}\n\n"

            missing_arg_embed.description += f"**Edit your [message above]({message.jump_url}) to continue.**"


            # prompt user
            if msg:
                await msg.edit(embed=missing_arg_embed)

            else:
                msg = await message.reply(embed=missing_arg_embed)
            await message.add_reaction(Support.emojis.x_emoji)


            # wait
            try:
                before, after = await client.wait_for("message_edit", check=message_edit_check, timeout=300)
                await Support.remove_reactions(message, client.user, [Support.emojis.x_emoji])
                message = after

            except asyncio.TimeoutError:
                missing_arg_embed.title += "\nTimed Out"
                await msg.edit(embed=missing_arg_embed)
                return

    # end while


    # get aciton_extra
    last_non_action_extra_arg = [i for i, a in enumerate(args) if str(action_sources[-1].id) in a][-1]
    action_extra = " ".join(args[last_non_action_extra_arg+1:]).strip()

    if action_extra: # action_extra given
        emoji_event.action.extra = action_extra


    # all done
    await mesge.add_reaction(emoji_event.object.id)

    emoji_events = []
    for action_source in action_sources:
        e_e = copy.deepcopy(emoji_event) # copy

        e_e.action.id = action_source.id # udpate id
        emoji_events.append(e_e) # append

        e_e.edit_event(get_events()) # update db

        log("watch emoji", e_e.to_string())


    embed = await simple_bot_response(message.channel, # TODO better all done message
        title="Event Created",
        description='wip\n' + "\n\n".join([e_e.to_string() for e_e in emoji_events]),
        send=False
    )

    if msg:
        try:
            await msg.edit(embed=embed)
        except discord.errors.NotFound:
            pass
    else:
        await message.channel.send(embed=embed)


    return emoji_events
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

    remove_reaction = False
    if event.action.action == "create_private_text_channel":
        channel = await create_private_text_channel(client, message, user, event)

        if channel:
            remove_reaction = True

            if event.guild_id == TemplarLeagues.templar_leagues_id:
                if event.condition.id == TemplarLeagues.series_report_message_id:
                    if event.object.id == Support.emojis.tick_emoji:
                        await TemplarLeagues.prepare_series_report_channel(channel, user)
                        remove_reaction = True

            elif event.guild_id == COTM.cotm_id:
                if event.condition.id == COTM.vote_msg_id:
                    if event.object.id == Support.emojis.tick_emoji:
                        await COTM.prepare_vote_channel(channel, message.embeds[0])
                        remove_reaction = True


    elif event.action.action in ["add_role", "remove_role"]:
        add = event.action.action == "add_role"
        remove = event.action.action == "remove_role"
        success = await Role.add_remove_role(user, event.action.id, add=add, remove=remove)

        if event.event == "reaction_add": 
            if success:
                try:
                    embed = await simple_bot_response(message.channel,
                        description=f"The role `{success}` was {'added to' if add else 'removed from'} you in `{message.guild.name}`.",
                        send=False
                    )
                    await user.send(embed=embed)
                except discord.errors.Forbidden:
                    pass

            else: # hopefully it simply just works and no issues
                remove_reaction = True



    return remove_reaction
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

    name = event.action.extra if event.action.extra else f"{user.display_name}-{user.discriminator}"
    name = re.sub(r"(.category|.channel)", source.name, name)
    name = name.replace(".user", f"{user.display_name}-{user.discriminator}")

    a, c = Support.get_args_from_content(name)
    name = "-".join(a).lower() # .lower last of replacements

    exists = [c for c in message.guild.channels if re.sub(r"(.max\(\S+\)[-\s]*)|(-$)", "", name) in c.name]

    max_count = 1
    if re.findall(r"(.max\(\S+\))", name): # get max number of channels allowed to create
        max_count = name.split(".max")[1].split("(")[1].split(")")[0]
        max_count = int(max_count) if max_count.isnumeric() else 1


    if not exists or len(exists) < max_count: # doesn't exist or can create more
        name = re.sub(r'(.max\(\S+\)[-\s]*)|(-$)', '', name) # regex same as above in exists = [...
        
        channel = await message.guild.create_text_channel(
            name=f"{name}-{len(exists) + 1 if max_count > 1 else ''}", 
            overwrites=overwrites,
            category=source.category if type(source) == discord.channel.TextChannel else source,
            position=source.category.channels[-1].position + 1 if type(source) == discord.channel.TextChannel else source.channels[-1].position  + 1,
        )
        
        await channel.send(user.mention)

        log("reaction_add event", f"private text channel created {event.to_string()}")
        return channel

    else:
        log('reaction add event', "failed to create channel, name already exists ;)")
# end create_private_text_channel


''' RESPONSES '''

async def send_event_help(client, message):

    watching_emoji_actions = [
        Help.help_links.add_remove_role["link"], # add/remove_role
        Help.help_links.create_private_text_channel["link"], # create_private_text_channel
    ]


    msg = await Help.send_help_embed(client, message, Help.help_links.event_menu, default_footer=False)
    log("Event", "Help")

    embed = msg.embeds[0]
    
    emojis = [Support.emojis.zany_emoji, Support.emojis.robot_emoji] 
    for r in emojis[:1]: # FIXME not all reactions are beeing added... ^^
        await msg.add_reaction(r)

    reactions = [] # some events have sub pages, those reactions are stored here

    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and
            r_user.id == message.author.id and
            str(reaction.emoji) in emojis + reactions
        )
    # end reaction_check

    try:

        event_type = ""
        while True:

            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

            
            # 2nd level
            if event_type == "watching_emoji" and str(reaction.emoji) in reactions: # action emoji clicked,
                embed = get_saved_embeds(link=watching_emoji_actions[Support.emojis.number_emojis.index(str(reaction.emoji))-1])[0].embed
                reactions = []


            # 1st level
            if str(reaction.emoji) == emojis[0]: # zany
                embed = get_saved_embeds(link=Help.help_links.watching_emojis["link"])[0].embed
                event_type = "watching_emoji"
                reactions = Support.emojis.number_emojis[1:3]

            elif str(reaction.emoji) == emojis[1]: # robot
                embed = get_saved_embeds(link=Help.help_links.watching_webhooks["link"])[0].embed
                event_type = "watching_webhook"
                reactions = []


            await Support.clear_reactions(msg)

            # send it
            if embed:
                await msg.edit(embed=embed)
                [await msg.add_reaction(r) for r in reactions]
                embed = None

            else:
                break

    except asyncio.TimeoutError:
        await Support.clear_reactions(msg)

# end send_embed_help