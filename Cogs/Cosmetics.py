import Config
import discord
from discord.ext import commands
import Utils
from Paginator import EmbedPaginatorSession


class Cosmetics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['cosmetic', 'titles', 't', 'colors'])
    async def cosmetics(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if account['selected_embed_image'] is not None:
            image = account['selected_embed_image']["name"]
        else:
            image = None
        desc = "**Selected Title:** " + str(account['selected_title']) + "\n**Selected Profile Color:** "+str(account['selected_embed_color']["name"])+"\n**Selected Profile Image:** "+str(image)+"\n\n"
        prefix = Utils.fetch_prefix(ctx)
        titles = discord.Embed(title="Cosmetics | Titles", description="", color = Config.MAINCOLOR)
        titles.description += desc
        emotes = discord.Embed(title="Cosmetics | Emotes", description="", color = Config.MAINCOLOR)
        emotes.description += desc
        images = discord.Embed(title="Cosmetics | Embed Images", description="", color = Config.MAINCOLOR)
        images.description += desc
        colors = discord.Embed(title="Cosmetics | Embed Colors", description="", color = Config.MAINCOLOR)
        colors.description += desc
        
        titles.set_footer(text=f"Get more cosmetics from {prefix}shop | use {prefix}select title <index> to select a title to use")
        emotes.set_footer(text=f"Get more cosmetics from {prefix}shop | use {prefix}chat <index> to chat during battle")
        images.set_footer(text=f"Get more cosmetics from {prefix}shop | use {prefix}select image <index> to select a embed image to use")
        colors.set_footer(text=f"Get more cosmetics from {prefix}shop | use {prefix}select color <index> to select a embed color to use")

        tit = 0
        emo = 0
        col = 0 
        img = 0
        for cosmetic in account['cosmetics']:
            if cosmetic['type'] == "title":
                tit += 1
                titles.description += "> " + str(tit) + f" | `{cosmetic['value']}` \n"
            elif cosmetic['type'] == "emote":
                emo += 1
                emotes.description += "> " + str(emo) + f" | {cosmetic['value']} \n"
            if cosmetic['type'] == "image":
                img += 1
                images.description += "> " + str(img) + f" | `{cosmetic['name']}` \n"
            if cosmetic['type'] == "color":
                col += 1
                colors.description += "> " + str(col) + f" | `{str(cosmetic['name'])}` \n"

        if msg is None:
            paginator = EmbedPaginatorSession(ctx, titles, emotes, images, colors)
            await paginator.run()
        else:
            await msg.edit(embed=titles)

    @commands.group()
    async def select(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = Utils.fetch_prefix(ctx)
            embed = discord.Embed(title="Select", color=Config.MAINCOLOR, description=f"Branches:\n `{prefix}select title (number of title you want to select)`\n`{prefix}select image (number of embed image you want to select)`\n`{prefix}select color (number of embed color you want to select)`")
            await ctx.send(embed=embed)

    @select.command()
    async def title(self, ctx, choice:str=None): 
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            embed = discord.Embed(title="Hmmmm...", description="Please type a number.", color = Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            choice = int(choice)
            titles = []
            for cosmetic in account['cosmetics']:
                if cosmetic['type'] == 'title':
                    titles.append(cosmetic)
            if choice > len(titles) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(len(titles)) + " Titles. Try using a number 1-" + str(len(titles)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                account['selected_title'] = titles[choice]['value']
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'selected_title': account['selected_title']}})
            embed = discord.Embed(title="Title Selected", description="You have changed your title to **" + account['selected_title'] + "**",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...", description="Thats not a title index. Try using a number 1-" + str(len(titles)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @select.command()
    async def image(self, ctx, choice:str=None): 
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            embed = discord.Embed(title="Hmmmm...", description="Please type a number.", color = Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            choice = int(choice)
            images = []
            for cosmetic in account['cosmetics']:
                if cosmetic['type'] == 'image':
                    images.append(cosmetic)
            if choice > len(images) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(len(images)) + " Images. Try using a number 1-" + str(len(images)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                account['selected_embed_image'] = {'name': str(images[choice]['name']), 'value': str(images[choice]['value'])}
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'selected_embed_image': account['selected_embed_image']}})
            embed = discord.Embed(title="Image Selected", description="You have changed your Embed Image to **" + account['selected_embed_image']["name"] + "**",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...", description="Thats not a image index. Try using a number 1-" + str(len(images)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @select.command()
    async def color(self, ctx, choice:str=None): 
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            embed = discord.Embed(title="Hmmmm...", description="Please type a number.", color = Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            choice = int(choice)
            colors = []
            for cosmetic in account['cosmetics']:
                if cosmetic['type'] == 'color':
                    colors.append(cosmetic)
            if choice > len(colors) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(len(colors)) + " Colors. Try using a number 1-" + str(len(colors)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                account['selected_embed_color'] = {'name': str(colors[choice]['name']), 'value': str(colors[choice]['value'])}
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'selected_embed_color': account['selected_embed_color']}})
            embed = discord.Embed(title="Color Selected", description="You have changed your Embed Color to **" + account['selected_embed_color']["name"] + "**",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...", description="Thats not a color index. Try using a number 1-" + str(len(colors)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @commands.command(aliases=['crown', 'donate'])
    async def crowns(self, ctx):
        # embed = discord.Embed(title="Crowns", description="Please type the number by the amount you want\n```md\n1. <$1.00> 100 Crowns\n2. <$5.00> 600 Crowns (100 bonus)\n3. <$10.00> 1,300 Crowns (300 bonus)\n4. <$50.00> 7,500 Crowns (2,500 bonus)\n```", color = Config.MAINCOLOR)
        # og_message = await ctx.send(embed=embed)
        # def check(msg):
        #     return msg.channel.id == og_message.channel.id and msg.author.id == og_message.author.id
        # try:
        #     msg = await self.bot.wait_for('message', timeout=200, check=check)

        #     if
        # except asyncio.TimeoutError:
        #     await og_message.delete()

        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        
        embed = discord.Embed(
            title="Crowns", 
            description="You currently have: **" + str(account["crowns"]) + "** " + Config.EMOJI["crown"] + f" crowns\nCrowns can be used to buy cosmetic items.  You can gain for free through season resets and events. You can also gain a lot of crowns by donating. Check `{ctx.prefix}wiki donating` for more info!",
            color=Config.MAINCOLOR
        )
        
        if msg is None:
            await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        return


def setup(bot):
    bot.add_cog(Cosmetics(bot))