# Casino-Bonus-Scraper

A full-stack application that extracts casino bonus offers, wagering requirements, and minimum deposits from a public webpage using Python and the Gemini API, then stores the structured results in JSON for the Vue 3 frontend.

## Tech Stack

- **Frontend:** Vue 3, Vite, JavaScript, Tailwind
- **Scraper:** Python 3.10+, Requests, BeautifulSoup4
- **AI Integration:** Gemini API (OpenAI-compatible endpoint)
- **Data Storage:** JSON

## Prerequisites

- Node.js and npm
- Python 3.10+
- Gemini API key

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd Casino-Bonus-Scraper
```

### 2. Install frontend dependencies

```bash
npm install
```

### 3. Install Python dependencies

```bash
py -m pip install requests beautifulsoup4
```

### 4. Configure environment variables

In PowerShell, set your Gemini API key:

```powershell
$env:GEMINI_API_KEY="your-gemini-api-key"
```

Optional configuration:

```powershell
$env:SOURCE_URL="https://betproof.co.za/casino-bonuses-south-africa/"
$env:LLM_MODEL="your-supported-gemini-model"
```

### 5. Run the scraper

```bash
py scraper.py
```

The scraper extracts three casino records and saves them to `src/data/bonuses.json`.

### 6. Run the frontend

```bash
npm run dev
```

## Production Build

```bash
npm run build
```

## Notes

- Checks `robots.txt` before scraping.
- Uses the Gemini API to structure bonus information.
- Validates casino names and the number of returned records.
- Retries rate-limited API requests.
- Keeps missing bonus details as `null`.
- Requires a valid API key and a supported Gemini model.
