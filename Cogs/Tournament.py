import asyncio
import datetime
import sys
import time
import random

import discord
from discord.ext import commands, tasks

import Config
import Utils
import Battle_Utils


async def event_start(ctx):
    if Config.EVENT_ACTIVE == "tourneyS":
        return True
    else:
        embed = discord.Embed(color=Config.EVENTCOLOR, title="Event hasn't started yet",
                              description=f"You can't play before the tournament starts!")
        await ctx.send(content=ctx.author.mention, embed=embed)
        return False


class Tournament(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_image = "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/twitter/281/" \
                           "tulip_1f337.png"
        self.bot = bot
        self.battles = 0
        self.battling_users = []
        self.friendly_matchmaking = []
        self.chats = []
        self.tickets = []
        self.ticket_garbage.start()
        if Config.testing:
            self.server_ids = [844649871754395689, 736315344854974535]
        else:
            self.server_ids = [844649871754395689]
        self.event_start = datetime.datetime(2021, 5, 29)
        self.event_rewards = "`TBC`"

    def cog_unload(self):
        """
        Called when the cog unloads
        """
        Config.LOGGING.info("Shutting down queue cleaning system")
        self.ticket_garbage.cancel()

    async def valid_server(self, ctx):
        if ctx.guild.id in self.server_ids:
            return True
        else:
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Invalid server",
                                  description=f"You can only run this command in the tournament server."
                                              f"\n[You can join the server here!](https://discord.com/)")
            await ctx.send(content=ctx.author.mention, embed=embed)
            return False

    @commands.group(aliases=['ev'])
    @commands.bot_has_permissions(send_messages=True, external_emojis=True)
    async def event(self, ctx):
        """
        Base event command

        Displays current event info (if there's one active) when no subcommand is run
        """
        # Check the event is active and we aren't checking the stats
        if Config.EVENT_ACTIVE is None and str(ctx.invoked_subcommand) != "event stats":
            # There's no event, so no event details to share
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Enchanted Events",
                                  description=f"Current Event: `None`")
            embed.set_footer(text=f"Use '{ctx.prefix}event stats [mention]' to view the stats for events for that player.")
            await ctx.send(embed=embed)
            return

        # Get the user's data
        if ctx.invoked_subcommand is not None:
            return

        # Display the current event info
        embed = discord.Embed(color=Config.EVENTCOLOR, title="Enchanted Events",
                              description=f"Current Event: **Spring Tournament**\n[Join the Tournament Server]"
                                          f"(https://discord.com/)",
                              timestamp=self.event_start)
        embed.set_thumbnail(url=self.event_image)

        embed.add_field(name="Commands", inline=False,
                        value="`battle <mention>` - Sends out an invitation to battle that user"
                              "\n`accept <mention>` - Accepts a battle invitation from a user"
                              "\n`cancel` - Cancels an invitation to battle"
                              "\n`stats [mention]` - Checks the event stats for a user")
        embed.add_field(name="How it works", inline=False,
                        value="__Swiss Style tournament__"
                              "\nIn each round, you will battle your opponent in a best of three pvp. You may switch"
                              " classes and spells in between battles. You must play all three battles, any battle"
                              " missed will count as a loss."
                              "\nTo win a battle, you must deplete your opponent's mana/health to 0. If both reach 0 on"
                              "the same turn, it is a draw."
                              "\n__Special Rules__"
                              "\nAbilities are banned."
                              "\nYou will fight with Iron Scythe and Iron Shield and max level."
                              "\nYou may not use the same class twice in a round.")
        embed.add_field(name="Event Rewards", inline=False,
                        value=self.event_rewards)

        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        embed.set_footer(text="Tournament begins on ")

        # Send the info
        await ctx.send(embed=embed)

    @event.command(aliases=['toggle'])
    async def toggle_event(self, ctx, number: int):
        """
        Toggle the current event's status to active or inactive
        """
        states = {0: None, 1: "tourneyU", 2: "tourneyS"}
        if ctx.author.id in Config.OWNERIDS:
            try:
                Config.EVENT_ACTIVE = states[number]
            except KeyError:
                await ctx.send("` " + str(number) + " not in range(0, 3)`")

    @event.command()
    async def stats(self, ctx, member: discord.Member = None):
        """
        Displays the past and current stats for a user in an event
        """
        # Get the member (if it's either specified or not
        if member is None:
            member = ctx.author
        msg, account = await Utils.get_account_lazy(self.bot, ctx, member.id)
        if account is None:
            await ctx.send(
                embed=discord.Embed(title="User has no profile", description=member.name + " does not have a profile.",
                                    color=Config.EVENTCOLOR))
            return

        # Find out if the user has attended an event
        try:
            event_data = account['event']
        except KeyError:
            event_data = None

        # Creates the main stats embed
        embed = discord.Embed(color=Config.EVENTCOLOR, title="Enchanted Event Stats",
                              description=f"Stats for " + member.name + "#" + member.discriminator)
        embed.set_author(name=member.name, icon_url=member.avatar_url)

        # Check the user has participated in any events
        if event_data is None:
            embed.description = member.name + " hasn't participated in any events yet."

        # Easter 2021 event
        try:
            embed.add_field(name="🥚 Tower of Beginnings - Easter 2021",
                            value="Highest Floor: " + str(event_data['easter2021']['high']) +
                                  "\nAttempts: " + str(event_data['easter2021']['attempts']))
        except KeyError:
            pass
        except TypeError:
            pass

        # Spring Tournament 2021
        try:
            print(event_data)
            embed.add_field(name="🌷 Spring Tournament - May 2021",
                            value="Position: " + str(event_data['mayTourney2021']['position']) +
                                  "\nRounds Won: " + str(event_data['mayTourney2021']['wins']) +
                                  "\nBattles Won: " + str(event_data['mayTourney2021']['battle_wins']))
        except KeyError:
            pass
        except TypeError:
            pass

        await ctx.send(embed=embed)

    async def setup_chat_box(self, match):
        """
        Returns the chat box for the users
        """
        field_description = "╔ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        found = False
        for chat in self.chats:
            if match[0]['account']['user_id'] in chat[0]["ids"]:
                for c in chat[1:]:
                    field_description += f"│ **{c['user']}**: {c['msg']}\n"
                    found = True
        if not found:
            field_description += f"│ *No chat logs, use the chat command to chat*\n"
        field_description += "╚ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

        return field_description

    async def construct_embeds(self, match, turn):
        """
        Constructs the embed for the battle using Battle_Utils
        """
        for user_number in range(2):
            chat_log = await self.setup_chat_box(match)
            # Create embed
            if turn == user_number:
                if match[turn]['stunned']:
                    embed = discord.Embed(color=Config.EVENTCOLOR,
                                          description="It's your turn, but you're stunned! You can't do anything!")
                else:
                    embed = discord.Embed(color=Config.EVENTCOLOR,
                                          description="It's your turn. React with a number to use a spell. "
                                                      "Or react with 💤 to pass")
            else:
                if match[turn]['stunned']:
                    embed = discord.Embed(color=Config.EVENTCOLOR,
                                          description="It is " + match[int(not bool(user_number))]['ctx'].author.name
                                                      + "'s turn, but they're stunned and can't do anything!")
                else:
                    embed = discord.Embed(color=Config.EVENTCOLOR,
                                          description="It is " + match[int(not bool(user_number))]['ctx'].author.name
                                                      + "'s turn. Please wait for them to cast a spell.")

            # Spell book
            equipped_string = Battle_Utils.construct_spell_book(match[user_number])
            embed.description += "\n\n**Spellbook**:" + equipped_string

            # Add users to embed
            embed = Battle_Utils.add_users_to_embed(match, embed)

            # Title
            embed.title = "Battle against " + match[int(not bool(user_number))]['ctx'].author.name \
                          + match[int(not bool(user_number))]['account']['selected_title']

            # Effects
            footer_string = ""
            for effect in match[turn]['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] \
                                 + " effect for " + str(effect['turns']) + " turns."

            # Mana Generation
            embed.set_footer(text="You gain 3 mana at the beginning of your turn." + footer_string)

            embed.add_field(name="💬 **Chat**", value=chat_log, inline=False)

            await match[user_number]['message'].edit(embed=embed)

    async def construct_embeds_with_message(self, turn, match, message):
        """
        Constructs an embed with a message using Battle_Utils
        """
        for user_number in range(2):
            if turn == user_number:
                embed = discord.Embed(color=Config.EVENTCOLOR, description=message)
            else:
                embed = discord.Embed(color=Config.EVENTCOLOR, description=message)

            # Spell book
            equipped_string = Battle_Utils.construct_spell_book(match[user_number])
            embed.description += "\n\n**Spellbook**:" + equipped_string

            # Add users to embed
            embed = Battle_Utils.add_users_to_embed(match, embed)

            # Title
            embed.title = "Battle against " + match[int(not bool(user_number))]['ctx'].author.name \
                          + match[int(not bool(user_number))]['account']['selected_title']

            # Effects
            footer_string = ""
            for effect in match[turn]['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] \
                                 + " effect for " + str(effect['turns']) + " turns."

            # Mana Generation
            embed.set_footer(text="You gain 3 mana at the beginning of your turn." + footer_string)

            embed.add_field(name="💬 **Chat**", value=await self.setup_chat_box(match), inline=False)
            await match[user_number]['message'].edit(embed=embed)

    async def battle_thread(self, match):
        """
        The thread for the actual battle
        """
        try:
            # Setup the battle
            await Config.LOGGING.info("Battle thread started: Current threads: " + str(self.battles))
            self.battling_users.append({"id": match[0]['ctx'].author.id, "time": time.time()})
            self.battling_users.append({"id": match[1]['ctx'].author.id, "time": time.time()})
            # Randomly choose who goes first
            turn = random.randint(0, 1)
            # Setup for draws
            total_turns = 1
            draw = False

            # Let both user's know a battle has been found
            embed = discord.Embed(title="Match Started", color=Config.EVENTCOLOR,
                                  description="[jump](" + match[0]['message'].jump_url + ")")
            one_message = await match[0]['ctx'].send(match[0]['ctx'].author.mention, embed=embed)
            await one_message.delete(delay=10)
            embed = discord.Embed(title="Match Started", color=Config.EVENTCOLOR,
                                  description="[jump](" + match[1]['message'].jump_url + ")")
            one_message = await match[1]['ctx'].send(match[1]['ctx'].author.mention, embed=embed)
            await one_message.delete(delay=10)

            # Amplify turn
            a_turn = False

            for _ in range(2):
                # Setup stats for each user
                match[_]['health'] = match[_]['account']['stats']['health']
                match[_]['mana'] = match[_]['account']['stats']['endurance']
                match[_]['effects'] = []
                match[_]['afk'] = 0
                match[_]['account']['stats']['defense'] += 8.7
                match[_]['account']['stats']['strength'] += 5.8

                # Add reactions to both messages
                if match[_]['account']['slots'][0] is not None:
                    await match[_]['message'].add_reaction("1️⃣")
                if match[_]['account']['slots'][1] is not None:
                    await match[_]['message'].add_reaction("2️⃣")
                if match[_]['account']['slots'][2] is not None:
                    await match[_]['message'].add_reaction("3️⃣")
                if match[_]['account']['slots'][3] is not None:
                    await match[_]['message'].add_reaction("4️⃣")
                await match[_]['message'].add_reaction("💤")

            # The actual match stuff
            # Make sure nobody's died and we've played less than 100 turns
            while match[0]['health'] > 0 and match[1]['health'] > 0 and match[0]['mana'] > 0 and \
                    match[1]['mana'] > 0 and total_turns < 100:
                # If the current user has been afk too much, kill them
                if match[turn]['afk'] > 2:
                    match[turn]['health'] = 0
                    match[turn]['mana'] = 0
                    continue

                # Calculate effects for beginning of round
                for _ in range(2):
                    effects_remove = []
                    for effect in match[_]['effects']:
                        if effect["name"] in ["Regenerating", "Restoring"]:
                            match[_][effect['type']] += effect['amount']
                        else:
                            match[_][effect['type']] -= effect['amount']
                        match[_][effect['type']] = round(match[_][effect['type']], 1)
                        effect['turns'] -= 1
                        if effect['turns'] < 1:
                            effects_remove.append(effect)
                    for effect in effects_remove:
                        match[_]['effects'].remove(effect)

                # Add mana to player
                resource = 'mana'
                resource_number = 3

                # If it's amplify, or we're stunned, no need to regen
                if a_turn is True:
                    resource_number = 0
                    a_turn = False
                elif match[turn]['stunned']:
                    resource_number = 0

                match[turn][resource] += resource_number

                # Check nobody's died
                if not (match[0]['health'] > 0 and match[1]['health'] > 0 and match[0]['mana'] > 0 and
                        match[1]['mana'] > 0):
                    break

                # Check all stats are a.o.k.
                match = Battle_Utils.match_check(match)

                # Check nobody's died after the check
                for _ in range(2):
                    if match[_]['health'] <= 0 or match[_]['mana'] <= 0:
                        break

                # We're going to play a turn, so increment the turn counter
                total_turns += 1

                # Create the embed for the turn
                await self.construct_embeds(match, turn)

                # Begin a turn
                try:
                    # Check if the user is stunned
                    if match[turn]['stunned']:
                        match[turn]['stunned'] = False
                        await asyncio.sleep(3)
                        turn = turn = int(not bool(turn))
                        continue

                    # Setup checks for reactions from user
                    reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '💤': 5}

                    def check(check_payload):
                        if check_payload.user_id == match[turn]['ctx'].author.id and \
                                check_payload.message_id == match[turn]['message'].id:
                            if str(check_payload.emoji) in reaction_dict.keys():
                                if reaction_dict[str(check_payload.emoji)] < 4:
                                    return match[turn]['account']['slots'][
                                               reaction_dict[str(check_payload.emoji)]] is not None
                                else:
                                    return True
                        return False

                    temp_msg = await match[turn]['ctx'].channel.fetch_message(match[turn]['message'].id)
                    reaction = None
                    # Check if user has reacted prior to turn
                    for temp_reaction in temp_msg.reactions:
                        users = await temp_reaction.users().flatten()
                        if match[turn]['ctx'].author.id in [x.id for x in users] and temp_reaction.me:
                            reaction = temp_reaction
                            try:
                                await temp_reaction.remove(match[turn]['ctx'].author)
                            except:
                                await Config.LOGGING.error("Cannot remove emoji (not a big deal)")
                    # Wait for user to react
                    if reaction is None:
                        payload = await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=check)
                        reaction = payload.emoji
                        try:
                            await match[turn]['message'].remove_reaction(payload.emoji, match[turn]['ctx'].author)
                        except:
                            await Config.LOGGING.error("Cannot remove emoji (not big deal)")

                    # User's chosen to sleep
                    if str(reaction) == "💤":
                        turn = int(not bool(turn))
                        continue
                    # User is casting a spell
                    elif str(reaction) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']:
                        spell = Utils.get_spell(match[turn]['account']['class'],
                                                match[turn]['account']['slots'][reaction_dict[str(reaction)]])

                        match[turn], match[int(not bool(turn))], text = Battle_Utils.spell_effect(
                            spell, match[turn], match[int(not bool(turn))], True)

                        await self.construct_embeds_with_message(turn, match, text)

                        turn = int(not bool(turn))

                        await asyncio.sleep(5)
                        continue

                # Issue when taking turn
                except Exception as e:
                    # AFK
                    if isinstance(e, asyncio.TimeoutError):
                        embed = discord.Embed(title="AFK WARNING", color=Config.EVENTCOLOR,
                                              description="Your battle is still going! You lost this turn because you "
                                                          "took over 30 seconds to choose a spell.\n\n[Click to go to "
                                                          "fight](" + match[turn]['message'].jump_url + ")")
                        timeout_msg = await match[turn]['ctx'].send(match[turn]['ctx'].author.mention, embed=embed)
                        await timeout_msg.delete(delay=20)
                        match[turn]['afk'] += 1
                        turn = int(not bool(turn))
                        continue
                    # User deleted the message
                    elif isinstance(e, discord.errors.NotFound):
                        draw = True
                        break

            # We've left the while loop
            person_lost = False
            if (match[0]['mana'] > 0 or match[0]['health'] > 0) and (match[1]['mana'] > 0 or match[1]['health'] > 0):
                draw = True
            for _ in range(2):
                try:
                    await match[_]['message'].clear_reactions()
                except:
                    await Config.LOGGING.error("Cannot remove emoji (not a big deal)")

                # Check if match was a draw
                if draw or total_turns >= 100:
                    embed = discord.Embed(color=Config.EVENTCOLOR, description="**DRAW**")

                # Check the current user died
                elif match[_]['mana'] > 0 and match[_]['health'] > 0 or person_lost:
                    embed = discord.Embed(color=Config.EVENTCOLOR,
                                          description="**Congratulations! You have won!**")
                # User didn't die
                else:
                    embed = discord.Embed(color=Config.EVENTCOLOR,
                                          description="**You lost...**")

                # Display post-match data
                for __ in range(2):
                    embed.add_field(
                        name=Utils.get_rank_emoji(match[__]['account']['power']) + match[__]['ctx'].author.name
                        + match[__]['account']['selected_title'],
                        value="Health: " + str(match[__]['health']) + Config.EMOJI['hp'] + "\nMana: "
                        + str(match[__]['mana']) + Config.EMOJI['flame'])
                embed.title = "Battle against " + match[int(not bool(_))]['ctx'].author.name + \
                              match[int(not bool(_))]['account']['selected_title']
                # Attempt to edit the match message
                try:
                    await match[_]['message'].edit(embed=embed)
                except:
                    await Config.LOGGING.error("While cleaning up match message is not found. ignoring.")
                # Cleaning up any battle stuff
                await Config.LOGGING.info("Cleaning up a battle")
                # Increment user's battle stats
                Config.USERS.update_many({'user_id': {'$in': [match[0]['ctx'].author.id, match[1]['ctx'].author.id]}},
                                         {'$inc': {'battles.pvp': 1}})
                # Remove users from battling lists
                i = 0
                while i != len(self.battling_users):
                    if self.battling_users[i]["id"] == match[0]['ctx'].author.id or match[1]['ctx'].author.id:
                        self.battling_users.pop(i)
                    else:
                        i += 1

        # Issue during battle
        except:
            frames = ""
            tb_next = sys.exc_info()[2]
            while tb_next is not None:
                frames += "\n" + str(tb_next.tb_frame)
                tb_next = tb_next.tb_next
            await Config.LOGGING.error("Battle has errored! It has been disbanded and players were dequeued. "
                                       "\nError: `" + str(sys.exc_info()[1]) + "`"
                                       "\nLine #: `" + str(sys.exc_info()[2].tb_lineno) + "`"
                                       "\nFrames: ```Python" + frames + "```")
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Battle has ended",
                                  description="The battle has ended.")
            for _ in match:
                try:
                    await _['message'].edit(embed=embed)
                except:
                    pass
        # Clean up anything left
        finally:
            self.battles -= 1
            i = 0
            while i != len(self.battling_users):
                if self.battling_users[i]["id"] == match[0]['ctx'].author.id or \
                        self.battling_users[i]["id"] == match[1]['ctx'].author.id:
                    self.battling_users.pop(i)
                else:
                    i += 1

    @event.command()
    async def clear_q(self, ctx):
        """
        Stops invitations
        """
        if ctx.author.id not in Config.OWNERIDS:
            await ctx.send("You do not have permission to do this")
        else:
            self.friendly_matchmaking = []
            await ctx.send("All tickets in event matchmaking Queue have been cleared.")

    async def user_can_battle(self, ctx):
        """
        Gets the user's data and checks that the bot isn't in maintenance
        """
        # Check there is an account
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        # Enchanted is under maintenance
        if not Config.OPEN_QUEUES:
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Enchanted Maintenance",
                                  description="Queuing is disabled at the moment. Enchanted is under maintenance.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return -1, -1, True

        return msg, account, False

    async def is_user_battling(self, msg, ctx, target):
        """
        Checks if the user is currently battling
        """
        i = 0
        while i != len(self.battling_users):
            b_user = self.battling_users[i]
            if b_user["id"] == ctx.author.id:
                if (b_user["time"] + 600) > time.time():
                    if target == ctx.author:
                        embed = discord.Embed(color=Config.EVENTCOLOR, title="Error entering Queue",
                                              description="You are already battling someone. Please finish that battle "
                                                          "first.")
                    else:
                        embed = discord.Embed(color=Config.EVENTCOLOR, title="Error",
                                              description="This person is battling already.")
                    if msg is None:
                        await ctx.send(embed=embed)
                    else:
                        await msg.edit(embed=embed)
                    return True
                else:
                    self.battling_users.pop(self.battling_users.index(b_user))
                    continue
            else:
                i += 1

        return False

    @event.command(aliases=['b'])
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def battle(self, ctx, member: discord.Member = None, weapons: bool = True):
        """
        Challenges someone to a battle
        """
        # Check they're in the correct server
        if not await self.valid_server(ctx):
            return

        # Check if the event has started
        if not await event_start(ctx):
            return

        # Get the user's data
        msg, account, error = await self.user_can_battle(ctx)
        if error:
            return

        # Check they're not already battling
        error = await self.is_user_battling(msg, ctx, ctx.author)
        if error:
            return

        # Tell them they didn't pick anyone
        prefix = Utils.fetch_prefix(ctx)
        if member is None:
            discord.Embed(color=Config.EVENTCOLOR, title="No user selected",
                          description="Please mention a user to battle!")
            return

        # Check target isn't matching
        error = await self.is_user_battling(msg, ctx, member)
        if error:
            return

        # Check for current invite
        for invite in self.friendly_matchmaking:
            if invite["inviter"] == ctx.author.id:
                embed = discord.Embed(color=Config.EVENTCOLOR, title="Error",
                                      description=f"You already sent a pending invitation, delete that first with "
                                                  f"`{prefix}cancel` before sending a new invite.")
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return

        # Setup weapons
        weapon = Utils.get_item("Iron Scythe")
        armor = Utils.get_item("Iron Shield")

        embed = discord.Embed(color=Config.EVENTCOLOR, title=f"Battle invitation | Tournament!!",
                              description=f"Invitation sent to `{member.name}`\nDo {prefix}ev accept"
                                          f" {ctx.author.mention} to accept.",
                              timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=2))
        embed.set_footer(text=f'type {prefix}cancel to stop searching | timeout at ')
        embed.set_thumbnail(
            url=self.event_image)
        msg = await ctx.send(embed=embed)

        self.friendly_matchmaking.append(({'ability': None, 'friendly': True, 'inviter': ctx.author.id,
                                           'invited': member.id, 'weapons': weapons, 'weapon': weapon,
                                           'armor': armor, 'power': account['power'], 'ctx': ctx,
                                           'account': account, 'message': msg,
                                           'expire': datetime.datetime.utcnow() + datetime.timedelta(minutes=2),
                                           'stunned': False}))

    @event.command()
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def accept(self, ctx, member: discord.Member = None):
        """
        Accepts and invitation to battle
        """
        # Check they're in the correct server
        if not await self.valid_server(ctx):
            return

        # Check if the event has started
        if not await event_start(ctx):
            return

        # Check if the user can battle
        msg, account, error = await self.user_can_battle(ctx)
        if error:
            return
        error = await self.is_user_battling(msg, ctx, ctx.author)
        if error:
            return

        # Battle Data
        battle = []

        # Check if the user has been invited
        invited = False
        for invite in self.friendly_matchmaking:
            if invite["invited"] == ctx.author.id and invite["inviter"] == member.id:
                # If the user has been invited, setup the battle
                invited = True
                # Using Iron items
                armor = Utils.get_item("Iron Shield")
                weapon = Utils.get_item("Iron Scythe")

                # Let the user know we're starting now
                msg = await ctx.send(embed=discord.Embed(color=Config.EVENTCOLOR, title=f"invitation Accept",
                                                         description="Starting battle against"
                                                                     f"`{invite['ctx'].author.name}`",
                                                         timestamp=datetime.datetime.utcnow() + datetime.timedelta(
                                                             minutes=1)))

                ticket = {'friendly': True, 'ability': None, 'weapon': weapon, 'armor': armor,
                          'power': account['power'], 'ctx': ctx, 'account': account, 'message': msg,
                          'expire': datetime.datetime.utcnow() + datetime.timedelta(minutes=2),
                          'user': ctx.author, 'stunned': False}

                battle.append([invite, ticket])
                self.friendly_matchmaking.remove(invite)
                # Let the users know the battle is starting
                for match in battle:
                    await match[0]['message'].edit(embed=discord.Embed(color=Config.EVENTCOLOR, title="Match found!",
                                                                       description="Battling " + match[1][
                                                                           'ctx'].author.name))
                    await match[1]['message'].edit(embed=discord.Embed(color=Config.EVENTCOLOR, title="Match found!",
                                                                       description="Battling " + match[0][
                                                                           'ctx'].author.name))
                    self.battles += 1
                    id1 = match[0]['ctx'].author.id
                    id2 = match[1]['ctx'].author.id
                    match[0]['user'] = match[0]['ctx'].author
                    self.chats = [[{"ids": [id1, id2]}]]
                    battle = self.bot.loop.create_task(self.battle_thread(match))

        # Nobody's been invited
        if invited is False:
            embed = discord.Embed(color=Config.EVENTCOLOR, title="No invitation found",
                                  description="This person has not invited you to a battle.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @event.command()
    async def cancel(self, ctx):
        """
        Cancels an invitation to battle
        """
        # Check they're in the correct server
        if not await self.valid_server(ctx):
            return

        # Check if the event has started
        if not await event_start(ctx):
            return

        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        # Locate the invite ticket
        invited = None
        for invite in self.friendly_matchmaking:
            if invite["inviter"] == ctx.author.id:
                invited = invite

        # Remove the ticket
        if invited is not None:
            self.friendly_matchmaking.remove(invited)
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Invitation Canceled",
                                  description="You have removed the battle invitation.")
            await invited['message'].edit(embed=discord.Embed(color=Config.EVENTCOLOR, title="Invitation Cancelled!",
                                                              description="This battle invitation to has been "
                                                                          "cancelled"))

            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
                await msg.delete(delay=10)
                await ctx.message.delete(delay=10)

        # No ticket to cancel
        else:
            prefix = Utils.fetch_prefix(ctx)
            embed = discord.Embed(color=Config.EVENTCOLOR, title=f"You look confused.",
                                  description=f"You are not actively looking for a battle. "
                                              f"Use {prefix}battle to start looking for one.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=10)
            await ctx.message.delete(delay=10)

    @battle.error
    async def battle_error(self, error, ctx):
        """
        If there's an issue during a battle, does this
        """
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..",
                                               description="I'm missing some permissions, please make sure i have the "
                                                           "following:\n\nadd_reactions, manage_messages, "
                                                           "send_messages, external_emojis"),
                           color=Config.ERRORCOLOR)

    async def after_battle(self, task, match):
        """
        Called after a battle
        """
        await Config.LOGGING.info("Callback for after match has been called.")
        try:
            task.result()
        except:
            frames = ""
            tb_next = sys.exc_info()[2]
            while tb_next is not None:
                frames += "\n" + str(tb_next.tb_frame)
                tb_next = tb_next.tb_next
            await Config.LOGGING.error("Battle has errored! It has been disbanded and players were dequeued. "
                                       "\nError: `" + str(sys.exc_info()[1]) + "`"
                                       "\nLine #: `" + str(sys.exc_info()[2].tb_lineno) + "`"
                                       "\nFrames: ```Python" + frames + "```")
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Battle has ended",
                                  description="The battle has ended.")
            print(match)
            print(task)
            for _ in match:
                await _['message'].edit(embed=embed)
        finally:
            self.battles -= 1
            i = 0
            while i != len(self.battling_users):
                if self.battling_users[i]["id"] == match[0]['ctx'].author.id or match[1]['ctx'].author.id:
                    self.battling_users.pop(i)
                else:
                    i += 1
            loop = 0
            for chat in self.chats:
                if match[0]['ctx'].author.id in chat[0]["ids"]:
                    self.chats.remove(self.chats[loop])
                loop += 1

    @event.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def chat(self, ctx, *, choice: str = None):
        """
        Sends a chat message
        """
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            prefix = Utils.fetch_prefix(ctx)
            embed = discord.Embed(title="Emotes", description="", color=Config.EVENTCOLOR)
            i = 0
            for cosmetic in account['cosmetics']:
                if cosmetic["type"] == "emote":
                    i += 1
                    embed.description += "> " + str(i) + " | **" + cosmetic["value"] + "**\n"
            embed.set_footer(text=f"Get more emotes from the shop | use {prefix}chat <index> to chat in battle")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        emotes = []
        try:
            for cosmetic in account['cosmetics']:
                if cosmetic["type"] == "emote":
                    emotes.append(cosmetic)
            choice = int(choice)
            if choice > len(emotes) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                    len(emotes)) + " Emotes. Try using a number 1-" + str(len(emotes)),
                                      color=Config.EVENTCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                loop = 0
                for chat in self.chats:
                    if ctx.author.id in chat[0]["ids"]:
                        if len(chat) > 5:
                            self.chats[loop].remove(self.chats[loop][1])
                        self.chats[loop].append({'user': str(ctx.author.name), 'msg': emotes[choice]['value']})
                        embed = discord.Embed(
                            description=f"Chat sent!\n**{str(ctx.author.name)}**: {emotes[choice]['value']}",
                            color=Config.EVENTCOLOR)
                        if msg is None:
                            message = await ctx.send(embed=embed)
                            await asyncio.sleep(5)
                            await message.delete()
                            await ctx.message.delete()
                        else:
                            await msg.edit(embed=embed)
                        return
                    loop += 1
                embed = discord.Embed(title="Whoops..",
                                      description=f"You can only use this command when you're battling!",
                                      color=Config.EVENTCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...",
                                  description="That's not a emote index. Try using a number 1-" + str(len(emotes)),
                                  color=Config.EVENTCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @tasks.loop(seconds=30)
    async def ticket_garbage(self):
        """
        Cleans up the tickets
        """
        if len(self.friendly_matchmaking) > 0:
            for invite in self.friendly_matchmaking:
                if invite['expire'] < datetime.datetime.utcnow():
                    await invite['message'].edit(
                        embed=discord.Embed(color=Config.EVENTCOLOR, title="Invitation Cancelled!",
                                            description="This battle invitation to has been cancelled"))
                    self.friendly_matchmaking.remove(invite)

    @event.command()
    async def set_time(self, ctx, month: int, day: int):
        if ctx.author.id in Config.OWNERIDS:
            self.event_start = datetime.datetime(2021, month, day)

    @event.command()
    async def set_rewards(self, ctx, *, rewards):
        if ctx.author.id in Config.OWNERIDS:
            self.event_rewards = rewards


def setup(bot):
    bot.add_cog(Tournament(bot))
