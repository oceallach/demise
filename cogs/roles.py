import discord
from discord.ext import commands
from discord import app_commands

# ---------------- CONFIG ----------------
OWNER_ROLE_NAME = "Owners"   # Only members with this role can use the commands
# ----------------------------------------

class RoleDropdown(discord.ui.Select):
    def __init__(self, options, multiple: bool):
        max_values = len(options) if multiple else 1
        super().__init__(
            placeholder="Choose your role(s)...",
            min_values=0,
            max_values=max_values,
            options=[
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in options
            ],
            custom_id=f"role_dropdown_{'multi' if multiple else 'single'}"
        )

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild
        selected_roles = [guild.get_role(int(role_id)) for role_id in self.values]
        multiple = self.max_values > 1

        # remove unselected roles if single-select
        if not multiple:
            for option in self.options:
                role = guild.get_role(int(option.value))
                if role in member.roles and role not in selected_roles:
                    await member.remove_roles(role)

        for role in selected_roles:
            if role not in member.roles:
                await member.add_roles(role)

        await interaction.response.send_message(
            f"✅ Roles updated: {', '.join([r.name for r in selected_roles]) or 'none'}",
            ephemeral=True
        )

class RoleDropdownView(discord.ui.View):
    def __init__(self, roles, multiple: bool):
        super().__init__(timeout=None)
        self.add_item(RoleDropdown(roles, multiple))

class RoleSelector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _is_owner_or_admin(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        owner_role = discord.utils.get(interaction.guild.roles, name=OWNER_ROLE_NAME)
        return owner_role in interaction.user.roles if owner_role else False

    # -------- CREATE --------
    @app_commands.command(name="create", description="Create a role selector dropdown.")
    @app_commands.describe(
        roles="Mention the roles to include",
        multiple="Allow multiple selections (True/False)"
    )
    async def create_role_selector(self, interaction: discord.Interaction, roles: str, multiple: bool):
        if not await self._is_owner_or_admin(interaction):
            return await interaction.response.send_message("❌ You lack permission.", ephemeral=True)

        mentioned_roles = [role for role in interaction.message.role_mentions] if interaction.message else []
        if not mentioned_roles and roles:
            for word in roles.split():
                role_id = int(word.strip("<@&>")) if word.startswith("<@&") else None
                if role_id:
                    role = interaction.guild.get_role(role_id)
                    if role:
                        mentioned_roles.append(role)

        if not mentioned_roles:
            return await interaction.response.send_message("⚠️ Please mention at least one valid role.", ephemeral=True)

        embed = discord.Embed(
            title="🎭 Role Selector",
            description="Pick your roles below.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Selection mode: {'Multiple' if multiple else 'Single'}")

        view = RoleDropdownView(mentioned_roles, multiple)
        msg = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Role selector created! [Jump to message]({msg.jump_url})",
            ephemeral=True
        )

    # -------- LIST --------
    @app_commands.command(name="list", description="List all role selector messages in this channel.")
    async def list_role_selectors(self, interaction: discord.Interaction):
        if not await self._is_owner_or_admin(interaction):
            return await interaction.response.send_message("❌ You lack permission.", ephemeral=True)

        found = []
        async for message in interaction.channel.history(limit=100):
            if message.author == interaction.client.user and message.components:
                for row in message.components:
                    for comp in row.children:
                        if isinstance(comp, discord.ui.Select) and comp.custom_id.startswith("role_dropdown_"):
                            select_type = "Single" if comp.max_values == 1 else "Multiple"
                            link = f"[Jump](https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message.id})"
                            found.append(f"🆔 `{message.id}` — **{select_type}** ({len(comp.options)} roles) {link}")
            elif (
                message.author == interaction.client.user
                and message.embeds
                and message.embeds[0].footer
                and message.embeds[0].footer.text
                and "Selection mode:" in message.embeds[0].footer.text
            ):
                select_type = "Single" if "Single" in message.embeds[0].footer.text else "Multiple"
                link = f"[Jump](https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message.id})"
                found.append(f"🆔 `{message.id}` — **{select_type}** (Embed only) {link}")

        if not found:
            return await interaction.response.send_message("⚠️ No role selectors found.", ephemeral=True)

        embed = discord.Embed(
            title=f"Role Selectors in #{interaction.channel.name}",
            description="\n".join(found),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------- CLEANUP --------
    @app_commands.command(name="cleanup", description="Remove broken or orphaned role selectors in this channel.")
    async def cleanup_role_selectors(self, interaction: discord.Interaction):
        if not await self._is_owner_or_admin(interaction):
            return await interaction.response.send_message("❌ You lack permission.", ephemeral=True)

        deleted = 0
        async for message in interaction.channel.history(limit=100):
            if (
                message.author == interaction.client.user
                and (message.components or message.embeds)
                and (
                    (message.components and any(
                        isinstance(c, discord.ui.Select) and c.custom_id.startswith("role_dropdown_")
                        for row in message.components for c in row.children
                    ))
                    or (
                        message.embeds
                        and message.embeds[0].footer
                        and "Selection mode:" in message.embeds[0].footer.text
                    )
                )
            ):
                await message.delete()
                deleted += 1

        await interaction.response.send_message(f"🧹 Cleaned up {deleted} role selector message(s).", ephemeral=True)

async def setup_persistent_views(bot: commands.Bot):
    await bot.wait_until_ready()
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=100):
                    if (
                        message.author == bot.user
                        and message.embeds
                        and message.embeds[0].footer
                        and "Selection mode:" in message.embeds[0].footer.text
                    ):
                        multiple = "Multiple" in message.embeds[0].footer.text
                        roles = [r for r in guild.roles if r.name not in ("@everyone", OWNER_ROLE_NAME)]
                        await message.edit(view=RoleDropdownView(roles, multiple))
            except Exception:
                continue

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleSelector(bot))
    bot.loop.create_task(setup_persistent_views(bot))
