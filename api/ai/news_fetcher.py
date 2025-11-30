import requests
from datetime import datetime, timedelta
import os

class NewsFetcher:
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")  # Get free key from newsapi.org
        self.base_url = "https://newsapi.org/v2"
    
    def get_top_headlines(self, query=None, category=None, country='us', limit=5):
        """Fetch top headlines from News API"""
        endpoint = f"{self.base_url}/top-headlines"
        params = {
            'apiKey': self.news_api_key,
            'country': country,
            'pageSize': limit
        }
        
        if query:
            params['q'] = query
        if category:
            params['category'] = category
            
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            articles = response.json().get('articles', [])
            return self._format_articles(articles)
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def search_news(self, query, days_back=7, limit=5):
        """Search for news articles"""
        endpoint = f"{self.base_url}/everything"
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        params = {
            'apiKey': self.news_api_key,
            'q': query,
            'from': from_date,
            'sortBy': 'publishedAt',
            'pageSize': limit,
            'language': 'en'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            articles = response.json().get('articles', [])
            return self._format_articles(articles)
        except Exception as e:
            print(f"Error searching news: {e}")
            return []
    
    def _format_articles(self, articles):
        """Format articles for context"""
        formatted = []
        for article in articles:
            formatted.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'source': article.get('source', {}).get('name'),
                'published': article.get('publishedAt'),
                'url': article.get('url')
            })
        return formatted