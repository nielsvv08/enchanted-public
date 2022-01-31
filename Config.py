# Imports
import pymongo
import discord

from motor.motor_asyncio import AsyncIOMotorClient

# # MongoDB
# Cluster (Replace the <password> part of your uri with your password and remove the "<>")
myclient = pymongo.MongoClient(
    "!!!! MongoDB secret !!!!")

myclient_motor = AsyncIOMotorClient(
    "!!!! MongoDB secret !!!!")

# SWITCH BETWEEN TESTING AND NOT TESTING
testing = False

if testing:
    USERS = myclient["enchanted-testing"]['users']
    CLASSES = myclient["enchanted-testing"]['classes']
    CLANS = myclient["enchanted-testing"]['clans']

    motor_USERS = myclient_motor["enchanted-testing"]['users']
    motor_CLANS = myclient_motor["enchanted-testing"]['clans']

    LOG_CHANNEL = # LOG CHANNEL ID
else:
    USERS = myclient["enchanted-main"]['users']
    CLASSES = myclient["enchanted-main"]['classes']
    CLANS = myclient["enchanted-main"]['clans']

    motor_USERS = myclient_motor["enchanted-main"]['users']
    motor_CLANS = myclient_motor["enchanted-main"]['clans']

    LOG_CHANNEL = 839493531118600202
CLAN_MESSAGES = myclient["enchanted-main"]['clan_messages']
SPELLS = myclient["enchanted-main"]['spells']
ABILITIES = myclient["enchanted-main"]['abilities']
PLANTS = myclient['enchanted-main']['plants']
ITEMS = myclient['enchanted-main']['items']
OLD_ITEMS = myclient['enchanted-main']['old-items']
SERVERS = myclient['enchanted-main']['servers']
BLACKLIST = myclient['enchanted-main']['blacklist']
REPORTS = myclient['enchanted-main']['reports']
DROPPED_ITEMS = myclient['enchanted-main']['dropped_items']
WIKIS = myclient['enchanted-main']['wiki']
CODES = myclient['enchanted-main']['codes']
MAIN = myclient['enchanted-main']['main']
RAIDS = myclient['enchanted-main']['raids']

# Rewards in format:
# amount;type
# Valid Types: Coin, Ruby, Crown, Artifact, Chest
RANK_LINKS = {-1: {'name': "Unranked", "emoji": "<:unranked:848205908323860480>", "rewards": "None"},
              0: {'name': "Iron 1", 'emoji': "<:iron1:838658153716645949>", "rewards": "100;Coin"},
              10: {'name': "Iron 2", 'emoji': "<:iron2:838658153612443668>", "rewards": "100;Ruby"},
              20: {'name': "Iron 3", 'emoji': "<:iron3:838658153847324692>", "rewards": "150;Coin"},
              30: {'name': "Bronze 1", 'emoji': "<:bronze1:838658153582297089>", "rewards": "5;Crown"},
              50: {'name': "Bronze 2", 'emoji': "<:bronze2:838658154077880330>", "rewards": "10;Artifact"},
              70: {'name': "Bronze 3", 'emoji': "<:bronze3:838662809126436874>", "rewards": "5;Chest"},
              100: {'name': "Silver 1", 'emoji': "<:silver1:838658153545203722>", "rewards": "10;Crown"},
              125: {'name': "Silver 2", 'emoji': "<:silver2:838658153847193641>", "rewards": "500;Coin"},
              150: {'name': "Silver 3", 'emoji': "<:silver3:838658153666838578>", "rewards": "600;Ruby"},
              175: {'name': "Gold 1", 'emoji': "<:gold1:838658153557786644>", "rewards": "15;Crown"},
              200: {'name': "Gold 2", 'emoji': "<:gold2:838658153569976350>", "rewards": "25;Artifact"},
              250: {'name': "Gold 3", 'emoji': "<:gold3:838658153783885844>", "rewards": "50;Chest"},
              300: {'name': "Emerald 1", 'emoji': "<:emerald1:838658153880617002>", "rewards": "20;Crown"},
              350: {'name': "Emerald 2", 'emoji': "<:emerald2:838658153569976351>", "rewards": "1500;Coin"},
              400: {'name': "Emerald 3", 'emoji': "<:emerald3:838658153296953348>", "rewards": "2000;Ruby"},
              450: {'name': "Enchanter 1", 'emoji': "<:enchanter1:838658153889529906>", "rewards": "25;Crown"},
              500: {'name': "Enchanter 2", 'emoji': "<:enchanter2:838658154219962397>", "rewards": "100;Artifact"},
              600: {'name': "Enchanter 3", 'emoji': "<:enchanter3:838658153847324697>", "rewards": "???"},
              700: {'name': "Revenant 1", 'emoji': "<:revenant1:838658153545203725>", "rewards": "30;Crown"},
              800: {'name': "Revenant 2", 'emoji': "<:revenant2:843184378615562260>", "rewards": "???"},
              900: {'name': "Revenant 3", 'emoji': "<:revenant3:843184436022738955>", "rewards": "???"},
              1000: {'name': "Champion", 'emoji': "<:champion:843184444126265344>", "rewards": "???"}}

