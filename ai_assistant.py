"""
AI Assistant Module
Gemini-powered natural language understanding for OmniStream
"""

import google.generativeai as genai
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIAssistant:
    """Base AI assistant with Gemini integration"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.enabled = os.getenv('AI_ENABLED', 'true').lower() == 'true'
        self.model_name = os.getenv('AI_MODEL', 'gemini-1.5-flash')
        
        if self.enabled and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
    
    def is_available(self) -> bool:
        """Check if AI is configured and available"""
        return self.enabled and self.model is not None


class AICommandParser(AIAssistant):
    """Parse natural language commands into structured download configurations"""
    
    def __init__(self):
        super().__init__()
        self.conversation_history = []
    
    def parse_command(self, user_input: str, detected_url: str = None, site_info: Dict = None) -> Dict:
        """
        Parse natural language command into structured config
        
        Args:
            user_input: Natural language command
            detected_url: URL if already provided
            site_info: Site detection info from SiteDetector
            
        Returns:
            Structured configuration with confidence score
        """
        if not self.is_available():
            return self._fallback_parse(user_input, detected_url)
        
        # Build context
        context = self._get_recent_context()
        site_context = ""
        if site_info:
            site_context = f"\nDetected Site: {site_info['name']}\nAvailable Content Types: {', '.join(site_info['content_types'])}\nQuality Options: {', '.join(site_info['quality_options'])}"
        
        prompt = f"""You are OmniStream's download configuration parser. Parse natural language into precise download settings.

Recent Context:
{context}

Current Input: "{user_input}"
URL: {detected_url or "Not provided"}{site_context}

Parse into JSON with this EXACT structure:
{{
  "url": "validated URL or null if missing",
  "content_type": "one of: All Videos, Shorts Only, Reels Only, Stories Only, Audio Only, Clips Only",
  "scope": "single, playlist, channel, or date_range",
  "max_downloads": positive integer or null (for 'latest N'),
  "date_from": "YYYY-MM-DD or null",
  "date_to": "YYYY-MM-DD or null",
  "quality": "Best Available, 4K, 1440p, 1080p, 720p, 480p, or Audio Only",
  "download_subtitles": boolean,
  "skip_existing": boolean,
  "interpretation": "clear 1-sentence explanation of what will be downloaded",
  "confidence": integer 0-100,
  "ambiguities": ["list any unclear aspects"],
  "suggestions": ["alternative interpretations if ambiguous"],
  "needs_clarification": boolean
}}

CRITICAL RULES:
1. If URL not in input, set url to null and needs_clarification to true
2. Convert relative dates ("last week" → actual YYYY-MM-DD dates)
3. Default quality is "Best Available" unless specified
4. If count not specified for bulk operations, set max_downloads to null (unlimited)
5. Confidence < 70 means ambiguous, add to ambiguities list
6. Today's date: {datetime.now().strftime('%Y-%m-%d')}

Examples:
- "all MrBeast shorts from December" → content_type: "Shorts Only", date_from: "2024-12-01", date_to: "2024-12-31"
- "latest 10 videos" → max_downloads: 10, needs_clarification: true (missing URL)
- "grab this video in 720p" → quality: "720p", scope: "single"
- "download the playlist" → scope: "playlist", needs_clarification: false if URL provided

Return ONLY valid JSON, no markdown formatting."""

        try:
            response = self.model.generate_content(prompt)
            config = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            
            # Post-processing validation
            validated = self._validate_and_enhance(config, detected_url, site_info)
            
            # Add to conversation history
            self.conversation_history.append({
                'input': user_input,
                'output': validated,
                'timestamp': datetime.now().isoformat()
            })
            
            return validated
            
        except Exception as e:
            return {
                'error': str(e),
                'fallback': True,
                'interpretation': f"AI parsing failed: {str(e)}. Using manual configuration.",
                'confidence': 0,
                'needs_clarification': True
            }
    
    def _validate_and_enhance(self, config: Dict, detected_url: str, site_info: Dict) -> Dict:
        """Validate AI output and add safety checks"""
        
        # Ensure URL is set if provided
        if detected_url and not config.get('url'):
            config['url'] = detected_url
        
        # Validate content type against site capabilities
        if site_info and config.get('content_type'):
            if config['content_type'] not in site_info['content_types']:
                # Find closest match
                config['content_type'] = site_info['content_types'][0]
                config.setdefault('warnings', []).append(
                    f"Content type adjusted to match site capabilities"
                )
        
        # Cap excessive counts (safety)
        if config.get('max_downloads', 0) > 500:
            config['max_downloads'] = 500
            config.setdefault('warnings', []).append('Count capped at 500 for safety')
        
        # Validate date ranges
        date_from = config.get('date_from')
        date_to = config.get('date_to')
        
        if date_from and date_to:
            try:
                from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                
                if from_dt > to_dt:
                    config['date_from'], config['date_to'] = config['date_to'], config['date_from']
                    config.setdefault('warnings', []).append('Date range was reversed, corrected automatically')
            except:
                pass
        
        # Set defaults
        config.setdefault('download_subtitles', False)
        config.setdefault('skip_existing', True)
        config.setdefault('quality', 'Best Available')
        
        return config
    
    def _fallback_parse(self, user_input: str, detected_url: str) -> Dict:
        """Simple fallback parsing when AI unavailable"""
        return {
            'url': detected_url,
            'content_type': 'All Videos',
            'scope': 'single',
            'quality': 'Best Available',
            'download_subtitles': False,
            'skip_existing': True,
            'interpretation': 'AI unavailable - using default settings',
            'confidence': 50,
            'fallback': True,
            'needs_clarification': not detected_url
        }
    
    def _get_recent_context(self) -> str:
        """Get recent conversation context"""
        if not self.conversation_history:
            return "No previous context"
        
        recent = self.conversation_history[-3:]  # Last 3 interactions
        context_lines = []
        for item in recent:
            context_lines.append(f"User: {item['input']}")
            context_lines.append(f"Parsed: {item['output'].get('interpretation', 'N/A')}")
        
        return "\n".join(context_lines)


class AIContentDetector(AIAssistant):
    """Analyze unknown sites using AI + Playwright"""
    
    def analyze_unknown_site(self, url: str, html_snippet: str = None, 
                            media_urls: List[str] = None) -> Dict:
        """
        Use AI to analyze unknown site structure
        
        Args:
            url: Target URL
            html_snippet: HTML content (first 2000 chars)
            media_urls: List of detected media URLs
            
        Returns:
            Analysis with extraction strategy
        """
        if not self.is_available():
            return {'strategy': 'playwright', 'confidence': 50}
        
        prompt = f"""Analyze this webpage for downloadable media content:

