---
name: world-news
description: Use when the user asks about current events, world news, global headlines, market-moving news, or any request requiring awareness of recent news. Fetches top headlines via NewsAPI and produces an AI-summarized morning brief.
---

# World News — Morning Brief

Fetches top global headlines via NewsAPI, then synthesizes them into an AI-written morning brief with categorized analysis and key takeaways.

## Setup

```bash
pip install -r scripts/requirements.txt
```

Get a **free API key** at [newsapi.org/register](https://newsapi.org/register) (100 requests/day).

### Option A: .env file (recommended)

```bash
# Copy template and paste your key
copy scripts\.env.example scripts\.env
# Then edit scripts\.env and put your key in

# Script auto-loads .env from the same directory
python scripts/world_news.py
```

### Option B: Environment variable

```bash
# PowerShell
$env:NEWSAPI_KEY = "your-key-here"
python scripts/world_news.py
```

### Option C: Pass inline

```bash
python scripts/world_news.py --api-key KEY
```

## Quick Commands

```bash
# All top headlines (US, general)
python scripts/world_news.py --api-key KEY

# Business & markets
python scripts/world_news.py --topic business --api-key KEY

# Technology
python scripts/world_news.py --topic tech --max 10 --api-key KEY

# Politics
python scripts/world_news.py --topic politics --api-key KEY

# World affairs (popular stories across all sources)
python scripts/world_news.py --topic world --api-key KEY

# Prestige sources only (Reuters, BBC, AP, WSJ, Bloomberg, FT)
python scripts/world_news.py --prestige --api-key KEY

# Raw JSON output (for AI processing)
python scripts/world_news.py --topic all --max 50 --json --api-key KEY

# Using env var instead of --api-key
$env:NEWSAPI_KEY = "your-key"
python scripts/world_news.py --topic world --json
```

## Parameters

| Argument | Description | Default |
|----------|-------------|---------|
| `--api-key` | NewsAPI key (or `NEWSAPI_KEY` env var) | — |
| `--max` | Max articles (max 100) | `15` |
| `--topic` | `all`, `business`, `tech`, `politics`, `world` | `all` |
| `--prestige` | Reuters, BBC, AP, WSJ, Bloomberg, FT only | `False` |
| `--json` | Raw JSON output | `False` |

## Workflow

1. **Set key:** `$env:NEWSAPI_KEY = "your-key"`
2. **Fetch:** `python scripts/world_news.py --topic all --max 50 --json`
3. **Synthesize:** AI reads JSON → writes Morning Brief

## Morning Brief Template

```markdown
╔═══════════════════════════════════════╗
║        WORLD NEWS BRIEF              ║
║        {current date}                ║
╚═══════════════════════════════════════╝

[🌍 OVERVIEW]
{1-2 sentence macro summary of the day's most important theme}

[🏛 POLITICS & POLICY]
{bullet list of key political headlines with 1-line impact note}

[💰 BUSINESS & MARKETS]
{bullet list of key business headlines with market context}

[🔬 TECHNOLOGY & SCIENCE]
{bullet list of key tech/science headlines}

[⚡ TRENDS TO WATCH]
{1-3 cross-cutting themes or patterns observed across articles}
```

## Output Format (JSON)

```json
{
  "title":   "Headline text",
  "url":     "https://...",
  "snippet": "Article description",
  "date":    "2026-05-22 14:30 UTC",
  "source":  "Reuters"
}
```

## Script Location

```
scripts/world_news.py
```

## Notes

- NewsAPI free tier: 100 requests/day, 100 articles/request max
- `--prestige` restricts to top-tier sources (no category filter)
- `--topic world` uses the "everything" endpoint sorted by popularity
- Other topics use the "top-headlines" endpoint by category
