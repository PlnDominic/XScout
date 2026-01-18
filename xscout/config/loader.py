import yaml
import os

class ConfigLoader:
    def __init__(self, config_path="xscout/config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        return {}

    def get(self, key, default=None):
        """Metadata aware get - supports nested keys and Env Vars"""
        # 1. Try Config File
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            if value is not None:
                return value
        except (KeyError, TypeError):
            pass

        # 2. Try Environment Variables (Cloud/Railway Support)
        # Custom mapping for critical keys
        env_map = {
            'api_keys.twitter.bearer_token': 'TWITTER_BEARER_TOKEN',
            'api_keys.linkedin.username': 'LINKEDIN_USERNAME',
            'api_keys.linkedin.password': 'LINKEDIN_PASSWORD',
            'api_keys.callmebot.phone_number': 'WHATSAPP_PHONE',
            'api_keys.callmebot.api_key': 'WHATSAPP_KEY',
            'app.scan_interval_minutes': 'SCAN_INTERVAL',
            'supabase.url': 'SUPABASE_URL',
            'supabase.key': 'SUPABASE_KEY'
        }
        
        if key in env_map:
            return os.getenv(env_map[key], default)
            
        if key == 'keywords':
            val = os.getenv('KEYWORDS')
            if val: return [k.strip() for k in val.split(',')]

        return default

# Global instance for easy access
config = ConfigLoader()
