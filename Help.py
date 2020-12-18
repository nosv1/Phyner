''' IMPORTS '''

import Support
import Logger



''' CONSTANTS '''

help_aliases = ["help", "h", "?", " ", ""]



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

async def help(message):
    """
        Help Message
    """

    embed = Support.load_embed_from_Embeds(link="https://discord.com/channels/789181254120505386/789181637748588544/789187242006020126")
    await message.channel.send(embed=embed)

    Logger.log("Bot reponse", "Help Message")
# end help

async def simple_help(message):
    """
        simple help message
    """

    phyner = Support.get_phyner_from_channel(message.channel)
    
    description = f"`@{phyner} help` - general help\n"
    description += f"`@{phyner} <command> help` - specific help\n"
    description += f"`@{phyner} ? <search_words>` - search help\n"

    await Support.simple_bot_response(message.channel, 
        title="No Comamnd Recognized",
        description=description,
        reply_message=message
    )
    
    Logger.log("Bot reponse", "Simple Help Message")
# end simple_help