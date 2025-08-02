import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
import difflib
import logging

logger = logging.getLogger(__name__)

class IntelligentCache:
    def __init__(self):
        self.prompt_cache: Dict[str, Dict[str, Any]] = {}
        self.preference_cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {"hits": 0, "misses": 0, "total": 0}
    
    def normalize_prompt(self, prompt: str) -> str:
        """Normalize prompt for better matching"""
        normalized = prompt.lower().strip()
        stop_words = ['please', 'create', 'make', 'build', 'generate', 'i want', 'i need', 'give me']
        for word in stop_words:
            normalized = normalized.replace(word, '').strip()
        return normalized
    
    def extract_component_type(self, prompt: str) -> str:
        """Extract the main component type from prompt"""
        prompt_lower = prompt.lower()
        
        component_keywords = {
            'testimonial': ['testimonial', 'testimonials', 'review', 'reviews', 'feedback'],
            'hero': ['hero', 'hero section', 'banner', 'header'],
            'pricing': ['pricing', 'price', 'cost', 'plan', 'plans'],
            'contact': ['contact', 'form', 'contact form', 'enquiry'],
            'gallery': ['gallery', 'image gallery', 'photo gallery', 'portfolio'],
            'team': ['team', 'member', 'members', 'staff'],
            'service': ['service', 'services', 'feature', 'features'],
            'blog': ['blog', 'post', 'article', 'news'],
            'faq': ['faq', 'question', 'questions', 'help'],
            'cta': ['cta', 'call to action', 'button', 'action']
        }
        
        for component_type, keywords in component_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    return component_type
        
        return 'general'
    
    def extract_preferences(self, prompt: str) -> Dict[str, Any]:
        """Extract user preferences from prompt"""
        prompt_lower = prompt.lower()
        preferences = {
            'has_image': False,
            'has_video': False,
            'has_color': False,
            'is_required': False,
            'is_optional': False,
            'is_simple': False,
            'is_detailed': False
        }
        
        # Check for image preferences
        if any(word in prompt_lower for word in ['image', 'photo', 'picture', 'avatar', 'profile']):
            preferences['has_image'] = True
        
        # Check for video preferences
        if any(word in prompt_lower for word in ['video', 'media', 'clip']):
            preferences['has_video'] = True
        
        # Check for color preferences
        if any(word in prompt_lower for word in ['color', 'colour', 'theme', 'styling']):
            preferences['has_color'] = True
        
        # Check for requirement preferences
        if any(word in prompt_lower for word in ['required', 'must', 'essential', 'necessary']):
            preferences['is_required'] = True
        
        if any(word in prompt_lower for word in ['optional', 'not needed', 'no need']):
            preferences['is_optional'] = True
        
        # Check for complexity preferences
        if any(word in prompt_lower for word in ['simple', 'basic', 'minimal']):
            preferences['is_simple'] = True
        
        if any(word in prompt_lower for word in ['detailed', 'comprehensive', 'full', 'complete']):
            preferences['is_detailed'] = True
        
        return preferences
    
    def find_similar_cached_prompt(self, prompt: str, component_type: str, preferences: Dict[str, Any]) -> Optional[str]:
        """Find similar cached prompt based on component type and preferences"""
        normalized_prompt = self.normalize_prompt(prompt)
        
        for cache_key, cache_data in self.prompt_cache.items():
            cached_prompt = cache_data.get('normalized_prompt', '')
            cached_component_type = cache_data.get('component_type', '')
            cached_preferences = cache_data.get('preferences', {})
            
            # Check if component type matches
            if cached_component_type != component_type:
                continue
            
            # Check if preferences are compatible
            preference_match = True
            for key, value in preferences.items():
                if value and key in cached_preferences and cached_preferences[key] != value:
                    preference_match = False
                    break
            
            if not preference_match:
                continue
            
            # Check similarity using difflib
            similarity = difflib.SequenceMatcher(None, normalized_prompt, cached_prompt).ratio()
            if similarity > 0.7:  # 70% similarity threshold
                return cache_key
        
        return None
    
    def enhance_prompt_with_preferences(self, prompt: str, component_type: str, preferences: Dict[str, Any]) -> str:
        """Enhance prompt with learned preferences"""
        enhanced_prompt = prompt
        
        # Add image preference if learned
        if preferences.get('has_image') and 'image' not in prompt.lower():
            enhanced_prompt += " with image upload option"
        
        # Add video preference if learned
        if preferences.get('has_video') and 'video' not in prompt.lower():
            enhanced_prompt += " with video support"
        
        # Add color preference if learned
        if preferences.get('has_color') and 'color' not in prompt.lower():
            enhanced_prompt += " with color customization"
        
        return enhanced_prompt
    
    def get_cached_result(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get cached result for similar prompt"""
        self.stats["total"] += 1
        
        component_type = self.extract_component_type(prompt)
        preferences = self.extract_preferences(prompt)
        
        cache_key = self.find_similar_cached_prompt(prompt, component_type, preferences)
        
        if cache_key:
            self.stats["hits"] += 1
            logger.info(f"Cache HIT for prompt: {prompt}")
            return self.prompt_cache[cache_key]
        
        self.stats["misses"] += 1
        logger.info(f"Cache MISS for prompt: {prompt}")
        return None
    
    def cache_result(self, prompt: str, component: Dict[str, Any], fields: list) -> None:
        """Cache the generated result"""
        component_type = self.extract_component_type(prompt)
        preferences = self.extract_preferences(prompt)
        
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        self.prompt_cache[cache_key] = {
            "original_prompt": prompt,
            "normalized_prompt": self.normalize_prompt(prompt),
            "component_type": component_type,
            "preferences": preferences,
            "component": component,
            "fields": fields,
            "timestamp": datetime.now().isoformat()
        }
        
        # Learn preferences for this component type
        if component_type not in self.preference_cache:
            self.preference_cache[component_type] = {}
        
        for key, value in preferences.items():
            if value:
                self.preference_cache[component_type][key] = value
        
        logger.info(f"Cached result for prompt: {prompt}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = max(self.stats["total"], 1)
        return {
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "total_requests": self.stats["total"],
            "hit_rate": f"{(self.stats['hits'] / total) * 100:.1f}%",
            "cached_prompts": len(self.prompt_cache),
            "learned_preferences": len(self.preference_cache)
        }

# Global cache instance
cache = IntelligentCache() 