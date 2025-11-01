import discord
from discord import app_commands

def register(bot: discord.Client, helpers: dict):
    get_size_rank = helpers["get_size_rank"]
    has_role = helpers["has_role"]
    SIZE_ORDER = helpers["SIZE_ORDER"]
    SPELLCASTER_ROLE = helpers["SPELLCASTER_ROLE"]
    DEAD_ROLE = helpers["DEAD_ROLE"]

    # --- Emoji map for different actions ---
    ACTION_EMOJIS = {
        "step": "👠",
        "squish": "🫠",
        "devour": "👄",
        "poke": "👉",
        "pick_up": "✋",
    }

    # --- Core Size Interaction ---
    async def size_interaction(
        interaction, 
        user, 
        action_word: str, 
        success_verb: str, 
        causes_death: bool = False, 
        emoji: str = "💥"
    ):
        if interaction.user.id == user.id:
            await interaction.response.send_message("😒 You can’t target yourself, silly.", ephemeral=True)
            return

        actor_rank = get_size_rank(interaction.user)
        target_rank = get_size_rank(user)

        if actor_rank == -1 or target_rank == -1:
            await interaction.response.send_message("❌ Both users must have size roles first.", ephemeral=True)
            return

        if actor_rank > target_rank:
            await interaction.response.send_message(f"{emoji} {interaction.user.mention} {success_verb} {user.mention}!")
            if causes_death:
                dead_role = discord.utils.get(interaction.guild.roles, name=DEAD_ROLE)
                if dead_role:
                    await user.add_roles(dead_role)
        else:
            await interaction.response.send_message(
                f"😬 {interaction.user.mention} tried to {action_word} {user.mention}... embarrassing."
            )

    # --- Giant Commands ---
    @bot.tree.command(name="step", description="Step on a smaller user.")
    async def step(interaction: discord.Interaction, user: discord.Member):
        await size_interaction(interaction, user, "step on", "has stepped on", causes_death=True, emoji=ACTION_EMOJIS["step"])

    @bot.tree.command(name="squish", description="Squish a smaller user.")
    async def squish(interaction: discord.Interaction, user: discord.Member):
        await size_interaction(interaction, user, "squish", "has squished", causes_death=True, emoji=ACTION_EMOJIS["squish"])

    @bot.tree.command(name="devour", description="Devour a smaller user.")
    async def devour(interaction: discord.Interaction, user: discord.Member):
        await size_interaction(interaction, user, "devour", "has devoured", causes_death=True, emoji=ACTION_EMOJIS["devour"])

    @bot.tree.command(name="pick_up", description="Pick up a smaller user.")
    async def pick_up(interaction: discord.Interaction, user: discord.Member):
        await size_interaction(interaction, user, "pick up", "has picked up", emoji=ACTION_EMOJIS["pick_up"])

    @bot.tree.command(name="poke", description="Poke a smaller user.")
    async def poke(interaction: discord.Interaction, user: discord.Member):
        await size_interaction(interaction, user, "poke", "has poked", emoji=ACTION_EMOJIS["poke"])

    # --- Spellcaster Commands ---
    @bot.tree.command(name="revive", description="Revive a dead user.")
    async def revive(interaction: discord.Interaction, user: discord.Member):
        if not has_role(interaction.user, SPELLCASTER_ROLE):
            await interaction.response.send_message("❌ Only Spellcasters can revive!", ephemeral=True)
            return

        dead_role = discord.utils.get(interaction.guild.roles, name=DEAD_ROLE)
        if dead_role:
            await user.remove_roles(dead_role)
        await interaction.response.send_message(f"💫 {user.mention} has been revived!")

    @bot.tree.command(name="change_size", description="Change a user's size role (Spellcaster only).")
    async def change_size(interaction: discord.Interaction, user: discord.Member, size_role: str):
        if not has_role(interaction.user, SPELLCASTER_ROLE):
            await interaction.response.send_message("❌ Only Spellcasters can do that!", ephemeral=True)
            return

        if size_role not in SIZE_ORDER:
            await interaction.response.send_message("⚠️ Invalid size role.", ephemeral=True)
            return

        for r in SIZE_ORDER:
            role = discord.utils.get(interaction.guild.roles, name=r)
            if role:
                await user.remove_roles(role)

        new_role = discord.utils.get(interaction.guild.roles, name=size_role)
        if new_role:
            await user.add_roles(new_role)
        await interaction.response.send_message(f"✨ {user.mention} is now {size_role} sized!")

    # --- Info (Embed Version) ---
    @bot.tree.command(name="info", description="List all available commands.")
    async def info(interaction: discord.Interaction):
        embed = discord.Embed(
            title="📘 Demise Command List",
            description="Your guide to all available powers.",
            colour=discord.Colour.purple()
        )

        embed.add_field(
            name="👑 **For Larger People**",
            value=(
                "🔪 **Dangerous**\n"
                f"{ACTION_EMOJIS['step']} `/step` — Step on a user.\n"
                f"{ACTION_EMOJIS['squish']} `/squish` — Squish a user.\n"
                f"{ACTION_EMOJIS['devour']} `/devour` — Devour a user.\n\n"
                "🎯 **Fun**\n"
                f"{ACTION_EMOJIS['poke']} `/poke` — Poke a user.\n"
                f"{ACTION_EMOJIS['pick_up']} `/pick_up` — Pick up a user.\n"
            ),
            inline=False
        )

        embed.add_field(
            name="✨ **For Spellcasters**",
            value=(
                "💫 `/revive` — Revive a dead user.\n"
                "🔮 `/change_size` — Change a user's size role.\n"
            ),
            inline=False
        )

        embed.set_footer(text="Thank you for using Demise 💀")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- Invite ---
    @bot.tree.command(name="invite", description="Get an invite link to add the bot.")
    async def invite(interaction: discord.Interaction):
        app_info = await bot.application_info()
        invite_link = (
            f"https://discord.com/oauth2/authorize?client_id={app_info.id}&permissions=8&scope=bot%20applications.commands"
        )
        embed = discord.Embed(
            title="🔗 Invite Demise",
            description=f"[Click here to invite Demise to your server]({invite_link})",
            colour=discord.Colour.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)