import config
from datetime import datetime

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
        
        # Get the approval timeout
        timeout_hours = channel_info.get('approval_timeout') or config.DEFAULT_APPROVAL_TIMEOUT
        
        # Replace placeholders
        formatted_message = approval_message
        formatted_message = formatted_message.replace("{name}", user.first_name or "")
        formatted_message = formatted_message.replace("{username}", f"@{user.username}" if user.username else user.first_name or "")
        formatted_message = formatted_message.replace("{channel}", channel_info.get('title') or "the channel")
        formatted_message = formatted_message.replace("{timeout}", str(timeout_hours))
        
        # Add remaining time information if available
        pending_request = self.db.get_pending_request(channel_info.get('channel_id'), user.id)
        if pending_request and pending_request.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(pending_request['expires_at'])
                now = datetime.now()
                if expires_at > now:
                    time_remaining = expires_at - now
                    hours = time_remaining.seconds // 3600
                    minutes = (time_remaining.seconds % 3600) // 60
                    
                    time_info = f"\n\n⏰ Your request will expire in "
                    if time_remaining.days > 0:
                        time_info += f"{time_remaining.days} days, "
                    if hours > 0:
                        time_info += f"{hours} hours "
                    if minutes > 0 and time_remaining.days == 0:  # Only show minutes if less than a day
                        time_info += f"and {minutes} minutes"
                        
                    formatted_message += time_info
            except (ValueError, TypeError):
                pass  # If there's an error parsing the date, just skip the time remaining info
                
        return formatted_message
        
    def format_expired_message(self, channel_info):
        """Format message for expired join requests."""
        return (f"⏰ Your join request for {channel_info.get('title')} has expired.\n\n"
                f"You can request to join the channel again if you're still interested.")