ACTIVE_CONTRACT = 0
LOGGING = None

# # Main Discord bot settings
# Bot"s token (DO NOT SHARE WITH ANYONE ELSE!) (To find your token go to
# https://discordapp.com/developers/appli~cations/ > Your Wumpus-Bot Application >
# Bot (Turn the application into a bot if you haven"t already) > Token)
#
if testing:
    TOKEN = "!!! BOT TOKEN !!!!"  # TEST BOT TOKEN
else:
    TOKEN = "!!! BOT TOKEN !!!!"  # main bot token

# Owner IDS (People who have access to restart the bot)
OWNERIDS = [] 
if testing:
    OWNERIDS.append()  

# Channels
BLACKLIST_C = 715408045127106630
STAFF_C = 710352120880169010

# Main Color (Replace the part after 0x with a hex code)
MAINCOLOR = discord.Color(0xdb58dd)
TURNCOLOR = discord.Color.blue()
NOTTURN = discord.Color(0x000000)
DAMAGE = discord.Color.red()
OK = discord.Color.green()
EVENTCOLOR = discord.Color(0xfd7002)

EVENT_ACTIVE = None

CLAN_EMOTE_HOSTS = [] # FILL IN EMOTE HOST SEVER ID

OPEN_QUEUES = True
MAINTENANCE = False
DISABLED = ["code"]
PERM_SEASON = False  # Permission to run season reset

ALL_CLASSES = []

# Error Color (Replace the part after the 0x with a hex code)
ERRORCOLOR = 0xED4337

TITLES = [' the Warrior', ' the Guard', ' the Bard', ' I', ' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII', ' IX',
          ' X', ' the Holy', ' the One', ' the Only', ' the Emperor', ' the King', ' the Queen', ' the Duke',
          ' the Duchess', ' the Knight', ' <:Crystal:672975609135366145>']

EMOJI = {'artifact': "<:A:730357877281259582>", 'up1': "<:1:730357877243379712>",
         'up2': "<:2:730357877260419123>", 'up3': "<:3:730357877403025469>",
         'down1': "<:1:730357877088321558>", 'down2': "<:2:730357877272870993>",
         'down3': "<:3:730357877176533124>", 'scroll': "<:scroll:676183918487142421>",
         'coin': "<:Coin:676181520062349322>", 'flame': "<:mana:852257363977437275>",
         'chest': "<:box:671574326364995595>", 'ruby': "<:ruby:676177832963211284>",
         'battle': "<:battle:670882198450339855>", 'power': "<:power:852824647317454910>",
         'book': "<:book:670882689640955924>", 'key': "<:key:670880439199596545>", 'xp': "<:X:730357877310488636>",
         'crown': "<:C:731950698756964423>", 'hp': "<:L:730356470905831434>", "spell": "<:N:761582482197446716>",
         "ability": "<:N:761582084879679568>", "broken": "<:B:761582085449711628>",
         "shield": "<:sh:785848039792312320>", "sword": "<:cs:785848039431995494>"}

