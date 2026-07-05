from flask import Flask, jsonify, request, render_template
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import gzip
import zlib
import binascii
import json
import time
import re
from urllib.parse import urlparse

app = Flask(__name__)

# Regional credentials
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

# Regional domains
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

# Explicit mapped endpoint hex payloads
ENDPOINT_HEX_PAYLOADS = {
    "LoginGetDesc": "19d87e64f15e9db87392bc99506f0b94",
    "LoginGetAccountInfo": "701ab6a8dcd2e32bde5efd87d0da7545",
    "GetMailList": "59f0b3e90a6ff6ffed2f612996c74b04",
    "GetLimitedEventOpenInfo": "1a725b2c56ec52ba7d09623454c0a003",
    "GetCustomEventOpenInfo": "9aeaea80bb2ba264078712b7c32a4116",
    "GetBPAllDescs": "1a725b2c56ec52ba7d09623454c0a003",
    "GetCollabDesc": "1a725b2c56ec52ba7d09623454c0a003"
}

server_tokens = {key: None for key in UID_PASSWORDS.keys()}

VERSION_CACHE = {
    "version": None
}

VALID_EXTENSIONS = [
    "png", "jpg", "jpeg", "webp", "gif",
    "bmp", "ktx", "html", "json",
    "mp4", "mp3", "wav", "ogg", "webm"
]

# Set up optimized HTTP session with retry logic
http_session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
http_session.mount("https://", adapter)
http_session.mount("http://", adapter)


@app.route("/")
def home():
    return render_template("ui.html")


def decompress_data(data):
    try:
        return gzip.decompress(data)
    except Exception:
        pass
    try:
        return zlib.decompress(data)
    except Exception:
        pass
    try:
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except Exception:
        pass
    return data


def get_release_version():
    if VERSION_CACHE["version"]:
        return VERSION_CACHE["version"]
    try:
        response = http_session.get("https://ff-version.vercel.app/update", timeout=15)
        response.raise_for_status()
        version = response.json().get("latest_release_version")
        if version:
            VERSION_CACHE["version"] = version
            return version
    except Exception as e:
        print("Failed to fetch game version dynamically:", e)
    return "OB53"  # Standard dynamic fallback


@app.route("/get_version")
def get_version_route():
    try:
        version = get_release_version()
        return jsonify({"version": version})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_payload_for_endpoint(endpoint_name):
    if not endpoint_name:
        return "8533b7e1d34a5dfd9a830ee5cc36664e"
    clean_name = endpoint_name.strip()
    for endpoint, hex_val in ENDPOINT_HEX_PAYLOADS.items():
        if endpoint.lower() == clean_name.lower():
            return hex_val.replace(" ", "").lower()
    return "8533b7e1d34a5dfd9a830ee5cc36664e"


def get_token(server, release_version):
    if server_tokens[server]:
        return server_tokens[server]
    try:
        uid = UID_PASSWORDS[server]["uid"]
        password = UID_PASSWORDS[server]["password"]
        token_url = f"https://macxjwt.vercel.app/get_jwt_token?uid={uid}&password={password}&version={release_version}"
        response = http_session.get(
            token_url,
            timeout=20,
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
    try:
        server = request.args.get("server")
        api_name = request.args.get("name")
        version_param = request.args.get("version")  # Extracted from webpage parameter

        if server not in UID_PASSWORDS:
            return jsonify({"error": "Invalid server selection"})

        if not api_name:
            return jsonify({"error": "Missing target API name parameter"})

        if "://" in api_name:
            api_path = urlparse(api_name).path.lstrip("/")
        else:
            api_path = api_name.lstrip("/")

        clean_api_name = api_path.split("/")[-1]
        payload_hex = get_payload_for_endpoint(clean_api_name)

        # Uses version parameter passed from frontend, otherwise queries dynamically
        release_version = version_param if version_param else get_release_version()
        token = get_token(server, release_version)

        if not token:
            return jsonify({"error": f"Failed to acquire security token for {server.upper()}"})

        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "ReleaseVersion": release_version,
            "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "X-GA": "v1 1",
            "X-Unity-Version": "2022.3.47f1",
            "Authorization": f"Bearer {token}"
        }

        binary_payload = binascii.unhexlify(payload_hex)
        url = API_DOMAINS[server].rstrip("/") + "/" + api_path

        try:
            response = http_session.post(
                url,
                headers=headers,
                data=binary_payload,
                timeout=30
            )
        except requests.exceptions.Timeout:
            return jsonify({"error": f"Timeout connecting to regional server: {server.upper()}"})
        except requests.exceptions.ConnectionError as ce:
            return jsonify({"error": f"Connection error communicating with {server.upper()}: {str(ce)}"})

        if response.status_code == 401:
            server_tokens[server] = None
            token = get_token(server, release_version)
            if not token:
                return jsonify({"error": f"Token refresh failure on region {server.upper()}"})
            headers["Authorization"] = f"Bearer {token}"

            try:
                response = http_session.post(
                    url,
                    headers=headers,
                    data=binary_payload,
                    timeout=30
                )
            except requests.exceptions.Timeout:
                return jsonify({"error": "Timeout on token verification retry request."})
            except requests.exceptions.ConnectionError as ce:
                return jsonify({"error": f"Connection retry error: {str(ce)}"})

        response.raise_for_status()
        content = decompress_data(response.content)
        decoded = content.decode("utf-8", errors="ignore")

        # Decode using the Protobuf decoder API
        protobuf_data = {}
        try:
            dec_res = http_session.post(
                "https://protobuf-decoder-seven.vercel.app/decode",
                json={"data": content.hex()},
                timeout=30
            )
            if dec_res.status_code == 200:
                protobuf_data = dec_res.json().get("protobuf", {})
                if isinstance(protobuf_data, str):
                    try:
                        protobuf_data = json.loads(protobuf_data)
                    except Exception:
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

        # local json fallback parsing
        try:
            raw_json = json.loads(decoded)
            def extract_from_json(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(k, str):
                            extracted_strings.add(k)
                        extract_from_json(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_from_json(item)
                elif isinstance(obj, str):
                    extracted_strings.add(obj)
            extract_from_json(raw_json)
        except Exception:
            pass

        # String extraction fallback from binary stream
        def extract_ascii_strings(binary_data, min_len=4):
            result = []
            current = []
            for byte in binary_data:
                if 32 <= byte <= 126:
                    current.append(chr(byte))
                else:
                    if len(current) >= min_len:
                        result.append("".join(current))
                    current = []
            if len(current) >= min_len:
                result.append("".join(current))
            return result

        for s in extract_ascii_strings(content):
            cleaned = s.strip()
            if len(cleaned) >= 4 and not cleaned.startswith(("%%", "##", "$$")):
                extracted_strings.add(cleaned)

        # Direct path searches using regexes
        found_paths = re.findall(
            r'(https?://[^\s"\'()<>]+|[\w\-_]+/[\w\-_/]+\.(?:png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp)[\w\-_/]*)',
            decoded,
            re.IGNORECASE
        )
        for path in found_paths:
            extracted_strings.add(path)

        urls = set()
        for val in extracted_strings:
            val = val.strip()
            if not val:
                continue
            val_lower = val.lower()

            if val_lower.startswith(("http://", "https://")):
                urls.add(val)
                continue
            if any(f".{ext}" in val_lower for ext in VALID_EXTENSIONS) or val_lower.endswith((".ff_extend", ".ktxp")) or ("local/" in val_lower):
                urls.add(val)
                continue
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
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)