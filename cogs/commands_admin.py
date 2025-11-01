import discord
from discord import app_commands

def register(bot: discord.Client, helpers: dict):
    has_role = helpers["has_role"]
    SIZE_ORDER = helpers["SIZE_ORDER"]
    SPELLCASTER_ROLE = helpers["SPELLCASTER_ROLE"]
    DEAD_ROLE = helpers["DEAD_ROLE"]
    OWNER_ROLE = helpers["OWNER_ROLE"]

    # --- Roles Setup ---
    @bot.tree.command(name="roles_setup", description="Creates or updates all default roles for the RP system (Owner only).")
    async def roles_setup(interaction: discord.Interaction):
        if not has_role(interaction.user, OWNER_ROLE):
            await interaction.response.send_message("❌ Only users with the @Owner role can do that.", ephemeral=True)
            return

        guild = interaction.guild
        existing_roles = {role.name: role for role in guild.roles}
        created = []

        ROLE_ORDER = [
            ("Tiny", discord.Colour.yellow()),
            ("Normal", discord.Colour.green()),
            ("Giant", discord.Colour.blue()),
            ("Giantess", discord.Colour.purple()),
            ("Dead", discord.Colour.from_rgb(0, 0, 0)),
            (SPELLCASTER_ROLE, discord.Colour(0x9b59b6)),
        ]

        for role_name, colour in ROLE_ORDER:
            if role_name in existing_roles:
                await existing_roles[role_name].edit(colour=colour)
            else:
                role = await guild.create_role(name=role_name, colour=colour)
                created.append(role_name)

        msg = "✅ Roles created: " + ", ".join(created) if created else "ℹ️ All roles updated successfully."
        await interaction.response.send_message(msg)

    # --- Roles Remove ---
    @bot.tree.command(name="roles_remove", description="Removes all roles created by the bot (Owner only).")
    async def roles_remove(interaction: discord.Interaction):
        if not has_role(interaction.user, OWNER_ROLE):
            await interaction.response.send_message("❌ Only users with the @Owner role can do that.", ephemeral=True)
            return

        guild = interaction.guild
        removed = []

        for role_name in SIZE_ORDER + [DEAD_ROLE, SPELLCASTER_ROLE]:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await role.delete()
                removed.append(role_name)

        msg = f"🗑️ Removed roles: {', '.join(removed)}" if removed else "ℹ️ No roles to remove."
        await interaction.response.send_message(msg)