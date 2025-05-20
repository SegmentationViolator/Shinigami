# Shinigami - A Discord bot to automate the hosting of L's game
# Copyright (C) 2025  Segmentation Violator
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import enum

import hikari
import aiosqlite


@enum.unique
class Item(enum.IntEnum):
    """
    Represents an item in the game
    """

    MYTHICAL_CHOCOLATES = -1
    USED = 1
    GUN = 2
    USED_GUN = GUN + USED
    POISON = 4
    USED_POISON = POISON + USED
    BAT = 6
    USED_BAT = BAT + USED
    BUG = 8
    USED_BUG = BUG + USED
    VOTE_CANCELLOR = 10
    USED_VOTE_CANCELLOR = VOTE_CANCELLOR + USED
    VOTE_DOUBLER = 12
    USED_VOTE_DOUBLER = VOTE_DOUBLER + USED
    VOTE_MANIPULATOR = 14
    USED_VOTE_MANIPULATOR = VOTE_MANIPULATOR + USED

    def used(self) -> bool:
        match self:
            case Item.MYTHICAL_CHOCOLATES:
                return False
            case Item.USED:
                raise ValueError("Item.USED is not to be used as an item")
            case _:
                return self.value % 2 != 0


@enum.unique
class Role(enum.IntEnum):
    """
    Represents a role in the game
    """

    Neutral = 0
    L = 1
    Kira = 2
    Investigator = 3
    KiraWorshipper = 4


class GameState:
    """
    Represents the state of a game
    """

    __slots__ = ("phase", "round", "turn")

