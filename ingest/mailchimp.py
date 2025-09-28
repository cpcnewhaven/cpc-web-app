"""
Mailchimp ingester for newsletter content
Supports both RSS feed and API approaches
"""
import re
from typing import Dict, List, Any
from .base import BaseIngester


class MailchimpIngester(BaseIngester):
    """Ingester for Mailchimp newsletter content"""
    
    def fetch_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch Mailchimp data using RSS feed or API"""
        # Try RSS feed first (simpler, no API key needed)
        rss_url = config.get("MAILCHIMP_RSS_URL")
        if rss_url and not rss_url.startswith("<PASTE_"):
            return self._fetch_from_rss(rss_url)
        
        # Fall back to API if RSS not available
        api_key = config.get("MAILCHIMP_API_KEY")
        server_prefix = config.get("MAILCHIMP_SERVER_PREFIX")
        list_id = config.get("MAILCHIMP_LIST_ID")
        
        if api_key and server_prefix and list_id:
            return self._fetch_from_api(api_key, server_prefix, list_id)
        
        return {"error": "Mailchimp not configured - need either RSS URL or API credentials"}
    
    def _fetch_from_rss(self, rss_url: str) -> Dict[str, Any]:
        """Fetch from Mailchimp RSS feed"""
        try:
            response = self.make_request(rss_url)
            response.raise_for_status()
            parsed = self.parse_rss(response.content)
            
            items = []
            for entry in parsed.entries[:10]:  # Limit to 10 most recent
                # Clean up Mailchimp-specific content
                title = self._clean_title(entry.get("title", ""))
                summary = self._clean_summary(entry.get("summary", ""))
                
                # Extract events from content
                events = self._extract_events_from_content(summary)
                
                items.append({
                    "title": title,
                    "url": entry.get("link"),
                    "published": entry.get("published"),
                    "summary": summary,
                    "image": self._extract_image(entry),
                    "content_type": "newsletter",
                    "events": events
                })
            
            return {
                "source": parsed.feed.get("title", "CPC Weekly Newsletter"),
                "items": items,
                "method": "rss"
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch from RSS: {str(e)}"}
    
    def _fetch_from_api(self, api_key: str, server_prefix: str, list_id: str) -> Dict[str, Any]:
        """Fetch from Mailchimp API"""
        try:
            # Get recent campaigns
            campaigns_url = f"https://{server_prefix}.api.mailchimp.com/3.0/campaigns"
            params = {
                "list_id": list_id,
                "status": "sent",
                "count": 10,
                "sort_field": "send_time",
                "sort_dir": "DESC"
            }
            
            response = self.make_request(campaigns_url, params=params, auth=("anystring", api_key))
            response.raise_for_status()
            campaigns_data = response.json()
            
            items = []
            for campaign in campaigns_data.get("campaigns", []):
                # Get campaign content
                content_url = f"https://{server_prefix}.api.mailchimp.com/3.0/campaigns/{campaign['id']}/content"
                content_response = self.make_request(content_url, auth=("anystring", api_key))
                
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    html_content = content_data.get("html", "")
                    
                    items.append({
                        "title": campaign.get("settings", {}).get("subject_line", "Newsletter"),
                        "url": campaign.get("archive_url"),
                        "published": campaign.get("send_time"),
                        "summary": self._extract_text_from_html(html_content),
                        "image": self._extract_image_from_html(html_content),
                        "content_type": "newsletter",
                        "campaign_id": campaign.get("id")
                    })
            
            return {
                "source": "CPC Weekly Newsletter",
                "items": items,
                "method": "api"
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch from API: {str(e)}"}
    
    def _clean_title(self, title: str) -> str:
        """Clean up Mailchimp title formatting for CPC newsletters"""
        # Remove common Mailchimp prefixes
        title = re.sub(r'^CPC Weekly Highlights?\s*[-|]\s*', '', title)
        title = re.sub(r'^CPC Weekly\s*[-|]\s*', '', title)
        title = re.sub(r'^Christ Presbyterian Church\s*[-|]\s*', '', title)
        title = re.sub(r'^Large Print Bulletin\s*[-|]\s*', '', title)
        return title.strip()
    
    def _clean_summary(self, summary: str) -> str:
        """Clean up Mailchimp summary content for CPC newsletters"""
        # Remove HTML tags
        summary = re.sub(r'<[^>]+>', '', summary)
        
        # Remove CPC-specific footer content
        summary = re.sub(r'Connect Board.*?Email\s*Email.*', '', summary, flags=re.DOTALL)
        summary = re.sub(r'Copyright.*?All rights reserved.*', '', summary, flags=re.DOTALL)
        summary = re.sub(r'You are receiving this email.*?unsubscribe.*', '', summary, flags=re.DOTALL)
        summary = re.sub(r'Our mailing address:.*?Add us to your address book.*', '', summary, flags=re.DOTALL)
        summary = re.sub(r'Email Marketing Powered by Mailchimp.*', '', summary, flags=re.DOTALL)
        
        # Clean up common CPC newsletter formatting
        summary = re.sub(r'10:30am Worship This Sunday\s*Highlights?', '', summary)
        summary = re.sub(r'OUR REGULAR SUNDAY SCHEDULE IS BACK FOR FALL', 'Regular Sunday Schedule:', summary)
        
        # Clean up whitespace
        summary = re.sub(r'\s+', ' ', summary).strip()
        return summary
    
    def _extract_image(self, entry: Dict[str, Any]) -> str:
        """Extract image from RSS entry"""
        # Try media_thumbnail first
        if entry.get("media_thumbnail"):
            return entry.get("media_thumbnail", [{}])[0].get("url", "")
        
        # Try enclosures
        for enc in entry.get("enclosures", []):
            if enc.get("type", "").startswith("image"):
                return enc.get("href", "")
        
        return None
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract plain text from HTML content"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Remove common Mailchimp elements
        text = re.sub(r'Copyright.*?All rights reserved.*', '', text, flags=re.DOTALL)
        text = re.sub(r'You are receiving this email.*?unsubscribe.*', '', text, flags=re.DOTALL)
        text = re.sub(r'Email Marketing Powered by Mailchimp.*', '', text, flags=re.DOTALL)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:500] + "..." if len(text) > 500 else text
    
    def _extract_image_from_html(self, html: str) -> str:
        """Extract first image from HTML content"""
        img_match = re.search(r'<img[^>]+src="([^"]+)"', html)
        return img_match.group(1) if img_match else None
    
    def _extract_events_from_content(self, content: str) -> List[Dict[str, str]]:
        """Extract events from CPC newsletter content"""
        events = []
        
        # Pattern for events with dates and times
        event_patterns = [
            r'([A-Z][^.!?]*(?:Starts?|Begins?|Continues?|Meeting|Retreat|Training|Group|Hours?)[^.!?]*?)(?:\d{1,2}:\d{2}[ap]m|\d{1,2}/\d{1,2}|\d{1,2}:\d{2})[^.!?]*[.!?]',
            r'([A-Z][^.!?]*(?:Sept|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug)[^.!?]*?)(?:\d{1,2}:\d{2}[ap]m|\d{1,2}/\d{1,2})[^.!?]*[.!?]',
            r'([A-Z][^.!?]*(?:Friday|Saturday|Sunday|Monday|Tuesday|Wednesday|Thursday)[^.!?]*?)(?:\d{1,2}:\d{2}[ap]m|\d{1,2}/\d{1,2})[^.!?]*[.!?]'
        ]
        
        for pattern in event_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if len(match.strip()) > 20:  # Filter out short matches
                    events.append({
                        "title": match.strip(),
                        "type": "event",
                        "source": "newsletter"
                    })
        
        return events[:10]  # Limit to 10 events
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Mailchimp data to standard format"""
        if "error" in raw_data:
            return raw_data
        
        return {
            "type": "mailchimp_newsletter",
            "source": raw_data.get("source", "CPC Weekly Newsletter"),
            "count": len(raw_data.get("items", [])),
            "items": raw_data.get("items", []),
            "method": raw_data.get("method", "unknown"),
            "last_updated": raw_data.get("last_updated")
        }