BARS = {"health": {"icon": "<:hh_a:782606471077822505>",
        "connector": ["<:hh_b_0:782606470956318773>", "<:hh_b_1:782606470855917589>", "<:hh_b_2:782606471354777600>",
                      "<:hh_b_3:782606471296843776>", "<:hh_b_4:782613196107808778>", "<:hh_b_5:782606471430275103>",
                      "<:hh_b_6:782606471140737025>"],
                   "middle": ["<:c_0:782382041940754473>", "<:hh_c_1:782381997208240168>",
                              "<:hh_c_2:782381997254901790>", "<:hh_c_3:782381996797722625>",
                              "<:hh_c_4:782381997078478878>", "<:hh_c_5:782381997199851520>",
                              "<:hh_c_6:782381997216759858>"],
                   "end": ["<:d_0:782382041978503179>", "<:hh_d_1:782381996872695834>", "<:hh_d_2:782381997212827688>",
                           "<:hh_d_3:782381997204307999>", "<:hh_d_4:782381997313097738>",
                           "<:hh_d_5:782381996843991060>"]},
        "mana": {"icon": "<:mh_a:782382022101696542>",
                 "connector": ["<:mh_b_0:782382021905088532>", "<:mh_b_1:782382021837455371>",
                               "<:mh_b_2:782382022106284042>", "<:mh_b_3:782382022210879498>",
                               "<:mh_b_4:782382021611618325>", "<:mh_b_5:782382021992382464>",
                               "<:mh_b_6:782382021640716329>"],
                 "middle": ["<:c_0:782382041940754473>", "<:mh_c_1:782382022042714152>", "<:mh_c_2:782382021515149325>",
                            "<:mh_c_3:782382022001557524>", "<:mh_c_4:782382021992644638>",
                            "<:mh_c_5:782382021653037058>", "<:mh_c_6:782382022009290792>"],
                 "end": ["<:d_0:782382041978503179>", "<:mh_d_1:782382022109954049>", "<:mh_d_2:782382022287032330>",
                         "<:mh_d_3:782382021954633748>", "<:mh_d_4:782382022101958716>",
                         "<:mh_d_5:782382021984911430>"]}}

GROWTH = {-1: "🥀", 0: "<:dirt:674075707772764160>", 1: "🌱", 2: "🌿", 3: "🌾", 4: "🌴"}

CONTRACTS = [{'1': {'xp': 10000, 'name': EMOJI['chest'] + " Chest", 'reward': 1, 'type': 'chest'},
              '2': {'xp': 30000, 'name': EMOJI['scroll'] + " '[FIRST CONTRACT]' Title", 'reward': ' [FIRST CONTRACT]',
                    'type': 'title'},
              '3': {'xp': 50000, 'name': EMOJI['chest'] + "x2 Chest", 'reward': 2, 'type': 'chest'},
              '4': {'xp': 80000, 'name': EMOJI['ruby'] + "x50 Rubies", 'reward': 50, 'type': 'ruby'},
              '5': {'xp': 100000, 'name': "<a:orb:710795781921177601> Orb Badge",
                    'reward': ' <a:orb:710795781921177601>', 'type': 'title'}}]

