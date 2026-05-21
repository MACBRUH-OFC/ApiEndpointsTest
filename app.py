from flask import Flask, jsonify, render_template, request
import requests
import gzip
import binascii
import re

app = Flask(__name__)

TOKEN_BASE_URL = "https://jwt-gen-new.vercel.app/token"

UID_PASSWORDS = {
    "ind": {"uid": "4258906717", "password": "RockingGamerz65-1WDTR63DX"},
    "mea": {"uid": "4103849657", "password": "EF315D040E99F9B63D79C7AEE6DC697F297D298EF384BAA4E50E003DB56514C4"},
    "id": {"uid": "4109659017", "password": "7CE44389FE7D03FF892E682D00C5BE586B12789019CCCB466080CED41806DBAB"},
    "cis": {"uid": "3301239795", "password": "DD40EE772FCBD61409BB15033E3DE1B1C54EDA83B75DF0CDD24C34C7C8798475"},
    "br": {"uid": "4113330289", "password": "FA684A835410A8AFFE785552154AD87A4CB928C03D8870DEE37AB7C019B2D162"},
    "latam": {"uid": "4113343938", "password": "F7F739FCFB96A09B019D87C6B45174B76FAE406A4CD7A785F187E46C7F7A71FF"},
    "vn": {"uid": "4113363250", "password": "47269BFC4695E93FFABA1AA426847669D12AF36F6B7FCA52BF660459EE2B4092"},
    "tw": {"uid": "4113375272", "password": "6AB01F7FB110A4C9EB95DBA21BD0E63E622DF8E566157811910F81E54394A17D"},
    "th": {"uid": "4113415247", "password": "2542DD73DD60B33E183C6A894F9F6A2FC7DAEC457B826C71D44BFD4470788BBB"},
    "sg": {"uid": "4139211052", "password": "3BA22FEF36B7118B9FB1E1EB3E5A6DD84BDE696BD66B494269496E9834F00F3B"},
    "eu": {"uid": "4139177376", "password": "E29B0A5C48E8B426BE3E9D977927606842310E2F14EB108F2B5D7F73D9C4B105"},
    "na": {"uid": "4139196327", "password": "FA680B796474B22907BFD3DF2AFA29577FA43C5B2068417AA24453F25212B854"},
    "pk": {"uid": "4139224003", "password": "1812098F2587DCAEF5CC21EAD93FAA751D212CD81C586CFD4B4F48C1B49D2A88"},
    "bd": {"uid": "4139230703", "password": "6C2D5409593C61CFD31CDA18146054D05E72F261F24343CDEA75AEF38ADF5C95"}
}

API_DOMAINS = {
    "ind": "https://client.ind.freefiremobile.com/",
    "mea": "https://clientbp.ggpolarbear.com/",
    "id": "https://clientbp.ggpolarbear.com/",
    "cis": "https://clientbp.ggpolarbear.com/",
    "br": "https://client.us.freefiremobile.com/",
    "latam": "https://client.us.freefiremobile.com/",
    "vn": "https://clientbp.ggpolarbear.com/",
    "tw": "https://clientbp.ggpolarbear.com/",
    "th": "https://clientbp.ggpolarbear.com/",
    "sg": "https://clientbp.ggpolarbear.com/",
    "eu": "https://clientbp.ggpolarbear.com/",
    "na": "https://client.us.freefiremobile.com/",
    "pk": "https://clientbp.ggpolarbear.com/",
    "bd": "https://clientbp.ggpolarbear.com/"
}

server_tokens = {k: None for k in UID_PASSWORDS}


@app.route("/")
def home():
    return render_template("ui.html")


def get_token(server):

    if server_tokens[server]:
        return server_tokens[server]

    try:

        uid = UID_PASSWORDS[server]["uid"]
        password = UID_PASSWORDS[server]["password"]

        response = requests.get(
            f"{TOKEN_BASE_URL}?uid={uid}&password={password}",
            timeout=15
        )

        text = response.text

        token_match = re.search(
            r'eyJ[a-zA-Z0-9_\-\.]+',
            text
        )

        if token_match:
            token = token_match.group(0)
            server_tokens[server] = token
            return token

    except Exception as e:
        print(e)

    return None


def clean_link(url):

    url = url.strip()

    garbage = [
        "\x00",
        "\x01",
        "\x02",
        "\x03",
        "\x04",
        "\x05",
        "\x06",
        "\x07",
        "\x08",
        "\x0b",
        "\x0c",
        "\x0e",
        "\x0f",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    ]

    for g in garbage:
        url = url.replace(g, "")

    url = re.sub(r'[\s"\'>]+$', '', url)

    url = re.sub(r'(\.png|\.jpg|\.jpeg|\.webp|\.gif|\.ktx|\.ktxp|\.mp4|\.html|\.json|\.ff_extend)0+$', r'\1', url)

    return url.strip()


def extract_urls(text):

    pattern = r'''(?:
        https?://
        [^\s<>"']+
    )'''

    raw = re.findall(pattern, text, re.VERBOSE)

    final = []

    seen = set()

    for url in raw:

        url = clean_link(url)

        if len(url) < 8:
            continue

        if url in seen:
            continue

        seen.add(url)

        final.append(url)

    return final


@app.route("/run_script")
def run_script():

    server = request.args.get("server")
    api_name = request.args.get("name")

    if server not in UID_PASSWORDS:
        return jsonify({
            "success": False,
            "error": "Invalid server"
        })

    if not api_name:
        return jsonify({
            "success": False,
            "error": "Missing API name"
        })

    token = get_token(server)

    if not token:
        return jsonify({
            "success": False,
            "error": "Token fetch failed"
        })

    url = API_DOMAINS[server].rstrip("/") + "/" + api_name.lstrip("/")

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

    try:

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=25
        )

        raw = response.content

        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)

        decoded = raw.decode(
            "utf-8",
            errors="ignore"
        )

        strings = re.findall(
            r'[\x20-\x7E]{4,}',
            decoded
        )

        urls = extract_urls(decoded)

        return jsonify({
            "success": True,
            "status": response.status_code,
            "count": len(urls),
            "links": urls,
            "strings": strings,
            "strings_count": len(strings),
            "raw_size": len(raw)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(debug=True)