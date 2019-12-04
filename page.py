"""
Made by catzoo
Description:
    Basically used to go through pages.
"""
import discord
import asyncio


class EmbedPage:
    """
    Similar to class Page, only more simpler and only helps with
    embed fields
    """

    def __init__(self, max_fields=25, max_fields_title=256, max_fields_value=1024,
                 color=discord.Colour.default()):
        self.max_fields = max_fields
        self.max_fields_title = max_fields_title
        self.max_fields_value = max_fields_value
        self._pages = []
        self.embed = discord.Embed()
        self.colour = color

    def add_field(self, title, value, inline=False):
        if len(title) > self.max_fields_title:
            value = title[self.max_fields_title:]
            title = title[:self.max_fields_title]

        while len(value) > self.max_fields_value:
            self.embed.add_field(name=title, value=value[:self.max_fields_value], inline=inline)

            if len(self.embed.fields) == self.max_fields:
                self._pages.append(self.embed)
                self.embed = discord.Embed()

        self.embed.add_field(name=title, value=value[:self.max_fields_value], inline=inline)
        if len(self.embed.fields) == self.max_fields:
            self._pages.append(self.embed)
            self.embed = discord.Embed()

    def pages(self):
        if self.embed.fields:
            self._pages.append(self.embed)
        return self._pages


class Page:
    """
    Basically input a string (add_line) and it will
    add it to the page(s).
    If it goes over the maximum, it will create a new page
    and add the line.

    If the string is too big (example: over 2000), it will
    cut the string to where its below the maximum.
    But if the line is under the maximum, it will
    add the line to the next page
    """

    def __init__(self, maximum=2000):
        self.maximum = maximum
        # temp_string, used to keep track of the next page
        self.string = ''
        self._pages = []  # list of pages

    def add_line(self, line):
        # checking if the line + string will be too big
        # string should already be below the maximum
        # so if string + line is too big, we'll just
        # add it to the pages
        line += '\n'
        if len(self.string) + len(line) > self.maximum:
            if self.string:
                self._pages.append(self.string)
                self.string = ''
            while len(line) > self.maximum:
                string = line[:self.maximum]
                line = line[self.maximum:]
                self._pages.append(string)
            self.string = line
        else:
            self.string += line

    def add_page(self, string):
        if self.string:
            self._pages.append(self.string)
            self.string = ''

        if len(string) > self.maximum:
            self.add_line(string)
        else:
            self._pages.append(string)

    def pages(self):
        if self.string:
            self._pages.append(self.string)
            self.string = ''
        return self._pages


class Paginator:
    def __init__(self, bot, ctx, pages, footer=None, set_footer=True):
        self.ctx = ctx
        self.pages = pages
        self.page_number = 0
        self.bot = bot
        self.footer = footer
        self.set_footer = set_footer

    def get_page(self):
        """
        Gets the page depending on self.pages[self.page_number]
        
        returns: discord.Embed"""
        def add_footer(embed2):
            if self.footer is None and self.set_footer:
                embed2.set_footer(text=f'Page: {self.page_number + 1} / {len(self.pages)}')
            elif self.set_footer:
                embed2.set_footer(text=f'{self.footer} - Page: {self.page_number + 1} / {len(self.pages)}')
            return embed2

        if isinstance(self.pages[self.page_number], discord.Embed):
            embed = self.pages[self.page_number]
            embed = add_footer(embed)
            return embed

        embed = discord.Embed(description=self.pages[self.page_number])
        embed.colour = discord.Colour.blue()
        embed = add_footer(embed)

        return embed

    """
    Page Controls
    """

    def next_page(self):
        max_pages = len(self.pages) - 1
        if self.page_number < max_pages:
            self.page_number += 1

    def opposite_of_next_page(self):
        if self.page_number > 0:
            self.page_number -= 1

    def last_page(self):
        self.page_number = len(self.pages) - 1

    def first_page(self):
        self.page_number = 0

    async def start(self):
        """
        Basically starts the loop
        Will output a message to the channel,
        depending on the context. Then will wait for the user
        to react / respond and change the pages depending on the reaction
        """

        def check(reaction, user):
            return user == self.ctx.author

        if not self.pages:
            await self.ctx.send('List is empty')
        else:
            msg = await self.ctx.send(embed=self.get_page())
            try:
                # if len(self.pages) == 1:
                # can't really do much with one page
                # await msg.add_reaction('☑')
                # reaction, _ = await self.bot.wait_for('reaction_add', check=check, timeout=120.0)
                # await msg.delete()
                # else:
                if len(self.pages) > 1:
                    await msg.add_reaction('⏪')
                    await msg.add_reaction('◀')
                    await msg.add_reaction('▶')
                    await msg.add_reaction('⏩')
                    await msg.add_reaction('☑')
                    while True:
                        reaction, _ = await self.bot.wait_for('reaction_add', check=check, timeout=120.0)
                        if str(reaction.emoji) == '◀':
                            self.opposite_of_next_page()
                            await msg.edit(embed=self.get_page())

                        elif str(reaction.emoji) == '▶':
                            self.next_page()
                            await msg.edit(embed=self.get_page())

                        elif str(reaction.emoji) == '⏪':
                            self.first_page()
                            await msg.edit(embed=self.get_page())

                        elif str(reaction.emoji) == '⏩':
                            self.last_page()
                            await msg.edit(embed=self.get_page())

                        elif str(reaction.emoji) == '☑':
                            break
                    await msg.delete()
            except asyncio.TimeoutError:
                embed = self.get_page()
                embed.description += '⚠ - Timeout Error'
                await msg.remove_reaction('◀', self.ctx.me)
                await msg.remove_reaction('▶', self.ctx.me)
                await msg.remove_reaction('☑', self.ctx.me)
                await msg.remove_reaction('⏪', self.ctx.me)
                await msg.remove_reaction('⏩', self.ctx.me)
                await msg.edit(embed=embed)
