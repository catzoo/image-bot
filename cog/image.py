"""
created by catzoo
created on 11/9/2019
"""
import os
import typing

from datetime import datetime
from datetime import timedelta

import logging

import discord
from discord.ext import tasks, commands

import env_config
import asqlite
from random import randint
from checks import Checks
import page

__cog_name__ = 'image'
logger = logging.getLogger(__name__)


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

        # These are used for image_loops
        self.channel = None  # the text channel that the image is sent on
        self.image = None  # SQLite image that we sent
        self.image_sent = False  # if there is a image sent or not
        self.time = None  # used to keep track of the next time it will send

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
        time_every = env_config.image_time_every

        def get_date():
            # returns a timedelta object
            return self.time - datetime.now()

        def add_time():
            # This will add self.time depending on the mode (if time_every is None)
            # It will only add the time if its in the past (if days == -1)
            check = get_date()
            if check.days < 0:
                if time_every:
                    self.time += timedelta(hours=time_every[0], minutes=time_every[1])
                else:
                    self.time += timedelta(days=1)
                return True
            else:
                return False

        if self.time is None:
            # set self.time
            now = datetime.now()
            config_time = env_config.image_time
            # there are two modes, we determine that if time_every is None or not
            # config_time = [h, m, s]
            if time_every:
                config_time = [now.hour, config_time[0], config_time[1]]
            else:
                config_time = [config_time[0], config_time[1], 0]

            self.time = datetime(year=now.year, month=now.month, day=now.day,
                                 hour=config_time[0], minute=config_time[1], second=config_time[2])
            logging.info(f'Setting the time to {self.time}')
            # might be in the past, since the loop just started we don't want to instantly send an image
            while add_time():
                # some configuration may still have it in the past, so adding a while loop
                pass

        # starting image_loop if datetime is still in the past
        later = get_date()
        if later.days < 0:
            if self.image_sent:
                self.image_loop.cancel()
                await self.channel.send(embed=discord.Embed(title='Ran out of time!',
                                                            description=f'The answer was ``{self.image[2]}``',
                                                            color=discord.Color.red()))
            logging.info('Sending image')
            self.image_loop.start()

        # waiting until the next image send
        add_time()
        logging.info(f'Sending next image at {self.time}')
        self.image_before_loop.change_interval(seconds=get_date().total_seconds())

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

    async def get_member(self, id):
        c = await self.connection.cursor()
        await c.execute("SELECT * FROM users WHERE user_id=?", (id))

        member_data = await c.fetchone()
        if not member_data:
            await c.execute("INSERT INTO users VALUES (?, ?)", (id, 0))
            member_data = [id, 0]

        return member_data

    @commands.check(Checks.manager_check)
    @commands.command()
    async def user_edit(self, ctx, user: discord.Member, points):
        c = await self.connection.cursor()
        member_data = list(await self.get_member(user.id))

        try:
            if '+' in points:
                points = points.replace('+', '')
                member_data[1] += int(points)
            elif '-' in points:
                points = points.replace('-', '')
                member_data[1] -= int(points)
            else:
                member_data[1] = int(points)
        except ValueError:
            raise commands.BadArgument('Points only supports a number and optional ``+`` or ``-``. '
                                       'Examples: ``+2`` and ``3``')

        await c.execute("UPDATE users SET points=? WHERE user_id=?", (member_data[1], user.id))
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description=f'Edited {user.display_name}\'s points to ``{member_data[1]}``'))

    @commands.guild_only()
    @commands.command()
    async def top(self, ctx):
        c = await self.connection.cursor()
        await c.execute("SELECT * FROM users ORDER BY points")
        users = await c.fetchmany(10)
        users = users[::-1]  # reversing the list for the for loop

        embed = discord.Embed(title="Top 10 Users", color=discord.Color.blue())
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
        member = await self.get_member(ctx.author.id)

        embed = discord.Embed(color=discord.Color.blue(), description=f'Current score: {member[1]}')
        embed.set_author(name=ctx.author.display_name, icon_url=str(ctx.author.avatar_url))
        await ctx.send(embed=embed)

    @commands.command()
    async def time(self, ctx):
        """The next time the image will be sent at"""
        time_format = ''
        days = self.time.day - datetime.now().day

        if days == 0:
            time_format += 'Today at '
        elif days == 1:
            time_format += 'Tomorrow at '
        elif days > 1:
            time_format += '%b, %d, '
        elif days < 0:
            time_format += '[error] %b, %d, '
        time_format += '%I:%M %p (CST)'

        embed = discord.Embed(color=discord.Color.blue(), title='Next image will be sent at:')
        embed.description = self.time.strftime(time_format)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Image(bot))
