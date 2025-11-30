from openai import OpenAI
import os
from dotenv import load_dotenv
from .news_fetcher import NewsFetcher
import json

load_dotenv()

class AIAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.news_fetcher = NewsFetcher()
        self.model = "gpt-4o-mini"  # Use a stable model
        self.pending_news_request = None  # Track if we need to fetch news
        
    def _build_context_from_news(self, articles):
        """Build context string from news articles"""
        if not articles:
            return "\n\n--- NO NEWS FOUND ---\nNo recent articles found for this query.\n"
        
        context = "\n\n--- CURRENT NEWS CONTEXT (ACTIVE NEWS DATA) ---\n"
        context += "IMPORTANT: The following are REAL, CURRENT news articles. Present them to the user.\n\n"
        for i, article in enumerate(articles, 1):
            context += f"{i}. **{article['title']}**\n"
            context += f"   Source: {article['source']} | Published: {article['published']}\n"
            if article['description']:
                context += f"   Summary: {article['description']}\n"
            context += f"   URL: {article['url']}\n\n"
        context += "--- END NEWS CONTEXT ---\n\n"
        context += "INSTRUCTION: Present these news items to the user in a clear, readable format. Do NOT ask for confirmation - the data is already fetched.\n\n"
        return context
    
    def _detect_news_query(self, message, conversation_history):
        """Detect if we should fetch news"""
        news_keywords = ['news', 'latest', 'current', 'today', 'recent', 'happening', 
                        'what\'s new', 'update', 'events', 'headlines', 'stories']
        message_lower = message.lower()
        
        # Direct news request
        if any(keyword in message_lower for keyword in news_keywords):
            return True
    
        # Check if this is a confirmation/follow-up to a news request
        if conversation_history:
            confirmation_keywords = ['yes', 'yeah', 'sure', 'please', 'go ahead', 'do it', 
                                    'ok', 'okay', 'proceed', 'fetch', 'pull', 'get', 'show', 'new']
            last_assistant_msg = None
            for msg in reversed(conversation_history):
                if msg['role'] == 'assistant':
                    last_assistant_msg = msg['content'].lower()
                    break
            
            # If assistant was asking about news and user confirms
            if last_assistant_msg and any(kw in message_lower for kw in confirmation_keywords):
                if any(word in last_assistant_msg for word in ['headline', 'news', 'fetch', 'pull', 'stories']):
                    return True
        
        return False
    
    def _extract_search_params(self, message, conversation_history):
        """Extract search parameters from conversation context"""
        # Combine recent messages for context
        context_messages = []
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            context_messages.append(f"{msg['role']}: {msg['content']}")
        context_messages.append(f"user: {message}")
        full_context = "\n".join(context_messages)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": """Extract news search parameters from the conversation. Output ONLY valid JSON.

                Example output:
                {"query": "cybersecurity", "category": "technology", "country": "us", "limit": 5}

                Categories: business, entertainment, general, health, science, sports, technology
                If no specific topic, use the most relevant general query.
                Always include a query - never leave it empty."""
                                }, {
                                    "role": "user", 
                                    "content": f"Conversation:\n{full_context}\n\nExtract search parameters:"
                                }],
                                temperature=0
                            )
            
            result = response.choices[0].message.content.strip()
            # Clean up potential markdown formatting
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            
            params = json.loads(result)
            return params
        except Exception as e:
            print(f"Error extracting params: {e}")
            # Fallback: extract keywords from message
            return {"query": message, "category": "technology", "limit": 5}
    
    def chat(self, message, conversation_history=None, model='gpt-4o-mini'):
        """Main chat function with news awareness"""
        if conversation_history is None:
            conversation_history = []
        
        context = ""
        has_news = False
        
        # Check if we should fetch news
        if self._detect_news_query(message, conversation_history):
            # Extract search parameters from full conversation
            params = self._extract_search_params(message, conversation_history)
            print(f"Fetching news with params: {params}")  # Debug log
            
            # Try headlines first, then search
            articles = self.news_fetcher.get_top_headlines(
                query=params.get("query"),
                category=params.get("category"),
                country=params.get("country", "us"),
                limit=params.get("limit", 5)
            )
            
            # If no headlines, try search endpoint
            if not articles and params.get("query"):
                articles = self.news_fetcher.search_news(
                    query=params.get("query"),
                    days_back=params.get("days_back", 7),
                    limit=params.get("limit", 5)
                )
            
            context = self._build_context_from_news(articles)
            has_news = bool(articles)
        
        # Build messages for API
        messages = [
            {
                "role": "system",
                "content": """You are a helpful AI assistant with access to real-time news data.

            IMPORTANT RULES:
            1. When you receive news context (marked with "--- CURRENT NEWS CONTEXT ---"), these are REAL articles that have been fetched. Present them immediately to the user.
            2. Do NOT ask for confirmation before showing news - just show it.
            3. Format news clearly with titles, sources, dates, and brief summaries.
            4. Always cite the source for each news item.
            5. If the user asks follow-up questions about the news, answer based on the provided context.
            6. If no news context is provided, you can discuss general topics or ask clarifying questions."""
                        }
                    ]
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current user message with context
        user_message = context + message if context else message
        messages.append({"role": "user", "content": user_message})
        
        # Get response
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        
        return {
            "response": assistant_message,
            "has_news_context": has_news,
            "conversation_history": conversation_history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": assistant_message}
            ]
        }


# Usage example
if __name__ == "__main__":
    assistant = AIAssistant()
    
    # First message
    result = assistant.chat("What's the latest news in technology?")
    print(result["response"])
    print("\n" + "="*50 + "\n")
    
    # Follow-up
    result = assistant.chat(
        "Tell me more about cybersecurity",
        conversation_history=result["conversation_history"]
    )
    print(result["response"])