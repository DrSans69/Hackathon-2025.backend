from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.vectorstores import Chroma
from django.conf import settings
from typing import List, Dict, Optional
import json
import re
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi
from io import BytesIO
import docx
import requests
from bs4 import BeautifulSoup

class MentorService:
    """
    Core AI mentor service using LangChain and OpenAI.
    Handles adaptive teaching, resource recommendations, and quiz generation.
    """
    
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        # Modern way to store chat history
        self.recommended_sources = []  # Store AI-recommended sources
        self.approved_sources = []  # Store user-approved sources
        

    
    def recommend_resources(
        self, 
        topic: str, 
        learning_style: str = "mixed",
        num_resources: int = 7
    ) -> List[Dict]:
        """
        Recommend high-quality external resources with enhanced curation.
        
        Args:
            topic: Learning topic
            learning_style: visual | reading | interactive | mixed
            num_resources: Number of resources to recommend (default 7)
        
        Returns:
            List of curated resource recommendations
        """
        learning_style_context = {
            "visual": "Prioritize video content, diagrams, and visual explanations",
            "reading": "Focus on articles, textbooks, and written tutorials",
            "interactive": "Emphasize interactive exercises, coding playgrounds, and hands-on labs",
            "mixed": "Provide a balanced mix of videos, articles, and interactive resources"
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert educational resource curator with deep knowledge of online learning platforms.

            Learning Style Preference: {learning_style} - {learning_style_context.get(learning_style, '')}

            Recommend ONLY from these trusted sources:
            
            VIDEO PLATFORMS:
            - YouTube channels: Khan Academy, MIT OpenCourseWare, Crash Course, 3Blue1Brown, freeCodeCamp
            - Coursera, edX, Udacity (free courses)
            
            READING MATERIALS:
            - MDN Web Docs (web development)
            - GeeksforGeeks, Real Python (programming)
            - Khan Academy articles
            - MIT OCW lecture notes
            - Wikipedia (for overviews)
            
            INTERACTIVE:
            - Codecademy, freeCodeCamp (programming)
            - Brilliant.org (math/science)
            - LeetCode, HackerRank (coding practice)
            
            Return ONLY valid JSON array:
            [
            {{
                "title": "specific resource title",
                "type": "video|article|interactive|pdf|course",
                "source": "platform name (YouTube, Khan Academy, etc.)",
                "url": "direct URL or specific search query",
                "duration": "estimated time (e.g., '15 min', '2 hours', '4 weeks')",
                "difficulty": "beginner|intermediate|advanced",
                "description": "why this resource is valuable (2-3 sentences)",
                "key_topics": ["topic1", "topic2", "topic3"]
            }}
            ]

            Requirements:
            - Provide {num_resources} resources
            - Mix difficulty levels (start easier, progress harder)
            - Include variety of formats
            - Use REAL, existing resources (not made-up)
            - Prefer free resources
            - Include specific URLs when possible
            - For YouTube, include channel name and video title"""),
            ("human", f"""Topic: {topic}
            
            Recommend {num_resources} high-quality learning resources in JSON format.""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        parsed = self._parse_json_response(response.content)
        
        if "raw_response" in parsed:
            return []
        
        resources = parsed if isinstance(parsed, list) else []
        
        # Store for potential approval
        self.recommended_sources = resources
        
        return resources

    def parse_external_resources(
        self,
        resources: List[Dict],
        max_content_length: int = 10000
    ) -> Dict:
        """
        Parse content from various external resource types into plain text.
        
        Args:
            resources: List of resource dicts with 'type', 'url', 'title'
            max_content_length: Maximum characters to extract per resource
        
        Returns:
            Dict with parsed content and metadata
        """
        parsed_resources = []
        
        for resource in resources:
            resource_type = resource.get('type', '').lower()
            url = resource.get('url', '')
            title = resource.get('title', 'Untitled')
            
            try:
                if resource_type == 'video' and ('youtube.com' in url or 'youtu.be' in url):
                    content = self._parse_youtube_video(url, max_content_length)
                    
                elif resource_type == 'article' or resource_type == 'webpage':
                    content = self._parse_webpage(url, max_content_length)
                    
                elif resource_type == 'pdf' and url:
                    content = self._parse_pdf_from_url(url, max_content_length)
                    
                else:
                    # Generic web scraping fallback
                    content = self._parse_webpage(url, max_content_length)
                
                if content:
                    parsed_resources.append({
                        'title': title,
                        'type': resource_type,
                        'url': url,
                        'content': content,
                        'word_count': len(content.split()),
                        'source': resource.get('source', 'Unknown')
                    })
                    
            except Exception as e:
                print(f"Error parsing {title} ({url}): {e}")
                parsed_resources.append({
                    'title': title,
                    'type': resource_type,
                    'url': url,
                    'content': f"[Could not parse content: {str(e)}]",
                    'error': str(e)
                })
        
        return {
            'total_resources': len(resources),
            'successfully_parsed': len([r for r in parsed_resources if 'error' not in r]),
            'resources': parsed_resources,
            'total_words': sum(r.get('word_count', 0) for r in parsed_resources)
        }
    
    
    def process_uploaded_materials(self, files: List[Dict]) -> Dict:
        """
        Process uploaded study materials (PDFs, DOCX, TXT, URLs, YouTube videos).
        
        Args:
            files: List of dicts with:
                - For files: 'filename', 'content' (bytes), 'content_type'
                - For URLs: 'filename', 'url', 'content_type' = 'url/webpage' or 'url/youtube'
        
        Returns:
            Summary of processed materials
        """
        processed_count = 0
        failed_items = []
        total_text = ""
        max_content_length = 10000  # Max chars per resource
        
        for file_data in files:
            filename = file_data.get('filename', 'Untitled')
            content = file_data.get('content')  # bytes or None
            content_type = file_data.get('content_type', '')
            url = file_data.get('url', '')
            
            try:
                text = None
                
                # Handle YouTube videos
                if 'youtube' in content_type.lower() or ('url' in content_type.lower() and url and ('youtube.com' in url or 'youtu.be' in url)):
                    text = self._parse_youtube_video(url, max_content_length)
                    if text and not text.startswith('['):  # Check if parsing was successful
                        filename = f"[YouTube] {filename}"
                    else:
                        raise Exception(f"Failed to extract YouTube transcript: {text}")
                
                # Handle webpages/URLs
                elif 'url' in content_type.lower() or 'webpage' in content_type.lower():
                    if not url:
                        raise Exception("URL not provided for webpage")
                    text = self._parse_webpage(url, max_content_length)
                    if text.startswith('[Could not'):
                        raise Exception(text)
                    filename = f"[Webpage] {filename}"
                
                # Handle PDF files
                elif content and ('pdf' in content_type.lower()):
                    text = self._extract_pdf_text(content)
                
                # Handle DOCX files
                elif content and ('docx' in content_type.lower() or 'word' in content_type.lower()):
                    text = self._extract_docx_text(content)
                
                # Handle plain text files
                elif content and ('text' in content_type.lower() or 'txt' in content_type.lower()):
                    text = content.decode('utf-8')
                
                # Handle PDF from URL``
                elif url and url.endswith('.pdf'):
                    text = self._parse_pdf_from_url(url, max_content_length)
                    if text.startswith('[Could not'):
                        raise Exception(text)
                    filename = f"[PDF URL] {filename}"
                
                else:
                    failed_items.append({
                        'filename': filename,
                        'error': f"Unsupported content type: {content_type}"
                    })
                    continue
                
                if text:
                    self.approved_sources.append({
                        'filename': filename,
                        'text': text,
                        'word_count': len(text.split()),
                        'source_type': 'youtube' if 'YouTube' in filename else 'webpage' if 'Webpage' in filename else 'file',
                        'url': url if url else None
                    })
                    
                    total_text += f"\n\n=== {filename} ===\n{text}"
                    processed_count += 1
                
            except Exception as e:
                failed_items.append({
                    'filename': filename,
                    'error': str(e)
                })
                print(f"Error processing {filename}: {e}")
        
        # Generate summary of uploaded content
        summary = self._summarize_materials(total_text) if total_text else "No materials successfully processed."
        
        return {
            'processed_files': processed_count,
            'total_files': len(files),
            'failed_files': len(failed_items),
            'failures': failed_items,
            'materials': self.approved_sources,
            'summary': summary,
            'total_words': sum(m['word_count'] for m in self.approved_sources)
        }
    
    def generate_topic_name_from_materials(self) -> str:
        """
        Generate a short, concise topic name based on uploaded materials.
        
        Returns:
            A brief topic name (2-5 words)
        """
        
        # Combine text from all materials (limited preview)
        combined_text = "\n\n".join([
            f"{m['filename']}\n{m['text'][:1000]}"
            for m in self.uploaded_materials
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are analyzing study materials to identify the core topic.
            
            Based on the content, generate a SHORT topic name (2-5 words maximum).
            
            Requirements:
            - Be specific and descriptive
            - Use standard academic terminology
            - Capture the main subject area
            - Keep it concise
            
            Return ONLY the topic name, nothing else.
            
            Examples:
            - "Calculus Fundamentals"
            - "Organic Chemistry"
            - "Python Programming"
            - "World War II History"
            - "Machine Learning Basics"
            """),
            ("human", "What is the main topic of these materials?\n\n{materials}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"materials": combined_text})
        
        # Clean up response (remove quotes, extra whitespace)
        topic_name = response.content.strip().strip('"').strip("'")
        
        return topic_name

    def generate_study_notes(
        self,
        topic: str,
        difficulty: str = "medium",
        explanation_mode: str = "standard",
    ) -> str:
        """
        Generate comprehensive study notes in Markdown format based on topic and materials.
        
        Args:
            topic: The topic to generate notes for
            difficulty: easy | medium | hard
            explanation_mode: standard | eli12 | expert | practical | analogy
            include_images: Whether to include image references from approved sources
            
        Returns:
            Markdown formatted study notes
        """
        # Prepare materials context
        materials_text = "\n\n".join([
            f"From {m['filename']}:\n{m['text'][:2000]}..."
            for m in self.uploaded_materials
        ]) if self.uploaded_materials else "No uploaded materials available."
        
        # Prepare approved sources context
        sources_context = ""
        image_sources = []
        
        if self.approved_sources:
            sources_context = "\n\nApproved External Sources:\n"
            for source in self.approved_sources:
                sources_context += f"- {source['type']}: {source['title']} ({source.get('url', 'N/A')})\n"
                
                
        
        # Explanation mode descriptions
        mode_prompts = {
            "standard": "Clear and balanced explanations suitable for general learning",
            "eli12": "Simple language as if explaining to a 12-year-old, with everyday examples",
            "expert": "Technical and detailed, assuming advanced knowledge",
            "practical": "Focus on real-world applications and hands-on usage",
            "analogy": "Use creative analogies and metaphors to explain concepts"
        }
        
        difficulty_context = {
            "easy": "Keep explanations simple and foundational. Focus on basic concepts.",
            "medium": "Balance fundamentals with some depth. Include intermediate examples.",
            "hard": "Dive deep into complex aspects. Include advanced topics and nuances."
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are creating comprehensive study notes in Markdown format.

            Topic: {topic}
            Difficulty Level: {difficulty} - {difficulty_context.get(difficulty, '')}
            Explanation Mode: {explanation_mode} - {mode_prompts.get(explanation_mode, mode_prompts['standard'])}

            Generate well-structured Markdown notes with:

            1. **Title and Overview**
            - Topic name as # heading
            - Brief introduction (what and why it matters)

            2. **Main Points** (use ## headings)
            - 5-8 key concepts
            - Each with clear explanations
            - Bullet points for sub-topics
            - Code blocks for technical examples (if applicable)

            3. **Visual Elements**
            - Use > blockquotes for important notes
            - Use **bold** for key terms
            - Use `code` for technical terms

            4. **Examples**
            - Practical examples for each main point
            - Use ``` code blocks where relevant

            5. **Common Mistakes** (if applicable)
            - What learners typically get wrong

            6. **Practice Tips**
            - How to apply this knowledge
            - Suggested exercises

            7. **Further Reading**
            - Reference the approved sources
            - Link to specific sections/chapters

            Format Requirements:
            - Use proper Markdown syntax
            - Include table of contents with links
            - Use horizontal rules (---) to separate sections
            - Add emoji icons where appropriate (📚 💡 ⚠️ ✅ ❌)

            Base your content on the provided materials and sources."""),
            ("human", f"""Create comprehensive study notes for: {topic}

            UPLOADED MATERIALS:
            {materials_text}

            {sources_context}

            Generate complete Markdown study notes following the structure above.""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        markdown_content = response.content
        
        
        # Add metadata header
        metadata = f"""---
                    generated: {self._get_current_datetime()}
                    topic: {topic}
                    difficulty: {difficulty}
                    mode: {explanation_mode}
                    sources: {len(self.approved_sources)}
                    ---

                    """
        
        return metadata + markdown_content


    def set_approved_sources(self, approved_indices: List[int]) -> Dict:
        """
        User approves which recommended sources to use.
        
        Args:
            approved_indices: List of indices from recommended_sources to approve
        """
        self.approved_sources = [
            self.recommended_sources[i] 
            for i in approved_indices 
            if i < len(self.recommended_sources)
        ]
        
        return {
            'approved_count': len(self.approved_sources),
            'approved_sources': self.approved_sources
        }
            
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response."""
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        # Also try without the json tag
        if not json_match:
            json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
        
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Try to find JSON in the response
            try:
                # Look for array or object patterns
                array_match = re.search(r'\[.*\]', response, re.DOTALL)
                if array_match:
                    return json.loads(array_match.group(0))
                
                obj_match = re.search(r'\{.*\}', response, re.DOTALL)
                if obj_match:
                    return json.loads(obj_match.group(0))
            except:
                pass
            
            return {"raw_response": response}
        
    
    
    def _check_answer_similarity(self, answer1: str, answer2: str) -> bool:
        """Basic answer similarity check."""
        # Simple implementation - can be enhanced with embeddings
        return answer1.strip().lower() == answer2.strip().lower()
    
    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        pdf_file = BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def _extract_docx_text(self, docx_bytes: bytes) -> str:
        """Extract text from DOCX bytes."""
        docx_file = BytesIO(docx_bytes)
        doc = docx.Document(docx_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    def _summarize_materials(self, text: str) -> str:
        """Generate summary of uploaded materials."""
        if not text.strip():
            return "No materials uploaded."
        
        # Truncate if too long
        text_preview = text[:4000]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are analyzing student study materials. 
            
            Provide a brief summary (3-4 sentences) covering:
            - Main topics covered
            - Depth level (beginner/intermediate/advanced)
            - What's missing or could be supplemented"""),
                        ("human", "Summarize these study materials:\n\n{text}")
                    ])
        
        chain = prompt | self.llm
        response = chain.invoke({"text": text_preview})
        
        return response.content
    
    def _parse_youtube_video(self, url: str, max_length: int) -> str:
        """
        Extract transcript from YouTube video.
        """
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return "[Could not extract YouTube video ID]"
        
        try:
            # Try to get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine transcript segments
            full_transcript = " ".join([segment['text'] for segment in transcript_list])
            
            # Truncate if needed
            if len(full_transcript) > max_length:
                full_transcript = full_transcript[:max_length] + "..."
            
            return full_transcript
            
        except Exception as e:
            # Fallback: return video metadata
            return f"[YouTube video transcript unavailable. Video ID: {video_id}]"


    def _parse_webpage(self, url: str, max_length: int) -> str:
        """
        Extract text content from webpage.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Truncate
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            return f"[Could not parse webpage: {str(e)}]"


    def _parse_pdf_from_url(self, url: str, max_length: int) -> str:
        """
        Download and extract text from PDF URL.
        """
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            text = self._extract_pdf_text(response.content)
            
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            return f"[Could not download/parse PDF: {str(e)}]"


    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([^&\s]+)',
            r'(?:youtu\.be\/)([^&\s]+)',
            r'(?:youtube\.com\/embed\/)([^&\s]+)',
            r'(?:youtube\.com\/v\/)([^&\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None


    def add_parsed_resources_to_materials(self, parsed_resources: Dict) -> Dict:
        """
        Add successfully parsed external resources to uploaded_materials 
        for use in course generation and study notes.
        """
        added_count = 0
        
        for resource in parsed_resources.get('resources', []):
            if 'error' not in resource and resource.get('content'):
                self.uploaded_materials.append({
                    'filename': f"[EXTERNAL] {resource['title']}",
                    'text': resource['content'],
                    'word_count': resource.get('word_count', 0),
                    'source_type': 'external',
                    'url': resource.get('url', ''),
                    'resource_type': resource.get('type', 'unknown')
                })
                added_count += 1
        
        return {
            'added_to_materials': added_count,
            'total_materials': len(self.uploaded_materials)
        }

    def _get_current_datetime(self) -> str:
        """Get current datetime as string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
