import discord
from discord.ext import commands, tasks
import os
import certifi
import aiohttp
import io
import base64
import re
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix SSL certificate issues on macOS by setting cert file path
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Configure Gemini API key (for image analysis)
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    # Try reloading .env file
    load_dotenv(override=True)
    gemini_api_key = os.getenv('GEMINI_API_KEY')

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for member join events

bot = commands.Bot(command_prefix='!', intents=intents)

# Track processed events to prevent duplicates
processed_members = set()

# Chat clear scheduling
chat_clear_enabled = True  # Set to False when !notclear is used
target_channel_id = 1440064713584279632  # Channel to clear and send warnings
warnings_sent = {'3days': False, '1day': False, '1hour': False, '1minute': False}  # Track sent warnings


@bot.event
async def on_ready():
    print(f'{bot.user} has logged in and is ready!')
    # Start the scheduled tasks
    if not check_chat_clear.is_running():
        check_chat_clear.start()


@tasks.loop(minutes=1)  # Check every minute for accurate 1-minute warnings
async def check_chat_clear():
    """Check if chat clear warnings or actual clear needs to happen"""
    global chat_clear_enabled, warnings_sent
    
    try:
        now = datetime.now()
        
        # Calculate next 1st of month
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1, 0, 0, 0)
        else:
            next_month = datetime(now.year, now.month + 1, 1, 0, 0, 0)
        
        days_until = (next_month - now).days
        hours_until = (next_month - now).total_seconds() / 3600
        
        # Get the target channel for warnings and clearing
        target_channel = bot.get_channel(target_channel_id)
        
        if not target_channel:
            return  # Can't proceed without channel
        
        # Check if it's time to clear (1st of month, midnight)
        if now.day == 1 and now.hour == 0 and now.minute < 5:  # Check within first 5 minutes
            if chat_clear_enabled:
                try:
                    # Delete all messages
                    deleted = await target_channel.purge(limit=None, check=lambda m: not m.pinned)
                    await target_channel.send(f"Chat cleared! Deleted {len(deleted)} messages.")
                except discord.Forbidden:
                    print("No permission to clear chat")
                except Exception as e:
                    print(f"Error clearing chat: {e}")
            
            # Reset for next month
            chat_clear_enabled = True
            warnings_sent = {'3days': False, '1day': False, '1hour': False, '1minute': False}
        
        # Check for warning dates (only if clear is enabled)
        elif chat_clear_enabled:
            # 3 days before (approximately 72 hours)
            if 2.5 <= days_until <= 3.5 and not warnings_sent['3days']:
                try:
                    await target_channel.send(f"⚠️ Chat clear scheduled: 3 days remaining. Channel will be cleared on {next_month.strftime('%B 1st, %Y at %I:%M %p')}.")
                    warnings_sent['3days'] = True
                except:
                    pass
            
            # 1 day before (approximately 24 hours)
            elif 0.5 <= days_until <= 1.5 and not warnings_sent['1day']:
                try:
                    await target_channel.send(f"⚠️ Chat clear scheduled: 1 day remaining. Channel will be cleared on {next_month.strftime('%B 1st, %Y at %I:%M %p')}.")
                    warnings_sent['1day'] = True
                except:
                    pass
            
            # 1 hour before (approximately 60 minutes)
            elif 58 <= hours_until <= 62 and not warnings_sent['1hour']:
                try:
                    await target_channel.send(f"⚠️ Chat clear scheduled: 1 hour remaining. Channel will be cleared on {next_month.strftime('%B 1st, %Y at %I:%M %p')}.")
                    warnings_sent['1hour'] = True
                except:
                    pass
            
            # 1 minute before (approximately 60 seconds)
            elif 0.8 <= hours_until <= 1.2 and not warnings_sent['1minute']:
                minutes_until = hours_until * 60
                if 58 <= minutes_until <= 62:
                    try:
                        await target_channel.send(f"⚠️ Chat clear scheduled: 1 minute remaining. Channel will be cleared on {next_month.strftime('%B 1st, %Y at %I:%M %p')}.")
                        warnings_sent['1minute'] = True
                    except:
                        pass
            
            # Reset warnings if more than 4 days away (new month cycle)
            if days_until > 4:
                warnings_sent = {'3days': False, '1day': False, '1hour': False, '1minute': False}
    
    except Exception as e:
        print(f"Error in check_chat_clear: {e}")


@bot.command(name='notclear')
async def cancel_chat_clear(ctx):
    """
    Cancels the next scheduled chat clear.
    
    Usage: !notclear
    """
    global chat_clear_enabled, warnings_sent
    
    try:
        # Check if command is used in a server (not DM)
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in direct messages.")
            return
        
        # Check if user has admin/manage server permissions
        if not ctx.author.guild_permissions.manage_guild and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        chat_clear_enabled = False
        warnings_sent = {'3days': True, '1day': True, '1hour': True, '1minute': True}  # Mark as sent to prevent sending more
        
        # Calculate next 1st of month for confirmation
        now = datetime.now()
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        await ctx.send(f"✅ Chat clear cancelled. The scheduled clear on {next_month.strftime('%B 1st, %Y')} has been cancelled.")
    
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.command(name='yesclear')
async def enable_chat_clear(ctx):
    """
    Re-enables the chat clear if it was cancelled with !notclear.
    
    Usage: !yesclear
    """
    global chat_clear_enabled, warnings_sent
    
    try:
        # Check if command is used in a server (not DM)
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in direct messages.")
            return
        
        # Check if user has admin/manage server permissions
        if not ctx.author.guild_permissions.manage_guild and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        chat_clear_enabled = True
        warnings_sent = {'3days': False, '1day': False, '1hour': False, '1minute': False}  # Reset warnings
        
        # Calculate next 1st of month for confirmation
        now = datetime.now()
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        await ctx.send(f"✅ Chat clear **RE-ENABLED**. The scheduled clear on {next_month.strftime('%B 1st, %Y')} is now active.")
    
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.event
async def on_member_join(member):
    """
    Welcomes new members to the server.
    """
    try:
        # Prevent duplicate welcome messages
        member_key = f"{member.id}_{member.guild.id}"
        if member_key in processed_members:
            return
        processed_members.add(member_key)
        
        # Clean up old entries (keep last 1000)
        if len(processed_members) > 1000:
            processed_members.clear()
        
        # Assign guest role to new members
        guest_role = discord.utils.get(member.guild.roles, name="guest")
        if not guest_role:
            guest_role = discord.utils.get(member.guild.roles, name="Guest")
        
        if guest_role:
            try:
                if member.guild.me.guild_permissions.manage_roles:
                    if member.guild.me.top_role > guest_role:
                        if guest_role not in member.roles:
                            await member.add_roles(guest_role, reason="New member - assigned guest role")
            except:
                pass  # Silently fail if can't assign
        
        # Get the target welcome channel ID
        welcome_channel_id = 1440064713584279632
        welcome_channel = bot.get_channel(welcome_channel_id)
        
        if welcome_channel:
            welcome_message = f"Welcome, {member.mention}!"
            await welcome_channel.send(welcome_message)
    except Exception as e:
        # Silently fail if welcome message can't be sent
        pass


