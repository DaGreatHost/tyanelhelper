import config

class Messages:
    def __init__(self, db):
        self.db = db

    def format_welcome_message(self, channel_info, user):
        """Format welcome message with placeholders."""
        welcome_message = channel_info.get('welcome_message') or config.DEFAULT_WELCOME_MESSAGE
        
        # Replace placeholders
        formatted_message = welcome_message
        formatted_message = formatted_message.replace("{name}", user.first_name or "")
        formatted_message = formatted_message.replace("{username}", f"@{user.username}" if user.username else user.first_name or "")
        formatted_message = formatted_message.replace("{channel}", channel_info.get('title') or "the channel")
        
        return formatted_message

    def format_approval_message(self, channel_info, user):
        """Format approval message with placeholders."""
        approval_message = channel_info.get('approval_message') or config.DEFAULT_APPROVAL_MESSAGE
        
        # Replace placeholders
        formatted_message = approval_message
        formatted_message = formatted_message.replace("{name}", user.first_name or "")
        formatted_message = formatted_message.replace("{username}", f"@{user.username}" if user.username else user.first_name or "")
        formatted_message = formatted_message.replace("{channel}", channel_info.get('title') or "the channel")
        
        return formatted_message
