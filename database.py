import os
import asqlite


class DatabaseError(Exception):
    pass


class ImageDatabase:
    def __init__(self, db_location):
        self.connection = None  # sqlite connection made in setup
        self.db_location = db_location  # the file location of the database

    async def get_cursor(self):
        if self.connection is None:
            raise DatabaseError('No connection!')

        return await self.connection.cursor()

    async def setup(self):
        """Creates the connection"""
        conn = await asqlite.connect(self.db_location)
        if not os.path.exists(self.db_location):
            c = await conn.cursor()
            await c.execute("CREATE TABLE users (user_id integer NOT NULL PRIMARY KEY, points integer)")
            await c.execute("CREATE TABLE images (img_id integer NOT NULL PRIMARY KEY, url text, name text, "
                            "own integer)")

            await c.execute("CREATE TABLE adoptions (adopt_id integer NOT NULL PRIMARY KEY, owner integer, "
                            "image integer, FOREIGN KEY(owner) REFERENCES users(user_id), "
                            "FOREIGN KEY(image) REFERENCES images(img_id))")

            await c.execute("CREATE TABLE ignore (channel_id integer NOT NULL)")

        self.connection = conn

    """
    Images table
    """
    async def add_image(self, url, name, own=0):
        c = await self.get_cursor()
        await c.execute("INSERT INTO images (url, name, own) VALUES (?, ?, ?)", (url, name, own))
        # returning the ID since SQLite created it
        return c.get_cursor().lastrowid

    async def remove_image(self, img_id):
        c = await self.get_cursor()
        image = await self.get_image(img_id)
        # make sure it exists
        if image is None:
            return False
        else:
            await c.execute("DELETE FROM images WHERE img_id=?", (img_id))
            return True

    async def edit_image(self, img_id, url=None, name=None, own=None):
        c = await self.get_cursor()

        set_query = []  # will be used in query string
        query_vars = []  # used for sqlite to remove sql injects
        if url is not None:
            set_query.append("url=?")
            query_vars.append(url)
        if name is not None:
            set_query.append("name=?")
            query_vars.append(name)
        if own is not None:
            set_query.append("own=?")
            query_vars.append(own)

        # getting the query string, with set values and vars for sqlite
        set_query = ",".join(set_query)
        query_string = f"UPDATE images SET {set_query} WHERE img_id=?"
        query_vars = tuple(query_vars + [img_id])
        # executing
        await c.execute(query_string, query_vars)

    async def get_image(self, img_id):
        c = await self.get_cursor()
        await c.execute("SELECT * FROM images WHERE img_id=?", (img_id))
        image = await c.fetchone()

        if image is None:
            return
        else:
            return {
                'img_id': image[0],
                'url': image[1],
                'name': image[2],
                'own': image[3]
            }

    async def get_all_images(self, only_own=None):
        """Gets all the images
        If only_own is None, it will send all the images
        If only_own = True, it will send only images with owners
        If only_own = False, it will send only images without owners"""
        c = await self.get_cursor()

        query_string = "SELECT * FROM images"
        if only_own is not None:
            if only_own:
                query_string += " WHERE own != 0"
            else:
                query_string += " WHERE own = 0"

        await c.execute(query_string)
        raw_images = await c.fetchall()

        images = []
        for image in raw_images:
            images.append({
                'img_id': image[0],
                'url': image[1],
                'name': image[2],
                'own': image[3]
            })
        return images

    """
    Users table
    """

    async def add_member(self, user_id, points=0):
        c = await self.get_cursor()
        await c.execute("INSERT INTO users VALUES (?,?)", (user_id, points))

    async def remove_member(self, user_id):
        c = await self.get_cursor()
        await c.execute("DELETE FROM users WHERE user_id=?", (user_id))

    async def edit_member(self, user_id, points):
        c = await self.get_cursor()
        await c.execute("UPDATE users SET points=? WHERE user_id=?", (points, user_id))

    async def get_member(self, user_id):
        c = await self.get_cursor()
        await c.execute("SELECT * FROM users WHERE user_id=?", (user_id))
        member = await c.fetchone()

        if not member:
            # if we don't have a member saved, we can create it with 0 points
            await self.add_member(user_id)
            member = [user_id, 0]

        return {
            'user_id': member[0],
            'points': member[1]
        }

    async def get_all_members(self, order=''):
        """Gets all the members from the database
        Order argument can take "ASC", "DESC" or "" for no order
        It will add "ORDER BY {order}" in the query string

        It will return a list of members with dicts"""
        c = await self.get_cursor()
        query_string = "SELECT * FROM users"
        if order != '':
            query_string += f" ORDER BY points {order}"

        await c.execute(query_string)
        raw_members = await c.fetchall()

        members = []
        for member in raw_members:
            members.append({
                'user_id': member[0],
                'points': member[1]
            })

        return members

    async def add_member_points(self, user_id, points):
        """This will add the member's points by number of points (arg)"""
        member = await self.get_member(user_id)
        points = member['points'] + points
        await self.edit_member(user_id, points=points)

        return points

    """
    Ignore table
    """
    async def add_ignore(self, channel_id):
        """Add an ignore channel"""
        c = await self.get_cursor()
        await c.execute("INSERT INTO ignore VALUES (?)", (channel_id))

    async def remove_ignore(self, channel_id):
        """Remove the ignored channel"""
        c = await self.get_cursor()
        await c.execute("DELETE FROM ignore WHERE channel_id=?", (channel_id))

    async def get_ignore(self, channel_id):
        """mostly used to see if the channel is in the database"""
        c = await self.get_cursor()
        await c.execute("SELECT * FROM ignore WHERE channel_id=?", (channel_id))

        channel = await c.fetchone()
        if channel is None:
            return None
        else:
            return channel[0]

    async def get_all_ignore(self):
        """Gets all the ignored channels
        Returns its in a list so its easier to see if the channel
        is in the list rather than a dict"""
        c = await self.get_cursor()
        await c.execute("SELECT * FROM ignore")
        raw_ignore_channels = await c.fetchall()

        ignore_channels = []
        for ignore in raw_ignore_channels:
            ignore_channels.append(ignore[0])

        return ignore_channels

    """
    Adoptions table
    """
    async def add_adoption(self, img_id, member_id):
        """Insert an adoption to the database"""
        c = await self.get_cursor()
        await c.execute("INSERT INTO adoptions (owner, image) VALUES (?, ?)", (member_id, img_id))

    async def remove_adoption(self, adopt_id):
        """Delete the adoption from the database"""
        c = await self.get_cursor()
        await c.execute("DELETE FROM adoptions WHERE adopt_id=?", (adopt_id))

    async def edit_adoption(self, adopt_id, owner=None, image=None):
        """Edit an adoption. This will set owner or image values to something else"""
        c = await self.get_cursor()

        set_query = []  # will be used in query string
        query_vars = []  # used for sqlite to remove sql injects
        if owner is not None:
            set_query.append("owner=?")
            query_vars.append(owner)
        if image is not None:
            set_query.append("image=?")
            query_vars.append(image)

        # getting the query string, with set values and vars for sqlite
        set_query = ",".join(set_query)
        query_string = f"UPDATE adoptions SET {set_query} WHERE adopt_id=?"
        query_vars = tuple(query_vars + [adopt_id])
        # executing
        await c.execute(query_string, query_vars)

    async def get_adoptions(self, img_id=None, member_id=None):
        """Gets all the adoptions depending on img_id or member_id
        img_id and member_id will be used with the WHERE statement
        If both of these are None, all of the adoptions will be returned

        It will return:
        [ (for each adoption) {
            'adopt_id',
            'owner': {
                'user_id',
                'points'
            },
            'image': {
                'img_id',
                'url',
                'name',
                'own'
            },
        } ]
        """
        c = await self.get_cursor()

        query_where = []
        query_values = []
        if img_id:
            query_where.append(f'image=?')
            query_values.append(img_id)

        if member_id:
            query_where.append(f'owner=?')
            query_values.append(member_id)

        if query_where:
            query_where = ' AND '.join(query_where)
            query_where = f'WHERE {query_where}'

        query_string = "SELECT * FROM adoptions " \
                       "JOIN users u on adoptions.owner = u.user_id " \
                       "JOIN images i on adoptions.image = i.img_id " \
                       f"{query_where}"

        await c.execute(query_string, tuple(query_values))
        raw_adoptions = await c.fetchall()

        adoptions = []
        for adopt in raw_adoptions:
            adoptions.append({
                'adopt_id': adopt[0],
                'owner': {
                    'user_id': adopt[3],
                    'points': adopt[4]
                },
                'image': {
                    'img_id': adopt[5],
                    'url': adopt[6],
                    'name': adopt[7],
                    'own': adopt[8]
                },
            })
        if adoptions:
            return adoptions
        else:
            return None
