import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import threading
import http.server
import socketserver
import asyncio
import traceback

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

def get_size_rank(member):
    for i, size in enumerate(SIZE_ORDER):
        if discord.utils.get(member.roles, name=size):
            return i
    return -1

def has_role(member, role_name):
    return discord.utils.get(member.roles, name=role_name) is not None

helpers = {
    "get_size_rank": get_size_rank,
    "has_role": has_role,
    "SIZE_ORDER": SIZE_ORDER,
    "SPELLCASTER_ROLE": SPELLCASTER_ROLE,
    "DEAD_ROLE": DEAD_ROLE,
    "OWNER_ROLE": OWNER_ROLE,
}

# --- Register command modules ---
import cogs.commands_user as commands_user
import cogs.commands_admin as commands_admin

commands_user.register(bot, helpers)
commands_admin.register(bot, helpers)

# --- Cog Loader with Logging ---
async def load_extensions():
    cogs_to_load = ["cogs.roles", "cogs.sync"]
    loaded = 0

    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            print(f"⚙️  Loaded cog: {cog}")
            loaded += 1
        except Exception as e:
            print(f"❌ Failed to load cog: {cog}\n{traceback.format_exc()}")

    await bot.tree.sync()
    print(f"✅ Slash commands synced. ({loaded}/{len(cogs_to_load)} cogs loaded successfully)")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# --- Dummy hosting server (for Repl.it/Render etc.) ---
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Dummy server running on port {PORT}")
        httpd.serve_forever()

# --- Main startup ---
def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()

    async def start_bot():
        await load_extensions()
        await bot.start(TOKEN)

    asyncio.run(start_bot())

if __name__ == "__main__":
    main()
