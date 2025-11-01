import discord
from discord import app_commands
from discord.ext import commands


class RoleDropdown(discord.ui.Select):
    def __init__(self, roles: list[discord.Role], select_type: str):
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles
        ]

        max_values = 1 if select_type.lower() == "single" else len(roles)
        placeholder = "Select your roles..." if max_values > 1 else "Select one role..."

        # Persist view by including all role IDs in custom_id
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=max_values,
            options=options,
            custom_id=f"role_dropdown_{select_type.lower()}_" + "_".join([str(r.id) for r in roles])
        )

    async def callback(self, interaction: discord.Interaction):
        selected_roles = [
            discord.utils.get(interaction.guild.roles, id=int(value))
            for value in self.values
        ]
        user = interaction.user
        added, removed = [], []

        # If single, remove other roles first
        if self.max_values == 1:
            for opt in self.options:
                r = discord.utils.get(interaction.guild.roles, id=int(opt.value))
                if r in user.roles and r not in selected_roles:
                    await user.remove_roles(r)
                    removed.append(r.name)

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

        await interaction.response.send_message("\n".join(msg) or "No changes.", ephemeral=True)


class RoleSelector(discord.ui.View):
    def __init__(self, roles: list[discord.Role], select_type: str):
        super().__init__(timeout=None)
        self.add_item(RoleDropdown(roles, select_type))


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.views_added = False

    @app_commands.command(name="create_role_selector", description="Create a role selector embed")
    @app_commands.describe(
        type="Choose 'single' (radio) or 'multiple' (checkbox).",
        message="The message displayed above the dropdown.",
        roles="Mention one or more roles separated by spaces."
    )
    async def create_role_selector(
        self,
        interaction: discord.Interaction,
        type: str,
        message: str,
        roles: str
    ):
        if interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("❌ Only the server owner can use this command.", ephemeral=True)

        role_ids = [int(r[3:-1]) for r in roles.split() if r.startswith("<@&") and r.endswith(">")]
        role_objs = [interaction.guild.get_role(rid) for rid in role_ids if interaction.guild.get_role(rid)]

        if not role_objs:
            return await interaction.response.send_message("❌ You must mention at least one valid role.", ephemeral=True)

        if type.lower() not in ["single", "multiple"]:
            return await interaction.response.send_message("❌ Type must be `single` or `multiple`.", ephemeral=True)

        embed = discord.Embed(title="Role Selector", description=message, color=discord.Color.blurple())
        view = RoleSelector(role_objs, type)

        sent_msg = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Role selector created!", ephemeral=True)

        # Register view persistently
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
                                        select_type = "single" if "single" in comp.custom_id else "multiple"
                                        role_ids = [int(v) for v in comp.custom_id.split("_")[3:]]
                                        roles = [
                                            discord.utils.get(guild.roles, id=r)
                                            for r in role_ids
                                            if discord.utils.get(guild.roles, id=r)
                                        ]
                                        if roles:
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