URL: {url}
Media URLs found: {media_urls[:10] if media_urls else 'None detected'}
HTML snippet: {html_snippet[:2000] if html_snippet else 'Not provided'}

Identify and return JSON:
{{
  "media_type": "video, audio, or mixed",
  "player_type": "youtube_embed, custom_player, direct_file, m3u8_stream, or unknown",
  "extraction_method": "yt-dlp, direct_download, playwright_capture, or api",
  "requires_authentication": boolean,
  "anti_bot_level": "none, basic, or advanced",
  "recommended_strategy": "specific approach description",
  "confidence": 0-100
}}

Return ONLY valid JSON."""

        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        except:
            return {'strategy': 'playwright', 'confidence': 50}


class AIErrorPredictor(AIAssistant):
    """Predict potential issues before download starts"""
    
    def predict_issues(self, url: str, config: Dict, site_info: Dict) -> Dict:
        """
        Analyze configuration for potential problems
        
        Args:
            url: Target URL
            config: Download configuration
            site_info: Site detection info
            
        Returns:
            Predicted issues and recommendations
        """
        if not self.is_available():
            return {'predicted_issues': [], 'risk_score': 0}
        
        prompt = f"""Review this download configuration for potential issues:

URL: {url}
Site: {site_info.get('name', 'Unknown')}
Config: {json.dumps(config, indent=2)}

Check for:
1. URL accessibility (geo-blocks, authentication requirements)
2. Format compatibility issues
3. Excessive resource usage (too many videos, large file sizes)
4. Known site-specific issues
5. Cookie/authentication requirements

Return JSON:
{{
  "predicted_issues": [
    {{
      "type": "authentication|geo_block|rate_limit|format|size|other",
      "severity": "low|medium|high",
      "description": "clear explanation",
      "prevention": "specific action to avoid issue"
    }}
  ],
  "estimated_download_time": "human-readable estimate",
  "estimated_total_size": "size estimate",
  "risk_score": 0-100,
  "recommendations": ["list of suggestions"]
}}

Return ONLY valid JSON."""

        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        except:
            return {'predicted_issues': [], 'risk_score': 0}


class AIErrorDiagnostics(AIAssistant):
    """Diagnose download failures and suggest fixes"""
    
    def diagnose_failure(self, error: Exception, context: Dict) -> Dict:
        """
        Analyze error and suggest fixes
        
        Args:
            error: Exception that occurred
            context: Download context (URL, config, etc.)
            
        Returns:
            Diagnosis with fix suggestions
        """
        if not self.is_available():
            return {
                'diagnosis': 'AI diagnostics unavailable',
                'suggestions': ['Check error message manually']
            }
        
        prompt = f"""Diagnose this download failure and suggest fixes:

Error: {str(error)}
Error Type: {type(error).__name__}
Context: {json.dumps(context, indent=2)}

Provide JSON:
{{
  "root_cause": "likely cause of failure",
  "severity": "minor|moderate|critical",
  "user_friendly_explanation": "explain in simple terms",
  "fix_suggestions": [
    {{
      "action": "specific step to try",
      "likelihood": "high|medium|low chance of fixing",
      "technical_details": "why this might work"
    }}
  ],
  "requires_user_action": boolean,
  "auto_fixable": boolean
}}

Return ONLY valid JSON."""

        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        except:
            return {
                'diagnosis': 'Diagnostic analysis failed',
                'suggestions': ['Review error message and try manual configuration']
            }
