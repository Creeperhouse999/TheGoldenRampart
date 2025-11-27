# Discord Bot - Channel Message Sender

A Discord bot that sends messages to different channels based on commands.

## Command Format

```
!sendmessage channel_name message_text
```

### Example Usage

```
!sendmessage general Hello everyone!
!sendmessage announcements Important update!
!sendmessage general This is a longer message that can contain multiple words.
```

---

## 📋 DETAILED SETUP INSTRUCTIONS

### Step 1: Install Python (if not already installed)

1. **Check if Python is installed:**
   ```bash
   python --version
   ```
   or
   ```bash
   python3 --version
   ```

2. **If Python is not installed:**
   - **Windows:** Download from https://www.python.org/downloads/
   - **Mac:** Usually pre-installed, or use Homebrew: `brew install python3`
   - **Linux:** `sudo apt-get install python3 python3-pip`

3. **Verify installation:**
   ```bash
   python --version
   # Should show something like: Python 3.9.x or higher
   ```

---

### Step 2: Navigate to Project Directory

1. **Open Terminal/Command Prompt**

2. **Navigate to the bot folder:**
   ```bash
   cd /none
   ```
   (Or use the path where you saved the bot files)

3. **Verify you're in the right directory:**
   ```bash
   ls
   # Should show: bot.py, requirements.txt, README.md, .gitignore
   ```

---

### Step 3: Install Python Dependencies

1. **Install pip (if not installed):**
   ```bash
   python -m ensurepip --upgrade
   ```

2. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```
   
   **If you get permission errors, use:**
   ```bash
   pip install --user -r requirements.txt
   ```
   
   **Or on Mac/Linux:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Verify installations:**
   ```bash
   pip list
   # Should show: discord.py and python-dotenv
   ```

---

### Step 4: Create Discord Application and Bot

#### 4.1. Create Discord Application

1. **Go to Discord Developer Portal:**
   - Open your browser and visit: https://discord.com/developers/applications
   - Log in with your Discord account

2. **Create New Application:**
   - Click the **"New Application"** button (top right)
   - Give it a name (e.g., "Message Bot" or "Channel Sender Bot")
   - Click **"Create"**

3. **Note the Application ID:**
   - You'll see an **Application ID** on the General Information page
   - You might need this later, but you can always find it here

#### 4.2. Create Bot User

1. **Go to Bot Section:**
   - In the left sidebar, click **"Bot"**

2. **Add Bot:**
   - Click **"Add Bot"** button
   - Confirm by clicking **"Yes, do it!"**

3. **Configure Bot Settings:**
   - **Username:** Change if desired (this is the bot's display name)
   - **Icon:** Upload an image if you want a custom bot avatar
   - **Public Bot:** Leave unchecked (unless you want others to invite it)
   - **Requires OAuth2 Code Grant:** Leave unchecked
   - **Message Content Intent:** Turn this **ON** (Important!)
     - Scroll down to "Privileged Gateway Intents"
     - Enable **"MESSAGE CONTENT INTENT"**
     - This is required for the bot to read command messages

#### 4.3. Get Bot Token

1. **Copy Bot Token:**
   - Under the "Token" section, click **"Reset Token"** or **"Copy"**
   - Click **"Yes, do it!"** if prompted
   - **IMPORTANT:** Copy the token immediately - it looks like:
     ```
     MTAyMzQ1Njc4OTAxMjM0NTY3OA.GaBcDe.FgHiJkLmNoPqRsTuVwXyZaBcDeFgHiJkLmNoPqRsTuVw
     ```
   - **⚠️ NEVER share this token publicly!** Treat it like a password.

2. **Save Token Securely:**
   - Keep it in a safe place temporarily (you'll add it to .env file next)

---

### Step 5: Configure Bot Token in Project

1. **Create .env file:**
   
   **On Mac/Linux:**
   ```bash
   touch .env
   ```
   
   **On Windows:**
   ```bash
   type nul > .env
   ```
   
   **Or manually create a file named `.env` in the project folder**

2. **Open .env file in a text editor:**
   - Use any text editor (Notepad, VS Code, TextEdit, etc.)

3. **Add your bot token:**
   ```
   DISCORD_BOT_TOKEN=your_actual_bot_token_here
   ```
   
   **Example:**
   ```
   DISCORD_BOT_TOKEN=MTAyMzQ1Njc4OTAxMjM0NTY3OA.GaBcDe.FgHiJkLmNoPqRsTuVwXyZaBcDeFgHiJkLmNoPqRsTuVw
   ```
   
   **Important:**
   - No spaces around the `=` sign
   - No quotes around the token
   - Replace `your_actual_bot_token_here` with the actual token you copied

4. **Save the file**

5. **Verify .env file exists:**
   ```bash
   cat .env
   # Should show: DISCORD_BOT_TOKEN=your_token
   ```

---

### Step 6: Invite Bot to Your Discord Server

#### 6.1. Generate Invite URL

1. **Go to OAuth2 URL Generator:**
   - In Discord Developer Portal, click **"OAuth2"** in the left sidebar
   - Then click **"URL Generator"**

2. **Select Scopes:**
   - Check the box for **"bot"**
   - Optionally check **"applications.commands"** (not required for this bot)

3. **Select Bot Permissions:**
   - Scroll down to "Bot Permissions"
   - Check these permissions:
     - ✅ **Send Messages**
     - ✅ **Read Message History**
     - ✅ **View Channels**
   
   **Optional but recommended:**
   - ✅ **Embed Links** (if you plan to send embeds later)
   - ✅ **Attach Files** (if you plan to send files later)

4. **Copy Generated URL:**
   - At the bottom, you'll see a "Generated URL"
   - It looks like: `https://discord.com/api/oauth2/authorize?client_id=...`
   - Click **"Copy"** button

