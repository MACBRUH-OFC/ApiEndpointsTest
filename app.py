from flask import Flask, jsonify, request, render_template
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

server_tokens = {}

def get_token(server):

    try:

        if server in server_tokens:
            return server_tokens[server]

        uid = UID_PASSWORDS[server]["uid"]
        password = UID_PASSWORDS[server]["password"]

        token_url = f"{TOKEN_BASE_URL}?uid={uid}&password={password}"

        response = requests.get(token_url, timeout=20)

        if response.status_code != 200:
            return None

        text = response.text

        match = re.search(
            r'token\s*[:=]\s*"([^"]+)"',
            text
        )

        if not match:
            match = re.search(
                r'"token"\s*:\s*"([^"]+)"',
                text
            )

        if not match:
            match = re.search(
                r'eyJ[A-Za-z0-9._-]+',
                text
            )

        if match:

            token = match.group(1) if match.lastindex else match.group(0)

            server_tokens[server] = token

            return token

        return None

    except Exception:
        return None


def fetch_api(server, api_name):

    token = get_token(server)

    if not token:
        return {
            "success": False,
            "error": "Token fetch failed"
        }

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": "OB53",
        "User-Agent": "UnityPlayer/2022.3.47f1",
        "X-GA": "v1 1",
        "X-Unity-Version": "2022.3.47f1",
        "Authorization": f"Bearer {token}"
    }

    payload = binascii.unhexlify(
        "8533b7e1d34a5dfd9a830ee5cc36664e"
    )

    url = API_DOMAINS[server].rstrip("/") + "/" + api_name.lstrip("/")

    try:

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=20
        )

        raw = response.content

        if raw[:2] == b"\x1f\x8b":
            try:
                raw = gzip.decompress(raw)
            except:
                pass

        return {
            "success": True,
            "status": response.status_code,
            "raw": raw
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def clean_link(link):

    link = link.strip()

    bad_endings = ["@", "0", "X", "J"]

    changed = True

    while changed:

        changed = False

        for bad in bad_endings:

            if link.endswith(bad):
                link = link[:-1]
                changed = True

    return link


def extract_links(raw):

    results = []

    patterns = [

        rb'https?://[^\s\'"<>()]+',

        rb'dl\.[^\s\'"<>()]+',

        rb'ffredirect\.[^\s\'"<>()]+',

        rb'discord\.gg/[^\s\'"<>()]+',

        rb'whatsapp\.com/[^\s\'"<>()]+',

        rb'instagram\.com/[^\s\'"<>()]+',

        rb'OB\d+/[^\s\'"<>()]+\.(png|jpg|jpeg|webp|gif|ktx|html|json|ff_extend)',

    ]

    for pattern in patterns:

        try:

            matches = re.findall(pattern, raw, re.IGNORECASE)

            for match in matches:

                try:

                    if isinstance(match, tuple):
                        match = match[0]

                    text = match.decode(
                        "utf-8",
                        errors="ignore"
                    )

                    if not text.startswith("http"):

                        if text.startswith("dl."):
                            text = "https://" + text

                        elif text.startswith("ffredirect."):
                            text = "https://" + text

                        elif text.startswith("discord.gg"):
                            text = "https://" + text

                        elif text.startswith("instagram.com"):
                            text = "https://" + text

                        elif text.startswith("whatsapp.com"):
                            text = "https://" + text

                        elif text.startswith("OB"):
                            text = (
                                "https://dl.dir.freefiremobile.com/common/"
                                + text
                            )

                    text = clean_link(text)

                    if len(text) > 10:

                        if text not in results:
                            results.append(text)

                except:
                    pass

        except:
            pass

    return results


@app.route("/")
def home():
    return render_template("ui.html")


@app.route("/run_script")
def run_script():

    server = request.args.get("server")
    api_name = request.args.get("name")

    if not server or server not in UID_PASSWORDS:
        return jsonify({
            "success": False,
            "error": "Invalid server"
        })

    if not api_name:
        return jsonify({
            "success": False,
            "error": "API name missing"
        })

    api_response = fetch_api(server, api_name)

    if not api_response["success"]:
        return jsonify(api_response)

    raw = api_response["raw"]

    links = extract_links(raw)

    strings = re.findall(rb"[ -~]{4,}", raw)

    decoded = []

    for s in strings:

        try:
            decoded.append(
                s.decode("utf-8", errors="ignore")
            )
        except:
            pass

    return jsonify({
        "success": True,
        "status": api_response["status"],
        "links": links,
        "count": len(links),
        "strings_count": len(decoded),
        "raw_size": len(raw),
        "strings": decoded[:200]
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )