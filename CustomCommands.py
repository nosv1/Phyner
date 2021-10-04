''' IMPORTS '''

import asyncio
from datetime import datetime
import discord
import traceback


import Copy
import Database
import Guilds
import Logger
from Logger import log
import Support
from Support import create_aliases, edit_aliases, delete_aliases
from Support import simple_bot_response



''' CONSTANTS '''

custom_command_aliases = ["command", "cmd"]



''' CLASS '''
class Command:
    """
        Command in CustomCommands Table
        guild_id - varchar(20)
        prefix - varchar(30) # length is same as Guild.prefix
        response - varchar(2000) 
        ref_msg_id - varchar(20)
        creator_id - varchar(20)
        editor_id - varchar(20)

    """


    def __init__(self, prefix=None, response=None, ref_msg_id=None, ref_channel_id=None, creator_id=None, editor_id=None, guild_id=None):
        self.prefix = prefix
        self.old_prefix = prefix
        self.response = response

        self.ref_msg_id = ref_msg_id
        self.ref_channel_id = ref_channel_id
        self.ref_msg = None
        self.ref_channel = None

        self.creator_id = creator_id # creator of command
        self.editor_id = editor_id # last edited by 

        self.guild_id = guild_id
        self.guild = Guilds.get_phyner_guild(guild_id) if guild_id else None
    # end __init__


    async def send_command(self, client, message):
        """
        """

        if self.ref_msg_id: # referencing a message

            try:
                self.ref_channel = client.get_channel(self.ref_channel_id)
                self.ref_msg = await self.ref_channel.fetch_message(self.ref_msg_id)

            except:
                await simple_bot_response(message.channel,
                    content=f"<@{self.editor_id}>",
                    description=f"**There was an error sending this command. Use `@Phyner#2797 command edit {self.prefix}` to check for issues.**"
                )
                return

            await message.channel.send(
                content=self.ref_msg.content, 
                embed=self.ref_msg.embeds[0] if self.ref_msg.embeds else None
            )

        else:
            await message.channel.send(content=self.response)
    # end send_command


    def update_command(self):
        """
        """

        db = Database.connect_database()

        existing = False
        for command in get_guild_comamnds(guild_id=self.guild_id):

            if ( # guild_id + prefix = unique command
                self.guild_id == command.guild_id and 
                self.old_prefix == command.prefix 
            ):
                existing = True

                sql = f"""
                    UPDATE CustomCommands SET
                        `prefix` = '{self.prefix}',
                        `response` = {Support.quote(self.response) if self.response else 'NULL'},
                        `ref_msg_id` = {Support.quote(self.ref_msg_id) if self.ref_msg_id else 'NULL'},
                        `ref_channel_id` = {Support.quote(self.ref_channel_id) if self.ref_channel_id else 'NULL'},
                        `creator_id` = '{self.creator_id}',
                        `editor_id` = '{self.editor_id}'
                    WHERE 
                        `guild_id` = '{self.guild_id}' AND
                        `prefix` = '{self.old_prefix}'

                ;"""
                break

        if not existing:
            sql = f"""
                INSERT INTO CustomCommands (

                    `guild_id`,
                    `prefix`,
                    `response`,
                    `ref_msg_id`,
                    `ref_channel_id`,
                    `creator_id`,
                    `editor_id`

                ) VALUES (

                    '{self.guild_id}',
                    '{self.prefix}',
                    {Support.quote(self.response) if self.response else 'NULL'},
                    {Support.quote(self.ref_msg_id) if self.ref_msg_id else 'NULL'},
                    {Support.quote(self.ref_channel_id) if self.ref_channel_id else 'NULL'},
                    '{self.creator_id}',
                    '{self.editor_id}'

                )
            ;"""

        db.cursor.execute(sql)
        db.connection.commit()
        db.connection.close()
    # end update_table

    def delete(self):
        """
        """

        db = Database.connect_database()
        db.cursor.execute(f"""
            DELETE FROM CustomCommands 
            WHERE
                `guild_id` = '{self.guild_id}' AND
                `prefix` = '{self.prefix}'
        """)
        db.connection.commit()
        db.connection.close()
    # end delete


    def to_string(self):
        return f"prefix: {self.prefix}, response: {str(self.response)[:100]}, ref_msg_id: {self.ref_msg_id}, creator_id: {self.creator_id}, editor_id: {self.editor_id}, guild_id: {self.guild_id}, guild: {self.guild}"
    # end to_stirng

# end Command


