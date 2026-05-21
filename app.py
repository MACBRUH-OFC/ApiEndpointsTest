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

server_tokens = {key: None for key in UID_PASSWORDS.keys()}

BASE_LINK = "https://dl.dir.freefiremobile.com/common/"


@app.route("/")
def home():
    return render_template("ui.html")


def get_token(server):

    if server_tokens[server] is not None:
        return server_tokens[server]

    try:

        uid = UID_PASSWORDS[server]["uid"]
        password = UID_PASSWORDS[server]["password"]

        token_url = f"{TOKEN_BASE_URL}?uid={uid}&password={password}"

        response = requests.get(
            token_url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*"
            }
        )

        if response.status_code != 200:
            return None

        token_res = response.json()

        response_text = str(token_res.get("response", ""))

        match = re.search(
            r'token\s*:\s*"([^"]+)"',
            response_text,
            re.DOTALL
        )

        if not match:
            match = re.search(
                r'"token"\s*:\s*"([^"]+)"',
                response_text,
                re.DOTALL
            )

        if match:

            token = match.group(1).strip()

            server_tokens[server] = token

            return token

    except Exception as e:
        print(e)

    return None


def fix_common_errors(url):

    url = re.sub(
        r'/common/[a-z]{2,8}/common/',
        '/common/',
        url,
        flags=re.IGNORECASE
    )

    url = re.sub(
        r'/common/[A-Z0-9]+Local/',
        '/common/Local/',
        url,
        flags=re.IGNORECASE
    )

    url = re.sub(
        r'/common/[0-9]+OB([0-9]+)/',
        r'/common/OB\1/',
        url,
        flags=re.IGNORECASE
    )

    url = re.sub(
        r'/common/[A-Z]+OB([0-9]+)/',
        r'/common/OB\1/',
        url,
        flags=re.IGNORECASE
    )

    url = re.sub(
        r'/common/common/',
        '/common/',
        url,
        flags=re.IGNORECASE
    )

    return url


def clean_url(url):

    url = url.strip()

    url = re.sub(r'[\x00-\x1f]+', '', url)

    url = url.replace(".ff_extend", ".jpg")
    url = url.replace(".ktxp", ".png")

    url = fix_common_errors(url)

    url = re.sub(
        r'(\.(png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3))(?:[0-9]+)',
        r'\1',
        url,
        flags=re.IGNORECASE
    )

    ext_match = re.search(
        r'\.(png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3)',
        url,
        re.IGNORECASE
    )

    if ext_match:

        ext = ext_match.group(0)

        pos = url.lower().find(ext.lower())

        url = url[:pos + len(ext)]

    return url


def extract_urls(text):

    urls = set()

    text = text.replace(".ff_extend", ".jpg")
    text = text.replace(".ktxp", ".png")

    full_urls = re.findall(
        r'https?://[^\s"<>\']+',
        text,
        re.IGNORECASE
    )

    for url in full_urls:

        cleaned = clean_url(url)

        if cleaned.startswith("http"):
            urls.add(cleaned)

    partials = re.findall(
        r'([A-Za-z0-9_\-/]+\.(png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3))',
        text,
        re.IGNORECASE
    )

    for item in partials:

        path = item[0]

        if not path.startswith("http"):

            fixed = BASE_LINK + path.lstrip("/")

            fixed = clean_url(fixed)

            urls.add(fixed)

    return sorted(list(urls))


@app.route("/run_script")
def run_script():

    server = request.args.get("server")
    api_name = request.args.get("name")

    if server not in UID_PASSWORDS:
        return jsonify({"error": "Invalid server"})

    if not api_name:
        return jsonify({"error": "Missing API name"})

    token = get_token(server)

    if not token:
        return jsonify({"error": "Token fetch failed"})

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": "OB53",
        "User-Agent": "UnityPlayer/2022.3.47f1",
        "X-GA": "v1 1",
        "X-Unity-Version": "2022.3.47f1",
        "Authorization": f"Bearer {token}"
    }

    hex_payload = "8533b7e1d34a5dfd9a830ee5cc36664e"

    binary_payload = binascii.unhexlify(hex_payload)

    url = API_DOMAINS[server].rstrip("/") + "/" + api_name.lstrip("/")

    try:

        response = requests.post(
            url,
            headers=headers,
            data=binary_payload,
            timeout=25
        )

        if response.status_code == 401:

            server_tokens[server] = None

            token = get_token(server)

            if not token:
                return jsonify({"error": "Token refresh failed"})

            headers["Authorization"] = f"Bearer {token}"

            response = requests.post(
                url,
                headers=headers,
                data=binary_payload,
                timeout=25
            )

        response.raise_for_status()

        content = response.content

        try:

            if content[:2] == b'\x1f\x8b':
                content = gzip.decompress(content)

        except:
            pass

        decoded = content.decode("utf-8", errors="ignore")

        raw_strings = re.findall(rb"[ -~]{4,}", content)

        decoded_strings = [
            s.decode("utf-8", errors="ignore")
            for s in raw_strings
        ]

        urls = extract_urls(decoded)

        return jsonify({
            "success": True,
            "count": len(decoded_strings),
            "raw_count": len(urls),
            "strings": decoded_strings,
            "urls": urls,
            "raw_response": decoded
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)