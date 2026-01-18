import requests
import urllib.parse
from ..config.loader import config

class WhatsAppNotifier:
    def __init__(self):
        self.phone_number = config.get("api_keys.callmebot.phone_number")
        self.api_key = config.get("api_keys.callmebot.api_key")
        self.base_url = "https://api.callmebot.com/whatsapp.php"

    def send_alert(self, lead):
        """
        Send a WhatsApp message for a high-intent lead.
        """
        if not self.phone_number or not self.api_key:
            print("[Notifications] Missing credentials. Skipping WhatsApp alert.")
            return False

        message = (
            f"🚀 *New Lead Detected!*\n\n"
            f"Platform: {lead['platform']}\n"
            f"Intent: {lead['intent_label']} ({lead['intent_score']}/10)\n"
            f"Contact: {lead['contact_info']}\n"
            f"User: {lead['username']}\n"
            f"Post: {lead['post_text'][:100]}...\n\n"
            f"Link: {lead['profile_url']}"
        )
        
        encoded_msg = urllib.parse.quote(message)
        url = f"{self.base_url}?phone={self.phone_number}&text={encoded_msg}&apikey={self.api_key}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"[Notifications] Failed to send: {response.text}")
                return False
        except Exception as e:
            print(f"[Notifications] Error: {e}")
            return False