''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        @Phyner commands
        @Phyner command create <prefix> <response/ref_msg_id> [#channel]
        @Phyner command edit <prefix>
        @Phyner command delete <prefix>
    """

    if args[1] in ["commands", "cmds"]: # display command
        await Support.previous_action_error(client, message)
        log("custom commands", "view commands") # TODO custom commands error


    if author_perms.administrator:
        if args[0] in create_aliases:
            return await create_command(client, message, args[1:-1])

        elif args[0] in edit_aliases:
            # TODO check for existing command first fam
            await edit_command(client, message, get_guild_comamnds(message.guild.id if message.guild else message.author.id, args[1])[0])

        elif args[0] in delete_aliases:
            # TODO check for existing command first fam
            await delete_command(message, get_guild_comamnds(message.guild.id if message.guild else message.author.id, args[1])[0])
            

    else:
        await Support.previous_action_error(client, message)
        log("custom commands", "not admin") # TODO custom commands error
        



# end main


def command_from_entry(entry):
    command = Command(
        guild_id=int(entry[0]), # no primary key
        prefix=entry[1],
        response=entry[2],
        ref_msg_id=int(entry[3]) if entry[3] else None,
        ref_channel_id=int(entry[4]) if entry[4] else None,
        creator_id=int(entry[5]),
        editor_id=int(entry[6]),
    )
    return command
# end command_from_entry


def get_guild_comamnds(guild_id="", prefix=""):
    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT * FROM CustomCommands
        WHERE 
            guild_id LIKE '%{guild_id}%' AND
            prefix LIKE '%{Database.replace_chars(prefix)}%'
    ;""")
    db.connection.close()
    return [command_from_entry(entry) for entry in db.cursor.fetchall()]
# end get_guild_comamnds

