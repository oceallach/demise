import discord
from discord import app_commands
from discord.ext import commands

DEV_GUILD_ID = 1152640567445037140

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.synced = False  # prevent double-syncing

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.synced:
            await self.bot.wait_until_ready()
            try:
                synced = await self.bot.tree.sync(guild=discord.Object(id=DEV_GUILD_ID))
                print(f"✅ Auto-synced {len(synced)} slash commands with guild {DEV_GUILD_ID}")
                self.synced = True
            except Exception as e:
                print(f"❌ Auto-sync failed: {e}")

    @app_commands.command(
        name="sync",
        description="Sync slash commands with Discord (Owner-only, Dev Guild only)."
    )
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))
    @commands.is_owner()
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            synced = await self.bot.tree.sync(guild=discord.Object(id=DEV_GUILD_ID))
            await interaction.followup.send(f"✅ Synced {len(synced)} commands with Discord.")
        except Exception as e:
            await interaction.followup.send(f"❌ Sync failed: `{e}`")


async def setup(bot):
    await bot.add_cog(Sync(bot))
