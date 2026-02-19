"""
Review analysis module - LLM + Business Rules
"""
import json
import logging
import re
from typing import Dict, List, Tuple
from groq import Groq
import config
from prompts import (
    REVIEW_ANALYSIS_PROMPT, 
    REJECTION_REASONS_RULES,
    PRICE_PATTERNS, 
    CONTACT_PATTERNS, 
    OWNER_NAME_PATTERNS,
    PROFANITY_PATTERNS,
    SUSPICIOUS_LINK_PATTERNS,
    PROMPT_VERSION
)

logger = logging.getLogger(__name__)

client = None

def _get_client():
    """Lazy-load Groq client on first use"""
    global client
    if client is None:
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is not set. Please add it to your .env file.")
        client = Groq(api_key=config.GROQ_API_KEY)
    return client

class ReviewAnalyzer:
    """Analyze reviews using LLM and business rules"""
    
    def __init__(self):
        self.model_name = config.LLM_MODEL
        self.prompt_version = PROMPT_VERSION
    
    def analyze_review(self, review_id: str, hotel_id: str, rating: int, review_text: str) -> Dict:
        """
        Analyze a single review - comprehensive extraction + decision
        """
        try:
            signals, topic_tags, flags = self._analyze_with_llm(rating, review_text)
            
            signals = self._enhance_signals_with_regex(review_text, signals)
            
            sentiment = self._determine_sentiment(signals['sentiment'], rating)
            
            publish_decision, rejection_reasons = self._apply_publishing_rules(signals)
            
            sentiment_tag = self._get_sentiment_tag(sentiment)
            all_tags = self._generate_tags(signals, topic_tags, sentiment_tag)
            
            summary = signals.get('summary', self._auto_summarize(review_text))
            
            analysis_result = {
                "review_id": review_id,
                "hotel_id": hotel_id,
                "rating": rating,
                "review_text": review_text,
                "summary": summary,
                "sentiment": sentiment,
                "publish_decision": publish_decision,
                "rejection_reasons": rejection_reasons,
                "tags": all_tags,
                "detected_signals": signals,
                "flags": flags,
                "model_name": self.model_name,
                "prompt_version": self.prompt_version
            }
            
            return analysis_result
        
        except Exception as e:
            logger.error(f"Error analyzing review {review_id}: {e}")
            return self._get_safe_default_analysis(review_id, hotel_id, rating, review_text)
    
    def _analyze_with_llm(self, rating: int, review_text: str) -> Tuple[Dict, List[str], List[str]]:
        """Call LLM to analyze review"""
        try:
            prompt = REVIEW_ANALYSIS_PROMPT.format(
                rating=rating,
                review_text=review_text
            )
            
            response = _get_client().chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                timeout=30
            )
            
            response_text = response.choices[0].message.content.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(response_text)
            
            signals = analysis.get('signals', {})
            topic_tags = analysis.get('topic_tags', [])
            flags = analysis.get('flags', [])
            summary = analysis.get('summary', '')
            sentiment = analysis.get('sentiment', 'SENTIMENT_NEUTRAL')
            
            signals['summary'] = summary
            signals['sentiment'] = sentiment
            
            return signals, topic_tags, flags
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in LLM response: {e}")
            return self._get_default_signals(), [], []
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return self._get_default_signals(), [], []
    
    def _enhance_signals_with_regex(self, review_text: str, signals: Dict) -> Dict:
        """
        Enhanced regex-based checks to catch what LLM might miss
        These checks are definitive -override LLM if regex finds something
        """
        text_lower = review_text.lower()
        
        if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in PRICE_PATTERNS):
            signals['price_mentioned'] = True
        
        if any(re.search(pattern, review_text) for pattern in CONTACT_PATTERNS):
            signals['phone_email_present'] = True
        
        if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in OWNER_NAME_PATTERNS):
            signals['owner_name_mentioned'] = True
        
        if any(re.search(pattern, text_lower) for pattern in PROFANITY_PATTERNS):
            signals['abusive_language'] = True
        
        if any(re.search(pattern, review_text) for pattern in SUSPICIOUS_LINK_PATTERNS):
            signals['spam_or_links'] = True
        
        word_count = len(review_text.strip().split())
        if word_count < 15:
            signals['too_short'] = True
        
        return signals
    
    def _determine_sentiment(self, llm_sentiment: str, rating: int) -> str:
        """Determine sentiment from LLM and rating"""
        if llm_sentiment not in config.SENTIMENT_TAGS:
            llm_sentiment = 'SENTIMENT_NEUTRAL'
        
        if rating >= 4 and llm_sentiment == 'SENTIMENT_NEGATIVE':
            return 'SENTIMENT_POSITIVE'
        elif rating <= 2 and llm_sentiment == 'SENTIMENT_POSITIVE':
            return 'SENTIMENT_NEGATIVE'
        
        return llm_sentiment
    
    def _apply_publishing_rules(self, signals: Dict) -> Tuple[str, List[str]]:
        """
        Apply hard business rules for publishing decision
        """
        rejection_reasons = []
        
        hard_reject_checks = {
            'price_mentioned': 'PRICE_MENTIONED',
            'owner_name_mentioned': 'OWNER_MENTIONED',
            'phone_email_present': 'CONTACT_INFO',
            'abusive_language': 'ABUSIVE_LANGUAGE',
            'spam_or_links': 'SPAM_LINKS',
            'hate_sexual_violent': 'HATE_SEXUAL_VIOLENT'
        }
        
        for signal_key, reason_code in hard_reject_checks.items():
            if signals.get(signal_key, False):
                rejection_reasons.append(REJECTION_REASONS_RULES.get(reason_code, reason_code))
        
        publish_decision = "REJECT" if rejection_reasons else "PUBLISH"
        
        return publish_decision, rejection_reasons
    
    def _get_sentiment_tag(self, sentiment: str) -> str:
        """Get sentiment tag"""
        if sentiment in config.SENTIMENT_TAGS:
            return sentiment
        return "SENTIMENT_NEUTRAL"
    
    def _generate_tags(self, signals: Dict, topic_tags: List[str], sentiment_tag: str) -> List[str]:
        """Generate final tag list"""
        tags = [sentiment_tag]
        
        for tag in topic_tags:
            if tag in config.TOPIC_TAGS:
                tags.append(tag)
        
        special_tag_map = {
            'price_mentioned': 'PRICE_MENTIONED',
            'owner_name_mentioned': 'OWNER_MENTIONED',
            'phone_email_present': 'CONTACT_INFO_MENTIONED',
            'abusive_language': 'ABUSIVE_CONTENT',
            'spam_or_links': 'SPAM_SUSPECT'
        }
        
        for signal_key, special_tag in special_tag_map.items():
            if signals.get(signal_key, False):
                tags.append(special_tag)
        
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)
        
        return unique_tags
    
    def _auto_summarize(self, review_text: str) -> str:
        """Auto-generate summary if LLM doesn't provide one"""
        if len(review_text) <= 150:
            return review_text
        return review_text[:150] + "..."
    
    def _get_default_signals(self) -> Dict:
        """Returns default signals for error handling"""
        return {
            'price_mentioned': False,
            'owner_name_mentioned': False,
            'phone_email_present': False,
            'abusive_language': False,
            'spam_or_links': False,
            'hate_sexual_violent': False,
            'too_short': False,
            'summary': '',
            'sentiment': 'SENTIMENT_NEUTRAL'
        }
    
    def _get_safe_default_analysis(self, review_id: str, hotel_id: str, rating: int, review_text: str) -> Dict:
        """Return safe default analysis on complete failure"""
        signals = self._get_default_signals()
        signals = self._enhance_signals_with_regex(review_text, signals)
        
        publish_decision, rejection_reasons = self._apply_publishing_rules(signals)
        sentiment = 'SENTIMENT_NEUTRAL'
        
        return {
            "review_id": review_id,
            "hotel_id": hotel_id,
            "rating": rating,
            "review_text": review_text,
            "summary": review_text[:150] + "..." if len(review_text) > 150 else review_text,
            "sentiment": sentiment,
            "publish_decision": publish_decision,
            "rejection_reasons": rejection_reasons,
            "tags": [self._get_sentiment_tag(sentiment)],
            "detected_signals": signals,
            "flags": ["llm_analysis_failed"],
            "model_name": self.model_name,
            "prompt_version": self.prompt_version
        }
