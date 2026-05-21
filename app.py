import os
import re
from collections import Counter
from urllib.parse import urlparse

BASE_DIR = "/storage/emulated/0"

INPUT_FILE = os.path.join(BASE_DIR, "TestResponse.txt")
REPORT_FILE = os.path.join(BASE_DIR, "report.txt")

BASE_LINK = "https://dl.dir.freefiremobile.com/common/"

VALID_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".mp4",
    ".webm",
    ".ktx",
    ".html",
    ".json",
    ".txt",
    ".mp3",
    ".wav"
]

if not os.path.exists(INPUT_FILE):
    print("TestResponse.txt not found")
    exit()

with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
    raw = f.read()

# =========================================================
# CLEAN RAW RESPONSE
# =========================================================

raw = raw.replace(".ff_extend", ".jpg")
raw = raw.replace(".ktxp", ".png")

# remove binary garbage after extensions
raw = re.sub(r'(\.(?:png|jpg|jpeg|webp|gif|bmp|mp4|webm|ktx|html|json))(?:[0-9\x00-\x1f]+)', r'\1', raw, flags=re.IGNORECASE)

# =========================================================
# URL EXTRACTION
# =========================================================

url_pattern = re.compile(
    r'https?://[^\s"<>\']+',
    re.IGNORECASE
)

found_urls = url_pattern.findall(raw)

clean_urls = []
seen = set()

for url in found_urls:

    url = url.strip()

    # remove garbage chars
    url = re.sub(r'[\x00-\x1f]+', '', url)

    # trim symbols
    url = url.rstrip(',:;*|)}]>')

    # fix ff_extend
    url = url.replace(".ff_extend", ".jpg")

    # fix ktxp
    url = url.replace(".ktxp", ".png")

    # =====================================================
    # FIX EXTENSIONS
    # =====================================================

    ext_match = re.search(
        r'\.(png|jpg|jpeg|webp|gif|bmp|mp4|webm|ktx|html|json|txt|mp3|wav)',
        url,
        re.IGNORECASE
    )

    if ext_match:

        ext = ext_match.group(0)

        end_pos = url.lower().find(ext.lower())

        if end_pos != -1:
            url = url[:end_pos + len(ext)]

    # =====================================================
    # HANDLE HALF PATHS
    # =====================================================

    if not url.startswith("http"):

        if (
            "/" in url and
            any(url.lower().endswith(x) for x in VALID_EXTENSIONS)
        ):
            url = BASE_LINK + url.lstrip("/")

    # =====================================================
    # FILTER INVALIDS
    # =====================================================

    if len(url) < 8:
        continue

    if "http" not in url:
        continue

    if url not in seen:
        seen.add(url)
        clean_urls.append(url)

# =========================================================
# EXTRA HALF LINKS
# =========================================================

half_pattern = re.compile(
    r'([A-Za-z0-9_\-/]+?\.(?:png|jpg|jpeg|webp|gif|bmp|mp4|webm|ktx|html|json))',
    re.IGNORECASE
)

half_matches = half_pattern.findall(raw)

for item in half_matches:

    item = item.strip()

    if item.startswith("http"):
        continue

    if "/" not in item:
        continue

    full = BASE_LINK + item.lstrip("/")

    full = full.replace(".ff_extend", ".jpg")
    full = full.replace(".ktxp", ".png")

    if full not in seen:
        seen.add(full)
        clean_urls.append(full)

# =========================================================
# ANALYSIS
# =========================================================

domains = []
extensions = []

media_urls = []
html_urls = []
cdn_urls = []

for url in clean_urls:

    parsed = urlparse(url)

    domains.append(parsed.netloc)

    ext_match = re.search(
        r'\.(png|jpg|jpeg|webp|gif|bmp|mp4|webm|ktx|html|json|txt|mp3|wav)$',
        url,
        re.IGNORECASE
    )

    if ext_match:
        extensions.append(ext_match.group(0).lower())

    lower = url.lower()

    if any(lower.endswith(x) for x in [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".bmp",
        ".ktx",
        ".mp4"
    ]):
        media_urls.append(url)

    if lower.endswith(".html"):
        html_urls.append(url)

    if (
        "dl.dir.freefiremobile.com" in lower or
        "dl-tata.freefireind.in" in lower
    ):
        cdn_urls.append(url)

domain_counter = Counter(domains)
extension_counter = Counter(extensions)

# =========================================================
# REPORT
# =========================================================

report = []

report.append("=" * 70)
report.append("FREE FIRE RESPONSE ANALYSIS REPORT")
report.append("=" * 70)

report.append(f"\nTOTAL URLS: {len(clean_urls)}")
report.append(f"TOTAL UNIQUE DOMAINS: {len(set(domains))}")
report.append(f"TOTAL MEDIA URLS: {len(media_urls)}")
report.append(f"TOTAL HTML URLS: {len(html_urls)}")

report.append("\n" + "=" * 70)
report.append("TOP DOMAINS")
report.append("=" * 70)

for domain, count in domain_counter.most_common():
    report.append(f"{count:4}  {domain}")

report.append("\n" + "=" * 70)
report.append("EXTENSIONS")
report.append("=" * 70)

for ext, count in extension_counter.most_common():
    report.append(f"{count:4}  {ext}")

report.append("\n" + "=" * 70)
report.append("MEDIA URLS")
report.append("=" * 70)

for url in media_urls:
    report.append(url)

report.append("\n" + "=" * 70)
report.append("HTML URLS")
report.append("=" * 70)

for url in html_urls:
    report.append(url)

report.append("\n" + "=" * 70)
report.append("CDN URLS")
report.append("=" * 70)

for url in cdn_urls:
    report.append(url)

report.append("\n" + "=" * 70)
report.append("ALL CLEAN URLS")
report.append("=" * 70)

for url in clean_urls:
    report.append(url)

report.append("\n" + "=" * 70)
report.append("END")
report.append("=" * 70)

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("DONE")
print("REPORT:", REPORT_FILE)