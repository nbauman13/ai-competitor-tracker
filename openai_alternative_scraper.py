#!/usr/bin/env python3
"""
OpenAI Alternative Scraper
Uses alternative sources to get OpenAI news and updates
"""

import requests
import feedparser
import json
from datetime import datetime
import logging
from urllib.parse import urljoin
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OpenAIAlternativeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def try_rss_feeds(self):
        """Try various RSS feed URLs for OpenAI"""
        rss_urls = [
            'https://openai.com/rss.xml',
            'https://openai.com/feed.xml',
            'https://openai.com/blog/rss.xml',
            'https://openai.com/news/rss.xml'
        ]

        posts = []
        for url in rss_urls:
            try:
                logger.info(f"Trying RSS feed: {url}")
                feed = feedparser.parse(url)

                if feed.entries:
                    logger.info(f"Found {len(feed.entries)} entries in RSS feed")
                    for entry in feed.entries[:10]:  # Limit to 10 most recent
                        post = {
                            'title': entry.get('title', 'No title'),
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', entry.get('description', 'No description')),
                            'date': entry.get('published', entry.get('updated', 'Unknown date')),
                            'source': 'RSS Feed',
                            'scraped_at': datetime.now().isoformat()
                        }
                        posts.append(post)
                    return posts

            except Exception as e:
                logger.warning(f"RSS feed {url} failed: {e}")
                continue

        return posts

    def scrape_tech_news_sites(self):
        """Scrape tech news sites for OpenAI mentions"""
        posts = []

        # Search queries for OpenAI news
        sources = [
            {
                'name': 'TechCrunch',
                'search_url': 'https://techcrunch.com/?s=openai',
                'selectors': {
                    'articles': 'article.post-block',
                    'title': 'h2.post-block__title a',
                    'link': 'h2.post-block__title a',
                    'date': '.river-byline__time'
                }
            }
        ]

        for source in sources:
            try:
                logger.info(f"Checking {source['name']} for OpenAI news...")
                response = self.session.get(source['search_url'], timeout=30)

                if response.status_code == 200:
                    # For now, just log success - full implementation would parse HTML
                    logger.info(f"Successfully connected to {source['name']}")
                else:
                    logger.warning(f"HTTP {response.status_code} from {source['name']}")

            except Exception as e:
                logger.error(f"Error fetching from {source['name']}: {e}")

            time.sleep(2)  # Be respectful

        return posts

    def get_openai_github_releases(self):
        """Get latest releases from OpenAI GitHub repositories"""
        posts = []
        github_repos = [
            'openai/openai-python',
            'openai/whisper',
            'openai/triton',
            'openai/gpt-2'
        ]

        for repo in github_repos:
            try:
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                logger.info(f"Checking GitHub releases for {repo}")

                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    release = response.json()
                    post = {
                        'title': f"{repo}: {release.get('name', release.get('tag_name', 'New Release'))}",
                        'url': release.get('html_url', ''),
                        'description': release.get('body', 'No description available')[:300],
                        'date': release.get('published_at', 'Unknown date'),
                        'source': 'GitHub Release',
                        'scraped_at': datetime.now().isoformat()
                    }
                    posts.append(post)
                    logger.info(f"Found release: {post['title']}")
                else:
                    logger.warning(f"GitHub API returned {response.status_code} for {repo}")

            except Exception as e:
                logger.error(f"Error fetching GitHub releases for {repo}: {e}")

            time.sleep(1)  # GitHub rate limiting

        return posts

    def search_hacker_news(self):
        """Search Hacker News for OpenAI posts"""
        posts = []
        try:
            # Algolia HN Search API
            search_url = "https://hn.algolia.com/api/v1/search"
            params = {
                'query': 'OpenAI',
                'tags': 'story',
                'hitsPerPage': 10,
                'numericFilters': f'created_at_i>{int(time.time()) - 7*24*3600}'  # Last 7 days
            }

            logger.info("Searching Hacker News for OpenAI stories...")
            response = self.session.get(search_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                for hit in data.get('hits', []):
                    post = {
                        'title': hit.get('title', 'No title'),
                        'url': hit.get('url', f"https://news.ycombinator.com/item?id={hit.get('objectID')}"),
                        'description': f"Hacker News discussion - {hit.get('num_comments', 0)} comments",
                        'date': datetime.fromtimestamp(hit.get('created_at_i', 0)).isoformat(),
                        'source': 'Hacker News',
                        'scraped_at': datetime.now().isoformat()
                    }
                    posts.append(post)

                logger.info(f"Found {len(posts)} Hacker News stories")
            else:
                logger.warning(f"Hacker News API returned {response.status_code}")

        except Exception as e:
            logger.error(f"Error searching Hacker News: {e}")

        return posts

    def scrape_all_sources(self):
        """Scrape all alternative sources for OpenAI news"""
        all_posts = []

        # Try RSS feeds first
        rss_posts = self.try_rss_feeds()
        all_posts.extend(rss_posts)

        # Get GitHub releases
        github_posts = self.get_openai_github_releases()
        all_posts.extend(github_posts)

        # Search Hacker News
        hn_posts = self.search_hacker_news()
        all_posts.extend(hn_posts)

        # Remove duplicates and sort by date
        unique_posts = []
        seen_titles = set()

        for post in all_posts:
            if post['title'] not in seen_titles:
                seen_titles.add(post['title'])
                unique_posts.append(post)

        return unique_posts

    def save_posts_json(self, posts, filename='openai_alternative_posts.json'):
        """Save posts to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'total_posts': len(posts),
                'sources_checked': ['RSS Feeds', 'GitHub Releases', 'Hacker News'],
                'posts': posts
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(posts)} posts to {filename}")

    def print_posts(self, posts):
        """Print posts in a readable format"""
        if not posts:
            print("\n❌ No OpenAI posts found from alternative sources")
            return

        print(f"\n🔍 OpenAI News from Alternative Sources ({len(posts)} found)")
        print("=" * 70)

        for i, post in enumerate(posts, 1):
            print(f"\n{i}. {post['title']}")
            print(f"   Source: {post.get('source', 'Unknown')}")
            print(f"   URL: {post['url']}")
            print(f"   Date: {post['date']}")
            if post['description'] and len(post['description']) > 10:
                desc = post['description'][:150] + '...' if len(post['description']) > 150 else post['description']
                print(f"   Description: {desc}")


def main():
    """Main function"""
    scraper = OpenAIAlternativeScraper()

    print("🤖 OpenAI Alternative News Scraper")
    print("Since OpenAI blocks direct scraping, using alternative sources...")
    print()

    posts = scraper.scrape_all_sources()

    if posts:
        scraper.print_posts(posts)
        scraper.save_posts_json(posts)
        logger.info(f"Successfully found {len(posts)} OpenAI-related posts")
    else:
        print("❌ No posts found from any alternative sources")
        print("\nTip: You could also try:")
        print("- Monitoring @OpenAI on Twitter/X")
        print("- Checking their LinkedIn company page")
        print("- Setting up Google Alerts for 'OpenAI'")


if __name__ == "__main__":
    main()