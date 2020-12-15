''' IMPORTS '''

import discord


import Database
from Logger import log
import Support
from Support import simple_bot_response



''' CONSTANTS '''

events_aliases = ["watch", "detect", "handle"]



''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
        @Phyner watch webhook [webhook_id]
    """

    if author_perms.adminstraator:

        if args[0] == "webhook":
            await watch_webhook(message, args)

    else:
        log("Events", "missig perms")
# end main


async def watch_webhook(message, args):
    """
        Figure out what the user wants to watch for upon webhook message
    """

    webhook_id = args[-1]
    webhook = None
    guild_webhooks = message.guild.webhooks
    for wh in guild_webhooks:
        if str(wh.id) in webhook_id:
            webhook = wh

    embed = await simple_bot_response(message.channel,
        title="Confirm Webhook Identification",
        send=False
    )

    embed.description = f"A webhook with the given id/url `{webhook_id}` was not found. Choose from the list below the webhook you would like to watch."



# end watch_webhook