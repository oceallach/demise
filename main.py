import os
import discord
from discord import app_commands, Colour
from discord.ext import commands
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ No DISCORD_TOKEN found in .env file.")

# --- Intents ---
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Role Definitions ---
SIZE_ORDER = ["Tiny", "Normal", "Giant", "Giantess"]
SPELLCASTER_ROLE = "Spellcaster"
DEAD_ROLE = "Dead"
OWNER_ROLE = "Owner"

ROLE_ORDER = [
    ("Tiny", Colour.yellow()),
    ("Normal", Colour.green()),
    ("Giant", Colour.blue()),
    ("Giantess", Colour.purple()),
    ("Dead", Colour.from_rgb(0, 0, 0)),
    ("Spellcaster", Colour(0x9b59b6)),
]

# --- Helper Functions ---
def get_size_rank(member):
    for rank, role in enumerate(SIZE_ORDER):
        if discord.utils.get(member.roles, name=role):
            return rank
    return -1

def has_role(member, role_name):
    return discord.utils.get(member.roles, name=role_name) is not None

# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print(f"⚠️ Failed to sync commands: {e}")

# --- Setup Roles Command ---
@bot.tree.command(name="setup_roles", description="Creates or updates all default roles for the RP system (Owner only).")
async def setup_roles(interaction: discord.Interaction):
    if not has_role(interaction.user, OWNER_ROLE):
        await interaction.response.send_message("❌ Only users with the @Owner role can do that.", ephemeral=True)
        return

    guild = interaction.guild
    existing_roles = {role.name: role for role in guild.roles}
    created = []

    for role_name, colour in ROLE_ORDER:
        if role_name in existing_roles:
            await existing_roles[role_name].edit(colour=colour)
        else:
            role = await guild.create_role(name=role_name, colour=colour)
            created.append(role_name)

    msg = "✅ Roles created: " + ", ".join(created) if created else "ℹ️ All roles updated successfully."
    await interaction.response.send_message(msg)

# --- Remove Roles Command ---
@bot.tree.command(name="remove_roles", description="Removes all roles created by the bot (Owner only).")
async def remove_roles(interaction: discord.Interaction):
    if not has_role(interaction.user, OWNER_ROLE):
        await interaction.response.send_message("❌ Only users with the @Owner role can do that.", ephemeral=True)
        return

    guild = interaction.guild
    removed = []

    for role_name, _ in ROLE_ORDER:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await role.delete()
            removed.append(role_name)

    msg = f"🗑️ Removed roles: {', '.join(removed)}" if removed else "ℹ️ No roles to remove."
    await interaction.response.send_message(msg)

# --- Core Size Interaction ---
async def size_interaction(interaction, user, action_word: str, success_verb: str, causes_death: bool = False):
    # Prevent self targeting
    if interaction.user.id == user.id:
        await interaction.response.send_message("😒 You can’t target yourself, silly.", ephemeral=True)
        return

    actor_rank = get_size_rank(interaction.user)
    target_rank = get_size_rank(user)

    if actor_rank == -1 or target_rank == -1:
        await interaction.response.send_message("❌ Both users must have size roles first.", ephemeral=True)
        return

    if actor_rank > target_rank:
        await interaction.response.send_message(f"💥 {interaction.user.mention} {success_verb} {user.mention}!")
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
@app_commands.describe(user="The user to step on")
async def step(interaction: discord.Interaction, user: discord.Member):
    await size_interaction(interaction, user, "step on", "has stepped on", causes_death=True)

@bot.tree.command(name="squish", description="Squish a smaller user.")
@app_commands.describe(user="The user to squish")
async def squish(interaction: discord.Interaction, user: discord.Member):
    await size_interaction(interaction, user, "squish", "has squished", causes_death=True)

@bot.tree.command(name="devour", description="Devour a smaller user.")
@app_commands.describe(user="The user to devour")
async def devour(interaction: discord.Interaction, user: discord.Member):
    await size_interaction(interaction, user, "devour", "has devoured", causes_death=True)

@bot.tree.command(name="pick_up", description="Pick up a smaller user.")
@app_commands.describe(user="The user to pick up")
async def pick_up(interaction: discord.Interaction, user: discord.Member):
    await size_interaction(interaction, user, "pick up", "has picked up")

@bot.tree.command(name="poke", description="Poke a smaller user.")
@app_commands.describe(user="The user to poke")
async def poke(interaction: discord.Interaction, user: discord.Member):
    await size_interaction(interaction, user, "poke", "has poked")

# --- Spellcaster Commands ---
@bot.tree.command(name="revive", description="Revive a dead user.")
@app_commands.describe(user="The user to revive")
async def revive(interaction: discord.Interaction, user: discord.Member):
    if not has_role(interaction.user, SPELLCASTER_ROLE):
        await interaction.response.send_message("❌ Only Spellcasters can revive!", ephemeral=True)
        return

    dead_role = discord.utils.get(interaction.guild.roles, name=DEAD_ROLE)
    if dead_role:
        await user.remove_roles(dead_role)
    await interaction.response.send_message(f"💫 {user.mention} has been revived!")

@bot.tree.command(name="change_size", description="Change a user's size role (Spellcaster only).")
@app_commands.describe(user="Target user", size_role="New size role")
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

# --- Info Command ---
@bot.tree.command(name="info", description="List all available commands.")
async def info(interaction: discord.Interaction):
    info_text = (
        "📘 **Thank you for using Demise!**\n\n"
        "**For Larger People**\n"
        "🔪 **Dangerous**\n"
        "`/step` - steps on user.\n"
        "`/squish` - squishes the user.\n"
        "`/devour` - devours the user.\n\n"
        "🎯 **Fun**\n"
        "`/poke` - pokes the user.\n"
        "`/pick_up` - picks up the user.\n\n"
        "**Spellcasters**\n"
        "`/revive` - revives the user.\n"
        "`/change_size` - changes the size of the user.\n"
    )
    await interaction.response.send_message(info_text, ephemeral=True)

# --- Invite Command ---
@bot.tree.command(name="invite", description="Get an invite link to add the bot.")
async def invite(interaction: discord.Interaction):
    app_info = await bot.application_info()
    invite_link = f"https://discord.com/oauth2/authorize?client_id={app_info.id}&permissions=8&scope=bot%20applications.commands"
    await interaction.response.send_message(
        f"🔗 **Invite Demise to your server:**\n{invite_link}",
        ephemeral=True
    )

# --- Run Bot ---
bot.run(TOKEN)
