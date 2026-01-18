import os
import datetime
from xscout.config.loader import config
from supabase import create_client, Client

class DatabaseManager:
    def __init__(self):
        url = config.get("supabase.url")
        key = config.get("supabase.key")
        
        if not url or not key:
             # Fallback or error, but for now we assume they are set
             print("! Warning: Supabase credentials missing.")
             self.client = None
             return

        self.client: Client = create_client(url, key)

    def add_lead(self, lead_data):
        if not self.client: return
        
        data = {
            "platform": lead_data.get('platform'),
            "username": lead_data.get('username'),
            "profile_url": lead_data.get('profile_url'),
            "post_text": lead_data.get('post_text'),
            "post_id": lead_data.get('post_id'),
            "matched_keyword": lead_data.get('matched_keyword'),
            "intent_score": lead_data.get('intent_score'),
            "intent_label": lead_data.get('intent_label'),
            "contact_info": lead_data.get('contact_info'),
            "notified": False
        }
        
        try:
            self.client.table("leads").insert(data).execute()
            print(f"    + Saved to Supabase: {lead_data.get('profile_url')}")
        except Exception as e:
            print(f"    ! Supabase Insert Error: {e}")

    def lead_exists(self, post_id):
        if not self.client: return False
        try:
            response = self.client.table("leads").select("*").eq("post_id", post_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"    ! Supabase Query Error: {e}")
            return False

    def log(self, level, message):
        if not self.client: return
        try:
            self.client.table("logs").insert({"level": level, "message": message}).execute()
        except:
            pass # Silent fail for logs

    def mark_notified(self, post_id):
        if not self.client: return
        try:
            self.client.table("leads").update({"notified": True}).eq("post_id", post_id).execute()
        except Exception as e:
             print(f"    ! Supabase Update Error: {e}")

# Global instance
db_manager = DatabaseManager()
