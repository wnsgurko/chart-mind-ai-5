from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import requests, time, math, statistics
from typing import Optional

BASE = Path(__file__).parent
app = FastAPI(title="ChartMind AI Paper")
app.mount("/static", StaticFiles(directory=str(BASE)), name="static")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 ChartMindAI/5.0"})

CRYPTO_HOSTS = [
    "https://api.binance.com",
    "https://api.binance.us",
]
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/"

def clean_symbol(symbol: str, asset: str) -> str:
    s = "".join(ch for ch in symbol.upper() if ch.isalnum() or ch in ".-")
    if not s:
        raise ValueError("종목 코드가 비어 있습니다.")
    if asset == "crypto" and not s.endswith("USDT"):
        s += "USDT"
    return s

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    return {"ok": True, "service": "ChartMind AI Paper", "version": "5.0"}

@app.get("/api/market")
def market(
    asset: str = Query("crypto", pattern="^(crypto|stock)$"),
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("1m"),
    limit: int = Query(120, ge=30, le=250),
):
    try:
        symbol = clean_symbol(symbol, asset)
        if asset == "crypto":
            interval_map = {"1m":"1m", "5m":"5m", "15m":"15m", "1h":"1h", "4h":"4h"}
            interval = interval_map.get(interval, "1m")
            errors = []
            for host in CRYPTO_HOSTS:
                try:
                    url = host + "/api/v3/klines"
                    r = SESSION.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=8)
                    if r.status_code == 451:
                        errors.append(f"{host}: 지역 제한(451)")
                        continue
                    r.raise_for_status()
                    raw = r.json()
                    if not isinstance(raw, list) or len(raw) < 2:
                        errors.append(f"{host}: 캔들 데이터 부족")
                        continue
                    candles = []
                    for row in raw:
                        candles.append({
                            "time": int(row[0] // 1000),
                            "open": float(row[1]), "high": float(row[2]),
                            "low": float(row[3]), "close": float(row[4]),
                            "volume": float(row[5])
                        })
                    return {"ok": True, "asset": asset, "symbol": symbol, "currency": "USDT",
                            "source": "Binance public market data", "interval": interval,
                            "candles": candles, "updated": int(time.time()),
                            "note": "공개 시세 데이터이며 거래 주문은 전송하지 않습니다."}
                except Exception as e:
                    errors.append(f"{host}: {str(e)[:100]}")
            raise RuntimeError("코인 시세 제공처에 연결하지 못했습니다. " + " / ".join(errors))
        else:
            # Yahoo Finance intraday chart. For US stocks and major Korean listings.
            interval_map = {"1m":("1m","1d"), "5m":("5m","5d"), "15m":("15m","5d"), "1h":("60m","1mo"), "1d":("1d","6mo")}
            yf_interval, period = interval_map.get(interval, ("5m","5d"))
            url = YAHOO_CHART + requests.utils.quote(symbol, safe=".-") 
            r = SESSION.get(url, params={"range": period, "interval": yf_interval, "includePrePost": "false"}, timeout=10)
            r.raise_for_status()
            data = r.json().get("chart", {})
            if data.get("error"):
                raise RuntimeError(str(data["error"].get("description") or "Yahoo Finance returned an error"))
            result = (data.get("result") or [None])[0]
            if not result:
                raise RuntimeError("주식 시세 데이터가 비어 있습니다. 종목 코드를 확인해 주세요.")
            timestamps = result.get("timestamp") or []
            quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
            opens, highs, lows, closes, volumes = [quote.get(k) or [] for k in ("open","high","low","close","volume")]
            candles = []
            for i, ts in enumerate(timestamps):
                vals = [opens[i] if i < len(opens) else None, highs[i] if i < len(highs) else None,
                        lows[i] if i < len(lows) else None, closes[i] if i < len(closes) else None]
                if any(v is None for v in vals):
                    continue
                candles.append({"time": int(ts), "open": float(vals[0]), "high": float(vals[1]),
                                "low": float(vals[2]), "close": float(vals[3]),
                                "volume": float(volumes[i] or 0) if i < len(volumes) else 0})
            if len(candles) < 2:
                raise RuntimeError("유효한 주식 캔들이 충분하지 않습니다. 장 마감·휴장·종목 코드 문제일 수 있습니다.")
            currency = (result.get("meta") or {}).get("currency", "unknown")
            return {"ok": True, "asset": asset, "symbol": symbol, "currency": currency,
                    "source": "Yahoo Finance chart data", "interval": interval,
                    "candles": candles[-limit:], "updated": int(time.time()),
                    "note": "주식 데이터는 제공처 정책에 따라 지연될 수 있습니다."}
    except Exception as e:
        return {"ok": False, "asset": asset, "symbol": symbol, "error": str(e),
                "updated": int(time.time()), "hint": "새로고침 간격을 늘리거나 다른 종목을 선택해 보세요."}

@app.get("/api/news")
def news(q: str = "markets"):
    # Lightweight RSS retrieval; optional and non-blocking for core chart.
    try:
        from xml.etree import ElementTree as ET
        url = "https://news.google.com/rss/search"
        r = SESSION.get(url, params={"q": q, "hl":"en-US", "gl":"US", "ceid":"US:en"}, timeout=6)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = []
        for item in root.findall(".//item")[:8]:
            items.append({"title": item.findtext("title", default=""), "link": item.findtext("link", default=""),
                          "pubDate": item.findtext("pubDate", default="")})
        return {"ok": True, "items": items, "source": "Google News RSS"}
    except Exception as e:
        return {"ok": False, "items": [], "error": str(e)[:160]}