@bot.command(name='bot')
async def bot_chat(ctx, *, message: str):
    """
    Chat with the bot using Gemini AI.
    
    Usage: !bot your message here
    """
    try:
        # Check if command is used in a server (not DM)
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in direct messages.")
            return
        
        # Check for inappropriate content (only check for actual profanity, not common words)
        bad_words = ['fuck', 'shit', 'damn', 'asshole', 'bitch', 'crap', 'piss off', 'bastard', 'slut', 'whore', 'nigger', 'nigga', 'retard', 'fag', 'faggot', 'cunt', 'dickhead', 'motherfucker']
        message_lower = message.lower()
        # Only flag if it's clearly profanity (word boundaries to avoid false positives)
        bad_word_pattern = r'\b(' + '|'.join(re.escape(word) for word in bad_words) + r')\b'
        if re.search(bad_word_pattern, message_lower):
            await ctx.send("Hey! Don't be mean! That's not good to say this.")
            return
        
        # Reload API key if needed
        current_gemini_key = os.getenv('GEMINI_API_KEY')
        if not current_gemini_key:
            load_dotenv(override=True)
            current_gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not current_gemini_key:
            await ctx.send("❌ Gemini API key not configured.")
            return
        
        # Check for role mentions like "marshal"
        if "marshal" in message_lower or "who is the marshal" in message_lower:
            marshal_role = discord.utils.get(ctx.guild.roles, name="Marshal")
            if not marshal_role:
                marshal_role = discord.utils.get(ctx.guild.roles, name="marshal")
            
            if marshal_role:
                # Find members with marshal role
                members_with_role = [member.mention for member in ctx.guild.members if marshal_role in member.roles]
                if members_with_role:
                    await ctx.send(f"The Marshal is: {', '.join(members_with_role)}")
                    return
                else:
                    await ctx.send("No one currently has the Marshal role.")
                    return
        
        # Check for other role mentions
        for role in ctx.guild.roles:
            if role.name.lower() in message_lower and role.name.lower() not in ['everyone', 'here']:
                members_with_role = [member.mention for member in ctx.guild.members if role in member.roles]
                if members_with_role:
                    role_info = f"The {role.name} role is held by: {', '.join(members_with_role)}"
                    await ctx.send(role_info)
                    return
        
        # Prepare context for Gemini
        context = f"""You are a helpful bot in a Discord server called "The Golden Rampant" for the game "Bulwark".

Server context:
- Server name: The Golden Rampant
- Game: Bulwark (on Roblox)

About Bulwark:
- Bulwark is a dueling game on Roblox
- Set on a Mediterranean-like island called Bulwark
- Two rival empires compete: Guesmand and Sunderland
- Players compete in tournaments
- Combat system focuses on melee and blocking
- Gameplay involves dueling mechanics between the two empires

Important rules:
- Do NOT generate images
- Do NOT say odd or inappropriate things
- Be helpful and friendly
- Keep responses concise and relevant
- If asked about roles, mention that you can check who has specific roles
- If someone greets you (says hello, hi, etc.), respond with "Welcome to The Golden Rampant! How can I help?"
- If asked what AI model you are or what model you use, say you're just a helpful bot and don't reveal technical details
- Never mention Gemini, Google, AI models, or technical implementation details
- When discussing Bulwark, mention it's a Roblox game about dueling between Guesmand and Sunderland empires

User's message: {message}

Respond naturally and helpfully, but keep it short and appropriate."""
        
        # Use Gemini API to generate response (same approach as verify command)
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{"text": context}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500,
                }
            }
            
            # First, try to list available models (exact same approach as verify command)
            available_model = None
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://generativelanguage.googleapis.com/v1beta/models?key={current_gemini_key}",
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            models_result = await resp.json()
                            if 'models' in models_result:
                                # Find a model that supports generateContent
                                for model in models_result['models']:
                                    name = model.get('name', '')
                                    methods = model.get('supportedGenerationMethods', [])
                                    if 'generateContent' in methods:
                                        # Prefer vision models (or any working model)
                                        if 'vision' in name.lower() or '1.5' in name.lower() or 'flash' in name.lower():
                                            available_model = name.split('/')[-1]
                                            break
                                        elif not available_model:
                                            available_model = name.split('/')[-1]
            except:
                pass
            
            # Try different models and API versions (exact same as verify command)
            models_to_try = []
            if available_model:
                models_to_try.append(available_model)
            
            # Add common model names
            models_to_try.extend([
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ])
            
            response_text = None
            last_error = None
            
            for model_name in models_to_try:
                # Try both v1beta and v1
                for api_version in ["v1beta", "v1"]:
                    try:
                        endpoint = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={current_gemini_key}"
                        async with aiohttp.ClientSession() as session:
                            async with session.post(endpoint, headers=headers, json=data) as resp:
                                if resp.status == 200:
                                    result = await resp.json()
                                    if 'candidates' in result and len(result['candidates']) > 0:
                                        if 'content' in result['candidates'][0]:
                                            if 'parts' in result['candidates'][0]['content']:
                                                response_text = result['candidates'][0]['content']['parts'][0]['text']
                                                break
                                else:
                                    error_text = await resp.text()
                                    last_error = f"Status {resp.status}: {error_text[:200]}"
                                    continue
                    except Exception as e:
                        last_error = str(e)
                        continue
                if response_text:
                    break
            
            if response_text:
                # Check response for inappropriate content (with word boundaries)
                response_lower = response_text.lower()
                bad_word_pattern = r'\b(' + '|'.join(re.escape(word) for word in bad_words) + r')\b'
                if re.search(bad_word_pattern, response_lower):
                    await ctx.send("Hey! Don't be mean! That's not good to say this.")
                    return
                
                # Send response (limit to 2000 characters for Discord)
                if len(response_text) > 2000:
                    response_text = response_text[:1997] + "..."
                await ctx.send(response_text)
                return  # Explicit return to prevent any duplicate sending
            else:
                error_msg = "Sorry, I couldn't generate a response right now."
                if last_error:
                    error_msg += f" Error: {last_error}"
                await ctx.send(error_msg)
                return  # Explicit return to prevent any duplicate sending
                
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
            return  # Explicit return to prevent any duplicate sending
            
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command(name='sendmessage')
async def send_message(ctx, channel_name: str, *, message_text: str):
    """
    Sends a message to a specified channel.
    
    Usage: !sendmessage channel_name message_text
    
    Example: !sendmessage general Hello everyone!
    """
    try:
        # Check if command is used in a server (not DM)
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in direct messages.")
            return
        
        # Find the channel by name (case-insensitive)
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        
        if channel is None:
            await ctx.send(f"❌ Channel '{channel_name}' not found. Please check the channel name and try again.")
            return
        
        # Check if bot has permission to send messages in that channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ I don't have permission to send messages in {channel.mention}")
            return
        
        # Send the message to the specified channel
        await channel.send(message_text)
        await ctx.send(f"✅ Message sent to {channel.mention}!")
        
    except discord.Forbidden:
        await ctx.send(f"❌ I don't have permission to send messages in that channel.")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.command(name='clear')