#### 6.2. Invite Bot to Server

1. **Open the URL:**
   - Paste the URL in your browser
   - Press Enter

2. **Select Server:**
   - A Discord page will open showing "Add to Server"
   - Select the server you want to add the bot to from the dropdown
   - If you don't see your server, make sure you have "Manage Server" permission

3. **Authorize:**
   - Click **"Authorize"**
   - Complete any CAPTCHA if prompted

4. **Verify Bot Joined:**
   - Go to your Discord server
   - Check the member list or a channel - the bot should appear as offline
   - The bot will show as online once you run the Python script

---

### Step 7: Run the Bot

1. **Make sure you're in the project directory:**
   ```bash
   cd /Users/alandebowski/Downloads/CURSOR/BOT_KUBAANDTYMON
   ```

2. **Run the bot:**
   ```bash
   python bot.py
   ```
   
   **If that doesn't work, try:**
   ```bash
   python3 bot.py
   ```

3. **Look for success message:**
   - You should see: `Message Bot#1234 has logged in and is ready!`
   - (The bot name and numbers will match your bot)

4. **Check Discord:**
   - The bot should now appear as **online** in your server
   - You can see it in the member list

5. **Keep Terminal Open:**
   - **DON'T CLOSE** the terminal window while the bot is running
   - The bot will stop if you close the terminal or press `Ctrl+C`

---

### Step 8: Test the Bot

1. **Go to any channel in your Discord server**

2. **Send a test command:**
   ```
   !sendmessage general Hello, this is a test message!
   ```
   - Replace `general` with an actual channel name in your server
   - Make sure the channel name matches exactly (case-insensitive)

3. **Expected Results:**
   - You should see: "✅ Message sent to #channel_name!"
   - Check the target channel - your message should appear there

4. **Common Issues:**
   - **"Channel not found"** → Check the channel name spelling
   - **"Permission error"** → Make sure bot has "Send Messages" permission in that channel
   - **"Invalid command format"** → Make sure there's a space between channel name and message

---

## 🔧 TROUBLESHOOTING

### Bot won't start / Token error
- **Problem:** "DISCORD_BOT_TOKEN not found"
- **Solution:** 
  - Make sure `.env` file exists in the same folder as `bot.py`
  - Check that `.env` file contains: `DISCORD_BOT_TOKEN=your_token`
  - Make sure there are no extra spaces or quotes

### Bot is offline in Discord
- **Problem:** Bot appears offline even after running `python bot.py`
- **Solution:**
  - Check terminal for error messages
  - Verify bot token is correct
  - Make sure Message Content Intent is enabled in Discord Developer Portal
  - Check internet connection

### "Channel not found" error
- **Problem:** Bot says channel doesn't exist
- **Solution:**
  - Channel names are case-insensitive but must match exactly
  - Use the channel name without the `#` symbol
  - Example: For channel `#general`, use `general` not `General` or `#general`

### Permission errors
- **Problem:** "I don't have permission to send messages"
- **Solution:**
  - Right-click the channel → "Edit Channel" → "Permissions"
  - Add the bot role and enable "Send Messages"
  - Make sure bot role is above any roles with "Send Messages" disabled

### Command not working
- **Problem:** Bot doesn't respond to `!sendmessage`
- **Solution:**
  - Make sure you're using `!` (exclamation mark) as prefix
  - Check that Message Content Intent is enabled
  - Verify bot is online (green dot in Discord)

---

## 📝 RUNNING BOT IN BACKGROUND (Optional)

### On Mac/Linux:

**Using `nohup`:**
```bash
nohup python3 bot.py > bot.log 2>&1 &
```

**Using `screen`:**
```bash
screen -S discordbot
python3 bot.py
# Press Ctrl+A then D to detach
# To reattach: screen -r discordbot
```

### On Windows:

**Using a batch file:**
Create `start_bot.bat`:
```batch
@echo off
python bot.py
pause
```

---

## ✅ VERIFICATION CHECKLIST

Before using the bot, make sure:

- [ ] Python is installed and working
- [ ] All dependencies are installed (`pip list` shows discord.py)
- [ ] `.env` file exists with correct bot token
- [ ] Bot is created in Discord Developer Portal
- [ ] Message Content Intent is enabled
- [ ] Bot is invited to your server
- [ ] Bot has "Send Messages" permission
- [ ] Bot appears online when script is running
- [ ] Test command works in a channel

---

## Features

- ✅ Send messages to any channel by name
- ✅ Case-insensitive channel name matching
- ✅ Permission checking
- ✅ Error handling with helpful messages
- ✅ Confirmation when message is sent successfully

## Notes

- The channel name must match exactly (case-insensitive, without #)
- The bot needs permission to send messages in the target channel
- You must have permission to use the bot command in the server
- Keep the terminal/command prompt open while bot is running

