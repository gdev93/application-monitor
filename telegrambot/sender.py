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


def _format_stats_for_telegram(stats_data: dict) -> str:

    if not stats_data:
        formatted_message = "No container stats available"
    else:
        formatted_message = "📊 Container Stats:\n\n"
        for container, stats in stats_data.items():
            formatted_message += f"🐳 {container}:\n"
            formatted_message += f"  CPU: {stats.get('cpu_percent', 'N/A')}\n"
            formatted_message += f"  Memory: {stats.get('memory_percent', 'N/A')}\n\n"

    return formatted_message


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


def _create_cpu_alarm_message(container_name: str, cpu_percentage: float, threshold: float) -> str:
    """
    Create a CPU threshold violation alert message with emphasis

    Args:
        container_name: Name of the container
        cpu_percentage: Current CPU usage percentage
        threshold: CPU threshold that was violated

    Returns:
        str: Formatted Markdown V2 message
    """
    # Escape special characters for Markdown V2
    container_name_escaped = _escape_markdown_v2(container_name)
    cpu_percentage_escaped = _escape_markdown_v2(f"{cpu_percentage:.2f}%")
    threshold_escaped = _escape_markdown_v2(f"{threshold:.2f}%")

    # Get current timestamp
    timestamp = datetime.now(_SENDER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    timestamp_escaped = _escape_markdown_v2(timestamp)

    # Determine severity level
    severity_ratio = cpu_percentage / threshold
    if severity_ratio >= 1.5:
        severity_emoji = "🔴"
        severity_text = "CRITICAL"
    elif severity_ratio >= 1.2:
        severity_emoji = "🟠"
        severity_text = "HIGH"
    else:
        severity_emoji = "🟡"
        severity_text = "WARNING"

    # Create the formatted message
    formatted_message = f"""
🚨 *CPU THRESHOLD VIOLATION* 🚨

{severity_emoji} *{severity_text} ALERT*

🐳 *Container:* `{container_name_escaped}`
🕐 *Time:* {timestamp_escaped}

🔥 *CPU USAGE VIOLATION:*
📊 *Current Usage:* *{cpu_percentage_escaped}*
⚠️ *Threshold:* {threshold_escaped}
📈 *Violation:* *\\+{_escape_markdown_v2(f"{cpu_percentage - threshold:.2f}%")}*

💡 *Action Required:* CPU usage has exceeded the configured threshold\\. Consider scaling or optimizing this container immediately\\.
    """.strip()

    return formatted_message


def _create_memory_alarm_message(container_name: str, memory_percentage: float, threshold: float) -> str:
    """
    Create a memory threshold violation alert message with emphasis

    Args:
        container_name: Name of the container
        memory_percentage: Current memory usage percentage
        threshold: Memory threshold that was violated

    Returns:
        str: Formatted Markdown V2 message
    """
    # Escape special characters for Markdown V2
    container_name_escaped = _escape_markdown_v2(container_name)
    memory_percentage_escaped = _escape_markdown_v2(f"{memory_percentage:.2f}%")
    threshold_escaped = _escape_markdown_v2(f"{threshold:.2f}%")

    # Get current timestamp
    timestamp = datetime.now(_SENDER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    timestamp_escaped = _escape_markdown_v2(timestamp)

    # Determine severity level
    severity_ratio = memory_percentage / threshold
    if severity_ratio >= 1.5:
        severity_emoji = "🔴"
        severity_text = "CRITICAL"
    elif severity_ratio >= 1.2:
        severity_emoji = "🟠"
        severity_text = "HIGH"
    else:
        severity_emoji = "🟡"
        severity_text = "WARNING"

    # Create the formatted message
    formatted_message = f"""
🚨 *MEMORY THRESHOLD VIOLATION* 🚨

{severity_emoji} *{severity_text} ALERT*

🐳 *Container:* `{container_name_escaped}`
🕐 *Time:* {timestamp_escaped}

💾 *MEMORY USAGE VIOLATION:*
📊 *Current Usage:* *{memory_percentage_escaped}*
⚠️ *Threshold:* {threshold_escaped}
📈 *Violation:* *\\+{_escape_markdown_v2(f"{memory_percentage - threshold:.2f}%")}*

💡 *Action Required:* Memory usage has exceeded the configured threshold\\. Consider scaling or optimizing this container immediately\\.
    """.strip()

    return formatted_message


def _create_resource_alert_message(container_name: str, cpu_percentage: str, mem_percentage: str,
                                   cpu_threshold: float = None, mem_threshold: float = None) -> str:
    """
    Create a resource alert message with emojis and formatting

    Args:
        container_name: Name of the container
        cpu_percentage: CPU usage percentage as string (e.g., "75.25%")
        mem_percentage: Memory usage percentage as string (e.g., "80.50%")
        cpu_threshold: CPU threshold that was violated (optional)
        mem_threshold: Memory threshold that was violated (optional)

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

    # Create threshold violation details if thresholds are provided
    threshold_info = ""
    if cpu_threshold is not None and mem_threshold is not None:
        cpu_threshold_escaped = _escape_markdown_v2(f"{cpu_threshold:.2f}%")
        mem_threshold_escaped = _escape_markdown_v2(f"{mem_threshold:.2f}%")
        threshold_info = f"""
⚠️ *THRESHOLD VIOLATIONS:*
🔥 *CPU Threshold:* {cpu_threshold_escaped}
💾 *Memory Threshold:* {mem_threshold_escaped}

"""

    # Create the formatted message
    formatted_message = f"""
🚨 *RESOURCE THRESHOLD VIOLATIONS* 🚨

🔴 *CRITICAL ALERT \\- MULTIPLE VIOLATIONS*

🐳 *Container:* `{container_name_escaped}`
🕐 *Time:* {timestamp_escaped}

📊 *CURRENT RESOURCE USAGE:*
🔥 *CPU:* *{cpu_percentage_escaped}*
💾 *Memory:* *{mem_percentage_escaped}*

{threshold_info}💡 *URGENT ACTION REQUIRED:* Both CPU and memory usage have exceeded their configured thresholds\\. Immediate scaling or optimization is needed\\.
    """.strip()

    return formatted_message


def send_resource_alert(container_name: str, cpu_percentage: str, mem_percentage: str, cpu_threshold: float = None,
                        mem_threshold: float = None) -> bool:
    """
    Send a resource alert notification to Telegram

    Args:
        container_name: Name of the container reaching limits
        cpu_percentage: CPU usage percentage as string (e.g., "75.25%")
        mem_percentage: Memory usage percentage as string (e.g., "80.50%")
        cpu_threshold: CPU threshold that was violated (optional)
        mem_threshold: Memory threshold that was violated (optional)

    Returns:
        bool: True if alert was sent successfully, False otherwise
    """
    formatted_message = _create_resource_alert_message(container_name, cpu_percentage, mem_percentage, cpu_threshold,
                                                       mem_threshold)
    return _send_message(formatted_message)


class _TelegramBot:
    """
    Simple Telegram Bot client using HTTP requests
    """

    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

        # Base URL for Telegram Bot API
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

        logger.info(
            f"Telegram bot initialized with token '{self.bot_token}' and chat ID '{self.chat_id}'"
        )

    def send_message(self, message: str, parse_mode: str = None, chat_id: int = None) -> bool:
        """
        Send a message to the configured chat

        Args:
            message: The message to send
            parse_mode: Message format (MARKDOWN_V2, HTML, or None)

        Returns:
            bool: True if message was sent successfully, False otherwise
            :param message:
            :param parse_mode:
            :param chat_id:
        """
        try:
            url = f"{self.base_url}/sendMessage"
            chat_id_to_send = chat_id if chat_id else self.chat_id
            payload = {
                "chat_id": chat_id_to_send,
                "text": message,
            }

            # Add parse_mode if specified
            if parse_mode:
                payload["parse_mode"] = parse_mode

            print(f"Sending Telegram message: {payload}")
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


def _send_message(message: str, parse_mode: str = ParseMode.MARKDOWN_V2, chat_id: int = None) -> bool:
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
        return bot.send_message(message, parse_mode, chat_id)
    else:
        logger.warning("Telegram bot not available - message not sent")
        return False


def send_cpu_alarm(container_name: str, cpu_percentage: float, threshold: float) -> bool:
    """
    Send a CPU threshold violation alert to Telegram

    Args:
        container_name: Name of the container with CPU violation
        cpu_percentage: Current CPU usage percentage
        threshold: CPU threshold that was violated

    Returns:
        bool: True if alert was sent successfully, False otherwise
    """
    formatted_message = _create_cpu_alarm_message(container_name, cpu_percentage, threshold)
    return _send_message(formatted_message)


def send_memory_alert(container_name: str, memory_percentage: float, threshold: float) -> bool:
    """
    Send a memory threshold violation alert to Telegram

    Args:
        container_name: Name of the container with memory violation
        memory_percentage: Current memory usage percentage
        threshold: Memory threshold that was violated

    Returns:
        bool: True if alert was sent successfully, False otherwise
    """
    formatted_message = _create_memory_alarm_message(container_name, memory_percentage, threshold)
    return _send_message(formatted_message)