def get_guild_ids():
    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT guild_id FROM CustomCommands
    """)
    db.connection.close()
    return [int(g_id[0]) for g_id in db.cursor.fetchall()]
# end get_guild_ids


async def create_command(client, message, args):
    """
        create command if unique prefix + guild combo
    """


    guild_commands = get_guild_comamnds(guild_id=message.guild.id if message.guild else message.author.id)

    command = [c for c in guild_commands if c.prefix == args[0]]
    duplicate = None
    
    if command: # switch to edit as command exists already
        command = command[0]
        duplicate = command

    else:
        command = Command(
            prefix=args[0], 
            creator_id=message.author.id,
            editor_id=message.author.id,
            guild_id=message.guild.id if message.guild else message.channel.id # could be dm
        )
        command.update_command()
    
        
    if not duplicate:
        if len(args) > 1: # response provided

            command.response = message.content[message.content.index(args[1]):].strip()
            command.update_command()

        '''else: # just prefix
            await Support.previous_action_error(client, message)
            log("custom commands", "no response") # TODO custom commands error'''


    return command, duplicate
# end create_command


async def edit_command(client, message, command):
    """
    """
    await message.channel.trigger_typing()


    msg = None
    mesge = None
    reactions = []
    for c in "abc":
        reactions.append(Support.emojis.letter_emojis[c])

    def reaction_check(reaction, r_user):
        return (
            r_user.id == message.author.id and
            reaction.message.id == msg.id and
            str(reaction.emoji) in [Support.emojis.floppy_disk_emoji] + reactions
        )
    # end reaction_check

    def message_check(mesge):
        return (
            mesge.author.id == message.author.id and
            mesge.channel.id == message.channel.id
        )
    # end message_check

    def message_edit_check(before, after):
        return mesge and after.id == mesge.id
    # end message_edit_check


    async def build_embed():
        embed = await simple_bot_response(message.channel,
            title="**Command Editing**",
            description="",
            send=False
        )


        if command.ref_msg_id:
            try:
                command.ref_channel = [c for c in message.guild.channels if c.id == command.ref_channel_id][0]
                command.ref_msg = await command.ref_channel.fetch_message(command.ref_msg_id)

            except discord.errors.NotFound:
                await delete_command(message, command)
                await simple_bot_response(message.channel,
                    description=f"**The reference message no longer exists. The command was deleted.**"
                )
                log("edit command", "msg does not exist") # edit command error
                return
                
            except IndexError:
                await delete_command(message, command)
                await simple_bot_response(message.channel,
                    description=f"**The reference message channel no longer exists. The command was deleted.**"
                )
                return


        embed.description += f"{reactions[0]} **Prefix:** {command.prefix}\n"
        embed.description += f"{reactions[1]} **Response:** {command.response[:10] if command.response else ''}{'...' if command.response and len(command.response) > 10 else ''}\n"
        embed.description += f"{reactions[2]} **Referencing Message:** {f'[message]({command.ref_msg.jump_url})' if command.ref_msg_id else 'N/A'}\n\n"

        embed.description += f"**Created by:** <@{command.creator_id}>\n"
        embed.description += f"**Last Edited by:** <@{command.editor_id}>\n"

        return embed
    # end build_embed


    # build starter embed from existing command
    embed = await build_embed()

    if not embed: # embed could be empty if there were errors
        return

    msg = await message.channel.send(embed=embed)

    await msg.add_reaction(Support.emojis.floppy_disk_emoji)
    [await msg.add_reaction(r) for r in reactions]


    reaction = None
    r_user = None

    timeout = False # used for timeout warning
    warn = True # warn user about time out only if stuff has changed
    while True:
        
        done, pending = await asyncio.wait([
            client.wait_for('reaction_add', check=reaction_check),
            client.wait_for('message', check=message_check),
            client.wait_for('message_edit', check=message_edit_check),
            ],
            timeout=480 if not timeout else 120,
            return_when=asyncio.FIRST_COMPLETED
        )


        if done: # something finished
            timeout = False

            for task in done:
                result = task.result()
                
                if type(result) == discord.message.Message: # new message sent
                    mesge = result

                elif type(result[1]) == discord.message.Message: # message edited
                    mesge = result[1] # the 'after' message after a message is edited

                elif type(result[0]) == discord.reaction.Reaction: # reaction added
                    reaction, r_user = result

            footer = ""
            if reaction: # reaction clicked
                warn = True # sure
                await msg.add_reaction(Support.emojis._9b9c9f_emoji)

                if str(reaction.emoji) == Support.emojis.floppy_disk_emoji: # save command
                    timeout = True
                    command.update_command()
                    embed = await build_embed()
                    footer = f"{Support.emojis.floppy_disk_emoji} Save | Saved {datetime.utcnow().strftime('%H:%M UTC')}"


                elif reactions.index(str(reaction.emoji)) == 2: # referencing message
                    # check from og msg first, then get for mesge
                    args = ""
                    if message.channel_mentions:
                        args, c = Support.get_args_from_content(message.content)
                        args = args[4:]

                    elif mesge and mesge.channel_mentions:
                        args, c = Support.get_args_from_content(mesge.content)

                    if len(args) == 3: # ref_msg_id, #ref_channel, ''

                        try:
                            command.ref_msg_id = Support.get_id_from_str(args[0])[0]
                            command.ref_channel_id = Support.get_id_from_str(args[1])[0]
                            command.ref_channel = [c for c in message.guild.channels if c.id == command.ref_channel_id][0]

                            command.ref_msg = await command.ref_channel.fetch_message(command.ref_msg_id)
                            command.response = None


                        except discord.errors.NotFound:
                            await Support.previous_action_error(client, message)
                            log("edit command", "msg does not exist")

                        except IndexError:
                            await Support.previous_action_error(client, message)
                            log("edit command", "msg does not exist")


                elif str(reaction.emoji) in reactions and mesge: # letter emoji clicked and mesge sent

                    if reactions.index(str(reaction.emoji)) == 0: # prefix
                        command.prefix = mesge.content


                    if reactions.index(str(reaction.emoji)) == 1: # response
                        command.response = mesge.content
                        command.ref_msg_id = None
                        command.ref_msg = None
                        command.ref_channel_id = None
                        command.ref_channel = None

                    command.editor_id = mesge.author.id


                embed = await build_embed()
                if footer:
                    embed.set_footer(text=footer)

                await msg.edit(embed=embed)


                await Support.remove_reactions(msg, msg.author, Support.emojis._9b9c9f_emoji)
                await Support.remove_reactions(msg, r_user, str(reaction.emoji))
                reaction = None


            for future in pending:
                future.cancel()
                    

        elif timeout:
            embed.title += "\nTimed Out"
            await msg.edit(embed=embed)
            await Support.clear_reactions(msg)
            break

        elif warn:
            timeout = True
            await simple_bot_response(message.channel,
                description="**Command Editing times out in 2 minutes. Remember to save your changes.**",
                reply_message=message,
                delete_after=120
            )
# end edit_command


async def delete_command(message, command):
    """
    """

    command.delete()
    await simple_bot_response(message.channel,
        description=f"**`{command.prefix}` command deleted.**"
    )

# end delete_command