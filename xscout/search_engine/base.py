from abc import ABC, abstractmethod

class SearchProvider(ABC):
    @abstractmethod
    def search(self, query, count=10):
        """
        Search for posts matching the query.
        Must return a list of dictionaries with keys:
        - platform (str)
        - post_id (str)
        - post_text (str)
        - username (str)
        - profile_url (str)
        - timestamp (datetime)
        """
        pass