class Room:
    """
    Represents a room
    """

    __slots__ = ("host", "game_state")

    host: hikari.User
    "Discord user who manages this room"

    game_state: typing.Optional[GameState]
    "state of the ongoing game (if any)"

    def __init__(
        self, host: hikari.User, game_state: typing.Optional[GameState] = None
    ) -> None:
        self.host = host
        self.game_state = game_state

    @staticmethod
    async def fetch(
        connection: aiosqlite.Connection, host: hikari.User
    ) -> typing.Optional["Room"]:
        cursor: aiosqlite.Cursor = await connection.execute(
            "SELECT 1 FROM rooms WHERE host_id = ?", (host.id,)
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        game_state = None

        return Room(host, game_state)

    async def insert(self, connection: aiosqlite.Connection) -> None:
        await connection.execute(
            "INSERT INTO rooms (host_id) VALUES (?)", (self.host.id,)
        )

class Player:
    """
    Represents a player
    """

    __slots__ = ("user", "alias", "alive", "info", "item", "role")

    user: hikari.User
    "Discord user associated with this record"

    alias: str
    alive: bool
    "True if this user is alive else False"

    info: typing.Optional[str]
    "information provided to this player"

    item: typing.Optional[Item]
    ":class: Item provided to this player"

    role: Role
    ":class: Role assigned to this player"

    def __init__(
        self,
        user: hikari.User,
        alias: str,
        role: Role,
        alive: bool = True,
        info: typing.Optional[str] = None,
        item: typing.Optional[Item] = None,
    ) -> None:
        self.user = user
        self.alias = alias
        self.alive = alive
        self.info = info
        self.item = item
        self.role = role

    @staticmethod
    async def fetch(
        connection: aiosqlite.Connection, user: hikari.User
    ) -> typing.Optional["Player"]:
        cursor: aiosqlite.Cursor = await connection.execute(
            "SELECT alias, alive, info, item, role FROM players WHERE id = ?",
            (user.id,),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        (alias, alive, info, item, role) = row

        return Player(
            user, alias, Role(role), alive, info, None if item is None else Item(item)
        )

    async def insert(self, connection: aiosqlite.Connection, room: Room) -> None:
        await connection.execute(
            "INSERT INTO players (id, alias, alive, room_host, info, item, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                self.user.id,
                self.alias,
                self.alive,
                room.host.id,
                self.info,
                self.item,
                self.role,
            ),
        )

    async def update(self, connection: aiosqlite.Connection) -> None:
        await connection.execute(
            "UPDATE players SET alive = ?, item = ? WHERE id = ?",
            (
                self.alive,
                self.item,
                self.user.id,
            ),
        )

    def use_item(self) -> None:
        if self.item is None:
            raise ValueError("this player holds no item")
        self.item = Item(self.item + Item.USED)


class User:
    """
    Represents a user
    """

    __slots__ = ("user", "total_games", "wins", "xp")

    user: hikari.User
    "Discord user associated with this record"

    total_games: int
    "number of games this user has completed"

    wins: int
    "number of games this user has won"

    xp: int
    "experience points held by this user"

    def __init__(
        self,
        user: hikari.User,
        total_games: int = 0,
        wins: int = 0,
        xp: int = 0,
    ) -> None:
        self.user = user
        self.total_games = total_games
        self.wins = wins
        self.xp = xp

    @staticmethod
    async def fetch(
        connection: aiosqlite.Connection, user: hikari.User
    ) -> typing.Optional["User"]:
        """
        Fetch a user from the database

        :param connection: a connection to the database
        :param user: Discord user whose user record is to be fetched from the database
        """
        cursor: aiosqlite.Cursor = await connection.execute(
            "SELECT total_games, wins, xp FROM users WHERE id = ?", (user.id,)
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        (total_games, wins, xp) = row

        return User(user, total_games, wins, xp)

    async def insert(self, connection: aiosqlite.Connection) -> None:
        """
        Insert the user in the database

        :param connection: a connection to the database
        """
        await connection.execute(
            "INSERT INTO users (id, total_games, wins, xp) VALUES (?, ?, ?, ?)",
            (
                self.user.id,
                self.total_games,
                self.wins,
                self.xp,
            ),
        )

    async def update(self, connection: aiosqlite.Connection) -> None:
        """
        Update the user in the database

        :param connection: a connection to the database
        """
        await connection.execute(
            "UPDATE users SET total_games = ?, wins = ?, xp = ? WHERE id = ?",
            (
                self.total_games,
                self.wins,
                self.xp,
                self.user.id,
            ),
        )

    async def room_host_id(self, connection: aiosqlite.Connection) -> hikari.Snowflakeish | None:
        """
        Fetch the id of the host of the room that the user is currently in (if any)

        :param connection: a connection to the database
        """
        cursor: aiosqlite.Cursor = await connection.execute(
            "SELECT room_host FROM users WHERE id = ?", (self.user.id,)
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        host_id: int
        (host_id,) = row

        return host_id

    async def join_room(self, connection: aiosqlite.Connection, room: Room) -> None:
        """
        Add the user to a room

        :param connection: a connection to the database
        :param room: the room to be joined
        :raises KeyError: user doesn't exist in the databse
        :raises ValueError: attempting to join another room while being the host of a room
        """
        cursor: aiosqlite.Cursor = await connection.execute(
            "SELECT room_host FROM users WHERE id = ?", (self.user.id,)
        )
        row = await cursor.fetchone()

        if row is None:
            raise KeyError("user doesn't exist in the database")

        (host_id,) = row

        if host_id == self.user.id:
            raise ValueError("attempting to join another room while being the host of a room")

        await connection.execute(
            "UPDATE users SET room_host = ? WHERE id = ?",
            (
                room.host.id,
                self.user.id,
            ),
        )

    async def leave_room(self, connection: aiosqlite.Connection) -> None:
        """
        Leave the room that the user is currently in (if any)

        :param connection: connection to the database
        :raises KeyError: user doesn't exist in the databse
        :raises ValueError: attempting to leave the room while being the host
        """
        cursor: aiosqlite.Cursor = await connection.execute(
            "SELECT room_host FROM users WHERE id = ?", (self.user.id,)
        )
        row = await cursor.fetchone()

        if row is None:
            raise KeyError("user doesn't exist in the database")

        (host_id,) = row

        if host_id == self.user.id:
            raise ValueError("attempting to leave the room while being the host")

        await connection.execute(
            "UPDATE users SET room_host = NULL WHERE id = ?",
            (self.user.id,),
        )
