from flask import Flask, jsonify, request, render_template
import requests
import gzip
import binascii
import re
import json

app = Flask(__name__)

TOKEN_BASE_URL = "https://jwt-gen-new.vercel.app/token"

UID_PASSWORDS = {
    "ind": {"uid": "4258906717", "password": "RockingGamerz65-1WDTR63DX"},
    "br": {"uid": "4113330289", "password": "FA684A835410A8AFFE785552154AD87A4CB928C03D8870DEE37AB7C019B2D162"},
    "na": {"uid": "4139196327", "password": "FA680B796474B22907BFD3DF2AFA29577FA43C5B2068417AA24453F25212B854"},
    "eu": {"uid": "4139177376", "password": "E29B0A5C48E8B426BE3E9D977927606842310E2F14EB108F2B5D7F73D9C4B105"},
    "sg": {"uid": "4139211052", "password": "3BA22FEF36B7118B9FB1E1EB3E5A6DD84BDE696BD66B494269496E9834F00F3B"},
    "vn": {"uid": "4113363250", "password": "47269BFC4695E93FFABA1AA426847669D12AF36F6B7FCA52BF660459EE2B4092"},
    "th": {"uid": "4113415247", "password": "2542DD73DD60B33E183C6A894F9F6A2FC7DAEC457B826C71D44BFD4470788BBB"},
    "tw": {"uid": "4113375272", "password": "6AB01F7FB110A4C9EB95DBA21BD0E63E622DF8E566157811910F81E54394A17D"},
    "id": {"uid": "4109659017", "password": "7CE44389FE7D03FF892E682D00C5BE586B12789019CCCB466080CED41806DBAB"},
    "pk": {"uid": "4139224003", "password": "1812098F2587DCAEF5CC21EAD93FAA751D212CD81C586CFD4B4F48C1B49D2A88"},
    "bd": {"uid": "4139230703", "password": "6C2D5409593C61CFD31CDA18146054D05E72F261F24343CDEA75AEF38ADF5C95"}
}

API_DOMAINS = {
    "ind": "https://client.ind.freefiremobile.com/",
    "br": "https://client.us.freefiremobile.com/",
    "na": "https://client.us.freefiremobile.com/",
    "eu": "https://clientbp.ggpolarbear.com/",
    "sg": "https://clientbp.ggpolarbear.com/",
    "vn": "https://clientbp.ggpolarbear.com/",
    "th": "https://clientbp.ggpolarbear.com/",
    "tw": "https://clientbp.ggpolarbear.com/",
    "id": "https://clientbp.ggpolarbear.com/",
    "pk": "https://clientbp.ggpolarbear.com/",
    "bd": "https://clientbp.ggpolarbear.com/"
}

server_tokens = {}

BASE_LINK_DEFAULT = "https://dl.dir.freefiremobile.com/common/"
BASE_LINK_IND = "https://dl-tata.freefireind.in/common/"


@app.route("/")
def home():
    return render_template("ui.html")


def get_base(region):
    if region == "ind":
        return BASE_LINK_IND
    return BASE_LINK_DEFAULT


def get_token(region):

    if region in server_tokens:
        return server_tokens[region]

    creds = UID_PASSWORDS[region]

    url = f"{TOKEN_BASE_URL}?uid={creds['uid']}&password={creds['password']}"

    response = requests.get(url, timeout=20)

    text = response.text

    token = None

    patterns = [
        r'"token"\s*:\s*"([^"]+)"',
        r'token\s*:\s*"([^"]+)"',
        r'Bearer\s+([A-Za-z0-9\-_.]+)'
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:
            token = match.group(1)
            break

    if token:
        server_tokens[region] = token
        return token

    return None


def cleanup_link(link):

    if not link:
        return None

    link = link.strip()

    link = re.sub(r'^[^a-zA-Z0-9]+', '', link)

    while link.endswith(("0", "X", "J", "B", "@", "#", "`")):
        link = link[:-1]

    link = link.strip()

    return link


def fix_link(link, region):

    link = cleanup_link(link)

    if not link:
        return None

    if link.startswith("http://"):
        link = link.replace("http://", "https://")

    if link.startswith("https://"):
        return link

    if re.match(r'^OB\d+', link, re.IGNORECASE):
        return get_base(region) + link

    return None


def extract_assets(text, region):

    results = []

    patterns = [

        r'https?://[^\s"\']+',

        r'OB\d+/[^\s"\']+\.(?:png|jpg|jpeg|webp|ktx|json|html|ff_extend)',

        r'OB\d+/[^\s"\']+',

    ]

    for pattern in patterns:

        matches = re.findall(pattern, text, re.IGNORECASE)

        for m in matches:

            fixed = fix_link(m, region)

            if fixed:
                results.append(fixed)

    cleaned = []

    for r in results:

        r = cleanup_link(r)

        if not r:
            continue

        if any(ext in r.lower() for ext in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".ktx",
            ".json",
            ".html",
            ".ff_extend"
        ]):
            cleaned.append(r)

    return list(dict.fromkeys(cleaned))


@app.route("/run_script")
def run_script():

    try:

        region = request.args.get("server")
        endpoint = request.args.get("name")

        if not region or not endpoint:
            return jsonify({
                "error": "Missing parameters"
            })

        token = get_token(region)

        if not token:
            return jsonify({
                "error": "Token fetch failed"
            })

        url = API_DOMAINS[region].rstrip("/") + "/" + endpoint.lstrip("/")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "UnityPlayer/2022.3.47f1",
            "ReleaseVersion": "OB53",
            "X-Unity-Version": "2022.3.47f1"
        }

        payload = binascii.unhexlify(
            "8533b7e1d34a5dfd9a830ee5cc36664e"
        )

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=25
        )

        raw_content = response.content

        decompressed = False

        try:
            if raw_content[:2] == b'\x1f\x8b':
                raw_content = gzip.decompress(raw_content)
                decompressed = True
        except:
            pass

        decoded_text = raw_content.decode(
            "utf-8",
            errors="ignore"
        )

        assets = extract_assets(decoded_text, region)

        return jsonify({

            "success": True,

            "status_code": response.status_code,

            "endpoint": endpoint,

            "region": region,

            "decompressed": decompressed,

            "total_assets": len(assets),

            "strings": assets,

            "debug": {
                "response_length": len(decoded_text),
                "token_exists": bool(token),
                "sample": decoded_text[:3000]
            }

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(debug=True)