#!/usr/bin/env python3
"""
Podcast Analytics Dashboard
Provides insights and analytics about your podcast content.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class PodcastAnalytics:
    def __init__(self, sermons_file: str = "data/sermons.json"):
        self.sermons_file = sermons_file
        self.sermons_data = self.load_sermons()
        self.df = self.create_dataframe()
    
    def load_sermons(self) -> Dict:
        """Load sermons data from JSON file."""
        try:
            with open(self.sermons_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Sermons file {self.sermons_file} not found")
            return {"sermons": []}
    
    def create_dataframe(self) -> pd.DataFrame:
        """Create a pandas DataFrame for analysis."""
        sermons = self.sermons_data.get('sermons', [])
        return pd.DataFrame(sermons)
    
    def get_basic_stats(self) -> Dict:
        """Get basic statistics about the podcast."""
        total_sermons = len(self.df)
        
        # Date range
        if not self.df.empty and 'date' in self.df.columns:
            dates = pd.to_datetime(self.df['date'], errors='coerce')
            date_range = {
                'earliest': dates.min().strftime('%Y-%m-%d') if not dates.isna().all() else 'N/A',
                'latest': dates.max().strftime('%Y-%m-%d') if not dates.isna().all() else 'N/A',
                'span_days': (dates.max() - dates.min()).days if not dates.isna().all() else 0
            }
        else:
            date_range = {'earliest': 'N/A', 'latest': 'N/A', 'span_days': 0}
        
        # Authors
        authors = self.df['author'].value_counts().to_dict() if 'author' in self.df.columns else {}
        
        # Series distribution
        series = self.df['series'].value_counts().to_dict() if 'series' in self.df.columns else {}
        
        # Sermon types
        sermon_types = self.df['sermon_type'].value_counts().to_dict() if 'sermon_type' in self.df.columns else {}
        
        return {
            'total_sermons': total_sermons,
            'date_range': date_range,
            'authors': authors,
            'series': series,
            'sermon_types': sermon_types
        }
    
    def get_publishing_frequency(self) -> Dict:
        """Analyze publishing frequency patterns."""
        if self.df.empty or 'date' not in self.df.columns:
            return {}
        
        # Convert dates
        self.df['date_parsed'] = pd.to_datetime(self.df['date'], errors='coerce')
        df_clean = self.df.dropna(subset=['date_parsed'])
        
        if df_clean.empty:
            return {}
        
        # Group by month and year
        df_clean['year_month'] = df_clean['date_parsed'].dt.to_period('M')
        monthly_counts = df_clean['year_month'].value_counts().sort_index()
        
        # Group by day of week
        df_clean['day_of_week'] = df_clean['date_parsed'].dt.day_name()
        daily_counts = df_clean['day_of_week'].value_counts()
        
        # Calculate average per month
        avg_per_month = monthly_counts.mean() if not monthly_counts.empty else 0
        
        return {
            'monthly_counts': monthly_counts.to_dict(),
            'daily_distribution': daily_counts.to_dict(),
            'average_per_month': round(avg_per_month, 2),
            'total_months': len(monthly_counts)
        }
    
    def get_content_analysis(self) -> Dict:
        """Analyze content patterns and themes."""
        if self.df.empty:
            return {}
        
        # Scripture analysis
        scripture_analysis = {}
        if 'scripture' in self.df.columns:
            all_scriptures = []
            for scripture in self.df['scripture'].dropna():
                if scripture.strip():
                    all_scriptures.extend([s.strip() for s in scripture.split(',')])
            
            scripture_counter = Counter(all_scriptures)
            scripture_analysis = {
                'most_common_books': dict(scripture_counter.most_common(10)),
                'total_unique_scriptures': len(scripture_counter)
            }
        
        # Tag analysis
        tag_analysis = {}
        if 'tags' in self.df.columns:
            all_tags = []
            for tags in self.df['tags'].dropna():
                if isinstance(tags, list):
                    all_tags.extend(tags)
                elif isinstance(tags, str):
                    all_tags.extend([t.strip() for t in tags.split(',')])
            
            tag_counter = Counter(all_tags)
            tag_analysis = {
                'most_common_tags': dict(tag_counter.most_common(20)),
                'total_unique_tags': len(tag_counter)
            }
        
        # Title analysis
        title_analysis = {}
        if 'title' in self.df.columns:
            titles = self.df['title'].dropna()
            title_lengths = titles.str.len()
            
            # Common words in titles
            all_title_words = []
            for title in titles:
                words = title.lower().split()
                all_title_words.extend([word for word in words if len(word) > 3])
            
            word_counter = Counter(all_title_words)
            
            title_analysis = {
                'average_title_length': round(title_lengths.mean(), 2),
                'longest_title': titles[title_lengths.idxmax()] if not titles.empty else '',
                'shortest_title': titles[title_lengths.idxmin()] if not titles.empty else '',
                'most_common_words': dict(word_counter.most_common(15))
            }
        
        return {
            'scripture_analysis': scripture_analysis,
            'tag_analysis': tag_analysis,
            'title_analysis': title_analysis
        }
    
    def get_engagement_metrics(self) -> Dict:
        """Calculate engagement and popularity metrics."""
        if self.df.empty:
            return {}
        
        metrics = {}
        
        # Duration analysis
        if 'duration_minutes' in self.df.columns:
            durations = self.df['duration_minutes'].dropna()
            if not durations.empty:
                metrics['duration'] = {
                    'average_minutes': round(durations.mean(), 2),
                    'shortest_minutes': durations.min(),
                    'longest_minutes': durations.max(),
                    'total_hours': round(durations.sum() / 60, 2)
                }
        
        # Series popularity
        if 'series' in self.df.columns:
            series_counts = self.df['series'].value_counts()
            metrics['series_popularity'] = {
                'most_popular_series': series_counts.index[0] if not series_counts.empty else 'N/A',
                'series_count': series_counts.iloc[0] if not series_counts.empty else 0,
                'total_series': len(series_counts)
            }
        
        # Author productivity
        if 'author' in self.df.columns:
            author_counts = self.df['author'].value_counts()
            metrics['author_productivity'] = {
                'most_prolific_author': author_counts.index[0] if not author_counts.empty else 'N/A',
                'sermons_by_author': author_counts.to_dict()
            }
        
        return metrics
    
    def generate_insights(self) -> List[str]:
        """Generate actionable insights from the data."""
        insights = []
        stats = self.get_basic_stats()
        frequency = self.get_publishing_frequency()
        content = self.get_content_analysis()
        engagement = self.get_engagement_metrics()
        
        # Publishing insights
        if frequency.get('average_per_month', 0) > 0:
            if frequency['average_per_month'] < 2:
                insights.append("Consider increasing publishing frequency - currently averaging less than 2 episodes per month")
            elif frequency['average_per_month'] > 8:
                insights.append("High publishing frequency detected - ensure quality isn't compromised")
            else:
                insights.append(f"Good publishing frequency - averaging {frequency['average_per_month']} episodes per month")
        
        # Content insights
        if content.get('scripture_analysis', {}).get('most_common_books'):
            most_common_book = list(content['scripture_analysis']['most_common_books'].keys())[0]
            insights.append(f"Most frequently taught book: {most_common_book}")
        
        if content.get('tag_analysis', {}).get('most_common_tags'):
            most_common_tag = list(content['tag_analysis']['most_common_tags'].keys())[0]
            insights.append(f"Most common theme: {most_common_tag}")
        
        # Author insights
        if stats.get('authors'):
            authors = list(stats['authors'].keys())
            if len(authors) > 1:
                insights.append(f"Multiple speakers contributing: {', '.join(authors)}")
            else:
                insights.append(f"Single primary speaker: {authors[0]}")
        
        # Series insights
        if stats.get('series'):
            series_count = len(stats['series'])
            if series_count > 5:
                insights.append(f"Rich content variety with {series_count} different series")
            elif series_count > 1:
                insights.append(f"Good content diversity with {series_count} series")
        
        return insights
    
    def create_visualizations(self, output_dir: str = "analytics_charts"):
        """Create visualization charts for the analytics."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # 1. Publishing frequency over time
        if not self.df.empty and 'date' in self.df.columns:
            self.df['date_parsed'] = pd.to_datetime(self.df['date'], errors='coerce')
            df_clean = self.df.dropna(subset=['date_parsed'])
            
            if not df_clean.empty:
                df_clean['year_month'] = df_clean['date_parsed'].dt.to_period('M')
                monthly_counts = df_clean['year_month'].value_counts().sort_index()
                
                plt.figure(figsize=(12, 6))
                monthly_counts.plot(kind='line', marker='o')
                plt.title('Sermons Published Over Time')
                plt.xlabel('Month')
                plt.ylabel('Number of Sermons')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(f"{output_dir}/publishing_frequency.png", dpi=300, bbox_inches='tight')
                plt.close()
        
        # 2. Author distribution
        if 'author' in self.df.columns:
            author_counts = self.df['author'].value_counts()
            
            plt.figure(figsize=(10, 6))
            author_counts.plot(kind='bar')
            plt.title('Sermons by Author')
            plt.xlabel('Author')
            plt.ylabel('Number of Sermons')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/author_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Series distribution
        if 'series' in self.df.columns:
            series_counts = self.df['series'].value_counts().head(10)
            
            plt.figure(figsize=(12, 8))
            series_counts.plot(kind='pie', autopct='%1.1f%%')
            plt.title('Sermons by Series (Top 10)')
            plt.ylabel('')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/series_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def generate_report(self) -> str:
        """Generate a comprehensive analytics report."""
        stats = self.get_basic_stats()
        frequency = self.get_publishing_frequency()
        content = self.get_content_analysis()
        engagement = self.get_engagement_metrics()
        insights = self.generate_insights()
        
        report = f"""
# CPC New Haven Podcast Analytics Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- **Total Sermons**: {stats.get('total_sermons', 0)}
- **Date Range**: {stats.get('date_range', {}).get('earliest', 'N/A')} to {stats.get('date_range', {}).get('latest', 'N/A')}
- **Span**: {stats.get('date_range', {}).get('span_days', 0)} days

## Publishing Frequency
- **Average per Month**: {frequency.get('average_per_month', 0)}
- **Total Months Active**: {frequency.get('total_months', 0)}

## Content Analysis
- **Most Common Scripture Books**: {list(content.get('scripture_analysis', {}).get('most_common_books', {}).keys())[:5]}
- **Most Common Tags**: {list(content.get('tag_analysis', {}).get('most_common_tags', {}).keys())[:5]}
- **Average Title Length**: {content.get('title_analysis', {}).get('average_title_length', 'N/A')} characters

## Key Insights
"""
        for insight in insights:
            report += f"- {insight}\n"
        
        return report

def main():
    """Main function to run analytics."""
    analytics = PodcastAnalytics()
    
    # Generate basic stats
    stats = analytics.get_basic_stats()
    print("Basic Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Generate insights
    insights = analytics.generate_insights()
    print("\nKey Insights:")
    for insight in insights:
        print(f"- {insight}")
    
    # Generate report
    report = analytics.generate_report()
    with open("podcast_analytics_report.md", "w") as f:
        f.write(report)
    
    print(f"\nAnalytics report saved to podcast_analytics_report.md")

if __name__ == "__main__":
    main()
