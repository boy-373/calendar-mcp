# China Calendar & Lunar MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)
[![Remote](https://img.shields.io/badge/Streamable%20HTTP-hosted%20free-success)](https://mcp.pianam.cn/calendar-mcp/mcp)

Chinese calendar tools for AI agents: **statutory public holidays & makeup-workday schedules** (2025–2026, per the State Council of China) plus accurate **solar-to-lunar calendar conversion** (lunar date, zodiac animal, ganzhi / heavenly-stems-earthly-branches).

- **Try it in 30 seconds**: a free public MCP endpoint is already running — just paste the URL into your MCP client (no install, no API key).
- **Or self-host**: a small FastMCP server; holiday data is bundled locally, lunar conversion uses the `sxtwl` ephemeris library (pure-Python `lunardate` fallback supported).

## ⚡ Use the hosted endpoint (no setup)

```
https://mcp.pianam.cn/calendar-mcp/mcp
```

Transport: **Streamable HTTP** (MCP 2025-03-26 compatible). No authentication required.

## 🔌 Client configuration

Add this to your MCP client's `mcpServers` configuration (Claude Desktop `claude_desktop_config.json`, Cursor `mcp.json`, Cline, Cherry Studio, etc.):

```json
{
  "mcpServers": {
    "calendar": {
      "type": "http",
      "url": "https://mcp.pianam.cn/calendar-mcp/mcp"
    }
  }
}
```

> Clients that do not accept `"type": "http"` accept the same entry with just `"url"`.

## 🧰 Tools

| Tool | Parameters | Returns |
|

[![calendar-mcp MCP server](https://glama.ai/mcp/servers/boy-373/calendar-mcp/badges/score.svg)](https://glama.ai/mcp/servers/boy-373/calendar-mcp)

---|---|---|
| `query_holiday(date)` | `date`: solar date `YYYY-MM-DD`, e.g. `"2026-10-01"`. | Weekday, holiday name (if any), day type — public holiday off-day / makeup workday / normal workday / weekend — plus the lunar date for that day. |
| `solar_to_lunar(year, month, day)` | `year`/`month`/`day`: solar date integers. | Lunar year/month/day, leap-month flag, lunar date string (Chinese), zodiac animal, and year/month/day ganzhi (干支). |
| `list_holidays(year)` | `year`: integer year, e.g. `2026`. | All statutory holidays of the year: name, off-day count, date ranges, exact off dates and makeup-workday dates. |

### Examples

- "2026-10-01 是节假日吗？" → National Day holiday, with lunar date attached.
- "2026-02-17 农历是多少？" → lunar date, zodiac, ganzhi.
- "列出 2026 年全部法定节假日和调休安排" → full year schedule.

## 📡 Data

- **Holidays**: official holiday-arrangement notices issued by the General Office of the State Council of China (国务院办公厅). Bundled locally for 2025 and 2026; extend `HOLIDAY_DATA` to add more years.
- **Lunar conversion**: [`sxtwl`](https://pypi.org/project/sxtwl/) (ShouWang calendar ephemeris, C extension). If `sxtwl` is unavailable the server automatically falls back to the pure-Python [`lunardate`](https://pypi.org/project/lunardate/) library (install it separately).
- No external HTTP API and **no API key** is required.

## 🐢 Self-hosting

```bash
git clone https://github.com/boy-373/calendar-mcp.git
cd calendar-mcp
pip install -r requirements.txt
python server.py
# listens on 127.0.0.1:8000 by default; override with:
#   MCP_HOST=0.0.0.0 MCP_PORT=9000 python server.py
# behind a reverse proxy, allow your public hostname:
#   MCP_ALLOWED_HOSTS="your-domain.com,your-domain.com:*" python server.py
```

Then point your MCP client at `http://127.0.0.1:8000/mcp`.

You can also run the server with [uv](https://docs.astral.sh/uv/):

```bash
uv venv && uv pip install -r requirements.txt
uv run python server.py
```

## 🗂️ Files

- `calendar_server.py` — the MCP server: holiday data, lunar conversion, FastMCP tool definitions.
- `server.py` — standalone Streamable HTTP entry point (binds host/port, serves the MCP app at `/mcp`).
- `requirements.txt` — Python dependencies.
- `LICENSE` — MIT.

---

## 🇨🇳 中文说明

中国万年历 MCP：**法定节假日 / 调休安排查询**（2025–2026，依据国务院办公厅通知）与**公历转农历**（农历年月日、闰月、生肖、干支）。

**在线直连（免费、无需 Key）**：`https://mcp.pianam.cn/calendar-mcp/mcp`

**工具**：

- `query_holiday(date)`：查询某公历日期的节假日 / 调休安排，附带农历信息。
- `solar_to_lunar(year, month, day)`：公历转农历，返回农历日期、闰月、生肖、干支。
- `list_holidays(year)`：列出某年全部法定节假日放假与调休上班日期。

节假日数据内置本地（2025、2026，可逐年扩展）；农历转换使用 `sxtwl` 历库，缺失时自动降级到纯 Python 的 `lunardate`；全程无需外部 API 与密钥。

## 📄 License

[MIT](LICENSE) © 2026 boy-373 (刘扶阳)
