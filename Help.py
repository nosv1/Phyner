''' IMPORTS '''

import Embeds
import Logger
import Support



''' CONSTANTS '''

help_aliases = ["help", "h", "?", " ", ""] # these are used for command words' help, not ..p help

# Help Embed Links
simple_help_link = "https://discord.com/channels/789181254120505386/789566872139726938/789566903605002270"
general_help_link = "https://discord.com/channels/789181254120505386/789181637748588544/789187242006020126"
ids_help_link = "https://discord.com/channels/789181254120505386/789523955751976970/789565197312065546"



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

async def send_help_embed(channel, embed_link):
    """
        Help embeds are saved in /Embeds as well as in Phyner Support's HELP EMBEDS category
        The links are saved in the global variables at the top of this channel and sent using the saved versions in /Embeds
    """

    embed = Embeds.load_embed_from_Embeds(link=embed_link)

    phyner = Support.get_phyner_from_channel(channel)
    embed.color = phyner.roles[-1].color if phyner.roles else Support.colors.phyner_grey
    
    await channel.send(embed=embed)

    Logger.log("Help Embed", embed_link)
# end send_help_embed