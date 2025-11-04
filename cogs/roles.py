import discord
from discord import app_commands
from discord.ext import commands
import uuid


# ------------------------- UI COMPONENTS -------------------------

class RoleDropdown(discord.ui.Select):
    def __init__(self, roles: list[discord.Role], select_type: str):
        self.roles = roles
        self.select_type = select_type.lower()

        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles
        ]

        max_values = 1 if self.select_type == "single" else len(roles)
        placeholder = (
            "🎭 Select your roles..."
            if max_values > 1
            else "🎯 Choose one role..."
        )

        unique_id = str(uuid.uuid4())[:8]

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=max_values,
            options=options,
            custom_id=f"role_dropdown_{unique_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_roles = [
            discord.utils.get(interaction.guild.roles, id=int(value))
            for value in self.values
        ]
        user = interaction.user
        added, removed = [], []

        # If single-select, remove other roles
        if self.max_values == 1:
            for opt in self.options:
                role = discord.utils.get(interaction.guild.roles, id=int(opt.value))
                if role in user.roles and role not in selected_roles:
                    await user.remove_roles(role)
                    removed.append(role.name)

        # Toggle selected roles
        for role in selected_roles:
            if role in user.roles:
                await user.remove_roles(role)
                removed.append(role.name)
            else:
                await user.add_roles(role)
                added.append(role.name)

        msg = []
        if added:
            msg.append(f"✅ Added: {', '.join(added)}")
        if removed:
            msg.append(f"❌ Removed: {', '.join(removed)}")

        await interaction.response.send_message(
            "\n".join(msg) or "No changes made.",
            ephemeral=True
        )


class RoleSelector(discord.ui.View):
    def __init__(self, roles: list[discord.Role], select_type: str):
        super().__init__(timeout=None)
        self.add_item(RoleDropdown(roles, select_type))


# ------------------------- COMMAND GROUP -------------------------

