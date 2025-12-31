#!/usr/bin/env python3
"""
AI Metadata Generator
Generates titles, descriptions, and tags for videos using Gemini AI
"""

import os
from pathlib import Path
from typing import Dict, Optional
import google.generativeai as genai


class MetadataGenerator:
    """Generate video metadata using AI"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize metadata generator
        
        Args:
            api_key: Gemini API key (or from environment)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Using Gemini 2.5 Flash - best balance of speed and quality
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("✅ Gemini 2.5 Flash initialized")
        else:
            self.model = None
            print("⚠️  No Gemini API key found")
            print("   Set GEMINI_API_KEY environment variable or pass api_key parameter")
    
    def generate_from_filename(self, filename: str, platform: str = "youtube") -> Dict:
        """
        Generate metadata based on filename
        
        Args:
            filename: Video filename
            platform: Target platform (youtube/facebook)
            
        Returns:
            Dict with title, description, tags
        """
        if not self.model:
            return self._fallback_metadata(filename)
        
        prompt = f"""
Generate engaging social media metadata for a video file named: "{filename}"

Platform: {platform}

Generate:
1. TITLE: Catchy, attention-grabbing title (max 100 characters for YouTube)
2. DESCRIPTION: Detailed description explaining what viewers will see (max 500 characters)
3. HASHTAGS: 5-10 relevant hashtags (include the # symbol)

Format your response as JSON:
{{
  "title": "...",
  "description": "...",
  "hashtags": ["#tag1", "#tag2", "#tag3"]
}}

Make it engaging and optimized for {platform}!
"""
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            import json
            import re
            
            text = response.text
            # Find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                data = json.loads(json_match.group())
                
                return {
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'tags': ','.join(data.get('hashtags', []))
                }
        except Exception as e:
            print(f"⚠️  AI generation failed: {e}")
        
        return self._fallback_metadata(filename)
    
    def generate_from_video(self, video_path: str, platform: str = "youtube") -> Dict:
        """
        Generate metadata by analyzing video file
        (Currently uses filename, can be extended to analyze frames)
        
        Args:
            video_path: Path to video file
            platform: Target platform
            
        Returns:
            Dict with metadata
        """
        filename = Path(video_path).stem
        return self.generate_from_filename(filename, platform)
    
    def _fallback_metadata(self, filename: str) -> Dict:
        """Generate basic metadata without AI"""
        # Clean filename
        title = filename.replace('_', ' ').replace('-', ' ').title()
        
        return {
            'title': title[:100],  # Max 100 chars for YouTube
            'description': f"Video: {title}\n\nUploaded via OmniStream",
            'tags': '#viral,#trending,#video'
        }
    
    def enhance_metadata(
        self,
        title: str,
        description: str,
        tags: str,
        platform: str = "youtube"
    ) -> Dict:
        """
        Enhance existing metadata with AI improvements
        
        Args:
            title: Current title
            description: Current description  
            tags: Current tags
            platform: Target platform
            
        Returns:
            Improved metadata
        """
        if not self.model:
            return {'title': title, 'description': description, 'tags': tags}
        
        prompt = f"""
Improve this {platform} post metadata to be more engaging and viral:

Current Title: {title}
Current Description: {description}
Current Tags: {tags}

Generate improved versions that:
- Are more attention-grabbing
- Use emotional triggers
- Include relevant keywords
- Are optimized for {platform} algorithm

Format as JSON:
{{
  "title": "improved title (max 100 chars)",
  "description": "improved description",
  "hashtags": ["#tag1", "#tag2"]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            
            import json
            import re
            
            text = response.text
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                data = json.loads(json_match.group())
                
                return {
                    'title': data.get('title', title),
                    'description': data.get('description', description),
                    'tags': ','.join(data.get('hashtags', tags.split(',')))
                }
        except Exception as e:
            print(f"⚠️  Enhancement failed: {e}")
        
        return {'title': title, 'description': description, 'tags': tags}


if __name__ == "__main__":
    import sys
    
    # Test
    generator = MetadataGenerator()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        platform = sys.argv[2] if len(sys.argv) > 2 else "youtube"
        
        print(f"\n🤖 Generating metadata for: {filename}")
        print(f"Platform: {platform}\n")
        
        metadata = generator.generate_from_filename(filename, platform)
        
        print("=" * 60)
        print(f"Title: {metadata['title']}")
        print(f"\nDescription:\n{metadata['description']}")
        print(f"\nTags: {metadata['tags']}")
        print("=" * 60)
    else:
        print("Usage: python3 metadata_generator.py <filename> [platform]")
        print("Example: python3 metadata_generator.py 'amazing_sunset_timelapse.mp4' youtube")
