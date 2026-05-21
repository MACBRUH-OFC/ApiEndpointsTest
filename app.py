from flask import Flask, jsonify, request, render_template
import requests
import gzip
import binascii
import re
import time

app = Flask(__name__)

TOKEN_BASE_URL = "https://jwt-gen-new.vercel.app/token"

BASE_CDN = "https://dl.dir.freefiremobile.com/common/"
BASE_TATA = "https://dl-tata.freefireind.in/common/"

UID_PASSWORDS = {
    "ind": {
        "uid": "4258906717",
        "password": "RockingGamerz65-1WDTR63DX"
    },
    "mea": {
        "uid": "4103849657",
        "password": "EF315D040E99F9B63D79C7AEE6DC697F297D298EF384BAA4E50E003DB56514C4"
    },
    "id": {
        "uid": "4109659017",
        "password": "7CE44389FE7D03FF892E682D00C5BE586B12789019CCCB466080CED41806DBAB"
    },
    "cis": {
        "uid": "3301239795",
        "password": "DD40EE772FCBD61409BB15033E3DE1B1C54EDA83B75DF0CDD24C34C7C8798475"
    },
    "br": {
        "uid": "4113330289",
        "password": "FA684A835410A8AFFE785552154AD87A4CB928C03D8870DEE37AB7C019B2D162"
    },
    "latam": {
        "uid": "4113343938",
        "password": "F7F739FCFB96A09B019D87C6B45174B76FAE406A4CD7A785F187E46C7F7A71FF"
    },
    "vn": {
        "uid": "4113363250",
        "password": "47269BFC4695E93FFABA1AA426847669D12AF36F6B7FCA52BF660459EE2B4092"
    },
    "tw": {
        "uid": "4113375272",
        "password": "6AB01F7FB110A4C9EB95DBA21BD0E63E622DF8E566157811910F81E54394A17D"
    },
    "th": {
        "uid": "4113415247",
        "password": "2542DD73DD60B33E183C6A894F9F6A2FC7DAEC457B826C71D44BFD4470788BBB"
    },
    "sg": {
        "uid": "4139211052",
        "password": "3BA22FEF36B7118B9FB1E1EB3E5A6DD84BDE696BD66B494269496E9834F00F3B"
    },
    "eu": {
        "uid": "4139177376",
        "password": "E29B0A5C48E8B426BE3E9D977927606842310E2F14EB108F2B5D7F73D9C4B105"
    },
    "na": {
        "uid": "4139196327",
        "password": "FA680B796474B22907BFD3DF2AFA29577FA43C5B2068417AA24453F25212B854"
    },
    "pk": {
        "uid": "4139224003",
        "password": "1812098F2587DCAEF5CC21EAD93FAA751D212CD81C586CFD4B4F48C1B49D2A88"
    },
    "bd": {
        "uid": "4139230703",
        "password": "6C2D5409593C61CFD31CDA18146054D05E72F261F24343CDEA75AEF38ADF5C95"
    }
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

server_tokens = {
    key: None for key in UID_PASSWORDS
}

VALID_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".ktx",
    ".gif",
    ".webp",
    ".mp4",
    ".ff_extend",
    ".html",
    ".json"
]

TRASH_ENDINGS = [
    "0",
    "X",
    "@",
    ":",
    ";",
    "`",
    '"',
    "'",
    "!",
    "#",
    "%",
    "^",
    "&",
    "*",
    "(",
    ")",
    ","
]


def clean_link(link):

    link = link.strip()

    while len(link) > 0 and link[-1] in TRASH_ENDINGS:
        link = link[:-1]

    link = link.replace(" ", "")

    return link


def fix_link(raw):

    raw = raw.strip()

    raw = raw.replace("\\", "/")

    if raw.startswith("OB"):

        raw = clean_link(raw)

        return BASE_CDN + raw

    if raw.startswith("/OB"):

        raw = clean_link(raw[1:])

        return BASE_CDN + raw

    if raw.startswith(")OB") or raw.startswith("*OB") or raw.startswith("-OB"):

        raw = clean_link(raw[1:])

        return BASE_CDN + raw

    if raw.startswith("http://") or raw.startswith("https://"):

        return clean_link(raw)

    return None


def is_valid_link(link):

    for ext in VALID_EXTENSIONS:
        if ext in link.lower():
            return True

    if "http" in link:
        return True

    return False


def get_token(server):

    if server_tokens[server]:

        return server_tokens[server]

    try:

        uid = UID_PASSWORDS[server]["uid"]

        password = UID_PASSWORDS[server]["password"]

        url = f"{TOKEN_BASE_URL}?uid={uid}&password={password}"

        response = requests.get(url, timeout=15)

        data = response.json()

        response_text = data.get("response", "")

        match = re.search(
            r'token\s*:\s*"([^"]+)"',
            response_text
        )

        if match:

            token = match.group(1)

            server_tokens[server] = token

            return token

    except Exception as e:

        print(e)

    return None


@app.route("/")
def index():

    return render_template("ui.html")


@app.route("/run")
def run():

    server = request.args.get("server")

    endpoint = request.args.get("endpoint")

    version = request.args.get("version", "OB53")

    if not endpoint:

        return jsonify({
            "error": "Missing endpoint"
        })

    token = get_token(server)

    if not token:

        return jsonify({
            "error": "Token Failed"
        })

    url = API_DOMAINS[server].rstrip("/") + "/" + endpoint.lstrip("/")

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": version,
        "X-Unity-Version": "2022.3.47f1",
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "User-Agent": "UnityPlayer/2022.3.47f1"
    }

    payload = binascii.unhexlify(
        "8533b7e1d34a5dfd9a830ee5cc36664e"
    )

    start = time.time()

    try:

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=30
        )

        duration = round(
            (time.time() - start) * 1000
        )

        content = response.content

        if content[:2] == b'\x1f\x8b':

            content = gzip.decompress(content)

        strings = re.findall(
            rb"[ -~]{4,}",
            content
        )

        decoded = []

        for s in strings:

            try:

                decoded.append(
                    s.decode(
                        "utf-8",
                        errors="ignore"
                    )
                )

            except:
                pass

        links = []

        for item in decoded:

            found = re.findall(
                r'(?:https?:\/\/[^\s]+|[)\-*\/]?OB\d+\/[^\s]+)',
                item
            )

            for f in found:

                fixed = fix_link(f)

                if fixed and is_valid_link(fixed):

                    links.append(fixed)

        links = list(dict.fromkeys(links))

        image_links = []

        other_links = []

        for link in links:

            if any(
                ext in link.lower()
                for ext in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".ktx",
                    ".gif",
                    ".webp"
                ]
            ):

                image_links.append(link)

            else:

                other_links.append(link)

        return jsonify({

            "success": True,

            "status_code": response.status_code,

            "response_time": duration,

            "image_links": image_links,

            "other_links": other_links,

            "raw_strings": decoded

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )