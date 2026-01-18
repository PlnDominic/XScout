class LeadClassifier:
    def __init__(self):
        self.high_intent_keywords = [
            "urgently", "budget", "looking to hire", "pay", "quote", "startup", "launching"
        ]
        self.negative_keywords = [
            "hiring", "job", "vacancy", "career", "join our team", "salary", "recruit", "looking for a job"
        ]

    def score_text(self, text):
        """
        Score the text from 0 to 10 based on intent.
        Returns (score, explanation)
        """
        text = text.lower()
        score = 0
        
        # Check for negative keywords (Recruitment/Job posts)
        for bad_word in self.negative_keywords:
            if bad_word in text:
                return 0  # Immediate zero for recruitment posts

        # Base score for matching a search query (assumed if it got here)
        score += 3

        # Intent boosters
        for word in self.high_intent_keywords:
            if word in text:
                score += 2
        
        # 'I need' or 'We need' pattern is strong
        if "need a" in text or "looking for a" in text:
            score += 2

        return min(score, 10)

    def get_intent_label(self, score):
        if score >= 8:
            return "High"
        elif score >= 5:
            return "Medium"
        else:
            return "Low"

    def extract_contact_info(self, text):
        import re
        info = []
        # Email regex
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if emails:
            info.append(f"Emails: {', '.join(emails)}")
        
        # DM/Inbox mentions
        if "dm" in text.lower() or "inbox" in text.lower() or "message me" in text.lower():
            info.append("Request: DM/Inbox")
            
        return " | ".join(info) if info else "None"

    def analyze(self, text):
        score = self.score_text(text)
        return {
            "score": score,
            "label": self.get_intent_label(score),
            "contact_info": self.extract_contact_info(text)
        }
