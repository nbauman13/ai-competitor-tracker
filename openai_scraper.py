#!/usr/bin/env python3
"""
OpenAI Blog Scraper
Simple web scraper to get latest blog posts from OpenAI's website
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import logging
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OpenAIScraper:
    def __init__(self):
        self.session = requests.Session()
        # Use a more realistic user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # URLs to try (in order of preference)
        self.urls = [
            'https://openai.com/news',
            'https://openai.com/blog',
            'https://openai.com/research'
        ]

    def fetch_page(self, url, timeout=30):
        """Fetch page with error handling"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=timeout)

            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                logger.warning(f"Access forbidden (403) for {url}")
                return None
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def extract_blog_posts(self, html, base_url):
        """Extract blog post information from HTML"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        posts = []

        # Common selectors for blog posts (try multiple patterns)
        post_selectors = [
            'article',
            '.post',
            '.blog-post',
            '.news-item',
            '.content-item',
            '[data-testid*="post"]',
            '.card',
            'div[class*="post"]',
            'div[class*="article"]'
        ]

        # Try each selector
        for selector in post_selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")

                for element in elements[:10]:  # Limit to first 10
                    post = self.extract_post_data(element, base_url)
                    if post and post not in posts:
                        posts.append(post)

                if posts:
                    break  # Found posts, no need to try other selectors

        # Fallback: look for any links that might be blog posts
        if not posts:
            links = soup.find_all('a', href=True)
            for link in links[:20]:  # Check first 20 links
                if any(keyword in link.get('href', '').lower() for keyword in ['blog', 'news', 'post', 'article']):
                    post = {
                        'title': link.get_text(strip=True),
                        'url': urljoin(base_url, link['href']),
                        'description': 'No description available',
                        'date': 'Date not found',
                        'scraped_at': datetime.now().isoformat()
                    }
                    if post['title'] and len(post['title']) > 5:
                        posts.append(post)

        return posts

    def extract_post_data(self, element, base_url):
        """Extract data from a single post element"""
        try:
            # Try to find title
            title_selectors = ['h1', 'h2', 'h3', '.title', '.headline', 'a']
            title = None
            title_link = None

            for sel in title_selectors:
                title_elem = element.select_one(sel)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # If it's a link, get the href
                    if title_elem.name == 'a' and title_elem.get('href'):
                        title_link = urljoin(base_url, title_elem['href'])
                    # Look for links within the title element
                    elif title_elem.find('a'):
                        link_elem = title_elem.find('a')
                        if link_elem.get('href'):
                            title_link = urljoin(base_url, link_elem['href'])
                    break

            if not title or len(title) < 5:
                return None

            # Try to find description
            desc_selectors = ['.description', '.excerpt', '.summary', 'p']
            description = 'No description available'

            for sel in desc_selectors:
                desc_elem = element.select_one(sel)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if len(desc_text) > 20:  # Only use if substantial
                        description = desc_text[:200] + '...' if len(desc_text) > 200 else desc_text
                        break

            # Try to find date
            date_selectors = ['.date', '.published', 'time', '.timestamp']
            date = 'Date not found'

            for sel in date_selectors:
                date_elem = element.select_one(sel)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    if date_text and len(date_text) > 3:
                        date = date_text
                        break
                    # Check for datetime attribute
                    elif date_elem.get('datetime'):
                        date = date_elem['datetime']
                        break

            # If no direct link found, look for any link in the element
            if not title_link:
                link_elem = element.find('a', href=True)
                if link_elem:
                    title_link = urljoin(base_url, link_elem['href'])

            return {
                'title': title,
                'url': title_link or base_url,
                'description': description,
                'date': date,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None

    def scrape_openai_blog(self):
        """Main method to scrape OpenAI blog posts"""
        all_posts = []

        for url in self.urls:
            html = self.fetch_page(url)
            if html:
                posts = self.extract_blog_posts(html, url)
                if posts:
                    logger.info(f"Found {len(posts)} posts from {url}")
                    all_posts.extend(posts)
                    break  # Success with this URL, no need to try others
                else:
                    logger.info(f"No posts found from {url}")

            time.sleep(2)  # Be respectful between requests

        # Remove duplicates based on title
        seen_titles = set()
        unique_posts = []
        for post in all_posts:
            if post['title'] not in seen_titles:
                seen_titles.add(post['title'])
                unique_posts.append(post)

        return unique_posts

    def save_posts_json(self, posts, filename='openai_posts.json'):
        """Save posts to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'total_posts': len(posts),
                'posts': posts
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(posts)} posts to {filename}")

    def print_posts(self, posts):
        """Print posts in a readable format"""
        print(f"\n🤖 OpenAI Blog Posts ({len(posts)} found)")
        print("=" * 60)

        for i, post in enumerate(posts, 1):
            print(f"\n{i}. {post['title']}")
            print(f"   URL: {post['url']}")
            print(f"   Date: {post['date']}")
            print(f"   Description: {post['description'][:100]}...")


def main():
    """Main function"""
    scraper = OpenAIScraper()

    logger.info("Starting OpenAI blog scraper...")
    posts = scraper.scrape_openai_blog()

    if posts:
        scraper.print_posts(posts)
        scraper.save_posts_json(posts)
        logger.info(f"Successfully scraped {len(posts)} blog posts")
    else:
        logger.warning("No blog posts found. OpenAI may be blocking requests.")
        print("\n⚠️  Unable to scrape OpenAI blog posts.")
        print("This is likely due to bot protection on their website.")
        print("\nAlternative approaches:")
        print("1. Use OpenAI's RSS feed if available")
        print("2. Use their API if they provide one")
        print("3. Check for press releases on news sites")
        print("4. Monitor their social media accounts")


if __name__ == "__main__":
    main()