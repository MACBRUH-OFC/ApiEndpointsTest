from flask import Flask, jsonify, request, render_template
import requests
import gzip
import zlib
import binascii
import json
import re
import time
import base64
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

VERSION_API = "https://ff-version.vercel.app/update"
DECODER_API = "https://protobuf-decoder-seven.vercel.app/decode"
JWT_API = "https://macxjwt.vercel.app/get_jwt_token"

CLIENTS = {
    "client_ind": "https://client.ind.freefiremobile.com",
    "client_bp": "https://clientbp.ggpolarbear.com",
    "client_us": "https://client.us.freefiremobile.com"
}

REGIONS = {
    "ind": {"client": CLIENTS["client_ind"], "uid": "4258906717", "password": "RockingGamerz65-1WDTR63DX"},
    "br": {"client": CLIENTS["client_us"], "uid": "4113330289", "password": "FA684A835410A8AFFE785552154AD87A4CB928C03D8870DEE37AB7C019B2D162"},
    "na": {"client": CLIENTS["client_us"], "uid": "4139196327", "password": "FA680B796474B22907BFD3DF2AFA29577FA43C5B2068417AA24453F25212B854"},
    "sac": {"client": CLIENTS["client_us"], "uid": "4113343938", "password": "F7F739FCFB96A09B019D87C6B45174B76FAE406A4CD7A785F187E46C7F7A71FF"},
    "latam": {"client": CLIENTS["client_us"], "uid": "4113343938", "password": "F7F739FCFB96A09B019D87C6B45174B76FAE406A4CD7A785F187E46C7F7A71FF"},
    "mea": {"client": CLIENTS["client_bp"], "uid": "4103849657", "password": "EF315D040E99F9B63D79C7AEE6DC697F297D298EF384BAA4E50E003DB56514C4"},
    "vn": {"client": CLIENTS["client_bp"], "uid": "3688702515", "password": "18E3450FC131F6414A775896EDA8075A37818FEFEE7A795ED4BC7764346A5EEF"},
    "bd": {"client": CLIENTS["client_bp"], "uid": "4139230703", "password": "6C2D5409593C61CFD31CDA18146054D05E72F261F24343CDEA75AEF38ADF5C95"},
    "pk": {"client": CLIENTS["client_bp"], "uid": "4139224003", "password": "1812098F2587DCAEF5CC21EAD93FAA751D212CD81C586CFD4B4F48C1B49D2A88"},
    "sg": {"client": CLIENTS["client_bp"], "uid": "4139211052", "password": "3BA22FEF36B7118B9FB1E1EB3E5A6DD84BDE696BD66B494269496E9834F00F3B"},
    "id": {"client": CLIENTS["client_bp"], "uid": "4109659017", "password": "7CE44389FE7D03FF892E682D00C5BE586B12789019CCCB466080CED41806DBAB"},
    "cis": {"client": CLIENTS["client_bp"], "uid": "3301239795", "password": "DD40EE772FCBD61409BB15033E3DE1B1C54EDA83B75DF0CDD24C34C7C8798475"},
    "th": {"client": CLIENTS["client_bp"], "uid": "4113415247", "password": "2542DD73DD60B33E183C6A894F9F6A2FC7DAEC457B826C71D44BFD4470788BBB"},
    "tw": {"client": CLIENTS["client_bp"], "uid": "4113375272", "password": "6AB01F7FB110A4C9EB95DBA21BD0E63E622DF8E566157811910F81E54394A17D"},
    "eu": {"client": CLIENTS["client_bp"], "uid": "4139177376", "password": "E29B0A5C48E8B426BE3E9D977927606842310E2F14EB108F2B5D7F73D9C4B105"}
}

