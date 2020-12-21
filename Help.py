''' IMPORTS '''

import asyncio
from os import supports_bytes_environ
from types import SimpleNamespace


import Embeds
import Guilds
import Logger
import Support



''' CONSTANTS '''

help_aliases = ["help", "h", "?", " ", ""] # these are used for command words' help, not ..p help

# Help Embed Links
help_links = SimpleNamespace(**{
    "simple" : {"link" : "https://discord.com/channels/789181254120505386/789566872139726938/789566903605002270"},

    "general" : {"link" : "https://discord.com/channels/789181254120505386/789181637748588544/789187242006020126"},

    "command_list_1" : {"link" : "https://discord.com/channels/789181254120505386/789586399975178252/789586453978021898"},

    "ids" : {
        "link" : "https://discord.com/channels/789181254120505386/789523955751976970/789565197312065546",

        "demo" : "https://cdn.discordapp.com/attachments/789218327473160243/790481979794653215/ids.gif"
        },
})


''' FUNCTIONS '''

async def search(message, args): # TODO copy paste embed contents to the wiki, instead of rewriting everything
    """
        Sending a git hub search result
        https://github.com/nosv1/Phyner/search?q=&type=wikis
    """

    phyner = Support.get_phyner_from_channel(message.channel)
    

    query = " ".join(args[2:]).strip()
    results = None

    if query:
        results = Support.search_github(query)

        results_description = ""
        outputted = 0
        for result in results:
            if len(results_description) < 1000:
                outputted += 1

                results_description += f"**[{result['title']}]({result['link']})**\n"
                p = result['p'].split("\n") + [" "] # [@phyner command help, snippet]
                results_description += f"`{p[0].strip().replace('**', '')}`\n{p[1].strip()}\n\n"


        if not results_description: # no results
            results_description += f"{phyner} help\n"


        await Support.simple_bot_response(message.channel,
            title = f"{len(results)} Result{'s' if outputted != 1 else ''}",
            description=results_description
        )

        Logger.log("search", results_description)


    else:
        description = f"`@{phyner} ? <search_words>`\n"
        description += f"`@{phyner} ? custom embeds`"
        await Support.simple_bot_response(message.channel,
            title="No Search Words Provided",
            description=description,
            reply_message=message
        )

        Logger.log("Bot Reponse", "Simple Help Search")
# end search


''' HELP EMBEDS '''

async def send_help_embed(client, msg, embed_link, demo=False):
    """
        Help embeds are saved in /Embeds as well as in Phyner Support's HELP EMBEDS category
        The links are saved in the global variables at the top of this channel and sent using the saved versions in /Embeds
    """

    guild_prefix = Guilds.get_guild_prefix(msg.guild.id if msg.guild else msg.author.id)
    reactions = []
    message_author = None
    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and
            r_user.id == message_author.id and
            str(reaction.emoji) in reactions
        )
    # end reaction_check

    while True: # every iteration the thing that changes is the embed_link

        # get embed, message and channel
        channel = msg.channel
        embed, message, msg = Support.messageOrMsg(msg)
        message_author = message.author if message else message_author

        embed = Embeds.get_saved_embeds(link=embed_link["link"])[0].embed
        if demo:
            embed.set_image(url=embed_link["demo"])


        # add a footer if needed
        footer = []
        reactions = []
        if embed_link not in [help_links.general]: # not general help embed
            footer.append(f"{Support.emojis.question_emoji} `{guild_prefix} help`")
            reactions.append(Support.emojis.question_emoji)

        if embed_link not in [help_links.command_list_1]: # not command list embed
            footer.append(f"{Support.emojis.clipboard_emoji} `{guild_prefix} commands`")
            reactions.append(Support.emojis.clipboard_emoji)

        if "demo" in embed_link: # has demo
            footer.append(f"{Support.emojis.film_frames_emoji} `Demo`")
            reactions.append(Support.emojis.film_frames_emoji)

        if footer:
            embed.add_field(name=Support.emojis.space_char, value=" **|** ".join(footer))

            if msg:
                await Support.clear_reactions(msg)


        # send embed
        phyner = Support.get_phyner_from_channel(channel)
        embed.color = phyner.roles[-1].color if phyner.roles else Support.colors.phyner_grey
        
        if msg:
            await msg.edit(embed=embed)

        else:
           msg = await channel.send(embed=embed)


        # add rections
        for reaction in reactions:
            await msg.add_reaction(reaction)

        Logger.log("Help Embed", embed_link)


        # wait
        if footer:
            try:
                reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)

                if str(reaction.emoji) == Support.emojis.question_emoji:
                    embed_link = help_links.general

                elif str(reaction.emoji) == Support.emojis.clipboard_emoji:
                    embed_link = help_links.command_list_1

                elif str(reaction.emoji) == Support.emojis.film_frames_emoji:
                    demo = not demo

            except asyncio.TimeoutError:
                await Support.clear_reactions(msg)
                embed = Support.delete_last_field(embed)
                await msg.edit(embed=embed)
                break

# end send_help_embed