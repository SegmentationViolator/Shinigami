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

import typing

import aiosqlite
import arc
import hikari

from constants import PRIMARY_COLOR
from models import Player, Room, User

plugin = arc.GatewayPlugin("room")
group = plugin.include_slash_group("room", is_dm_enabled=False)

@group.include
@arc.slash_subcommand("create", "Create a room")
async def create(ctx: arc.GatewayContext, /) -> None:
    async with aiosqlite.connect("database.sqlite3") as connection:
        player = await Player.fetch(connection, ctx.user)
        room = await Room.fetch(connection, ctx.user)

        if room is not None:
            await ctx.respond("You already have a room")
            return

        if player is not None:
            await ctx.respond("You are already in a room")
            return

        room = Room(ctx.user)
        await room.insert(connection)

        user = await User.fetch(connection, ctx.user)

        if user is None:
            user = User(ctx.user)
            await user.insert(connection)

        await user.join_room(connection, room)

    await ctx.respond(
        f"A new room was created. Join using `/room join id:{ctx.user.id}`"
    )

@group.include
@arc.slash_subcommand("info", "Get information about a room")
async def info(
    ctx: arc.GatewayContext,
    /,
    host: arc.Option[
        hikari.User, arc.UserParams("ID of the room", name="id")
    ] = None,
) -> None:
    if is_host_none := host is None:
        host = ctx.user

    if host.is_bot:
        await ctx.respond("Room not found")
        return

    async with aiosqlite.connect("database.sqlite3") as connection:
        room = await Room.fetch(connection, host)

        if room is None:
            if not is_host_none:
                await ctx.respond("Room not found")
                return

            user = await User.fetch(connection, ctx.user)

            if user is None:
                await ctx.respond("You are not in a room")
                return

            host_id = await user.room_host_id(connection)

            if host_id is None:
                await ctx.respond("You are not in a room")
                return

            host = ctx.client.cache.get_user(host_id) or await ctx.client.rest.fetch_user(host_id)

    embed = hikari.Embed(color=PRIMARY_COLOR)
    embed.set_author(name="\u2022 Room information")
    embed.add_field(name="ID", value=str(host.id), inline=True)
    embed.set_footer(f"Host: {host.mention}")

    await ctx.respond(embed=embed)

@group.include
@arc.slash_subcommand("join", "Join a room")
async def join(
    ctx: arc.GatewayContext,
    /,
    host: arc.Option[
        hikari.User, arc.UserParams("ID of the room you wish to join", name="id")
    ],
) -> None:
    host = typing.cast(hikari.User, host)

    if host.is_bot:
        await ctx.respond("Room not found")
        return

    async with aiosqlite.connect("database.sqlite3") as connection:
        player = await Player.fetch(connection, ctx.user)

        if player is not None:
            await ctx.respond("You are already in a game that has started")
            return

        room = await Room.fetch(connection, host)

        if room is None:
            await ctx.respond("Room not found")
            return

        user = await User.fetch(connection, ctx.user)

        if user is None:
            user = User(ctx.user)
            await user.insert(connection)

        try:
            await user.join_room(connection, room)
        except ValueError:
            await ctx.respond(
                "You can't join another room while being the host of a room."
                "Make someone else the host using the `/room transfer` command or delete the room using `/room delete`"
            )

    await ctx.respond(
        f"Joined the room. Use `/room info id:{ctx.user.id}` for more details"
    )

@group.include
@arc.slash_subcommand("leave", "Leave the room that you are currently in")
async def leave(
    ctx: arc.GatewayContext,
    /,
) -> None:
    async with aiosqlite.connect("database.sqlite3") as connection:
        player = await Player.fetch(connection, ctx.user)

        if player is not None:
            await ctx.respond("You can't leave while in a game that has started")
            return

        user = await User.fetch(connection, ctx.user)

        if user is None:
            await ctx.respond("You are not in a room")
            return

        try:
            await user.leave_room(connection)
        except ValueError:
            await ctx.respond(
                "You can't leave the room while being the host."
                "Make someone else the host using the `/room transfer` command or delete the room using `/room delete`"
            )

    await ctx.respond("You are no longer in a room")


@arc.loader
def load(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)