ENDPOINT_HEX_PAYLOADS = {
    "logingetdesc": "19d87e64f15e9db87392bc99506f0b94",
    "logingetaccountinfo": "701ab6a8dcd2e32bde5efd87d0da7545",
    "getmaillist": "59f0b3e90a6ff6ffed2f612996c74b04",
    "getlimitedeventopeninfo": "1a725b2c56ec52ba7d09623454c0a003",
    "getcustomeventopeninfo": "9aeaea80bb2ba264078712b7c32a4116",
    "getbpalldescs": "1a725b2c56ec52ba7d09623454c0a003",
    "getcollabdesc": "1a725b2c56ec52ba7d09623454c0a003"
}

VERSION_CACHE = {"version": None}
VALID_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "gif", "bmp", "ktx", "html", "json", "mp4", "mp3", "wav", "ogg", "webm"]

SESSION = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
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
    try:
        response = SESSION.get(VERSION_API, timeout=8)
        response.raise_for_status()
        version = response.json().get("latest_release_version")
        if version:
            VERSION_CACHE["version"] = version
            return version
    except Exception:
        pass
    return "OB53"


def get_token(region_data, release_version):
    for _ in range(2):
        try:
            url = f"{JWT_API}?uid={region_data['uid']}&password={region_data['password']}&version={release_version}"
            jwt_response = SESSION.get(url, timeout=10)
            jwt_response.raise_for_status()
            token = jwt_response.json().get("token")
            if token:
                return token
        except Exception:
            pass
    return None


def get_payload_for_endpoint(endpoint_name):
    if not endpoint_name:
        return "19d87e64f15e9db87392bc99506f0b94"
    clean_name = endpoint_name.strip().lower()
    return ENDPOINT_HEX_PAYLOADS.get(clean_name, "19d87e64f15e9db87392bc99506f0b94")


def sanitize_garena_path(path):
    """
    Cleans unwanted prefixes like 'en;hi*(', 'pt;es#', 'zh-TW*', or language tags before valid asset paths
    (e.g., OB49/CSH/NewbieRing/NewbieRingIND_en.png).
    """
    if not path:
        return ""

    # Remove extension numbers (e.g. .png12 -> .png)
    cleaned = re.sub(
        r'\.(png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp)\d+$',
        r'.\1',
        path,
        flags=re.IGNORECASE
    ).strip('"\'* \t\n\r')

    # Look for OB version pattern (e.g., OB49/, OB53/)
    ob_match = re.search(r'(OB\d+/.+)', cleaned, re.IGNORECASE)
    if ob_match:
        return ob_match.group(1)

    # Look for explicit clean relative paths
    path_match = re.search(r'([\w\-_]+(?:/[\w\-_]+)+\.(?:png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp))', cleaned, re.IGNORECASE)
    if path_match:
        return path_match.group(1)

    # Strip dirty prefix before first valid folder letter
    cleaned = re.sub(r'^[a-zA-Z0-9_\-;*()$%#@!&+=]+(?=[\w\-_]+/[\w\-_/]+\.)', '', cleaned)
    return cleaned


def decode_protobuf(raw_hex):
    try:
        decoder_response = SESSION.post(DECODER_API, json={"data": raw_hex}, timeout=12)
        if decoder_response.status_code == 200:
            decoder_json = decoder_response.json()
            protobuf = decoder_json.get("protobuf", {})
            if isinstance(protobuf, str):
                try:
                    protobuf = json.loads(protobuf)
                except Exception:
                    protobuf = {}
            if isinstance(protobuf, dict):
                return protobuf
    except Exception:
        pass
    return {}


@app.route("/")
@app.route("/api")
def home():
    return render_template("ui.html")


@app.route("/get_version")
@app.route("/api/get_version")
def get_version_route():
    try:
        version = get_release_version()
        return jsonify({"version": version})
    except Exception as e:
        return jsonify({"version": "OB53", "warning": str(e)})


