import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Default messages
DEFAULT_WELCOME_MESSAGE = "Welcome {name} to {channel}! We're glad to have you here."
DEFAULT_APPROVAL_MESSAGE = "Hello {name}! To join {channel}, please click the approval button below. You have {timeout} hours to approve your request."

# Default settings
DEFAULT_APPROVAL_TIMEOUT = 24  # 24 hours

# Check if required environment variables are set
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set. Please set it in .env file or in your environment.")
