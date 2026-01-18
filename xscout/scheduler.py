import time
import schedule
from .config.loader import config
from .database.manager import db_manager
from .search_engine.twitter import TwitterProvider
from .search_engine.linkedin import LinkedInProvider
from .nlp.classifier import LeadClassifier
from .notifications.whatsapp import WhatsAppNotifier

class XScoutScheduler:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.keywords = config.get("keywords", [])
        self.min_score = config.get("app.min_intent_score", 7)
        
        # Initialize components
        self.providers = [
            TwitterProvider(
                api_key=config.get("api_keys.twitter.bearer_token")
            ),
            LinkedInProvider(
                email=config.get("api_keys.linkedin.username"),
                password=config.get("api_keys.linkedin.password")
            )
        ]
        self.classifier = LeadClassifier()
        self.notifier = WhatsAppNotifier()

    def scan(self):
        print(f"\n[Scheduler] Starting scan at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        blocked_providers = set()

        for keyword in self.keywords:
            print(f"  > Scanning for keyword: '{keyword}'")
            for provider in self.providers:
                # Skip if this provider already hit a rate limit in this cycle
                if provider in blocked_providers:
                    continue

                # Add delay to respect rate limits (especially Twitter)
                time.sleep(5) 
                
                try:
                    results = provider.search(keyword)
                    self.process_results(results, keyword)
                except Exception as e:
                    error_msg = str(e)
                    
                    if "429" in error_msg or "Too Many Requests" in error_msg:
                        print(f"    [!] Rate Limit hit for {provider.__class__.__name__}. Skipping rest of scan for this provider.")
                        db_manager.log("WARNING", f"Rate limit hit for {provider.__class__.__name__} - Skipping rest of cycle")
                        blocked_providers.add(provider)
                    else:
                        print(f"    ! Error scanning {provider.__class__.__name__}: {error_msg}")
                        db_manager.log("ERROR", f"Scan error on {provider.__class__.__name__}: {error_msg}") 

        print("[Scheduler] Scan complete.")

    def process_results(self, results, keyword):
        for post in results:
            if db_manager.lead_exists(post['post_id']):
                continue  # Skip duplicates

            # Analyze
            analysis = self.classifier.analyze(post['post_text'])
            score = analysis['score']
            
            # Enrich data
            post['matched_keyword'] = keyword
            post['intent_score'] = score
            post['intent_label'] = analysis['label']
            post['contact_info'] = analysis['contact_info']
            
            # Save
            db_manager.add_lead(post)
            
            # Notify
            if score >= self.min_score:
                if self.dry_run:
                    print(f"    [DRY-RUN] High intent lead found ({score}/10): {post['post_text'][:50]}...")
                    db_manager.log("INFO", f"Dry-run lead found: {post['post_id']}")
                else:
                    print(f"    [ALERT] High intent lead found ({score}/10). Sending notification...")
                    success = self.notifier.send_alert(post)
                    if success:
                        db_manager.mark_notified(post['post_id'])
                        db_manager.log("INFO", f"Notification sent for {post['post_id']}")
                    else:
                        db_manager.log("ERROR", f"Failed to notify for {post['post_id']}")

    def get_control_status(self):
        try:
            import json
            import os
            if os.path.exists("xscout/control.json"):
                with open("xscout/control.json", "r") as f:
                    return json.load(f)
        except:
            pass
        return {"running": True, "trigger_now": False}

    def reset_trigger(self):
        try:
            import json
            status = self.get_control_status()
            status["trigger_now"] = False
            with open("xscout/control.json", "w") as f:
                json.dump(status, f)
        except:
            pass

    def start(self):
        interval = config.get("app.scan_interval_minutes", 15)
        print(f"[*] XScout Agent started. Scanning every {interval} minutes.")
        print(f"[*] Dry-run mode: {self.dry_run}")
        
        # Run immediately once on startup
        self.scan()
        
        # Schedule
        schedule.every(interval).minutes.do(self.scan)
        
        print("[*] Waiting for schedule or manual triggers...")
        while True:
            # Check Control File
            status = self.get_control_status()
            
            # Manual Trigger
            if status.get("trigger_now"):
                print("[!] Manual trigger detected. Starting scan...")
                self.reset_trigger()
                self.scan()
            
            # Scheduled Run (only if running is True)
            if status.get("running", True):
                schedule.run_pending()
            
            time.sleep(1)
