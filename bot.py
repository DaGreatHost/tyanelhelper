import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ChatJoinRequestHandler,  # Added this import
)
from utils.database import Database
from utils.messages import Messages
import config

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Initialize messages handler
msg = Messages(db)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that handles self-approval and welcome messages for your channels.\n\n"
        f"Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/setup_channel - Set up a channel for management\n"
        "/set_welcome - Set a welcome message for a channel\n"
        "/set_approval - Set approval message\n"
        "/stats - Show channel statistics"
    )
    await update.message.reply_text(help_text)

async def setup_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set up a channel for the bot to manage."""
    if not await is_admin(update, context):
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Please provide a channel username or ID.\n"
            "Example: /setup_channel @yourchannel"
        )
        return
    
    channel_id = context.args[0]
    
    # Try to get channel info to verify the bot has access
    try:
        chat = await context.bot.get_chat(channel_id)
        bot_member = await chat.get_member(context.bot.id)
        
        if not bot_member.can_invite_users or not bot_member.can_restrict_members:
            await update.message.reply_text(
                "I need to be an admin with permissions to invite users and restrict members in that channel."
            )
            return
            
        # Save channel to database
        db.add_channel(chat.id, chat.title, update.effective_user.id)
        
        await update.message.reply_text(
            f"Successfully set up channel: {chat.title}\n"
            f"Use /set_welcome and /set_approval to customize messages."
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"Failed to set up the channel. Make sure:\n"
            f"1. The channel exists\n"
            f"2. I'm an admin in that channel\n"
            f"3. You provided the correct username/ID\n\n"
            f"Error: {str(e)}"
        )

async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a custom welcome message for new members."""
    if not await is_admin(update, context):
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Please provide a channel ID and welcome message.\n"
            "Example: /set_welcome @yourchannel Welcome {name} to our channel!"
        )
        return
    
    channel_id = context.args[0]
    welcome_message = " ".join(context.args[1:])
    
    try:
        chat = await context.bot.get_chat(channel_id)
        db.set_welcome_message(chat.id, welcome_message)
        
        await update.message.reply_text(
            f"Welcome message for {chat.title} has been set to:\n\n{welcome_message}\n\n"
            f"Available placeholders:\n"
            f"{{name}} - Member's name\n"
            f"{{username}} - Member's username\n"
            f"{{channel}} - Channel name"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def set_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a custom approval message for new members."""
    if not await is_admin(update, context):
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Please provide a channel ID and approval message.\n"
            "Example: /set_approval @yourchannel Click the button below to join our channel."
        )
        return
    
    channel_id = context.args[0]
    approval_message = " ".join(context.args[1:])
    
    try:
        chat = await context.bot.get_chat(channel_id)
        db.set_approval_message(chat.id, approval_message)
        
        await update.message.reply_text(
            f"Approval message for {chat.title} has been set to:\n\n{approval_message}\n\n"
            f"Available placeholders:\n"
            f"{{name}} - Member's name\n"
            f"{{username}} - Member's username\n"
            f"{{channel}} - Channel name"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics about managed channels."""
    if not await is_admin(update, context):
        return
        
    channels = db.get_admin_channels(update.effective_user.id)
    
    if not channels:
        await update.message.reply_text("You haven't set up any channels yet.")
        return
    
    stats_text = "Channel Statistics:\n\n"
    
    for channel in channels:
        approvals = db.get_approval_count(channel['channel_id'])
        stats_text += f"• {channel['title']}\n"
        stats_text += f"  - Total approvals: {approvals}\n"
    
    await update.message.reply_text(stats_text)

async def handle_chat_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle join requests for channels."""
    join_request = update.chat_join_request
    user = join_request.from_user
    chat = join_request.chat
    
    # Check if channel is in our database
    channel_info = db.get_channel(chat.id)
    if not channel_info:
        return
    
    # Create approval message with button
    approval_message = msg.format_approval_message(channel_info, user)
    keyboard = [
        [InlineKeyboardButton("✅ Approve Join Request", callback_data=f"approve:{chat.id}:{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send approval message to the user
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=approval_message,
            reply_markup=reply_markup
        )
        # Log the request
        db.log_join_request(chat.id, user.id)
    except Exception as e:
        logger.error(f"Failed to send approval message: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(':')
    if data[0] == "approve":
        chat_id = int(data[1])
        user_id = int(data[2])
        
        # Approve the join request
        try:
            await context.bot.approve_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )
            
            # Update approval count in the database
            db.approve_join_request(chat_id, user_id)
            
            # Send welcome message in the channel
            channel_info = db.get_channel(chat_id)
            user = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            
            # Format and send welcome message if set
            if channel_info and channel_info.get('welcome_message'):
                welcome_text = msg.format_welcome_message(channel_info, user.user)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text
                )
            
            # Update the approval button message
            await query.edit_message_text(
                text=f"✅ You have been approved to join the channel!\n\nWelcome to the community!"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Failed to approve your request: {str(e)}"
            )

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin for any registered channel."""
    user_id = update.effective_user.id
    
    # Check if user is in the admins list
    if db.is_admin(user_id):
        return True
    
    # If it's a new admin (first setup), allow them
    if not db.get_admins():
        # This is the first admin setting up the bot
        db.add_admin(user_id)
        return True
    
    await update.message.reply_text("You don't have permission to use this command.")
    return False

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setup_channel", setup_channel))
    application.add_handler(CommandHandler("set_welcome", set_welcome))
    application.add_handler(CommandHandler("set_approval", set_approval))
    application.add_handler(CommandHandler("stats", stats))
    
    # Chat join request handler - using ChatJoinRequestHandler instead of MessageHandler with filters
    application.add_handler(ChatJoinRequestHandler(handle_chat_join_request))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
