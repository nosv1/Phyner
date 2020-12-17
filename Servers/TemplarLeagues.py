''' IMPORTS '''

import discord


import Database
from Logger import log
import Support
from Support import simple_bot_response



''' CONSTANTS '''

templar_leagues_id = 437936224402014208
aliases = ["", ]



''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
        @Phyner _command_
    """
    pass

# end main




async def prepare_series_report_channel(channel, user):


    embed = Support.load_embed_from_Embeds(channel.guild.id, 547274914319826944, 789062173318053889)

    msg = await channel.send(content=user.mention, embed=embed)
    await msg.add_reaction(Support.emojis.ok_emoji)

    log("templar leagues", "submit series report")
# end series_report