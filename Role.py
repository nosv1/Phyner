''' IMPORTS '''

import copy
import discord
import re

import Database
from Logger import log
import Support
from Support import simple_bot_response
import Help



''' CONSTANTS '''

role_aliases = ["role", "roles"]
copy_aliases = ["copy", "duplicate"]



''' FUNCTIONS '''

async def main(client, message, args, author_perms):

    if args[0] in Help.help_aliases:
        log("role", "help")

    elif args[0] in Support.add_aliases + Support.remove_aliases:
        await edit_user_roles(message, args[1:], author_perms, 
            add=args[0] in Support.add_aliases, 
            remove=args[0] in Support.remove_aliases
        )

    elif args[0] in copy_aliases:
        log("role", "copy")
    
# end main


async def edit_user_roles(message, args, author_perms, add=False, remove=False):
    """
        @Phyner role add/remove <role_id/@role> [role_id/@role ...] <user_id/@user/User#0000> [user_id/@user/User#0000 ...] 
    """

    # TODO help, include protips, edit to avoid pings, open chat for all ping ability

    ids = [re.findall(r"[\d]+", a) for a in args]
    ids = [int(i[0]) for i in ids if i]

    names = [re.findall(r"(\S+#\d{4})", a.replace("@", "")) for a in args] # this will fail if 'Mo Bot#0697' it'll capture 'Bot#0697' not the 'Mo'
    names = [n[0].split("#") for n in names if n]
    guild_roles = message.guild.roles
    role_ids = [r.id for r in guild_roles]

    guild_members = message.guild.members
    member_ids = [m.id for m in guild_members]

    roles = []
    members = []

    for id in ids:
        if id in role_ids:
            roles.append(guild_roles[role_ids.index(id)])

        elif id in member_ids:
            members.append(guild_members[member_ids.index(id)])

    duplicate_members = []
    non_matches = []
    for name in names:
        matching_discriminators = [member for member in guild_members if member.discriminator == name[1]]
        
        possible_matches = []
        for member in matching_discriminators:
            if name[0] in member.name:
                possible_matches.append(member)

            else:
                non_matches.append(member)

        if len(possible_matches) == 1:
            members += possible_matches

        else:
            duplicate_members += possible_matches

    embed = await simple_bot_response(message.channel,
        title=f"{'Adding' if add else 'Removing'} Role{'s' if len(roles) > 1 else ''} {'to' if add else 'from'} Member{'s' if len(members) > 1 else ''}",
        description="",
        send=False
    )

    embeds = []


    for member in set(members):
        description = f"{member.mention}:\n"

        for role in set(roles):
            try:

                if add:

                    if role not in member.roles:
                        await member.add_roles(role)
                        description += f"{role.mention} added\n"

                    else:
                        description += f"{role.mention} skipped\n"

                elif remove:

                    if role in member.roles:
                        await member.remove_roles(role)
                        description += f"{role.mention} removed\n"

                    else:
                        description += f"{role.mention} skipped\n"

            except discord.errors.Forbidden:
                description += f"{role.mention} missing permissions\n"
            
        if add or remove:
            description += "\n"

        if len(description) > 500:
            embed.description += description
            embeds.append(copy.copy(embed))

            embed.description = ""
        
    embed.description += description


    for member in duplicate_members + non_matches: # untested...
        description += f"{member.mention} skipped\n"

    await message.channel.send(embed=embed)
# end edit_user_role

async def add_remove_role(member, role, add=False, remove=False):
    """
        role can be either a role_id or a discord.role.Role
    """

    if role != discord.role.Role:
        role = [r for r in member.guild.roles if r.id == role]
        if role:
            role = role[0]

        else:
            log("add_remove_role", f"role does not exist, guild: {member.guild.id}, role id: {role}")
            return False

    try:
        if add:
            await member.add_roles(role)
            log("add_remove_role", f"role added")
            return True

        elif remove:
            await member.remove_roles(role)
            log("add_remove_role", f"role removed")
            return True

    except discord.errors.Forbidden:
        log("add_remove_role", f"forbidden, guild: {member.guild.id}, add: {add} remove: {remove}, role_id: {role.id}")
        return False

# end add_remove_roles