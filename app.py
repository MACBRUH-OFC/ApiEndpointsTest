from flask import Flask, jsonify, request, render_template, Response
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

VERSION_API = "https://ff-version.vercel.app/update"
DECODER_API = "https://protobuf-decoder-seven.vercel.app/decode"
JWT_API = "https://macxjwt.vercel.app/get_jwt_token"

# Regional credentials and client routing
REGIONS = {
    "ind": {
        "client": "https://client.ind.freefiremobile.com",
        "uid": "4258906717",
        "password": "RockingGamerz65-1WDTR63DX"
    },
    "br": {
        "client": "https://client.us.freefiremobile.com",
        "uid": "4113330289",
        "password": "FA684A835410A8AFFE785552154AD87A4CB928C03D8870DEE37AB7C019B2D162"
    },
    "na": {
        "client": "https://client.us.freefiremobile.com",
        "uid": "4139196327",
        "password": "FA680B796474B22907BFD3DF2AFA29577FA43C5B2068417AA24453F25212B854"
    },
    "sac": {
        "client": "https://client.us.freefiremobile.com",
        "uid": "4113343938",
        "password": "F7F739FCFB96A09B019D87C6B45174B76FAE406A4CD7A785F187E46C7F7A71FF"
    },
    "mea": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4103849657",
        "password": "EF315D040E99F9B63D79C7AEE6DC697F297D298EF384BAA4E50E003DB56514C4"
    },
    "vn": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "3688702515",
        "password": "18E3450FC131F6414A775896EDA8075A37818FEFEE7A795ED4BC7764346A5EEF"
    },
    "bd": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4139230703",
        "password": "6C2D5409593C61CFD31CDA18146054D05E72F261F24343CDEA75AEF38ADF5C95"
    },
    "pk": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4139224003",
        "password": "1812098F2587DCAEF5CC21EAD93FAA751D212CD81C586CFD4B4F48C1B49D2A88"
    },
    "sg": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4139211052",
        "password": "3BA22FEF36B7118B9FB1E1EB3E5A6DD84BDE696BD66B494269496E9834F00F3B"
    },
    "id": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4109659017",
        "password": "7CE44389FE7D03FF892E682D00C5BE586B12789019CCCB466080CED41806DBAB"
    },
    "cis": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "3301239795",
        "password": "DD40EE772FCBD61409BB15033E3DE1B1C54EDA83B75DF0CDD24C34C7C8798475"
    },
    "th": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4113415247",
        "password": "2542DD73DD60B33E183C6A894F9F6A2FC7DAEC457B826C71D44BFD4470788BBB"
    },
    "tw": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4113375272",
        "password": "6AB01F7FB110A4C9EB95DBA21BD0E63E622DF8E566157811910F81E54394A17D"
    },
    "eu": {
        "client": "https://clientbp.ggpolarbear.com",
        "uid": "4139177376",
        "password": "E29B0A5C48E8B426BE3E9D977927606842310E2F14EB108F2B5D7F73D9C4B105"
    }
}

# Payload dictionary mapping matching endpoint configurations
ENDPOINT_HEX_PAYLOADS = {
    "LoginGetDesc": "19d87e64f15e9db87392bc99506f0b94",
    "LoginGetAccountInfo": "701ab6a8dcd2e32bde5efd87d0da7545",
    "GetMailList": "59f0b3e90a6ff6ffed2f612996c74b04",
    "GetLimitedEventOpenInfo": "1a725b2c56ec52ba7d09623454c0a003",
    "GetCustomEventOpenInfo": "9aeaea80bb2ba264078712b7c32a4116",
    "GetBPAllDescs": "1a725b2c56ec52ba7d09623454c0a003",
    "GetCollabDesc": "1a725b2c56ec52ba7d09623454c0a003"
}

# Global Token Cache
server_tokens = {key: None for key in REGIONS.keys()}

# Expiring dynamic release version cache
VERSION_CACHE = {
    "version": None,
    "last_fetched": 0
}

VALID_EXTENSIONS = [
    "png", "jpg", "jpeg", "webp", "gif",
    "bmp", "ktx", "html", "json",
    "mp4", "mp3", "wav", "ogg", "webm"
]

# Set up an HTTP session with connection pooling and robust retry strategies
http_session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=100,
    pool_maxsize=100
)
http_session.mount("http://", adapter)
http_session.mount("https://", adapter)

BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "X-GA": "v1 1",
    "X-Unity-Version": "2022.3.47f1"
}


@app.route("/")
def home():
    return render_template("ui.html")


def decompress_data(data):
    try:
        return gzip.decompress(data)
    except:
        pass
    try:
        return zlib.decompress(data)
    except:
        pass
    try:
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except:
        pass
    return data


def get_release_version():
    current_time = time.time()
    # Cache version configuration dynamically for up to 1 hour
    if VERSION_CACHE["version"] and (current_time - VERSION_CACHE["last_fetched"] < 3600):
        return VERSION_CACHE["version"]
    try:
        response = http_session.get(VERSION_API, timeout=15)
        response.raise_for_status()
        version = response.json().get("latest_release_version")
        if version:
            VERSION_CACHE["version"] = version
            VERSION_CACHE["last_fetched"] = current_time
            return version
    except Exception as e:
        print("Failed to fetch game version dynamically:", e)
        
    if VERSION_CACHE["version"]:
        return VERSION_CACHE["version"]
    return "OB53"


# Pre-fetch dynamic version on startup loading
try:
    initial_version = get_release_version()
    print(f"[*] Pre-fetched dynamic game version loaded: {initial_version}")
