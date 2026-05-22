# myskill

Custom skills for AI coding agents (OpenCode, Claude Code, Copilot CLI, Gemini CLI, and any agent that supports skill-based workflows).

## Skills

| Skill | Description |
|-------|-------------|
| **fundamental-analysis** | Analyze stocks using fundamental data — revenue, earnings, valuation ratios, profitability, balance sheet health, cash flow, and growth estimates. |
| **stock-analysis** | Analyze stocks with technical indicators including support/resistance levels, RSI, MACD, Bollinger Bands, moving averages, volume analysis, and candlestick patterns. |
| **stock-news-sentiment** | Fetch recent news headlines, classify sentiment (bullish/bearish/neutral), and compare against price trend to show alignment or divergence. |
| **world-news** | Fetch top headlines via NewsAPI and produce AI-summarized morning briefs. |

## Usage

Each skill lives in `.agents/skills/<skill-name>/` and contains a `SKILL.md` with instructions and any supporting scripts.

To use a skill, load it in your agent's skill configuration or reference it directly during a session.
