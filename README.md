# AI Competitor Tracker

A web scraping application that monitors AI companies and generates daily competitive intelligence reports.

## Features

- Automated web scraping of competitor websites
- Daily report generation in markdown format
- Configurable competitor URLs and CSS selectors
- Respectful scraping with rate limiting and retries
- Comprehensive logging and error handling
- Optional scheduling for automated daily runs

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Configure competitors in `config.json`:
```json
{
  "competitors": {
    "Company Name": {
      "url": "https://company.com/blog",
      "name": "Display Name",
      "selectors": {
        "title": "h1, h2, .post-title",
        "content": ".post-content, main",
        "date": ".date, time"
      }
    }
  }
}
```

## Usage

### Run Once
```bash
python scraper.py
```

### Enable Daily Scheduling
Edit `scraper.py` and uncomment the scheduling section in `main()` to run daily at 9:00 AM.

## Output

Reports are saved to the `reports/` directory with filename format:
`ai-competitor-report-YYYY-MM-DD.md`

## File Structure

```
ai-competitor-tracker/
├── scraper.py          # Main scraping logic
├── config.json         # Website URLs and settings
├── requirements.txt    # Python dependencies
├── reports/           # Generated daily reports
├── scraper.log        # Application logs
└── README.md          # This file
```

## Configuration

The `config.json` file contains:
- **competitors**: Website URLs and CSS selectors for each competitor
- **settings**: Request delays, timeouts, user agent, and retry limits

## Ethical Considerations

This scraper:
- Uses respectful request delays
- Includes proper User-Agent identification
- Implements retry limits and timeouts
- Logs all activities for transparency