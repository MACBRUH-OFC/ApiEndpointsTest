from flask import Flask, jsonify, request, render_template, Response
import requests
import gzip
import zlib
import binascii
import json
import re
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Attempt to configure flask_cors cleanly without throwing deployment errors if missing
try:
    from flask_cors import CORS
    has_cors = True
except ImportError:
    has_cors = False

app = Flask(__name__)
if has_cors:
    CORS(app)

VERSION_API = "https://ff-version.vercel.app/update"
DECODER_API = "https://protobuf-decoder-seven.vercel.app/decode"
JWT_API = "https://macxjwt.vercel.app/get_jwt_token"

CLIENTS = {
    "client_ind": "https://client.ind.freefiremobile.com",
    "client_bp": "https://clientbp.ggpolarbear.com",
    "client_us": "https://client.us.freefiremobile.com"
}

REGIONS = {
    "ind": {
        "client": CLIENTS["client_ind"],
        "uid": "4258906717",
        "password": "RockingGamerz65-1WDTR63DX"
    },
    "br": {
        "client": CLIENTS["client_us"],
        "uid": "4113330289",
        "password": "FA684A835410A8AFFE785552154AD87A4CB928C03D8870DEE37AB7C019B2D162"
    },
    "na": {
        "client": CLIENTS["client_us"],
        "uid": "4139196327",
        "password": "FA680B796474B22907BFD3DF2AFA29577FA43C5B2068417AA24453F25212B854"
    },
    "sac": {
        "client": CLIENTS["client_us"],
        "uid": "4113343938",
        "password": "F7F739FCFB96A09B019D87C6B45174B76FAE406A4CD7A785F187E46C7F7A71FF"
    },
    "latam": {
        "client": CLIENTS["client_us"],
        "uid": "4113343938",
        "password": "F7F739FCFB96A09B019D87C6B45174B76FAE406A4CD7A785F187E46C7F7A71FF"
    },
    "mea": {
        "client": CLIENTS["client_bp"],
        "uid": "4103849657",
        "password": "EF315D040E99F9B63D79C7AEE6DC697F297D298EF384BAA4E50E003DB56514C4"
    },
    "vn": {
        "client": CLIENTS["client_bp"],
        "uid": "3688702515",
        "password": "18E3450FC131F6414A775896EDA8075A37818FEFEE7A795ED4BC7764346A5EEF"
    },
    "bd": {
        "client": CLIENTS["client_bp"],
        "uid": "4139230703",
        "password": "6C2D5409593C61CFD31CDA18146054D05E72F261F24343CDEA75AEF38ADF5C95"
    },
    "pk": {
        "client": CLIENTS["client_bp"],
        "uid": "4139224003",
        "password": "1812098F2587DCAEF5CC21EAD93FAA751D212CD81C586CFD4B4F48C1B49D2A88"
    },
    "sg": {
        "client": CLIENTS["client_bp"],
        "uid": "4139211052",
        "password": "3BA22FEF36B7118B9FB1E1EB3E5A6DD84BDE696BD66B494269496E9834F00F3B"
    },
    "id": {
        "client": CLIENTS["client_bp"],
        "uid": "4109659017",
        "password": "7CE44389FE7D03FF892E682D00C5BE586B12789019CCCB466080CED41806DBAB"
    },
    "cis": {
        "client": CLIENTS["client_bp"],
        "uid": "3301239795",
        "password": "DD40EE772FCBD61409BB15033E3DE1B1C54EDA83B75DF0CDD24C34C7C8798475"
    },
    "th": {
        "client": CLIENTS["client_bp"],
        "uid": "4113415247",
        "password": "2542DD73DD60B33E183C6A894F9F6A2FC7DAEC457B826C71D44BFD4470788BBB"
    },
    "tw": {
        "client": CLIENTS["client_bp"],
        "uid": "4113375272",
        "password": "6AB01F7FB110A4C9EB95DBA21BD0E63E622DF8E566157811910F81E54394A17D"
    },
    "eu": {
        "client": CLIENTS["client_bp"],
        "uid": "4139177376",
        "password": "E29B0A5C48E8B426BE3E9D977927606842310E2F14EB108F2B5D7F73D9C4B105"
    }
}