class RoleSelectorGroup(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="role_selector", description="Manage role selector embeds.")
        self.bot = bot

    async def _is_owner_or_admin(self, interaction: discord.Interaction) -> bool:
        owner_role = discord.utils.get(interaction.guild.roles, name="Owner")
        return (
            interaction.user == interaction.guild.owner
            or (owner_role and owner_role in interaction.user.roles)
        )

    # -------- CREATE --------
    @app_commands.command(name="create", description="Create a new role selector embed.")
    @app_commands.describe(
        type="Choose 'single' (radio) or 'multiple' (checkbox).",
        header="The title of the embed.",
        message="The message shown below the title.",
        roles="Mention one or more roles separated by spaces."
    )
    async def create_role_selector(
        self,
        interaction: discord.Interaction,
        type: str,
        header: str,
        message: str,
        roles: str
    ):
        if not await self._is_owner_or_admin(interaction):
            return await interaction.response.send_message(
                "❌ Only the **server owner** or members with the `Owner` role can use this.",
                ephemeral=True
            )

        role_ids = [
            int(r[3:-1]) for r in roles.split() if r.startswith("<@&") and r.endswith(">")
        ]
        role_objs = [
            interaction.guild.get_role(rid)
            for rid in role_ids
            if interaction.guild.get_role(rid)
        ]

        if not role_objs:
            return await interaction.response.send_message("❌ No valid roles found.", ephemeral=True)
        if len(role_objs) > 25:
            return await interaction.response.send_message("⚠️ Max **25 roles**.", ephemeral=True)
        if type.lower() not in ["single", "multiple"]:
            return await interaction.response.send_message("❌ Type must be `single` or `multiple`.", ephemeral=True)

        embed = discord.Embed(title=header, description=message, color=discord.Color.blurple())
        embed.set_footer(text=f"Selection mode: {'Single' if type.lower() == 'single' else 'Multiple'}")

        view = RoleSelector(role_objs, type)
        sent_msg = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Role selector created! [Jump to message](https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{sent_msg.id})",
            ephemeral=True
        )

        self.bot.add_view(view, message_id=sent_msg.id)

    # -------- UPDATE --------
    @app_commands.command(name="update", description="Update an existing role selector embed.")
    @app_commands.describe(
        message_id="The ID of the message you want to update.",
        type="Choose 'single' or 'multiple'.",
        header="The new title of the embed.",
        message="The new message shown below the title.",
        roles="Mention one or more roles separated by spaces."
    )
    async def update_role_selector(
        self,
        interaction: discord.Interaction,
        message_id: str,
        type: str,
        header: str,
        message: str,
        roles: str
    ):
        if not await self._is_owner_or_admin(interaction):
            return await interaction.response.send_message("❌ Only the server owner or @Owner can use this.", ephemeral=True)

        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except Exception:
            return await interaction.response.send_message("❌ Message not found.", ephemeral=True)

        role_ids = [int(r[3:-1]) for r in roles.split() if r.startswith("<@&") and r.endswith(">")]
        role_objs = [
            interaction.guild.get_role(rid)
            for rid in role_ids
            if interaction.guild.get_role(rid)
        ]

        if not role_objs:
            return await interaction.response.send_message("❌ No valid roles found.", ephemeral=True)
        if len(role_objs) > 25:
            return await interaction.response.send_message("⚠️ Max **25 roles**.", ephemeral=True)
        if type.lower() not in ["single", "multiple"]:
            return await interaction.response.send_message("❌ Type must be `single` or `multiple`.", ephemeral=True)

        embed = discord.Embed(title=header, description=message, color=discord.Color.blurple())
        embed.set_footer(text=f"Selection mode: {'Single' if type.lower() == 'single' else 'Multiple'}")

        new_view = RoleSelector(role_objs, type)
        await msg.edit(embed=embed, view=new_view)
        self.bot.add_view(new_view, message_id=msg.id)

        await interaction.response.send_message("✅ Role selector updated successfully.", ephemeral=True)

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

        if not found:
            return await interaction.response.send_message("⚠️ No role selectors found.", ephemeral=True)

        embed = discord.Embed(
            title=f"Role Selectors in #{interaction.channel.name}",
            description="\n".join(found),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------- CLEANUP --------
    @app_commands.command(name="cleanup", description="Remove broken or deleted role selector views.")
    async def cleanup_selectors(self, interaction: discord.Interaction):
        if not await self._is_owner_or_admin(interaction):
            return await interaction.response.send_message("❌ You lack permission.", ephemeral=True)

        removed = 0
        async for message in interaction.channel.history(limit=100):
            if message.author == interaction.client.user and message.components:
                valid = False
                for row in message.components:
                    for comp in row.children:
                        if isinstance(comp, discord.ui.Select) and comp.custom_id.startswith("role_dropdown_"):
                            valid = True
                if not valid:
                    try:
                        await message.delete()
                        removed += 1
                    except Exception:
                        pass

        await interaction.response.send_message(f"🧹 Cleanup complete — {removed} old/broken messages removed.", ephemeral=True)


# ------------------------- MAIN COG -------------------------

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.views_added = False
        self.bot.tree.add_command(RoleSelectorGroup(bot))

    async def setup_persistent_views(self):
        if self.views_added:
            return

        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                try:
                    async for message in channel.history(limit=50):
                        if message.author == self.bot.user and message.components:
                            for row in message.components:
                                for comp in row.children:
                                    if isinstance(comp, discord.ui.Select) and comp.custom_id.startswith("role_dropdown_"):
                                        roles = [
                                            discord.utils.get(guild.roles, id=int(o.value))
                                            for o in comp.options
                                            if discord.utils.get(guild.roles, id=int(o.value))
                                        ]
                                        roles = [r for r in roles if r]
                                        if roles:
                                            select_type = "single" if comp.max_values == 1 else "multiple"
                                            self.bot.add_view(RoleSelector(roles, select_type), message_id=message.id)
                    self.views_added = True
                except Exception:
                    continue

    @commands.Cog.listener()
    async def on_ready(self):
        await self.setup_persistent_views()
        print("✅ Persistent role selectors loaded.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