@app.route("/run_script")
@app.route("/api/run_script")
def run_script():
    start_time = time.time()
    try:
        server = request.args.get("server", "ind").lower()
        api_name = request.args.get("name")
        version_param = request.args.get("version")

        if server not in REGIONS:
            return jsonify({"error": f"Invalid server region '{server}'"}), 400

        if not api_name:
            return jsonify({"error": "Missing endpoint target parameter 'name'"}), 400

        api_path = urlparse(api_name).path.lstrip("/") if "://" in api_name else api_name.lstrip("/")
        clean_api_name = api_path.split("/")[-1]
        payload_hex = get_payload_for_endpoint(clean_api_name)

        release_version = version_param if version_param else get_release_version()
        region_data = REGIONS[server]

        token = get_token(region_data, release_version)
        if not token:
            return jsonify({"error": f"Authentication token generation failed for {server.upper()}"}), 401

        headers = BASE_HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"
        headers["ReleaseVersion"] = release_version

        url = f"{region_data['client']}/{api_path}"

        try:
            raw_payload = binascii.unhexlify(payload_hex)
            response = SESSION.post(url, headers=headers, data=raw_payload, timeout=20)
        except requests.exceptions.Timeout:
            return jsonify({"error": f"Timeout connecting to Garena server [{server.upper()}]"}), 504
        except requests.exceptions.RequestException as req_err:
            return jsonify({"error": f"Garena Connection Fault: {str(req_err)}"}), 502

        if response.status_code == 401:
            token = get_token(region_data, release_version)
            if token:
                headers["Authorization"] = f"Bearer {token}"
                response = SESSION.post(url, headers=headers, data=raw_payload, timeout=20)

        if response.status_code != 200:
            return jsonify({"error": f"Garena Endpoint returned HTTP {response.status_code}"}), response.status_code

        raw_bytes = decompress_data(response.content)
        if not raw_bytes:
            return jsonify({"error": "Empty payload stream returned."}), 204

        raw_hex = raw_bytes.hex()
        raw_b64 = base64.b64encode(raw_bytes).decode("utf-8")
        decoded_ascii = raw_bytes.decode("utf-8", errors="ignore")

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
                if obj.strip().startswith(("{", "[")):
                    try:
                        extract_strings_recursively(json.loads(obj))
                    except Exception:
                        pass

        extract_strings_recursively(protobuf_data)

        # ASCII parsing
        current = []
        for byte in raw_bytes:
            if 32 <= byte <= 126:
                current.append(chr(byte))
            else:
                if len(current) >= 4:
                    extracted_strings.add("".join(current))
                current = []
        if len(current) >= 4:
            extracted_strings.add("".join(current))

        # Regex path discovery
        found_paths = re.findall(
            r'(https?://[^\s"\'()<>]+|[\w\-_]+/[\w\-_/]+\.(?:png|jpg|jpeg|webp|gif|bmp|ktx|html|json|mp4|mp3|wav|ogg|webm|ff_extend|ktxp)(?:\d+)?)',
            decoded_ascii,
            re.IGNORECASE
        )
        for path in found_paths:
            extracted_strings.add(path)

        clean_strings = set()
        urls = set()

        for val in extracted_strings:
            clean_str = sanitize_garena_path(val)
            if not clean_str or len(clean_str) < 3:
                continue
            clean_strings.add(clean_str)

            val_lower = clean_str.lower()
            if val_lower.startswith(("http://", "https://")):
                urls.add(clean_str)
            elif any(f".{ext}" in val_lower for ext in VALID_EXTENSIONS) or val_lower.endswith((".ff_extend", ".ktxp")) or "local/" in val_lower:
                urls.add(clean_str)

        urls_list = sorted(list(urls))
        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        clean_endpoint_filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', clean_api_name)

        return jsonify({
            "success": True,
            "endpoint": clean_endpoint_filename,
            "server": server,
            "version": release_version,
            "count": len(clean_strings),
            "raw_count": len(urls_list),
            "byte_size": len(raw_bytes),
            "execution_ms": execution_time_ms,
            "strings": sorted(list(clean_strings)),
            "urls": urls_list,
            "protobuf": protobuf_data,
            "raw_hex": raw_hex,
            "raw_b64": raw_b64,
            "raw_response": decoded_ascii
        })

    except Exception as e:
        return jsonify({"error": f"Internal Script Error: {str(e)}"}), 500


@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)