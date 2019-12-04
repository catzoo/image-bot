"""
created by catzoo
created on 11/9/2019
"""
import os
import typing

from datetime import datetime
from datetime import timedelta

import discord
from discord.ext import tasks, commands

import env_config
import asqlite
from random import randint
from checks import Checks
import page

__cog_name__ = 'image'


# noinspection PyRedundantParentheses
class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # location of the database, not going to make this go off of __cog_name__ since its a database
        # if we change the cog's name, it would change the database
        self.database_location = f'{env_config.data_folder}/image.db'
        self.ready = False  # used to only make on_ready event run once
        self.connection = None  # SQLite database
        self.guild = None  # the main guild. This is grabbed in on_ready() event

        self.channel = None  # the text channel that the image is sent on
        self.image = None  # SQLite image that we sent
        self.image_sent = False  # if there is a image sent or not
        self.loop_started = False  # used to not send a message when the bot starts

    @staticmethod
    def url_check(url):
        """Checks if the image url is supported
            going to expand this a bit more later"""
        image_formats = [
            "jpeg", "jpg", "jfif",
            "tiff", "gif", "bmp",
            "png", "pnm", "heif", "bpg",
        ]
        format_type = url.split('.')[-1]
        if format_type in image_formats:
            return True
        else:
            return False

    @commands.Cog.listener()
    async def on_ready(self):
        """Making sure the SQLite database is setup
            Reason why this is in on_ready event is for async"""
        # only run once
        if not self.ready:
            if not os.path.exists(self.database_location):
                # database file is not made, so we will assume the database isn't setup
                conn = await asqlite.connect(self.database_location)
                c = await conn.cursor()
                await c.execute("CREATE TABLE users (user_id integer NOT NULL, points integer)")
                await c.execute("CREATE TABLE images (img_id integer NOT NULL PRIMARY KEY, url text, name text)")
                await c.execute("CREATE TABLE ignore (channel_id integer NOT NULL)")
            else:
                conn = await asqlite.connect(self.database_location)
            self.ready = True

            self.connection = conn  # database connection
            self.guild = self.bot.get_guild(env_config.main_guild)

            self.image_before_loop.start()

    @commands.check(Checks.manager_check)
    @commands.command()
    async def add_image(self, ctx, name, url: typing.Optional[str]):
        if ctx.message.attachments:
            url = ctx.message.attachments[0].url
        if url:
            if self.url_check(url):
                # adding the image
                name = name.lower()
                c = await self.connection.cursor()
                await c.execute("INSERT INTO images (url, name) VALUES (?, ?)", (url, name))

                img_id = c.get_cursor().lastrowid  # getting the id
                # sending the success message
                embed = discord.Embed()
                embed.description = 'Image added successfully'
                embed.colour = discord.Color.green()
                embed.set_footer(text=f'ID: {img_id}')
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed(description='Not supported URL or file type',
                                                   color=discord.Color.red()))
        else:
            await ctx.send(embed=discord.Embed(description='URL or attachment is required',
                                               color=discord.Color.red()))

    @commands.check(Checks.manager_check)
    @commands.command()
    async def remove_image(self, ctx, img_id: int):
        c = await self.connection.cursor()
        await c.execute("SELECT * FROM images WHERE img_id=?", (img_id))
        # make sure it exists
        if await c.fetchone():
            await c.execute("DELETE FROM images WHERE img_id=?", (img_id))
            await ctx.send(embed=discord.Embed(description=f"Successfully removed the image",
                                               color=discord.Color.green()))
        else:
            await ctx.send(embed=discord.Embed(description=f"I can't find that image",
                                               color=discord.Color.red()))

    @commands.check(Checks.manager_check)
    @commands.command()
    async def list_image(self, ctx):
        c = await self.connection.cursor()
        await c.execute("SELECT * FROM images")
        images = await c.fetchall()
        pages = []
        for image in images:
            embed = discord.Embed(description=f'ID - {image[0]}, Name - {image[2]}', color=discord.Color.blue())
            embed.set_image(url=image[1])
            pages.append(embed)
        paginator = page.Paginator(self.bot, ctx, pages)
        await paginator.start()

    @commands.check(Checks.manager_check)
    @commands.command()
    async def send_image(self, ctx):
        self.image_before_loop.restart(forced=True)

    # noinspection PyCallingNonCallable
    @tasks.loop()
    async def image_before_loop(self, forced=False):
        time = [17, 30]  # hour, minute (24 hours)

        def get_time(days):
            # gives back timedelta depending on the time
            now = datetime.now()
            time_to = datetime(now.year, now.month, now.day, hour=time[0], minute=time[1])
            time_to = time_to + timedelta(days=days)
            time_to = time_to - now
            return time_to

        if self.loop_started:
            image = self.image
            if self.image_sent:
                self.image_loop.cancel()
                channel = self.channel
                await channel.send(embed=discord.Embed(title='Ran out of time!',
                                                       description=f'The answer was ``{image[2]}``',
                                                       color=discord.Color.red()))
            # elif image:
            #     c = await self.connection.cursor()
            #     await c.execute("DELETE FROM images WHERE img_id=?", (image[0]))
            #     print(f'deleting {image[0]}')

            # not going to change self.image_sent since its going to be started again
            if env_config.debug:
                print('Sending image')
            self.image_loop.start()

        else:
            self.loop_started = True
            print('Starting image loop')

        # setting it up to where its 24 hours repeating. Basically once per day at a certain time
        later = get_time(days=0)
        if later.days < 0 or forced:  # if the time passed or we forced an image to be sent
            later = get_time(days=1)

        if env_config.debug:
            print(f'image_time - {later} - forced: {forced}')

        # changing the time then loop it again
        self.image_before_loop.change_interval(seconds=later.total_seconds())

    # noinspection PyCallingNonCallable
    @tasks.loop(count=1)
    async def image_loop(self):
        self.image_sent = True  # start of the task

        guild = self.guild
        prefix = self.bot.command_prefix

        c = await self.connection.cursor()
        await c.execute("SELECT * FROM images")

        # grabbing the list of Images
        image_list = await c.fetchall()

        # getting the ignored channels
        ignore_list = []
        await c.execute("SELECT * FROM ignore")
        for row in await c.fetchall():
            ignore_list.append(row[0])

        # getting all the text channels without the ignored channels
        channel_list = []
        for x in guild.channels:
            if isinstance(x, discord.TextChannel):
                if x.id not in ignore_list:
                    channel_list.append(x)

        # sending the image and waiting for a response
        if channel_list:  # making sure we got channels to send to
            if image_list:  # making sure we got images
                channel = channel_list[randint(0, len(channel_list) - 1)]  # grabbing a random text channel
                image = image_list[randint(0, len(image_list) - 1)]  # grabbing a random image

                self.channel = channel
                self.image = image

                # id, url, name - image[0], image[1], image[2]
                async def send_image():
                    embed = discord.Embed()
                    embed.title = "Guess the name of the image"
                    embed.set_footer(text=f'Image not showing? Do {prefix}refresh | ID - {image[0]}')
                    embed.set_image(url=image[1])
                    embed.colour = discord.Color.blue()
                    await channel.send(embed=embed)
                await send_image()

                def check(m):
                    return m.channel.id == channel.id and (m.content.lower() == image[2]
                                                           or m.content.lower() == f'{prefix}refresh')
                while True:
                    msg = await self.bot.wait_for('message', check=check)

                    if msg.content != f'{prefix}refresh':
                        await c.execute("SELECT * FROM users WHERE user_id=?", (msg.author.id))
                        user = await c.fetchone()
                        # making sure the user is in the database
                        if user:
                            await c.execute("UPDATE users SET points=? WHERE user_id=?", (user[1] + 1, msg.author.id))
                            points = user[1] + 1
                        else:
                            await c.execute("INSERT INTO users VALUES (?,?)", (msg.author.id, 1))
                            points = 1
                        embed = discord.Embed(title=f'{msg.author.display_name} got the answer',
                                              description=f'You received a point, you now have ``{points}`` '
                                                          f'points\n\n Answer was ``{image[2]}``',
                                              color=discord.Color.green())
                        await channel.send(embed=embed)
                        await c.execute("DELETE FROM images WHERE img_id=?", (image[0]))
                        print(f'deleting {image[0]}')
                        break
                    else:
                        await send_image()
            else:
                print("Can't send image, no images to send!")
        else:
            print("All Text channels are ignored or there isn't any text channels to send to!")

        self.image_sent = False

    @commands.command()
    async def refresh(self, ctx):
        """Refreshes the image"""
        # this actually refresh in the image_loop.
        # Adding this here so it doesn't error when trying to find the command
        pass

    async def ignore(self, channel, ignore):
        c = await self.connection.cursor()
        await c.execute("SELECT * FROM ignore WHERE channel_id=?", (channel.id))
        channel_ignore = await c.fetchone()

        if channel_ignore and not ignore:
            await c.execute("DELETE FROM ignore WHERE channel_id=?", (channel.id))
        elif not channel_ignore and ignore:
            await c.execute("INSERT INTO ignore VALUES (?)", (channel.id))

    @commands.check(Checks.manager_check)
    @commands.command(name='ignore')
    async def ignore_command(self, ctx, channel: discord.TextChannel, ignore=True):
        await self.ignore(channel, ignore)

        if ignore:
            embed = discord.Embed(description=f'Added {channel} to the ignore list')
        else:
            embed = discord.Embed(description=f'Removed {channel} to the ignore list')
        embed.set_footer(text=f'Use {ctx.prefix}ignore_list to see the list')
        embed.colour = discord.Color.green()

        await ctx.send(embed=embed)

    @commands.check(Checks.manager_check)
    @commands.command()
    async def ignore_all_but(self, ctx, channel: discord.TextChannel):
        for c in ctx.guild.channels:
            if isinstance(c, discord.TextChannel):
                await self.ignore(c, True)
        await self.ignore(channel, False)

        embed = discord.Embed(description=f'Ignoring everything but {channel}')
        embed.set_footer(text=f'Use {ctx.prefix}ignore_list to see the list')
        embed.colour = discord.Color.green()

        await ctx.send(embed=embed)

    @commands.check(Checks.manager_check)
    @commands.command()
    async def ignore_clear(self, ctx):
        for c in ctx.guild.channels:
            if isinstance(c, discord.TextChannel):
                await self.ignore(c, False)

        embed = discord.Embed(description=f'Cleared the ignore list')
        embed.set_footer(text=f'Use {ctx.prefix}ignore_list to see the list')
        embed.colour = discord.Color.green()

        await ctx.send(embed=embed)

    @commands.check(Checks.manager_check)
    @commands.command()
    async def ignore_list(self, ctx):
        c = await self.connection.cursor()
        channels = ''
        await c.execute("SELECT * FROM ignore")
        for row in await c.fetchall():
            soda_can = ctx.guild.get_channel(row[0])
            if soda_can:
                channels += f'- {soda_can.name}\n'
            else:
                await c.execute("DELETE FROM ignore WHERE channel_id=?", (row[0]))

        if channels:
            await ctx.send(embed=discord.Embed(description=f'Ignored channels:\n{channels}',
                                               color=discord.Color.blue()))
        else:
            await ctx.send(embed=discord.Embed(description=f'Ignore list is empty',
                                               color=discord.Color.blue()))

    @commands.guild_only()
    @commands.command()
    async def top(self, ctx):
        c = await self.connection.cursor()
        await c.execute("SELECT * FROM users ORDER BY points")
        users = await c.fetchmany(10)
        users = users[::-1]  # reversing the list for the for loop

        embed = discord.Embed(title="Top Users", color=discord.Color.blue())
        string = ''
        for k, x in enumerate(users):
            # 1 - ID, 2 - Points
            member = ctx.guild.get_member(x[0])
            if member:
                name = member.display_name
            else:
                name = f'``Member with ID {x[0]} not found``'
            string += f'{k + 1}: | {name} - ``{x[1]}``\n'

        embed.description = string

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command()
    async def me(self, ctx):
        c = await self.connection.cursor()
        await c.execute("SELECT * FROM users WHERE user_id=?", (ctx.author.id))

        member = await c.fetchone()
        if not member:
            await c.execute("INSERT INTO users VALUES (?, ?)", (ctx.author.id, 0))
            member = [None, 0]  # first one isn't used, but we get 2 in a list from the database
        embed = discord.Embed(color=discord.Color.blue(), description=f'Current score: {member[1]}')
        embed.set_author(name=ctx.author.display_name, icon_url=str(ctx.author.avatar_url))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Image(bot))
