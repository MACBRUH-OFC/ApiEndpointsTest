from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
import requests
import gzip
import zlib
import binascii
import re
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)
CORS(app)

# API Endpoints
VERSION_API = "https://ff-version.vercel.app/update"
DECODER_API = "https://protobuf-decoder-seven.vercel.app/decode"
JWT_API = "https://macxjwt.vercel.app/get_jwt_token"

BASE_LINK = "https://dl.dir.freefiremobile.com/common/"

VALID_EXTENSIONS = [
    "png", "jpg", "jpeg", "webp", "gif",
    "bmp", "ktx", "html", "json",
    "mp4", "mp3", "wav", "ogg", "webm"
]

# Combined server details
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
    "latam": {
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

server_tokens = {key: None for key in REGIONS.keys()}
VERSION_CACHE = {"version": None}

# Set up Session connection pools & retry configurations
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


# Helper Functions
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
    if VERSION_CACHE["version"]:
        return VERSION_CACHE["version"]

    response = SESSION.get(VERSION_API, timeout=15)
    response.raise_for_status()
    version = response.json().get("latest_release_version")
    if not version:
        raise Exception("release_version_not_found")

    VERSION_CACHE["version"] = version
    return version


def get_token(server, release_version):
    if server_tokens.get(server):
        return server_tokens[server]

    region_data = REGIONS[server]
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
                server_tokens[server] = token
                return token
        except Exception as e:
            print(f"Token generation failed: {e}")
            pass
    return None


def decode_protobuf(raw_hex):
    try:
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
            except:
                protobuf = {}

        return protobuf if isinstance(protobuf, dict) else {}
    except Exception as e:
        print(f"Protobuf decoding failed: {e}")
        return {}


def extract_strings_from_protobuf(data, strings_set):
    """Recursively parses decoded protobuf fields to gather string candidates."""
    if isinstance(data, dict):
        for val in data.values():
            extract_strings_from_protobuf(val, strings_set)
    elif isinstance(data, list):
        for item in data:
            extract_strings_from_protobuf(item, strings_set)
    elif isinstance(data, str):
        strings_set.add(data)


def process_extracted_string(val):
    val = val.strip()
    if not val:
        return None

    # Normalise supported extension replacements as required
    val = re.sub(r'\.ff_extend', '.jpg', val, flags=re.IGNORECASE)
    val = re.sub(r'\.ktxp?', '.png', val, flags=re.IGNORECASE)

    val_lower = val.lower()

    # 1. Full URL matching
    if val_lower.startswith(("http://", "https://")):
        return val

    # 2. Match only paths that start with 'test' or 'common' to build CDNs
    if val_lower.startswith("test") or val_lower.startswith("common"):
        val_clean = val.lstrip("/")
        if val_clean.lower().startswith("common/"):
            return "https://dl.dir.freefiremobile.com/" + val_clean
        else:
            return BASE_LINK + val_clean

    # 3. Match social domain references
    social_domains = ["instagram.com", "discord.gg", "youtube.com", "youtu.be", "facebook.com", "twitter.com", "x.com", "whatsapp.com", "linktr.ee"]
    if any(domain in val_lower for domain in social_domains):
        if not val_lower.startswith(("http://", "https://")):
            return "https://" + val
        return val

    return None


# Flask Routes
@app.route("/")
def home():
    return render_template("ui.html")


@app.route("/run_script", methods=["GET"])
def run_script():
    server = request.args.get("server")
    api_name = request.args.get("name")
    payload_hex = request.args.get("payload", "8533b7e1d34a5dfd9a830ee5cc36664e")

    if server not in REGIONS:
        return jsonify({"error": "Invalid server"})

    if not api_name:
        return jsonify({"error": "Missing API name"})

    try:
        release_version = get_release_version()
    except Exception as e:
        return jsonify({"error": f"Failed to get release version: {str(e)}"})

    token = get_token(server, release_version)
    if not token:
        return jsonify({"error": "Token fetch failed"})

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

    url = REGIONS[server]["client"].rstrip("/") + "/" + api_name.lstrip("/")

    try:
        response = SESSION.post(
            url,
            headers=headers,
            data=binary_payload,
            timeout=25
        )

        # Handle token expiration (HTTP 401)
        if response.status_code == 401:
            server_tokens[server] = None
            token = get_token(server, release_version)
            if not token:
                return jsonify({"error": "Token refresh failed"})

            headers["Authorization"] = f"Bearer {token}"
            response = SESSION.post(
                url,
                headers=headers,
                data=binary_payload,
                timeout=25
            )

        response.raise_for_status()
        content = decompress_data(response.content)

        # Decode response using the external protobuf decoder API
        protobuf_data = decode_protobuf(content.hex())

        # Recursively retrieve unique strings inside the decoded structure
        extracted_strings = set()
        extract_strings_from_protobuf(protobuf_data, extracted_strings)

        # Build clean URLs from parsed strings
        urls = set()
        for raw_str in extracted_strings:
            cleaned = process_extracted_string(raw_str)
            if cleaned:
                urls.add(cleaned)

        urls_list = sorted(list(urls))

        grouped = {
            "images": [],
            "videos": [],
            "audio": [],
            "html": [],
            "social": [],
            "other": []
        }

        for item in urls_list:
            lower = item.lower()
            if any(lower.endswith(x) for x in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".ktx"]):
                grouped["images"].append(item)
            elif any(lower.endswith(x) for x in [".mp4", ".webm"]):
                grouped["videos"].append(item)
            elif any(lower.endswith(x) for x in [".mp3", ".wav", ".ogg"]):
                grouped["audio"].append(item)
            elif lower.endswith(".html"):
                grouped["html"].append(item)
            elif any(x in lower for x in [
                "discord.gg", "instagram.com", "youtube.com", "youtu.be",
                "facebook.com", "twitter.com", "x.com", "linktr.ee", "whatsapp.com"
            ]):
                grouped["social"].append(item)
            else:
                grouped["other"].append(item)

        return jsonify({
            "success": True,
            "raw_count": len(urls_list),
            "urls": urls_list,
            "groups": grouped,
            "protobuf": protobuf_data,
            "raw_strings": list(extracted_strings)
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)