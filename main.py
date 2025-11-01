import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import threading
import http.server
import socketserver

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

# --- Load cogs (sync, etc.) ---
async def load_extensions():
    await bot.load_extension("cogs.sync")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await load_extensions()

# --- Dummy server for hosting ---
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Dummy server running on port {PORT}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- Run Bot ---
bot.run(TOKEN)