WIKI = [{'name': "Spells", 'link': "wiki/spells", 'pages': [
    {'title': "Spells Page 1",
     'content': "<:D:761582483434242118> **[DAMAGE]**\nWill deal `(effect + strength) x scaling` damage to your "
                "opponent.\n*Costs: `cost` mana*\n\n"
     + "<:H:761582482809159693> **[HEAL]**\nWill give you back `effect` health.\n*Costs: (cost) mana*\n\n"
     + "<:S:761582482838519810> **[STUN]**\nWill deal `(effect + strength) x scaling` damage to your opponent, and has "
       "a 33% chance of stunning your opponent.\n*Costs: `cost` mana*\n\n"
     + "<:M:761582483237240902> **[MANA]**\nWill give you `effect` mana.\n*Costs: `cost` health*\n\n"
     + "<:D:761582483237371914> **[DRAIN]**\nWill steal `effect` of opponents mana and add it to yours.\n"
       "*Costs: `cost` health*\n\n"
     + "<:P:761582482708889631> **[PEN]**\nWill give you `effect` strength increase.\n*Costs: `cost` mana*"},
    {'title': "Spells Page 2",
     'content': "<:A:761582483153354752> **[ARMOR]**\nWill give you `effect` defense increase.\n"
                "*Costs: `cost` mana*\n\n"
     + "<:P:761582483245629510> **[POISON]**\nWill deal `effect` damage per "
       "turn (total of 2-8 turns) to your opponent. \n*Costs: `cost` mana*\n\n"
     + "<:B:761582483149815838> **[BLIND]**\nWill reduce opponents mana by `effect`"
       " per turn (total of 2-8 turns) \n*Costs: `cost` mana*\n\n"
     + "<:I:761582483212075008> **[IMPAIR]**\nWill remove `effect` defense from your opponent.\n*Costs: `cost` "
       "mana*\n\n"
     + "<:W:761582482919260161> **[WEAKEN]**\nWill remove `effect` strength from your opponent.\n*Costs: `cost` "
       "mana*\n\n"
     + "<:S:761582483401211945> **[STEAL]**\nWill rip `(effect + strength) x scaling` from your opponents health and "
       "heal yourself for 70% of that amount.\n*Costs: `cost` mana*\n\n"
     + "<:T:761582483128057887> **[TRUE]**\nWill deal `(effect + strength) x scaling` damage to your opponent without "
       "being affected by their armor.\n*Costs: `cost` mana*"}]},
    {'name': "Abilities", 'link': "wiki/abilities", 'pages': ""},
    {'name': "Classes", 'link': "wiki/classes/", 'pages': ""},
    {'name': "Battles", 'link': "wiki/pvp",
     'pages': [{'title': "Ranked Battles",
                'content': "You can use the command `battle` to search for another player to fight against. "
                           "You will be matched against players within `40` **power**"+EMOJI['power']+" of your own. "
                           "In a battle, your aim is to reduce your opponent's **health** "+EMOJI['hp']+" or **mana**"
                           +EMOJI['flame']+" to `0` before they do it to you. "
                           "\nIn battle, use the 1️⃣, 2️⃣, 3️⃣, and 4️⃣ reactions to cast your spells, "
                           "or 🔆 to use your ability. "
                           "You can use 💤 to skip a turn."
                           "\nAt the start of each turn, you gain `3` **mana**"+EMOJI['flame']+" "
                           "Do nothing in `30`s and your turn will be skipped and you gain an afk warning. "
                           "Gain `3` and you forfeit the fight. "
                           "\n\nAfter the battle, if you win, you will gain `7-9` **power**"+EMOJI['power']+" "
                           "but if you lose, you will also lose `5-7` **power**"+EMOJI['power']+" "
                           "Rewards will also be given to both players of **Coins** "+EMOJI['coin']+", "
                           "**Rubies** "+EMOJI['ruby']+" and **keys**"+EMOJI['key']+" "
                           "Greater rewards will be given to the winner than the loser."
                           "\n\n**Command Aliases**\n`battle`, `b`"
                           "\n\n*Check the next page to view info on friendly battles*"},
               {'title': "Friendly Battles",
                'content': "You can use the command `battle <mention>` to send an invitation to a player to fight "
                           "against you. "
                           "They can use `accept <mention>` to accept your invitation and begin the fight."
                           "Your **power**"+EMOJI['power']+" does not matter when sending out invitations. "
                           "\nIn a battle, your aim is to reduce your opponent's **health** "+EMOJI['hp']+" or **mana**"
                           +EMOJI['flame']+" to `0` before they do it to you. "
                           "\nIn battle, use the 1️⃣, 2️⃣, 3️⃣, and 4️⃣ reactions to cast your spells, "
                           "or 🔆 to use your ability. "
                           "You can use 💤 to skip a turn."
                           "\nAt the start of each turn, you gain `3` **mana**"+EMOJI['flame']+" "
                           "Do nothing in `30`s and your turn will be skipped and you gain an afk warning. "
                           "Gain `3` and you forfeit the fight. "
                           "\n\nAs this is a friendly battle, no rewards are granted, nor will your rank be affected."
                           "\n\n**Command Aliases**\n`battle <mention>`, `b <mention>`\n`accept <mention>`"
                           "\n\n*Check the previous page to view info on ranked battles*"}]},
    {'name': "Bosses", 'link': "wiki/bosses",
     'pages': [{'title': "Bosses",
                'content': "You can use the command `boss` to start a boss battle. "
                           "You can have up to `10` players in one boss battle. "
                           "In a battle, your aim is to reduce the boss's **health** "+EMOJI['hp']+" or **mana**"
                           +EMOJI['flame']+" to `0` before they do it to all participating players. "
                           "\nOn your turn, use the 1️⃣, 2️⃣, 3️⃣, and 4️⃣ reactions to cast your spells, "
                           "or 🔆 to use your ability. "
                           "You can use 💤 to skip a turn or 🏳️ to exit the fight. "
                           "\nAt the start of each turn, you gain `3` **mana**"+EMOJI['flame']+" however, the boss will "
                           "gain `8`. "
                           "Bosses will take a turn after every player. "
                           "Do nothing in `30`s and your turn will be skipped and you gain an afk warning. "
                           "Gain `3` and you will be kicked from the battle. "
                           "\n\nAfter killing a boss, all players who participated (no matter if they are still alive "
                           "or not) will gain some **Coins** "+EMOJI['coin']+" and **keys**"+EMOJI['key']+" "
                           "More rewards will be granted if there are more players participating."
                           "\n\n**Command Aliases**\n`boss`"
                           "\n\n*Check the next page for info on TITANs.*"},
               {'title': "TITAN Bosses",
                'content': "Upon running the `boss` command, there is a `12.5`% chance to summon a TITAN."
                           "\n\nTITANs have increased **health** "+EMOJI['hp']+", **mana**"+EMOJI['flame']+", "
                           "**strength** "+EMOJI["sword"]+" and **armor** "+EMOJI['shield']+" "
                           "Other than this, they behave like normal bosses, attacking after every player and "
                           "regenerate `8` **mana**"+EMOJI['flame']+" each turn."
                           "\n\nAs TITANs are harder to kill, there are greater rewards granted for killing them."
                           "\n\n**Command Aliases**\n`boss`"
                           "\n\n*Check the previous page for info on normal bosses.*"}]},
    {'name': "Dungeons", 'link': "wiki/dungeons",
     'pages': [{'title': "Dungeons",
                'content': "You can start a dungeon battle with the `dungeon` command. "
                           "Up to `10` people can join a dungeon run. "
                           "Dungeons are boss fights one after the other with incrementally stronger bosses each floor. "
                           "This scales with the amount of players participating. "
                           "\nEach floor behaves like a normal boss fight, however, abilities can only be used once. "
                           "__Stagnation__, __Healing Blood__ and __Inner Light__ effects will remain on all floors "
                           "once used. "
                           "\n\nAfter completing a floor, you will be rewarded **coins** "+EMOJI['coin']+" "
                           "and **artifacts**"+EMOJI['artifact']+" The rewards increase as you clear more floors. "
                           "**Artifacts**"+EMOJI['artifact']+" will be immediately be sent to the clan that started"
                           " the dungeon, and only that clan. "
                           "\n\nIn between floors, any players left alive will be fully healed, their "
                           "**strength** "+EMOJI['sword']+" and **armor** "+EMOJI['shield']+" refreshed. "
                           "This means it's possible to change spells, items and even class whilst in a dungeon. "
                           "\n\n**Dungeon Types**\nAll bosses in a dungeon are the same class. "
                           "This is decided on the first floor. "
                           "\nThere is also a `10`% chance for a dungeon to be a TITAN dungeon. "
                           "This means all bosses will be a TITAN, however, "
                           "it will also grant better rewards for defeating the same floor as a normal dungeon. "
                           "\n\n**Command Aliases**\n`dungeon`, `clanfight`, `floor`, `floors`"}]},
    {'name': "Clans", 'link': "wiki/clans",
     'pages': [{'title': "Basic Clans Info",
                'content': "Clans can be accessed with the `clan` command, and the full list of commands with "
                           "`clan help`. "
                           "\nClans are groups of players, with an initial cap of `20` that can later be upgraded to"
                           "a maximum of `30`. Clans offer two main benefits, generators and dungeons. "
                           "\nDungeon runs can only be started by players in a clan, but can be joined by anyone. "
                           "One of the rewards for clearing levels in a dungeon is **artifacts** "+EMOJI['artifact']+"."
                           " They can be spent by clan admins to upgrade the clan. "
                           "\n\nClans can be upgraded with `clan upgrade`, a command only available to **clan admins** ⭐. "
                           "There are three types of upgrades:"
                           "\n**Generators** 🔧 - Increases the amount of resources the selected generator produces "
                           "each hour."
                           "\n**Storage** 🧺 - Increases the maximum amount of the selected resource that can be stored "
                           "before needing to be collected."
                           "\n**Max Members** ⬆️ - Increases the maximum amount of members a clan can have."
                           "\n\nClan generators will generate resources every hour that can be claimed with "
                           "`clan claim`. This command will claim the resources for all users, so if a clan mate "
                           "claims before you do, you will both get the resources stored in the clan storage."
                           "\n\n*Check the next page for info on ranks and clan settings*"},
               {'title': "Clans - Ranks and Settings",
                'content': "\n\n**Clan Ranks**\n**Owner** 🌟 - Created the clan. Has full permissions."
                           "\n**Admin** ⭐ - Has permissions for all commands. "
                           "Can manage other members, but not other admins."
                           "\n**Member** - Permissions to start dungeon runs and claim from storage."
                           "\n\n**Clan Settings** - Only editable by **clan admins** ⭐"
                           "\n`clan edit name <name>` - The name of the clan."
                           "\n`clan edit icon` - Attach a `.png`, `.jpg` or `.gif` to change the clan icon."
                           "\n`clan edit invite <open/closed>` - Either `open` or `closed`. "
                           "Specifies if people can join the clan or not."
                           "\n`clan message <message>` - Sets the message at the bottom of the clan info embed."}]},
    {'name': "Items", 'link': "wiki/items",
     'pages': [{'title': "Items",
                'content': "Items are the way to progress in Enchanted. "
                           "Once equipped, they will increase your strength and defense in a fight. "
                           "\n\nYou can obtain items from the shop by purchasing them for **coins** "+EMOJI['coin']+"."
                           " There are `6` item tiers. Each with their own prices and stats, "
                           "with `3` weapons, and `3` armors at every tier. "
                           "\nAfter purchasing an item, you can equip it using `weapon [weapon name]` or "
                           "`armor [armor name]`. If you don't specify an item, you will unequip your current item. "
                           "\n\nEvery item can be upgraded, using the `upgrade` command. "
                           "This costs **rubies**"+EMOJI['ruby']+" with the cost increasing each upgrade. "
                           "Upgrading an item will increase the effect it has when you equip it. "
                           "\n\nEach item has a durability, this decreases each time you take a turn. "
                           "An item's maximum durability depends on its tier. "
                           "Upgrading an item will repair it back to full durability. "
                           "If an item it as its maximum level, you can still upgrade it to repair it, "
                           "however this will not increase the item effect."
                           "\n\n**Command Aliases**\n`weapon [weapon name]`, `w [weapon name]`"
                           "\n`armor [armor name]`, `a [armor name]`"
                           "\n`upgrade <item number>`, `u <item number>`"}]},
    {'name': "Resources", 'link': "wiki/items",
     'pages': [{'title': "Resources",
                'content': "**Coins** "+EMOJI['coin']+" - Collected from boss fights, dungeons, battles, "
                           "clan generators and **chests** "+EMOJI['chest']+", they can be used to purchase new items "
                           "from the daily `shop`."
                           "\n\n**Rubies** "+EMOJI['ruby']+" - Collected from battles, clan generators and "
                           "**chests** "+EMOJI['chest']+". They can be spent on item upgrades and repairs."
                           "\n\n**Keys**"+EMOJI['key']+" - Collected from boss fights, battles and "
                           "clan generators. Upon collecting `10` **keys**"+EMOJI['key']+", "
                           "they will be exchanged for one **chest** "+EMOJI['chest']+""
                           "\n\n**Chests** "+EMOJI['chest']+" - Collected from battles and earning `10` "
                           "**keys**"+EMOJI['key']+". You can gain **coins** "+EMOJI['coin']+", **rubies** "+EMOJI['ruby']+
                           ", **spells**, **classes**, (and **abilities** after reaching "+RANK_LINKS[100]['emoji']+")."
                           " They can be opened with `chest`, `c`, `open` or `o`, either one at a time, or ten at once."
                           "\n\n**Crowns** "+EMOJI['crown']+" - A cosmetic currency that can be spent in the shop for "
                           "special titles, embed colours, embed images and more chat messages. The best way to "
                           "get this currency is through __donating__, more info in `wiki donating`. It's also possible"
                           " to gain this currency through events and season rewards, but they will grant smaller amounts."}]},
    {'name': "Donating", 'link': "wiki/donating",
     'pages': [{'title': "Donating",
                'content': "You can __support the development of Enchanted__ by donating. All donations will be used"
                           "to host, improve or advertise Enchanted. Donators will be rewarded with a lot of crowns:"
                           "\n\n__Crowns:__\n```html\n1. <$1.00> 100 Crowns\n2. <$2.00> 210 Crowns (10 bonus)\n"
                           "3. <$5.00> 600 Crowns (100 bonus)\n4. <$10.00> 1,300 Crowns (300 bonus)\n"
                           "5. <$50.00> 6,500 Crowns (1500 bonus)\n6. <$100.00+> 15,000 Crowns (5000 bonus)\n```\n"
                           "\n__Special Perks__\n> Donations > $0: **Donator-only crown title**\n> Donations > $5:  "
                           "**Donator-only crown embed thumbnail**\n> Donations > $10: **\"Special\" Role**\n> "
                           "Donations > $20: **Beta access**\n\nTo donate (PayPal) please go to our "
                           "[**Discord**](https://discord.com/) server and *__open a support ticket!__*"}]},
    {'name': "Seasons", 'link': "wiki/pvp",
     'pages': [{'title': "Season Resets",
                'content': "Every reset, your **power**" + EMOJI['power'] + "would be reduced to the start of their "
                           "previous rank.\n__For Example:__"
                           "\n130" + EMOJI['power'] + "(" + RANK_LINKS[125]['emoji']
                           + "), would become 100" + EMOJI['power'] + "(" + RANK_LINKS[100]['emoji']
                           + ").\n300" + EMOJI['power'] + "(" + RANK_LINKS[300]['emoji']
                           + ") would become 250" + EMOJI['power'] + "(" + RANK_LINKS[250]['emoji']
                           + ")."
                           "\n\nEach season, you must battle another player to join the season. "
                           "Without joining the season, you cannot claim rewards at the end of the season, "
                           "nor will your rank be displayed, nor added to the clan's total power."
                           "\n\nAfter each season, you can claim rewards (`season claim`) based on your ranking "
                           "last season.\n\n*Check the next page to view the power requirements for ranks*"},
               {'title': "PVP Ranks",
                'content': "\n" + RANK_LINKS[0]['emoji'] + " 0 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[10]['emoji'] + " 10 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[20]['emoji'] + " 20 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[30]['emoji'] + " 30 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[50]['emoji'] + " 50 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[70]['emoji'] + " 70 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[100]['emoji'] + " 100 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[125]['emoji'] + " 125 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[150]['emoji'] + " 150 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[175]['emoji'] + " 175 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[200]['emoji'] + " 200 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[250]['emoji'] + " 250 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[300]['emoji'] + " 300 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[350]['emoji'] + " 350 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[400]['emoji'] + " 400 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[450]['emoji'] + " 450 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[500]['emoji'] + " 500 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[600]['emoji'] + " 600 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[700]['emoji'] + " 700 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[800]['emoji'] + " 800 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[900]['emoji'] + " 900 " + EMOJI['power'] +
                           "\n" + RANK_LINKS[1000]['emoji'] + " 1000+ " + EMOJI['power']}]},
        {'name': "Events", 'link': "",
         'pages': [{'title': "Events Info",
                    'content': "Event's are organised at irregular intervals by the Event Staff."
                               "\n\nThere has been two types of events organised since the release of events."
                               "\n__A PvE dungeon__, where you had to reach the highest floor possible, with rewards based "
                               "on which floor you managed to reach."
                               "\n__A PvP tournament__ that had players match up against one another, and play a best "
                               "of three battles. Rewards are given based on your final position."
                               "\n\n**Commands**\n`event`, `ev` - Main event command"
                               "\n`event stats [mention]` - Check the stats for all events you (or someone else) "
                               "has participated in\n\n*Check the next pages to see events previously organised*"},
                   {'title': "🌷 Spring 2021 - Tournament",
                    'content': "**Commands**"
                               "\n`battle <mention>` - Sends out an invitation to battle that user"
                               "\n`accept <mention>` - Accepts a battle invitation from a user"
                               "\n`cancel` - Cancels an invitation to battle"
                               "\n\n**How it works**"
                               "\n__Swiss-like Style tournament__"
                               "\nIn each round, you will battle your opponent in a best of three pvp. "
                               "You may switch classes and spells in between battles. "
                               "You must play all three battles, any battle missed will count as a loss."
                               "\nTo win a battle, you must deplete your opponent's mana/health to 0. "
                               "If both reach 0 on the same turn, it is a draw."
                               "\nFailure to turn up to a round, or too many losses, and you will be eliminated."
                               "\n__Special Rules__"
                               "\nAbilities are banned."
                               "\nYou will fight with Iron Scythe and Iron Shield and max level."
                               "\nYou may not use the same class twice in a round."
                               "\n\n**Rewards**"
                               "\nPlayers received various rewards based on their position, "
                               "including **Coins** "+EMOJI['coin']+", **rubies** "+EMOJI['ruby']+", "
                               "**chests** "+EMOJI['chest']+" and **crowns** "+EMOJI['crown']+" for all participants."
                               "\nFor the top three, a random new spell for the newly released **Elf** 🍂 "
                               "(or the class itself) was given."
                               "\nThe winner received **the winner** cosmetic title."},
                   {'title': "🥚 Easter 2021 - Tower of Beginnings",
                    'content': "**Commands**"
                               "\n`start` - Begins party searching for a Tower Quest"
                               "\n`top` - Displays the top 10 players with the highest floor count"
                               "\n\n**How it works**"
                               "\nWhen searching, you must be one of the three starter classes:"
                               "\n👐 Arcane"
                               "\n☘️ Druid"
                               "\n🌸 Warden"
                               "\nOnly one of each type is allowed per quest. "
                               "\nYou begin with just the starter spells and wooden items, no abilities. "
                               "\nEach time you clear a floor, you can pick one of three rewards. "
                               "Either an item level/material upgrade, new spell or ability."
                               "\nRemember, you can only carry up to 4 spells, so if you overwrite one, it's gone. "
                               "Abilities last for one floor, but you can still gain and use them after use. "
                               "Item upgrades persist, even if the material changes. "
                               "\nAs a fun bonus, stuns work on bosses, and can be used on you too! "
                               "\n\n**Ticket System**"
                               "\nThis was also the first time including a ticket system in the game. "
                               "Each entry into the tower cost a ticket. "
                               "Each player could earn more tickets by voting for the server and bot on top.gg, "
                               "event earning double tickets on weekends."
                               "\n\n**Event Rewards**"
                               "\n**Coins** "+EMOJI['coin']+", **rubies** "+EMOJI['ruby']+" and "
                               "**keys** "+EMOJI['key']+" were given for reach floor `1`."
                               "\n**Crowns** "+EMOJI['crown']+" were given for reaching floors `2`, `4`, `6` and `8`."
                               "\nVarious cosmetics were also granted:"
                               "\nFloor `3` - '🥚' title"
                               "\nFloor `5` - Egg embed image"
                               "\nFloor `7` - Spring green embed color (0x00ff7f)"
                               "\nFloor `10` - 'the Golden Egg' title"}]}]

WIKILINK = "https://greenfoot5.github.io/Enchanted-Docs/"

print("Config loaded")