ENDPOINT_HEX_PAYLOADS = {
    "LoginGetDesc": "19d87e64f15e9db87392bc99506f0b94",
    "LoginGetAccountInfo": "701ab6a8dcd2e32bde5efd87d0da7545",
    "GetMailList": "59f0b3e90a6ff6ffed2f612996c74b04",
    "GetLimitedEventOpenInfo": "1a725b2c56ec52ba7d09623454c0a003",
    "GetCustomEventOpenInfo": "9aeaea80bb2ba264078712b7c32a4116",
    "GetBPAllDescs": "1a725b2c56ec52ba7d09623454c0a003",
    "GetCollabDesc": "1a725b2c56ec52ba7d09623454c0a003"
}

VERSION_CACHE = {
    "version": None
}

VALID_EXTENSIONS = [
    "png", "jpg", "jpeg", "webp", "gif",
    "bmp", "ktx", "html", "json",
    "mp4", "mp3", "wav", "ogg", "webm"
]

SESSION = requests.Session()

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

SESSION.mount("http://", adapter)
SESSION.mount("https://", adapter)

BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "X-GA": "v1 1",
    "X-Unity-Version": "2022.3.47f1"
}


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

    response = SESSION.get(VERSION_API, timeout=15)
    response.raise_for_status()
    version = response.json().get("latest_release_version")
    if not version:
        raise Exception("release_version_not_found")
    VERSION_CACHE["version"] = version
    return version


@app.route("/get_version")
def get_version_route():
    try:
        version = get_release_version()
        return jsonify({"version": version})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_token(region_data, release_version):
    for _ in range(3):
        try:
            jwt_response = SESSION.get(
                f"{JWT_API}?uid={region_data['uid']}&password={region_data['password']}&version={release_version}",
                timeout=20
            )
            jwt_response.raise_for_status()
            jwt_json = jwt_response.json()
            token = jwt_json.get("token")
            if token:
                return token
        except Exception:
            pass
    return None


def get_payload_for_endpoint(endpoint_name):
    if not endpoint_name:
        return "19d87e64f15e9db87392bc99506f0b94"
    clean_name = endpoint_name.strip()
    for endpoint, hex_val in ENDPOINT_HEX_PAYLOADS.items():
        if endpoint.lower() == clean_name.lower():
            return hex_val.replace(" ", "").lower()
    return "19d87e64f15e9db87392bc99506f0b94"


def normalize_garena_path(path):
    """
    Cleans trailing trailing Garena digits on extensions (e.g. .png0 -> .png)
    """
    cleaned = re.sub(
        r'\.(png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp)\d+$',
        r'.\1',
        path,
        flags=re.IGNORECASE
    )
    return cleaned.strip('"\'* \t\n\r')


def extract_clean_path_from_string(val):
    """
    Isolates folder assets from Garena payload prefix parameters (e.g. '105;-378;0*test/img.png0').
    """
    match = re.search(
        r'(https?://[^\s"\'()<>]+|[\w\-_]+/[\w\-_/]+\.(?:png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp)(?:\d+)?)',
        val,
        re.IGNORECASE
    )
    if match:
        return normalize_garena_path(match.group(1))
    return normalize_garena_path(val)


def decode_protobuf(raw_hex):
    decoder_response = SESSION.post(
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
        except Exception:
            protobuf = {}

    if not isinstance(protobuf, dict):
        protobuf = {}

    return protobuf


@app.route("/run_script")
def run_script():
    try:
        server = request.args.get("server", "ind").lower()
        api_name = request.args.get("name")
        version_param = request.args.get("version")

        if server not in REGIONS:
            return jsonify({"error": "Invalid regional server selection"})

        if not api_name:
            return jsonify({"error": "Missing target API endpoint name"})

        if "://" in api_name:
            api_path = urlparse(api_name).path.lstrip("/")
        else:
            api_path = api_name.lstrip("/")

        clean_api_name = api_path.split("/")[-1]
        payload_hex = get_payload_for_endpoint(clean_api_name)

        # Utilize version loaded dynamically by frontend, otherwise dynamic fetch
        release_version = version_param if version_param else get_release_version()
        
        region_data = REGIONS[server]
        token = get_token(region_data, release_version)

        if not token:
            return jsonify({"error": "Dynamic bearer token generation failed"})

        headers = BASE_HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"
        headers["ReleaseVersion"] = release_version

        # Ensure correct slash joining matching your reference code
        url = f"{region_data['client']}/{api_path}"

        try:
            response = SESSION.post(
                url,
                headers=headers,
                data=binascii.unhexlify(payload_hex),
                timeout=30
            )
        except requests.exceptions.Timeout:
            return jsonify({"error": f"Timeout connecting to Garena edge node on {server.upper()}"})
        except requests.exceptions.ConnectionError as ce:
            return jsonify({"error": f"Connection lost on cluster {server.upper()}: {str(ce)}"})

        # Retries on 401 token expiration
        if response.status_code == 401:
            token = get_token(region_data, release_version)
            if not token:
                return jsonify({"error": "Bearer token refresh failed"})
            headers["Authorization"] = f"Bearer {token}"
            response = SESSION.post(
                url,
                headers=headers,
                data=binascii.unhexlify(payload_hex),
                timeout=30
            )

        response.raise_for_status()
        raw = decompress_data(response.content)

        if not raw:
            return jsonify({"error": "The regional pipeline returned an empty response stream."})

        raw_hex = raw.hex()
        decoded = raw.decode("utf-8", errors="ignore")

        # Unpack protobuf structures
        protobuf_data = decode_protobuf(raw_hex)

        extracted_strings = set()

        def extract_strings_recursively(obj):
            if isinstance(obj, dict):
                for val in obj.values():
                    extract_strings_recursively(val)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings_recursively(item)
            elif isinstance(obj, str):
                extracted_strings.add(obj)
                # Unpack potential nested serialized json inside protobuf fields
                if obj.strip().startswith(("{", "[")):
                    try:
                        nested_json = json.loads(obj)
                        extract_strings_recursively(nested_json)
                    except Exception:
                        pass

        # 1. Recursive extraction from protobuf dictionary
        extract_strings_recursively(protobuf_data)

        # 2. Local decompressed json backup checks
        try:
            raw_json = json.loads(decoded)
            extract_strings_recursively(raw_json)
        except Exception:
            pass

        # 3. Direct ASCII memory scanning
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

        for s in extract_ascii_strings(raw):
            cleaned = s.strip()
            if len(cleaned) >= 4 and not cleaned.startswith(("%%", "##", "$$")):
                extracted_strings.add(cleaned)

        # 4. Filter asset paths
        found_paths = re.findall(
            r'(https?://[^\s"\'()<>]+|[\w\-_]+/[\w\-_/]+\.(?:png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp)(?:\d+)?)',
            decoded,
            re.IGNORECASE
        )
        for path in found_paths:
            extracted_strings.add(path)

        clean_strings = set()
        urls = set()

        for val in extracted_strings:
            clean_str = extract_clean_path_from_string(val)
            if not clean_str:
                continue
            clean_strings.add(clean_str)

            val_lower = clean_str.lower()
            if val_lower.startswith(("http://", "https://")):
                urls.add(clean_str)
                continue
            if any(f".{ext}" in val_lower for ext in VALID_EXTENSIONS) or val_lower.endswith((".ff_extend", ".ktxp")) or ("local/" in val_lower):
                urls.add(clean_str)
                continue
            social_domains = ["instagram.com", "discord.gg", "youtube.com", "youtu.be", "facebook.com", "twitter.com", "x.com", "whatsapp.com", "linktr.ee"]
            if any(domain in val_lower for domain in social_domains):
                if not val_lower.startswith(("http://", "https://")):
                    clean_str = "https://" + clean_str
                urls.add(clean_str)
                continue

        urls_list = sorted(list(urls))

        return jsonify({
            "success": True,
            "count": len(clean_strings),
            "raw_count": len(urls_list),
            "strings": sorted(list(clean_strings)),
            "urls": urls_list,
            "raw_response": decoded
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)