except Exception as startup_err:
    print(f"[!] Initial version fetch failed, will fetch on demand: {startup_err}")


def get_payload_for_endpoint(endpoint_name):
    if not endpoint_name:
        return "8533b7e1d34a5dfd9a830ee5cc36664e"
    clean_name = endpoint_name.strip()
    for endpoint, hex_val in ENDPOINT_HEX_PAYLOADS.items():
        if endpoint.lower() == clean_name.lower():
            return hex_val.replace(" ", "").lower()
    return "8533b7e1d34a5dfd9a830ee5cc36664e"


def decode_protobuf(raw_hex):
    try:
        decoder_response = http_session.post(
            DECODER_API,
            json={"data": raw_hex},
            timeout=30
        )
        decoder_response.raise_for_status()
        decoder_json = decoder_response.json()
        protobuf = decoder_json.get("protobuf", {})
        if isinstance(protobuf, str):
            try:
                protobuf = json.loads(protobuf)
            except:
                protobuf = {}
        if not isinstance(protobuf, dict):
            protobuf = {}
        return protobuf
    except Exception as e:
        print("Protobuf decoder lookup failed:", e)
        return {}


def get_token(region_data, release_version):
    for _ in range(3):
        try:
            jwt_response = http_session.get(
                f"{JWT_API}?uid={region_data['uid']}&password={region_data['password']}&version={release_version}",
                timeout=20
            )
            jwt_response.raise_for_status()
            jwt_json = jwt_response.json()
            token = jwt_json.get("token")
            if token:
                return token
        except:
            pass
    return None


@app.route("/run_script")
def run_script():
    try:
        server = request.args.get("server")
        api_name = request.args.get("name")

        if not server or server not in REGIONS:
            return jsonify({"error": "Invalid region server selection"})

        if not api_name:
            return jsonify({"error": "Missing API name parameter"})

        # Route extraction for relative vs absolute queries
        if "://" in api_name:
            api_path = urlparse(api_name).path.lstrip("/")
        else:
            api_path = api_name.lstrip("/")

        clean_api_name = api_path.split("/")[-1]
        payload_hex = get_payload_for_endpoint(clean_api_name)

        release_version = get_release_version()
        region_data = REGIONS[server]

        # Token handling logic
        token = server_tokens[server]
        if not token:
            token = get_token(region_data, release_version)
            if not token:
                return jsonify({"error": f"Failed to acquire authorization token for {server.upper()}"})
            server_tokens[server] = token

        headers = BASE_HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"
        headers["ReleaseVersion"] = release_version

        binary_payload = binascii.unhexlify(payload_hex)
        url = region_data["client"].rstrip("/") + "/" + api_path

        try:
            response = http_session.post(
                url,
                headers=headers,
                data=binary_payload,
                timeout=25
            )
        except requests.exceptions.Timeout:
            return jsonify({"error": f"Timeout connecting to Garena regional server: {server.upper()}"})
        except requests.exceptions.ConnectionError as ce:
            return jsonify({"error": f"Connection error communicating with {server.upper()}: {str(ce)}"})

        # Handle token expiration (401 status)
        if response.status_code == 401:
            token = get_token(region_data, release_version)
            if not token:
                return jsonify({"error": f"Token verification refresh failure on {server.upper()}"})
            server_tokens[server] = token
            headers["Authorization"] = f"Bearer {token}"

            try:
                response = http_session.post(
                    url,
                    headers=headers,
                    data=binary_payload,
                    timeout=25
                )
            except requests.exceptions.Timeout:
                return jsonify({"error": "Timeout on token verification retry request."})
            except requests.exceptions.ConnectionError as ce:
                return jsonify({"error": f"Connection retry error: {str(ce)}"})

        response.raise_for_status()
        
        # Exact decompression procedure
        raw_data = decompress_data(response.content)
        if not raw_data:
            return jsonify({"error": "Received empty decompressed data from Garena server"})

        raw_hex = raw_data.hex()
        decoded_raw_text = raw_data.decode("utf-8", errors="ignore")

        # Decode via Protobuf API as specified
        protobuf_data = decode_protobuf(raw_hex)

        extracted_strings = set()

        # Step 1: Recursive extraction from JSON-based structures
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

        # Step 2: Fallback Unix-style strings extraction on raw decompressed bytes
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

        for ascii_str in extract_ascii_strings(raw_data):
            cleaned = ascii_str.strip()
            if len(cleaned) >= 4 and not cleaned.startswith(("%%", "##", "$$")):
                extracted_strings.add(cleaned)

        # Step 3: Fallback Regex scanning for nested URL/asset structures
        found_paths = re.findall(
            r'(https?://[^\s"\'()<>]+|[\w\-_]+/[\w\-_/]+\.(?:png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp)[\w\-_/]*)',
            decoded_raw_text,
            re.IGNORECASE
        )
        for path in found_paths:
            extracted_strings.add(path)

        # Finalize and isolate legitimate URLs
        urls = set()
        for val in extracted_strings:
            val = val.strip()
            if not val:
                continue
            val_lower = val.lower()

            if val_lower.startswith(("http://", "https://")):
                urls.add(val)
                continue

            if any(f".{ext}" in val_lower for ext in VALID_EXTENSIONS) or val_lower.endswith((".ff_extend", ".ktxp")) or ("local/" in val_lower) or ("test/" in val_lower):
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
            "raw_response": decoded_raw_text
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)