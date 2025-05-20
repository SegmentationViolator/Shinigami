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

import os

import hikari
import arc

from utils import panic

bot = hikari.GatewayBot(
    os.environ.get("BOT_TOKEN") or panic("Environment variable $BOT_TOKEN is not set")
)
client = arc.GatewayClient(
    bot, default_enabled_guilds=[959662014475685918, 1261714203169914893]
)

@client.include
@arc.slash_command(
    "latency", "Display the average heartbeat latency of all started shards"
)
async def latency(ctx: arc.GatewayContext, /) -> None:
    await ctx.respond("`{}` ms".format(round(client.app.heartbeat_latency * 1000)))

client.load_extension("extensions.room")

bot.run()
