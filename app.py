from flask import Flask, render_template, jsonify, request
import requests
import gzip
import binascii
import re
import json

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

CDN_DOMAINS = {
    "ind": "https://dl-tata.freefireind.in/common/",
    "default": "https://dl.dir.freefiremobile.com/common/"
}

server_tokens = {}


@app.route("/")
def home():
    return render_template("ui.html")


def extract_token(text):

    patterns = [
        r'"token"\s*:\s*"([^"]+)"',
        r'token\s*:\s*"([^"]+)"',
        r'"access_token"\s*:\s*"([^"]+)"',
        r'Bearer\s+([A-Za-z0-9\-\._]+)',
        r'(eyJ[A-Za-z0-9\-\._]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(1)

    return None


def get_token(server):

    if server in server_tokens:
        return server_tokens[server]

    try:

        uid = UID_PASSWORDS[server]["uid"]
        password = UID_PASSWORDS[server]["password"]

        response = requests.get(
            TOKEN_BASE_URL,
            params={
                "uid": uid,
                "password": password
            },
            timeout=20
        )

        raw = response.text

        try:
            data = response.json()

            if isinstance(data, dict):

                raw = json.dumps(data)

                if "token" in data:
                    token = data["token"]
                    server_tokens[server] = token
                    return token

        except:
            pass

        token = extract_token(raw)

        if token:
            server_tokens[server] = token
            return token

        return None

    except:
        return None


def clean_link(link):

    link = link.strip()

    link = re.sub(r'^[^a-zA-Z0-9:/]+', '', link)

    while len(link) > 0 and link[-1] in [
        "0", "X", "J", "B",
        "@", "#", "`", "*",
        ";", ":", '"', "'"
    ]:
        link = link[:-1]

    return link.strip()


def convert_ob_link(link, server):

    link = clean_link(link)

    if link.startswith("http://"):
        link = link.replace("http://", "https://")

    if link.startswith("https://"):
        return link

    if re.match(r'^OB\d+', link, re.IGNORECASE):

        base = CDN_DOMAINS.get(server)

        if not base:
            base = CDN_DOMAINS["default"]

        return base + link

    return None


def extract_links(text, server):

    results = []

    patterns = [

        r'https?://[^\s"\']+',

        r'OB\d+/[^\s"\']+\.(?:png|jpg|jpeg|webp|ktx|gif|json|html|ff_extend)',

        r'OB\d+/[^\s"\']+'
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for item in matches:

            fixed = convert_ob_link(item, server)

            if fixed:
                results.append(fixed)

    final = []

    for item in results:

        item = clean_link(item)

        if not item:
            continue

        if item not in final:
            final.append(item)

    return final


@app.route("/run_script")
def run_script():

    try:

        server = request.args.get("server", "ind")
        endpoint = request.args.get("name", "").strip()

        if not endpoint:
            return jsonify({
                "success": False,
                "error": "Endpoint missing"
            })

        token = get_token(server)

        if not token:
            return jsonify({
                "success": False,
                "error": "Token fetch failed"
            })

        url = API_DOMAINS[server].rstrip("/") + "/" + endpoint.lstrip("/")

        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/x-www-form-urlencoded",
            "ReleaseVersion": "OB53",
            "User-Agent": "UnityPlayer/2022.3.47f1",
            "X-Unity-Version": "2022.3.47f1",
            "Authorization": f"Bearer {token}"
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

        content = response.content

        try:
            if content[:2] == b'\x1f\x8b':
                content = gzip.decompress(content)
        except:
            pass

        decoded = content.decode(
            "utf-8",
            errors="ignore"
        )

        links = extract_links(decoded, server)

        return jsonify({
            "success": True,
            "endpoint": endpoint,
            "server": server,
            "count": len(links),
            "strings": links,
            "preview": decoded[:5000]
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(debug=True)