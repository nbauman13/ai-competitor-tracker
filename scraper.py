#!/usr/bin/env python3
"""
AI Competitor Tracker - Web Scraper
Monitors competitor websites and generates daily reports
"""

import json
import requests
import time
import os
from datetime import datetime, date
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import schedule
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CompetitorTracker:
    def __init__(self, config_file='config.json'):
        """Initialize the competitor tracker with configuration"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['settings']['user_agent']
        })

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

    def fetch_page(self, url, retries=None):
        """Fetch a webpage with error handling and retries"""
        if retries is None:
            retries = self.config['settings']['max_retries']

        for attempt in range(retries + 1):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(
                    url,
                    timeout=self.config['settings']['timeout']
                )
                response.raise_for_status()
                return response.text

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url}: {e}")
                if attempt < retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {retries + 1} attempts")
                    return None

    def extract_content(self, html, selectors):
        """Extract content from HTML using CSS selectors"""
        soup = BeautifulSoup(html, 'lxml')
        extracted = {}

        for key, selector in selectors.items():
            elements = []
            for sel in selector.split(', '):
                found = soup.select(sel.strip())
                elements.extend(found)

            if elements:
                if key == 'content':
                    # For content, get text from all matching elements
                    extracted[key] = '\n\n'.join([elem.get_text(strip=True) for elem in elements[:3]])
                else:
                    # For titles and dates, get the first match
                    extracted[key] = elements[0].get_text(strip=True)
            else:
                extracted[key] = 'Not found'

        return extracted

    def scrape_competitor(self, competitor_name, competitor_config):
        """Scrape a single competitor website"""
        logger.info(f"Scraping {competitor_name}...")

        html = self.fetch_page(competitor_config['url'])
        if html is None:
            return None

        content = self.extract_content(html, competitor_config['selectors'])

        return {
            'name': competitor_name,
            'url': competitor_config['url'],
            'scraped_at': datetime.now().isoformat(),
            'content': content
        }

    def scrape_all_competitors(self):
        """Scrape all competitors defined in config"""
        results = []
        delay = self.config['settings']['request_delay']

        for name, config in self.config['competitors'].items():
            result = self.scrape_competitor(name, config)
            if result:
                results.append(result)

            # Be respectful - add delay between requests
            if len(results) < len(self.config['competitors']):
                time.sleep(delay)

        return results

    def generate_markdown_report(self, data, report_date=None):
        """Generate a markdown report from scraped data"""
        if report_date is None:
            report_date = date.today()

        report = f"# AI Competitor Intelligence Report\n"
        report += f"**Date:** {report_date.strftime('%B %d, %Y')}\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if not data:
            report += "⚠️ No data available for this report.\n"
            return report

        report += "## Summary\n\n"
        report += f"Monitored {len(data)} competitor sources:\n"
        for item in data:
            report += f"- **{item['name']}**: {item['url']}\n"
        report += "\n"

        report += "## Competitor Updates\n\n"

        for item in data:
            report += f"### {item['name']}\n\n"
            report += f"**Source:** [{item['url']}]({item['url']})\n\n"
            report += f"**Scraped:** {item['scraped_at']}\n\n"

            content = item.get('content', {})

            if content.get('title', 'Not found') != 'Not found':
                report += f"**Latest Title:** {content['title']}\n\n"

            if content.get('date', 'Not found') != 'Not found':
                report += f"**Date:** {content['date']}\n\n"

            if content.get('content', 'Not found') != 'Not found':
                # Limit content length for readability
                content_text = content['content'][:500]
                if len(content['content']) > 500:
                    content_text += "..."
                report += f"**Content Preview:**\n{content_text}\n\n"
            else:
                report += "**Content:** Unable to extract content\n\n"

            report += "---\n\n"

        return report

    def save_report(self, report_content, report_date=None):
        """Save report to markdown file"""
        if report_date is None:
            report_date = date.today()

        filename = f"reports/ai-competitor-report-{report_date.strftime('%Y-%m-%d')}.md"

        os.makedirs('reports', exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Report saved to {filename}")
        return filename

    def run_daily_report(self):
        """Run the complete daily report generation process"""
        logger.info("Starting daily competitor tracking...")

        try:
            # Scrape all competitors
            data = self.scrape_all_competitors()

            # Generate report
            report = self.generate_markdown_report(data)

            # Save report
            filename = self.save_report(report)

            logger.info(f"Daily report completed successfully: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error during daily report generation: {e}")
            raise


def main():
    """Main function - can be run directly or scheduled"""
    tracker = CompetitorTracker()

    # Run immediately
    tracker.run_daily_report()

    # Setup daily scheduling (uncomment to enable)
    # schedule.every().day.at("09:00").do(tracker.run_daily_report)
    #
    # logger.info("Scheduler started - reports will run daily at 9:00 AM")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)


if __name__ == "__main__":
    main()