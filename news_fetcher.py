from datetime import datetime
import yfinance as yf


def _format_pub_date(raw):
    if not raw:
        return ""
    try:
        if isinstance(raw, (int, float)):
            dt = datetime.fromtimestamp(raw)
        else:
            text = str(raw).replace("Z", "+00:00")
            dt = datetime.fromisoformat(text)
        return dt.strftime("%d %b %Y")
    except (ValueError, TypeError, OSError):
        return ""


def _extract_link(content):
    click_through = content.get("clickThroughUrl") or {}
    if isinstance(click_through, dict) and click_through.get("url"):
        return click_through["url"]

    canonical = content.get("canonicalUrl") or {}
    if isinstance(canonical, dict) and canonical.get("url"):
        return canonical["url"]

    preview = content.get("previewUrl")
    if preview:
        return preview

    return ""


def _parse_modern_item(item):
    content = item.get("content") or {}
    if not isinstance(content, dict):
        return None

    title = (content.get("title") or "").strip()
    if not title:
        return None

    provider = content.get("provider") or {}
    publisher = provider.get("displayName", "Unknown") if isinstance(provider, dict) else "Unknown"

    pub_raw = content.get("displayTime") or content.get("pubDate") or ""
    link = _extract_link(content)

    return {
        "title": title,
        "publisher": publisher or "Unknown",
        "link": link,
        "published": _format_pub_date(pub_raw),
    }


def _parse_legacy_item(item):
    title = (item.get("title") or "").strip()
    if not title:
        return None

    link = item.get("link") or item.get("url") or ""
    publisher = item.get("publisher") or item.get("source") or "Unknown"
    pub_raw = item.get("providerPublishTime") or item.get("published") or ""

    return {
        "title": title,
        "publisher": publisher,
        "link": link,
        "published": _format_pub_date(pub_raw),
    }


def get_latest_news(ticker, count=5):
    """
    Fetches the latest news articles for a given ticker using yfinance.
    Supports both legacy and current Yahoo Finance news payload shapes.
    """
    try:
        news_data = yf.Ticker(ticker).news or []
        articles = []

        for item in news_data:
            if not isinstance(item, dict):
                continue

            parsed = None
            if "content" in item:
                parsed = _parse_modern_item(item)
            else:
                parsed = _parse_legacy_item(item)

            if parsed:
                articles.append(parsed)
            if len(articles) >= count:
                break

        return articles
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []
