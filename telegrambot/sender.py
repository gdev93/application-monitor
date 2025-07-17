import os
import logging
import zoneinfo
import requests
import json
from datetime import datetime
from typing import Optional

# Set up logging
logger = logging.getLogger(__name__)

_SENDER_TIMEZONE = zoneinfo.ZoneInfo(os.environ.get('TIME_ZONE', 'UTC'))


# Telegram parse modes
class ParseMode:
    MARKDOWN_V2 = 'MarkdownV2'
    MARKDOWN = 'Markdown'
    HTML = 'HTML'


def _escape_markdown_v2(text: str) -> str:
    """
    Escape special Markdown V2 characters for Telegram

    Args:
        text: Text to escape

    Returns:
        str: Escaped text
    """
    # Characters that need to be escaped in Telegram Markdown V2
    chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in chars_to_escape:
        text = text.replace(char, f'\\{char}')

    return text



def _create_resource_alert_message(container_name: str, cpu_percentage: str, mem_percentage: str) -> str:
    """
    Create a resource alert message with emojis and formatting

    Args:
        container_name: Name of the container
        cpu_percentage: CPU usage percentage as string (e.g., "75.25%")
        mem_percentage: Memory usage percentage as string (e.g., "80.50%")

    Returns:
        str: Formatted Markdown V2 message
    """
    # Escape special characters for Markdown V2
    container_name_escaped = _escape_markdown_v2(container_name)
    cpu_percentage_escaped = _escape_markdown_v2(cpu_percentage)
    mem_percentage_escaped = _escape_markdown_v2(mem_percentage)

    # Get current timestamp
    timestamp = datetime.now(_SENDER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    timestamp_escaped = _escape_markdown_v2(timestamp)

    # Create the formatted message
    formatted_message = f"""
🚨 *RESOURCE ALERT* 🚨

⚠️ *CONTAINER REACHING LIMITS*

🐳 *Container:* `{container_name_escaped}`
🕐 *Time:* {timestamp_escaped}

📊 *RESOURCE USAGE:*
🔥 *CPU:* {cpu_percentage_escaped}
💾 *Memory:* {mem_percentage_escaped}

💡 *Consider scaling or optimizing this container\\.*
    """.strip()

    return formatted_message


class _TelegramBot:
    """
    Simple Telegram Bot client using HTTP requests
    """

    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '5944161880:AAHGXJIHN4M8xHzPwYbbmNaNcNo9kjeUhuE')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '508229488')

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

        # Base URL for Telegram Bot API
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

        logger.info(
            f"Telegram bot initialized with token '{self.bot_token}' and chat ID '{self.chat_id}'"
        )

    def send_message(self, message: str, parse_mode: str = ParseMode.MARKDOWN_V2) -> bool:
        """
        Send a message to the configured chat

        Args:
            message: The message to send
            parse_mode: Message format (MARKDOWN_V2, HTML, or None)

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"

            payload = {
                "chat_id": self.chat_id,
                "text": message,
            }

            # Add parse_mode if specified
            if parse_mode:
                payload["parse_mode"] = parse_mode

            # Send the request
            response = requests.post(
                url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )

            # Check if request was successful
            response.raise_for_status()

            # Parse response
            response_data = response.json()

            if response_data.get('ok'):
                logger.info("Telegram message sent successfully")
                return True
            else:
                error_description = response_data.get('description', 'Unknown error')
                logger.error(f"Telegram API error: {error_description}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Telegram API request timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Telegram API connection error")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"Telegram API HTTP error: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram API request error: {e}")
            return False
        except json.JSONDecodeError:
            logger.error("Failed to parse Telegram API response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {str(e)}")
            return False


# Singleton instance
_bot_instance: Optional[_TelegramBot] = None


def _get_bot() -> Optional[_TelegramBot]:
    """
    Get the singleton bot instance

    Returns:
        _TelegramBot instance or None if configuration is missing
    """
    global _bot_instance

    if _bot_instance is None:
        try:
            _bot_instance = _TelegramBot()
        except ValueError as e:
            logger.warning(f"Telegram bot not configured: {str(e)}")
            return None

    return _bot_instance


def _send_message(message: str, parse_mode: str = ParseMode.MARKDOWN_V2) -> bool:
    """
    Send a message to Telegram (main public function)

    Args:
        message: The message to send
        parse_mode: Message format (MARKDOWN_V2, HTML, or None)

    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    bot = _get_bot()
    if bot:
        return bot.send_message(message, parse_mode)
    else:
        logger.warning("Telegram bot not available - message not sent")
        return False


def send_resource_alert(container_name: str, cpu_percentage: str, mem_percentage: str) -> bool:
    """
    Send a resource alert notification to Telegram

    Args:
        container_name: Name of the container reaching limits
        cpu_percentage: CPU usage percentage as string (e.g., "75.25%")
        mem_percentage: Memory usage percentage as string (e.g., "80.50%")

    Returns:
        bool: True if alert was sent successfully, False otherwise
    """
    formatted_message = _create_resource_alert_message(container_name, cpu_percentage, mem_percentage)
    return _send_message(formatted_message)