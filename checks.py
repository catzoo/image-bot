"""
Created by catzoo
Description: Discord.py role checks
"""
import os
import asqlite
import env_config


class NoDatabase(Exception):
    """Used for Checks.connection being None"""
    pass


# noinspection PyRedundantParentheses
class Checks:
    """
    This is used for discord.py checks
    Use:
        - developer_check(ctx)
            - Only checks for guild owner / debug_id(s)
        - manager_check(ctx)
            - Checks for level 3 roles / user check
        - moderator_check(ctx)
            - Checks for level 2 roles / user check
        - user_check(ctx)
            - Checks for level 1 roles / user check

    This will store roles in SQLite databases (location depending on env_config)
    """
    def __init__(self):
        self.connection = None

    @classmethod
    async def create(cls):
        """Creates the connection for the class
        Not doing this in __init__ since its async"""
        self = Checks()
        location = f'{env_config.data_folder}/mod.db'

        if not os.path.exists(location):
            conn = await asqlite.connect(location)
            c = await conn.cursor()
            await c.execute("CREATE TABLE roles (role_id integer NOT NULL, level integer)")
        else:
            conn = await asqlite.connect(location)

        self.connection = conn

        return self

    async def get_cursor(self):
        """Created this for use for most functions
        But can be used to execute commands to the database if needed"""
        if self.connection is None:
            raise NoDatabase('Checks is not created!')
        return await self.connection.cursor()

    async def add_role(self, role_id, level):
        """Adds the role to the database."""
        c = await self.get_cursor()
        await c.execute("INSERT INTO roles VALUES (?,?)", (role_id, level))

    async def remove_role(self, role_id):
        """Removes the role from the database."""
        c = await self.get_cursor()
        await c.execute("DELETE FROM roles WHERE role_id=?", (role_id))

    async def get_role(self, role_id):
        """Returns the role from the database.
        Might return None if it doesn't exist"""
        c = await self.get_cursor()
        await c.execute("SELECT * FROM roles WHERE role_id=?", (role_id))

        return await c.fetchone()

    async def get_all_roles(self):
        """Returns all the roles from the database
        Might return None if there aren't any"""
        c = await self.get_cursor()
        await c.execute("SELECT * FROM roles")

        return await c.fetchall()

    async def _role_check(self, role_id, level):
        """Checks if the role is in the database with correct level"""
        been_check = False
        role = await self.get_role(role_id)
        if role:
            if role[1] >= level:
                been_check = True

        return been_check

    async def _user_check(self, ctx):
        """See if its the guild's owner or the developer"""
        been_check = False

        if ctx.author.id in env_config.debug_id:
            been_check = True
        elif ctx.author == ctx.guild.owner:
            been_check = True

        return been_check

    async def _main_check(self, ctx, level):
        """Uses both _role_check and _user_check"""
        allow = False  # saying if the check passed or not

        c = await self.get_cursor()
        await c.execute("SELECT * FROM roles")

        if await self._user_check(ctx):
            allow = True
        else:
            for r in ctx.author.roles:
                if await self._role_check(r.id, level):
                    allow = True

        return allow

    @staticmethod
    async def developer_check(ctx):
        """Highest level check.
        Only checks for the developer or guild owner"""
        self = await Checks.create()
        return await self._user_check(ctx)

    @staticmethod
    async def manager_check(ctx):
        """Level 3 of role / user checking"""
        self = await Checks.create()
        return await self._main_check(ctx, 3)

    @staticmethod
    async def moderator_check(ctx):
        """Level 2 of role / user checking"""
        self = await Checks.create()
        return await self._main_check(ctx, 2)

    @staticmethod
    async def user_check(ctx):
        """Level 1 of role / user checking"""
        self = await Checks.create()
        return await self._main_check(ctx, 1)