async def clear_chat(ctx):
    """
    Manually clears the chat channel.
    
    Usage: !clear
    """
    try:
        # Check if command is used in a server (not DM)
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in direct messages.")
            return
        
        # Check if user has admin/manage server or manage messages permission
        if not (ctx.author.guild_permissions.manage_guild or 
                ctx.author.guild_permissions.administrator or 
                ctx.author.guild_permissions.manage_messages):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        # Get the target channel ID
        clear_channel_id = 1440064713584279632
        clear_channel = bot.get_channel(clear_channel_id)
        
        if not clear_channel:
            await ctx.send("❌ Could not find the target channel.")
            return
        
        # Check if bot has permission to manage messages
        if not clear_channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.send("❌ I don't have permission to clear messages in that channel.")
            return
        
        # Clear the channel (delete all messages, keeping pinned messages)
        try:
            deleted = await clear_channel.purge(limit=None, check=lambda m: not m.pinned)
            await ctx.send(f"✅ Chat cleared! Deleted {len(deleted)} messages.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages in that channel.")
        except Exception as e:
            await ctx.send(f"❌ Error clearing chat: {str(e)}")
            
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.command(name='nextclear')
async def next_clear_info(ctx):
    """
    Shows when the next chat clear is scheduled.
    
    Usage: !nextclear
    """
    try:
        # Check if command is used in a server (not DM)
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in direct messages.")
            return
        
        global chat_clear_enabled
        
        now = datetime.now()
        
        # Calculate next 1st of month (this month)
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1, 0, 0, 0)
        else:
            next_month = datetime(now.year, now.month + 1, 1, 0, 0, 0)
        
        # Calculate the month after that (in case current is cancelled)
        if next_month.month == 12:
            month_after = datetime(next_month.year + 1, 1, 1, 0, 0, 0)
        else:
            month_after = datetime(next_month.year, next_month.month + 1, 1, 0, 0, 0)
        
        if chat_clear_enabled:
            # Clear is enabled, show next clear
            days_until = (next_month - now).days
            hours_until = (next_month - now).total_seconds() / 3600
            await ctx.send(f"📅 Next chat clear: **{next_month.strftime('%B 1st, %Y at %I:%M %p')}**\n"
                          f"⏰ Time remaining: {days_until} day(s) ({int(hours_until)} hours)")
        else:
            # Clear is cancelled, show cancelled month and next active one
            days_until_next = (next_month - now).days
            days_until_after = (month_after - now).days
            hours_until_after = (month_after - now).total_seconds() / 3600
            
            await ctx.send(f"❌ Chat clear is **CANCELLED** for {next_month.strftime('%B 1st, %Y')}.\n\n"
                          f"📅 Next active chat clear: **{month_after.strftime('%B 1st, %Y at %I:%M %p')}**\n"
                          f"⏰ Time remaining: {days_until_after} day(s) ({int(hours_until_after)} hours)")
            
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.command(name='verify')
async def verify_user(ctx):
    """
    Analyzes an image to extract Roblox username, level, and rating.
    Then sends a formatted message and assigns the peasant role.
    
    Usage: !verify (with an image attached)
    """
    try:
        # Check if command is used in a server (not DM)
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in direct messages.")
            return
        
        # Check if user already has peasant role
        peasant_role = discord.utils.get(ctx.guild.roles, name="peasant")
        if not peasant_role:
            # Try case-insensitive search
            peasant_role = discord.utils.get(ctx.guild.roles, name="Peasant")
        if not peasant_role:
            # Try other variations
            for role in ctx.guild.roles:
                if role.name.lower() == "peasant":
                    peasant_role = role
                    break
        
        if peasant_role and peasant_role in ctx.author.roles:
            await ctx.send("✅ You are already verified!")
            return
        
        # Check if message has attachments
        if not ctx.message.attachments:
            await ctx.send("❌ Please attach an image with the `!verify` command.")
            return
        
        # Get the first image attachment
        attachment = ctx.message.attachments[0]
        
        # Check if it's an image
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.send("❌ Please attach a valid image file.")
            return
        
        # Download the image
        await ctx.send("🔍 Analyzing image...")
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                else:
                    await ctx.send("❌ Failed to download the image.")
                    return
        
        # Analyze image with Gemini API
        # Reload API key in case it wasn't loaded initially
        current_gemini_key = os.getenv('GEMINI_API_KEY')
        if not current_gemini_key:
            load_dotenv(override=True)
            current_gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not current_gemini_key:
            await ctx.send("❌ Gemini API key not configured. Please add GEMINI_API_KEY to your .env file.")
            return
        
        gemini_api_key = current_gemini_key
        
        try:
            # Use Gemini via HTTP API directly
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            headers = {
                'Content-Type': 'application/json',
            }
            
            # First, try to list available models
            available_model = None
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_api_key}",
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            models_result = await resp.json()
                            if 'models' in models_result:
                                # Find a model that supports generateContent
                                for model in models_result['models']:
                                    name = model.get('name', '')
                                    methods = model.get('supportedGenerationMethods', [])
                                    if 'generateContent' in methods:
                                        # Prefer vision models
                                        if 'vision' in name.lower() or '1.5' in name.lower() or 'flash' in name.lower():
                                            available_model = name.split('/')[-1]
                                            break
                                        elif not available_model:
                                            available_model = name.split('/')[-1]
            except:
                pass  # If listing fails, we'll try hardcoded models
            
            # Prepare the request data
            data = {
                "contents": [{
                    "parts": [
                        {"text": "Analyze this Roblox screenshot and extract: 1) Username on Roblox (name above/near character), 2) Level (number after 'Level:'), 3) Rating (number after 'Rating:'). Respond ONLY in format:\nUsername: [username]\nLevel: [level]\nRating: [rating]"},
                        {
                            "inline_data": {
                                "mime_type": attachment.content_type or "image/png",
                                "data": image_base64
                            }
                        }
                    ]
                }]
            }
            
            # Try different models and API versions
            models_to_try = []
            if available_model:
                models_to_try.append(available_model)
            
            # Add common model names
            models_to_try.extend([
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro",
            ])
            
            analysis_text = None
            last_error = None
            
            for model_name in models_to_try:
                # Try both v1beta and v1
                for api_version in ["v1beta", "v1"]:
                    try:
                        endpoint = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={gemini_api_key}"
                        async with aiohttp.ClientSession() as session:
                            async with session.post(endpoint, headers=headers, json=data) as resp:
                                if resp.status == 200:
                                    result = await resp.json()
                                    if 'candidates' in result and len(result['candidates']) > 0:
                                        if 'content' in result['candidates'][0]:
                                            if 'parts' in result['candidates'][0]['content']:
                                                analysis_text = result['candidates'][0]['content']['parts'][0]['text']
                                                break
                                else:
                                    error_text = await resp.text()
                                    last_error = f"Status {resp.status}: {error_text[:200]}"
                                    continue
                    except Exception as e:
                        last_error = str(e)
                        continue
                if analysis_text:
                    break
            
            if not analysis_text:
                error_msg = "Could not analyze image with Gemini API. "
                if last_error:
                    error_msg += f"Last error: {last_error}. "
                error_msg += "Tried listing models and common model names. Please check your API key has vision access."
                raise Exception(error_msg)
                
        except Exception as gemini_error:
            await ctx.send(f"❌ Error analyzing image with Gemini: {str(gemini_error)}")
            return
        
        # Parse the response
        username = "N/A"
        level = "N/A"
        rating = "N/A"
        
        if analysis_text:
            for line in analysis_text.split('\n'):
                if 'Username:' in line:
                    username = line.split('Username:')[1].strip()
                elif 'Level:' in line:
                    level = line.split('Level:')[1].strip()
                elif 'Rating:' in line:
                    rating = line.split('Rating:')[1].strip()
        
        # Find roles
        peasant_role = discord.utils.get(ctx.guild.roles, name="peasant")
        if not peasant_role:
            peasant_role = discord.utils.get(ctx.guild.roles, name="Peasant")
        if not peasant_role:
            for role in ctx.guild.roles:
                if role.name.lower() == "peasant":
                    peasant_role = role
                    break
        
        member_role = discord.utils.get(ctx.guild.roles, name="member")
        if not member_role:
            member_role = discord.utils.get(ctx.guild.roles, name="Member")
        if not member_role:
            for role in ctx.guild.roles:
                if role.name.lower() == "member":
                    member_role = role
                    break
        
        guest_role = discord.utils.get(ctx.guild.roles, name="guest")
        if not guest_role:
            guest_role = discord.utils.get(ctx.guild.roles, name="Guest")
        if not guest_role:
            for role in ctx.guild.roles:
                if role.name.lower() == "guest":
                    guest_role = role
                    break
        
        # Assign roles after verification
        if peasant_role:
            try:
                if ctx.guild.me.guild_permissions.manage_roles:
                    # Assign peasant role
                    if ctx.guild.me.top_role > peasant_role:
                        if peasant_role not in ctx.author.roles:
                            await ctx.author.add_roles(peasant_role, reason="Verified via !verify command")
                    
                    # Assign member role if it exists
                    if member_role and ctx.guild.me.top_role > member_role:
                        if member_role not in ctx.author.roles:
                            await ctx.author.add_roles(member_role, reason="Verified via !verify command")
                    
                    # Remove guest role if it exists and user has it
                    if guest_role and ctx.guild.me.top_role > guest_role:
                        if guest_role in ctx.author.roles:
                            await ctx.author.remove_roles(guest_role, reason="Verified - guest role removed")
            except discord.Forbidden:
                pass  # Silently fail if no permission
            except Exception as e:
                pass  # Silently fail on error
        
        # Get the target channel ID
        target_channel_id = 1440062982901207164
        target_channel = bot.get_channel(target_channel_id)
        
        if not target_channel:
            await ctx.send("❌ Could not find the target channel.")
            return
        
        # Format the message according to specification
        formatted_message = f"""Username on Roblox: {username}
Level: {level}
Rating: {rating}
Proof: 
{peasant_role.mention if peasant_role else "@Peasant"} {ctx.author.mention}"""
        
        # Send to the target channel with the image attached
        # Create a Discord file object from the image data
        image_file = discord.File(io.BytesIO(image_data), filename=f"verification_{ctx.author.id}.png")
        await target_channel.send(formatted_message, file=image_file)
        
        # Confirm to user in the channel they used
        await ctx.send("✅ Verification complete! Message sent to the verification channel.")
            
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Invalid command format. Usage: `!sendmessage channel_name message_text`\n"
                      "Example: `!sendmessage general Hello everyone!`")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")


# Create Flask app for UptimeRobot health check
app = Flask(__name__)

@app.route('/')
@app.route('/health')
@app.route('/uptime')
def health_check():
    """Health check endpoint for UptimeRobot"""
    return "ok", 200

def run_flask():
    """Run Flask server in a separate thread"""
    app.run(host='0.0.0.0', port=8080, debug=False)

# Run the bot
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("✅ Health check server started on http://0.0.0.0:8080")
    
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
    else:
        bot.run(token)

