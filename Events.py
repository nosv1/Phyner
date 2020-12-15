''' IMPORTS '''

import discord
import asyncio
import mysql.connector


import Database
from Logger import log
import Support
from Support import simple_bot_response
import Help



''' CONSTANTS '''

events_aliases = ["watch", "detect", "handle"]
watch_webhook_help = "'@Phyner#2797 watch webhook ?' for help"


''' CLASSES '''

class Webhook:
    """
        Webhook in Webhooks Table
        id - varchar(20), primary key
        guild_id - varchar(20)
    """
    def __init__(self, webhook_id=None, guild_id=None):
        self.id = webhook_id
        self.guild_id = guild_id
    # end __init__


    def edit_webhook(self):
        db = Database.connect_database()

        try:
            db.cursor.execute(f"""
                INSERT INTO Webhooks (
                    `id`, `guild_id`
                ) VALUES (
                    '{self.id}', '{self.guild_id}'
                )
            ;""")

        except mysql.connector.errors.IntegrityError:
            db.cursor.execute(f"""
                UPDATE Webhooks SET 
                    `guild_id` = '{self.guild_id}'
                WHERE 
                    id = '{self.id}'
            ;""")

        db.connection.commit()
        db.connection.close()
    # end edit_webhook

# end Webhook



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        @Phyner watch webhook [webhook_id]
    """

    if author_perms.administrator:

        if args[0] in Help.help_aliases:
            log("Events", "help")

        if args[0] == "webhook":

            return await watch_webhook(client, message, args)

    else:
        log("Events", "missig perms")
# end main


## WEBHOOKS ##

def get_webhook_from_entry(entry):
    """
        Returns Webhook
    """
    return Webhook(
        webhook_id=entry[0],
        guild_id=entry[1]
    )
# end get_webhook_from_entry


def get_phyner_webhooks():
    """
        Returns Webhooks
    """

    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT * FROM Webhooks
    ;""")
    db.connection.close()
    return [get_webhook_from_entry(entry) for entry in db.cursor.fetchall()]
# end get_phyner_webhooks

def get_webhook_ids():
    """
        Returns [int(id), ...]
    """

    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT id FROM Webhooks
    ;""")
    db.connection.close()
    return [int(wh_id[0]) for wh_id in db.cursor.fetchall()]
# end get_webhooks


async def watch_webhook(client, message, args):
    """
        Figure out what the user wants to watch for upon webhook message
    """

    phyner = Support.get_phyner_from_channel(message.channel)

    webhook_id = args[1]
    webhook = None

    guild_webhooks = [wh for wh in await message.guild.webhooks() if wh.type == discord.WebhookType.incoming] if message.guild else []
    for wh in guild_webhooks:
        if str(wh.id) in webhook_id: ## url may be given, not just webhook id
            webhook = wh

    embed = await simple_bot_response(message.channel,
        title="Confirm Webhook Identification",
        send=False
    )

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


    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in [Support.emojis.tick_emoji, Support.emojis.x_emoji]
        )
    # end reaction_check

    confirmed_webhook = None
    try:

        while not confirmed_webhook:
            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=60)

            if str(reaction.emoji) == Support.emojis.tick_emoji:
                if webhook: # existing webhook is confirmed
                    confirmed_webhook = webhook
                
                else:
                    msg = await msg.channel.fetch_message(msg.id)
                    for reaction in msg.reactions:
                        if str(reaction.emoji) in number_emojis_used:
                            async for user in reaction.users():
                                if user.id == message.author.id:
                                    confirmed_webhook = guild_webhooks[number_emojis_used.index(str(reaction.emoji))]
                                    break

                    if not confirmed_webhook: # user did not click a number emoji before the tick
                        lines = embed.description.split("\n")
                        lines[-2] = f"**{Support.emojis.exclamation_emoji} {lines[-2]}**"
                        embed.description = "\n".join(lines)
                        await msg.edit(embed=embed)

            else:
                await Support.clear_reactions(msg)
                embed.title += "\nCancelled"
                embed.description = "\n".join(embed.description.split("\n")[:-1 if webhook else -2])
                await msg.edit(embed=embed)
                log("watch webhook", "cancelled webhook identification confirmation")
                return

        # end while
        
    except asyncio.TimeoutError:
        await Support.clear_reactions(msg)
            
        embed.title += "\nTimed Out"
        embed.description = "\n".join(embed.description.split("\n")[:-1 if webhook else -2])
        await msg.edit(embed=embed)
        log("watch webhook", "timed out waiting for webhook identificaiton confirmation")
        return

    webhook = confirmed_webhook
    del confirmed_webhook

    embed.title=discord.Embed().Empty
    embed.description=f"**Now treating messages from <@{webhook.id}> as user messages.**"
    await Support.clear_reactions(msg)
    await msg.edit(embed=embed)

    phyner_webhook = Webhook(webhook_id=webhook.id, guild_id=message.guild.id)
    phyner_webhook.edit_webhook()
    return (phyner_webhook, get_webhook_ids())
# end watch_webhook