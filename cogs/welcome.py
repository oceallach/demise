import discord
from discord.ext import commands
from discord import app_commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="create_role_selector",
        description="Owner-only: Create a dynamic role selection embed."
    )
    @app_commands.describe(
        selector_type="Type of selector: 'single' for one role, 'multiple' for multiple roles",
        header_message="Message or header shown at the top of the embed",
        roles="Roles to be selectable (tag each role)"
    )
    @app_commands.checks.has_role("Owner")
    async def create_role_selector(
        self,
        interaction: discord.Interaction,
        selector_type: str,
        header_message: str,
        roles: str  # This will be a string of role mentions separated by spaces
    ):
        # Validate selector type
        if selector_type.lower() not in ["single", "multiple"]:
            await interaction.response.send_message("❌ Selector type must be `single` or `multiple`.", ephemeral=True)
            return

        # Extract roles from mentions
        role_objects = []
        for role_mention in roles.split():
            if role_mention.startswith("<@&") and role_mention.endswith(">"):
                role_id = int(role_mention[3:-1])
                role = discord.utils.get(interaction.guild.roles, id=role_id)
                if role:
                    role_objects.append(role)

        if not role_objects:
            await interaction.response.send_message("❌ No valid roles found.", ephemeral=True)
            return

        # Create Select options
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in role_objects
        ]

        # Set max values based on selector type
        max_values = 1 if selector_type.lower() == "single" else len(options)

        # Dropdown view
        class RoleSelect(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(RoleDropdown())

        class RoleDropdown(discord.ui.Select):
            def __init__(self):
                super().__init__(
                    placeholder="Choose your role(s)...",
                    min_values=1,
                    max_values=max_values,
                    options=options
                )

            async def callback(self, interaction: discord.Interaction):
                # Remove all old roles from the user in this set
                for role in role_objects:
                    if role in interaction.user.roles:
                        await interaction.user.remove_roles(role)
                
                # Assign selected roles
                for role_id_str in self.values:
                    role = discord.utils.get(interaction.guild.roles, id=int(role_id_str))
                    if role:
                        await interaction.user.add_roles(role)

                await interaction.response.send_message("✅ Your roles have been updated!", ephemeral=True)

        embed = discord.Embed(
            title=header_message,
            description="Select your role(s) from the dropdown below.",
            colour=discord.Colour.blurple()
        )

        await interaction.response.send_message(embed=embed, view=RoleSelect())

async def setup(bot):
    await bot.add_cog(Welcome(bot))