import re
from datetime import datetime, timedelta
from typing import Optional, Dict

class CallbackTimeExtractor:
    """Fast extraction of callback times from call summaries."""
    
    # Word to number mapping
    WORD_TO_NUM = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12
    }
    
    # Precompiled regex patterns for speed
    TIME_PATTERNS = [
        r'(?:tomorrow|next day)\s+at\s+(\w+)(?::(\d{2}))?\s*(am|pm)',
        r'(\w+)(?::(\d{2}))?\s*(am|pm)\s+(?:tomorrow|next day)',
        r'in\s+(\d+)\s+(hour|day)s?',
        r'at\s+(\w+)(?::(\d{2}))?\s*(am|pm)',
        r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)',
    ]
    
    DAY_PATTERNS = [
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(tomorrow|next day|today)',
        r'in\s+(\d+)\s+days?',
    ]
    
    def __init__(self):
        self.time_regex = [re.compile(p, re.IGNORECASE) for p in self.TIME_PATTERNS]
        self.day_regex = [re.compile(p, re.IGNORECASE) for p in self.DAY_PATTERNS]
    
    def extract_callback_time(self, summary: str, current_time: Optional[datetime] = None) -> Dict:
        """
        Extract callback time from summary text.
        
        Args:
            summary: Call summary text
            current_time: Reference time (defaults to now)
            
        Returns:
            Dict with 'datetime', 'relative_desc', and 'found' keys
        """
        if current_time is None:
            current_time = datetime.now()
        
        summary_lower = summary.lower()
        
        # Extract time component
        time_info = self._extract_time(summary_lower)
        
        # Extract day component
        day_offset = self._extract_day_offset(summary_lower, current_time)
        
        if time_info or day_offset is not None:
            callback_dt = self._calculate_datetime(current_time, time_info, day_offset)
            return {
                'datetime': callback_dt,
                'iso_format': callback_dt.isoformat(),
                'relative_desc': self._get_relative_description(current_time, callback_dt),
                'found': True
            }
        
        return {'datetime': None, 'iso_format': None, 'relative_desc': None, 'found': False}
    
    def _extract_time(self, text: str) -> Optional[Dict]:
        """Extract time from text (e.g., '5 pm', 'five pm', '17:00')."""
        for pattern in self.time_regex:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                hour_str = groups[0] if groups[0] else None
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                period = groups[2] if len(groups) > 2 else None
                
                if hour_str:
                    # Convert word to number if needed
                    if hour_str.isdigit():
                        hour = int(hour_str)
                    elif hour_str.lower() in self.WORD_TO_NUM:
                        hour = self.WORD_TO_NUM[hour_str.lower()]
                    else:
                        continue  # Skip this match, try next pattern
                    
                    # Convert to 24-hour format
                    if period and period.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif period and period.lower() == 'am' and hour == 12:
                        hour = 0
                    
                    return {'hour': hour, 'minute': minute}
        
        return None
    
    def _extract_day_offset(self, text: str, current_time: datetime) -> Optional[int]:
        """Extract day offset from text."""
        # Check for "tomorrow" or "next day"
        if 'tomorrow' in text or 'next day' in text:
            return 1
        
        if 'today' in text:
            return 0
        
        # Check for "in X days"
        match = re.search(r'in\s+(\d+)\s+days?', text)
        if match:
            return int(match.group(1))
        
        # Check for day of week
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days_of_week:
            if day in text:
                target_day = days_of_week.index(day)
                current_day = current_time.weekday()
                offset = (target_day - current_day) % 7
                return offset if offset > 0 else 7
        
        return None
    
    def _calculate_datetime(self, current_time: datetime, time_info: Optional[Dict], 
                           day_offset: Optional[int]) -> datetime:
        """Calculate final datetime from components."""
        # Start with base date
        if day_offset is not None:
            target_date = current_time + timedelta(days=day_offset)
        else:
            target_date = current_time
        
        # Apply time if specified
        if time_info:
            target_date = target_date.replace(
                hour=time_info['hour'],
                minute=time_info['minute'],
                second=0,
                microsecond=0
            )
        else:
            # Default to business hours if no time specified
            target_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return target_date
    
    def _get_relative_description(self, current: datetime, target: datetime) -> str:
        """Generate human-readable relative description."""
        delta = target - current
        
        if delta.days == 0:
            return f"Today at {target.strftime('%I:%M %p')}"
        elif delta.days == 1:
            return f"Tomorrow at {target.strftime('%I:%M %p')}"
        elif delta.days < 7:
            return f"{target.strftime('%A at %I:%M %p')}"
        else:
            return target.strftime('%B %d at %I:%M %p')


# Example usage for webhook processing
def process_webhook_summary(summary: str) -> Dict:
    """
    Fast processing function for webhook calls.
    
    Args:
        summary: The call summary text from webhook
        
    Returns:
        Callback information dictionary
    """
    extractor = CallbackTimeExtractor()
    result = extractor.extract_callback_time(summary)
    return result

# Demo
if __name__ == "__main__":
    # Test cases
    summaries = [
        "user asks to call back and proposes tomorrow at five pm",
        "schedule callback for Monday at 2:30 PM",
        "callback needed today at 3pm",
    ]
# extractor = CallbackTimeExtractor()
    
# for summary in summaries:
#     result = extractor.extract_callback_time(summary)
#     print(f"\nSummary: {summary}")
#     print(f"Found: {result['found']}")
#     if result['found']:
#         print(f"Time: {result['relative_desc']}")
#         print(f"ISO: {result['iso_format']}")

