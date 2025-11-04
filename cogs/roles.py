import discord
from discord import app_commands
from discord.ext import commands
import uuid


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

        # Short unique custom_id — avoids exceeding Discord’s 100-char limit
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

        # If single-select, remove all other dropdown roles before adding
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


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.views_added = False

    @app_commands.command(
        name="create_role_selector",
        description="Create a custom role selector embed."
    )
    @app_commands.describe(
        type="Choose 'single' (radio) or 'multiple' (checkbox).",
        header="The title of the embed (e.g. 'Choose your region!').",
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
        # Owner-only restriction
        if interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                "❌ Only the server owner can use this command.",
                ephemeral=True
            )

        # Extract role IDs from mentions
        role_ids = [
            int(r[3:-1])
            for r in roles.split()
            if r.startswith("<@&") and r.endswith(">")
        ]
        role_objs = [
            interaction.guild.get_role(rid)
            for rid in role_ids
            if interaction.guild.get_role(rid)
        ]

        if not role_objs:
            return await interaction.response.send_message(
                "❌ You must mention at least one valid role.",
                ephemeral=True
            )

        if len(role_objs) > 25:
            return await interaction.response.send_message(
                "⚠️ You can only include up to **25 roles** (Discord limit).",
                ephemeral=True
            )

        if type.lower() not in ["single", "multiple"]:
            return await interaction.response.send_message(
                "❌ Type must be `single` or `multiple`.",
                ephemeral=True
            )

        # Embed with custom title + message
        embed = discord.Embed(
            title=header,
            description=message,
            color=discord.Color.blurple()
        )
        embed.set_footer(
            text=f"Selection mode: {'Single' if type.lower() == 'single' else 'Multiple'}"
        )

        view = RoleSelector(role_objs, type)
        sent_msg = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Role selector created!", ephemeral=True)

        # Register the view persistently
        self.bot.add_view(view, message_id=sent_msg.id)

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
                                        # Recover roles from dropdown options
                                        roles = [
                                            discord.utils.get(guild.roles, id=int(o.value))
                                            for o in comp.options
                                            if discord.utils.get(guild.roles, id=int(o.value))
                                        ]
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
