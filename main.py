import os
import threading

from flask import Flask, request, jsonify

from docker_monitor import DockerMonitor
from telegrambot.sender import _format_stats_for_telegram

docker_monitor = DockerMonitor()
app = Flask(__name__)

# Start monitoring in a separate thread to avoid blocking Flask
monitoring_thread = threading.Thread(target=docker_monitor.start_monitoring, daemon=True)
monitoring_thread.start()


@app.route("/api/monitor", methods=["POST"])
def get_stats():
    """Handle Telegram webhook and return Docker stats if authorized"""
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({"error": "No message data"}), 400

        message = data['message']

        # Extract message text and chat information
        text = message.get('text', '').strip()
        chat_id = message.get('chat', {}).get('id')

        if chat_id != int(os.environ.get('TELEGRAM_CHAT_ID')):
            return jsonify({
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "Sorry, you are not authorized!"
            })

        if text == '/stats':
            stats_data = docker_monitor.get_stats()
            return jsonify({
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": _format_stats_for_telegram(stats_data)
            })
        else:
            return jsonify({
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "Use /stats command to get stats."
            })

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"error": "Internal server error"}), 500


def main():
    app.run(debug=True)


if __name__ == '__main__':
    main()