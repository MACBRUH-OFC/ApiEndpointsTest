from flask import Flask, jsonify, request, render_template
import requests
import gzip
import binascii
import re
import json

app = Flask(__name__)

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
    "sg": {"uid": "3615082916", "password": "60ACA52124148070458C031C2A003B3E1123B93D7B3B117FB7E775225439B2BC"},
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
VERSION_CACHE = {"version": None}

BASE_LINK = "https://dl.dir.freefiremobile.com/common/"

VALID_EXTENSIONS = [
    "png", "jpg", "jpeg", "webp", "gif",
    "bmp", "ktx", "html", "json",
    "mp4", "mp3", "wav", "ogg", "webm"
]


@app.route("/")
def home():
    return render_template("ui.html")


def get_release_version():
    if VERSION_CACHE["version"]:
        return VERSION_CACHE["version"]
    try:
        r = requests.get("https://ff-version.vercel.app/update", timeout=10)
        if r.status_code == 200:
            version = r.json().get("latest_release_version")
            if version:
                VERSION_CACHE["version"] = version
                return version
    except Exception as e:
        print("Failed to fetch game version dynamically:", e)
    return "OB53"  # Standard dynamic fallback


def get_token(server):
    if server_tokens[server]:
        return server_tokens[server]

    try:
        uid = UID_PASSWORDS[server]["uid"]
        password = UID_PASSWORDS[server]["password"]
        version = get_release_version()

        token_url = f"https://macxjwt.vercel.app/get_jwt_token?uid={uid}&password={password}&version={version}"

        response = requests.get(
            token_url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*"
            }
        )

        if response.status_code == 200:
            token_res = response.json()
            token = token_res.get("token")
            if token:
                server_tokens[server] = token
                return token

    except Exception as e:
        print("Token extraction failed:", e)

    return None


@app.route("/run_script")
def run_script():
    server = request.args.get("server")
    api_name = request.args.get("name")
    payload_hex = request.args.get("payload", "8533b7e1d34a5dfd9a830ee5cc36664e")

    if server not in UID_PASSWORDS:
        return jsonify({"error": "Invalid server"})

    if not api_name:
        return jsonify({"error": "Missing API name"})

    token = get_token(server)

    if not token:
        return jsonify({"error": "Token fetch failed"})

    release_version = get_release_version()

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": release_version,
        "User-Agent": "UnityPlayer/2022.3.47f1",
        "X-GA": "v1 1",
        "X-Unity-Version": "2022.3.47f1",
        "Authorization": f"Bearer {token}"
    }

    try:
        binary_payload = binascii.unhexlify(payload_hex)
    except Exception as e:
        return jsonify({"error": f"Invalid payload hex formatting: {str(e)}"})

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

        # Decode response utilising the external Protobuf decoding endpoint
        protobuf_data = {}
        try:
            dec_res = requests.post(
                "https://protobuf-decoder-seven.vercel.app/decode",
                json={"data": content.hex()},
                timeout=15
            )
            if dec_res.status_code == 200:
                protobuf_data = dec_res.json().get("protobuf", {})
                if isinstance(protobuf_data, str):
                    try:
                        protobuf_data = json.loads(protobuf_data)
                    except:
                        protobuf_data = {}
        except Exception as e:
            print("Protobuf decoder lookup failed:", e)

        extracted_strings = set()

        def extract_strings_from_protobuf(data):
            if isinstance(data, dict):
                for val in data.values():
                    extract_strings_from_protobuf(val)
            elif isinstance(data, list):
                for item in data:
                    extract_strings_from_protobuf(item)
            elif isinstance(data, str):
                extracted_strings.add(data)

        extract_strings_from_protobuf(protobuf_data)

        # Standardise and filter decoded string links
        urls = set()
        for val in extracted_strings:
            val = val.strip()
            if not val:
                continue

            val_lower = val.lower()

            # 1. Matches complete absolute URLs
            if val_lower.startswith(("http://", "https://")):
                urls.add(val)
                continue

            # 2. Prepend base CDN strictly if it starts with "test" or "common"
            if val_lower.startswith("test") or val_lower.startswith("common"):
                val_clean = val.lstrip("/")
                if val_clean.lower().startswith("common/"):
                    url_item = "https://dl.dir.freefiremobile.com/" + val_clean
                else:
                    url_item = BASE_LINK + val_clean
                urls.add(url_item)
                continue

            # 3. Match relative assets containing typical extensions without conversions
            if any(f".{ext}" in val_lower for ext in VALID_EXTENSIONS) or val_lower.endswith((".ff_extend", ".ktxp")):
                urls.add(val)
                continue

            # 4. Social media domains
            social_domains = ["instagram.com", "discord.gg", "youtube.com", "youtu.be", "facebook.com", "twitter.com", "x.com", "whatsapp.com", "linktr.ee"]
            if any(domain in val_lower for domain in social_domains):
                if not val_lower.startswith(("http://", "https://")):
                    val = "https://" + val
                urls.add(val)
                continue

        urls_list = sorted(list(urls))

        return jsonify({
            "success": True,
            "count": len(extracted_strings),
            "raw_count": len(urls_list),
            "strings": sorted(list(extracted_strings)),
            "urls": urls_list,
            "raw_response": decoded
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)