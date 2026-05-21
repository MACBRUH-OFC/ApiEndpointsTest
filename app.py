from flask import Flask, jsonify, request, Response

import requests
import gzip
import re
import binascii

app = Flask(__name__)

BASE_CDN = (
    "https://dl.dir.freefiremobile.com/common/"
)

TOKEN_BASE_URL = (
    "https://jwt-gen-new.vercel.app/token"
)

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

    "ind":
    "https://client.ind.freefiremobile.com/",

    "mea":
    "https://clientbp.ggpolarbear.com/",

    "id":
    "https://clientbp.ggpolarbear.com/",

    "cis":
    "https://clientbp.ggpolarbear.com/",

    "br":
    "https://client.us.freefiremobile.com/",

    "latam":
    "https://client.us.freefiremobile.com/",

    "vn":
    "https://clientbp.ggpolarbear.com/",

    "tw":
    "https://clientbp.ggpolarbear.com/",

    "th":
    "https://clientbp.ggpolarbear.com/",

    "sg":
    "https://clientbp.ggpolarbear.com/",

    "eu":
    "https://clientbp.ggpolarbear.com/",

    "na":
    "https://client.us.freefiremobile.com/",

    "pk":
    "https://clientbp.ggpolarbear.com/",

    "bd":
    "https://clientbp.ggpolarbear.com/"
}

server_tokens = {
    key: None
    for key in UID_PASSWORDS
}


def get_token(server):

    if server_tokens[server]:
        return server_tokens[server]

    try:

        creds = UID_PASSWORDS[server]

        url = (
            f"{TOKEN_BASE_URL}"
            f"?uid={creds['uid']}"
            f"&password={creds['password']}"
        )

        response = requests.get(
            url,
            timeout=15
        )

        if response.status_code != 200:
            return None

        data = response.json()

        response_text = data.get(
            "response",
            ""
        )

        match = re.search(
            r'token\s*:\s*"([^"]+)"',
            response_text
        )

        if not match:
            return None

        token = match.group(1)

        server_tokens[server] = token

        return token

    except Exception as e:

        print(e)

        return None


def normalize_link(link):

    link = link.strip()

    if link.startswith("!") \
    or link.startswith("%") \
    or link.startswith("*") \
    or link.startswith("-") \
    or link.startswith(")") \
    or link.startswith("(") \
    or link.startswith('"') \
    or link.startswith("'") \
    or link.startswith(",") \
    or link.startswith(".") \
    or link.startswith(":"):

        link = link[1:]

    if link.startswith("/http"):
        link = link[1:]

    if re.match(r"OB\d+\/", link, re.IGNORECASE):

        link = BASE_CDN + link

    return link


def extract_links(strings):

    found_links = []

    patterns = [

        r'OB\d+\/[^\s"\']+\.(?:png|jpg|jpeg|webp)',

        r'https?:\/\/[^\s"\']+',

        r'\/http[^\s"\']+'
    ]

    for string in strings:

        for pattern in patterns:

            matches = re.findall(
                pattern,
                string,
                re.IGNORECASE
            )

            for match in matches:

                link = normalize_link(match)

                if link not in found_links:
                    found_links.append(link)

    return found_links


@app.route("/")
def home():

    with open(
        "ui.html",
        "r",
        encoding="utf-8"
    ) as f:

        return Response(
            f.read(),
            mimetype="text/html"
        )


@app.route("/run")
def run():

    server = request.args.get("server")
    endpoint = request.args.get("endpoint")

    version = request.args.get(
        "version",
        "OB53"
    )

    if (
        server not in UID_PASSWORDS
        or not endpoint
    ):

        return jsonify({
            "error":
            "Invalid parameters"
        })

    token = get_token(server)

    if not token:

        return jsonify({
            "error":
            "Failed to fetch token"
        })

    url = (
        API_DOMAINS[server].rstrip("/")
        + "/"
        + endpoint.lstrip("/")
    )

    headers = {

        "Accept":
        "*/*",

        "Accept-Encoding":
        "gzip, deflate",

        "Content-Type":
        "application/octet-stream",

        "ReleaseVersion":
        version,

        "Authorization":
        f"Bearer {token}",

        "X-GA":
        "v1 1",

        "X-Unity-Version":
        "2022.3.47f1",

        "User-Agent":
        (
            "UnityPlayer/2022.3.47f1 "
            "(UnityWebRequest/1.0, libcurl/7.80.0-DEV)"
        )
    }

    payload = binascii.unhexlify(
        "8533b7e1d34a5dfd9a830ee5cc36664e"
    )

    try:

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=20
        )

        if response.status_code == 401:

            server_tokens[server] = None

            return jsonify({
                "error":
                "Token expired. Retry request."
            })

        response.raise_for_status()

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

        strings = re.findall(
            r"[ -~]{4,}",
            decoded
        )

        links = extract_links(strings)

        image_links = []

        other_links = []

        for link in links:

            if any(
                link.lower().endswith(ext)
                for ext in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp"
                ]
            ):

                image_links.append(link)

            else:

                other_links.append(link)

        return jsonify({

            "success": True,

            "server": server,

            "endpoint": endpoint,

            "version": version,

            "total_strings": len(strings),

            "total_links": len(links),

            "image_links": image_links,

            "other_links": other_links,

            "raw_strings": strings[:1000]

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