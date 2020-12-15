''' IMPORTS '''


import Database
import Guilds
from Logger import log



''' CONSTANTS '''

custom_command_aliases = ["command", "cmd"]
create_aliases = ["create", "add", "new"]



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


    def __init__(self, prefix=None, response=None, ref_msg_id=None, creator_id=None, editor_id=None, guild_id=None):
        self.prefix = prefix
        self.response = response
        self.ref_msg_id = ref_msg_id
        self.creator_id = creator_id # creator of command
        self.editor_id = editor_id # last edited by 

        self.guild_id = guild_id
        self.guild = Guilds.get_phyner_guild(guild_id) if guild_id else None
    # end __init__

# end Command


''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
        @Phyner commands
        @Phyner command create <prefix> [response/ref_msg_id] [#channel]
        @Phyner command edit <prefix>
    """

    if args[1] in ["commands", "cmds"]: # display command
        log("custom commands", "view commands")


    if author_perms.administrator:
        if args[2] in create_aliases:
            await create_command(message, args[3:-1])

    else:
        log("custom commands", "not admin")



# end main


def command_from_entry(entry):
    command = Command(
        prefix=entry[0],
        response=entry[1],
        ref_msg_id=int(entry[2]) if entry[2] else None,
        creator_id=int(entry[3]),
        editor_id=int(entry[4]),
        guild_id=int(entry[5])
    )
    return command
# end command_from_entry


def get_guild_comamnds(guild_id):
    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT * FROM CustomCommands
    ;""")
    guild_commands = [command_from_entry(entry) for entry in db.cursor.fetchall()]
    db.connection.close()
    return guild_commands
# end get_guild_comamnds


async def create_command(message, args):
    """
        create command if unique prefix + guild combo
    """

    command = Command(
        prefix=args[0], 
        creator_id=message.author.id,
        editor_id=message.author.id,
        guild_id=message.guild.id if message.guild else message.channel.id # could be dm
    )

    guild_commands = get_guild_comamnds(command.guild_id)

    duplicate = [c for c in guild_commands if c.prefix == command.prefix]
    if duplicate: # switch to edit
        duplicate = duplicate[0]

    else: # contintue create command
        
        if len(args) > 1: # response provided

            response = message.content[message.content.index(args[1]):].strip()

        else:
            # no prefix



# end create_command