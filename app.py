from flask import Flask, jsonify, request, render_template
import requests
import gzip
import binascii
import re

app = Flask(__name__)

TOKEN_BASE_URL = "https://jwt-gen-new.vercel.app/token"

UID_PASSWORDS = {
    "ind": {"uid": "4258906717", "password": "RockingGamerz65-1WDTR63DX"},
    "br": {"uid": "4113330289", "password": "FA684A835410A8AFFE785552154AD87A4CB928C03D8870DEE37AB7C019B2D162"},
    "na": {"uid": "4139196327", "password": "FA680B796474B22907BFD3DF2AFA29577FA43C5B2068417AA24453F25212B854"},
    "eu": {"uid": "4139177376", "password": "E29B0A5C48E8B426BE3E9D977927606842310E2F14EB108F2B5D7F73D9C4B105"},
    "sg": {"uid": "4139211052", "password": "3BA22FEF36B7118B9FB1E1EB3E5A6DD84BDE696BD66B494269496E9834F00F3B"},
    "vn": {"uid": "4113363250", "password": "47269BFC4695E93FFABA1AA426847669D12AF36F6B7FCA52BF660459EE2B4092"},
    "th": {"uid": "4113415247", "password": "2542DD73DD60B33E183C6A894F9F6A2FC7DAEC457B826C71D44BFD4470788BBB"},
    "tw": {"uid": "4113375272", "password": "6AB01F7FB110A4C9EB95DBA21BD0E63E622DF8E566157811910F81E54394A17D"},
    "id": {"uid": "4109659017", "password": "7CE44389FE7D03FF892E682D00C5BE586B12789019CCCB466080CED41806DBAB"},
    "pk": {"uid": "4139224003", "password": "1812098F2587DCAEF5CC21EAD93FAA751D212CD81C586CFD4B4F48C1B49D2A88"},
    "bd": {"uid": "4139230703", "password": "6C2D5409593C61CFD31CDA18146054D05E72F261F24343CDEA75AEF38ADF5C95"}
}

API_DOMAINS = {
    "ind": "https://client.ind.freefiremobile.com/",
    "br": "https://client.us.freefiremobile.com/",
    "na": "https://client.us.freefiremobile.com/",
    "eu": "https://clientbp.ggpolarbear.com/",
    "sg": "https://clientbp.ggpolarbear.com/",
    "vn": "https://clientbp.ggpolarbear.com/",
    "th": "https://clientbp.ggpolarbear.com/",
    "tw": "https://clientbp.ggpolarbear.com/",
    "id": "https://clientbp.ggpolarbear.com/",
    "pk": "https://clientbp.ggpolarbear.com/",
    "bd": "https://clientbp.ggpolarbear.com/"
}

server_tokens = {}

BASE_LINKS = {
    "ind": "https://dl-tata.freefireind.in/common/",
    "default": "https://dl.dir.freefiremobile.com/common/"
}


@app.route("/")
def home():
    return render_template("ui.html")


def get_token(server):

    if server in server_tokens:
        return server_tokens[server]

    try:

        creds = UID_PASSWORDS[server]

        url = f"{TOKEN_BASE_URL}?uid={creds['uid']}&password={creds['password']}"

        response = requests.get(url, timeout=15)

        data = response.json()

        text = str(data)

        match = re.search(r'token\s*:\s*"([^"]+)"', text)

        if match:
            token = match.group(1)
            server_tokens[server] = token
            return token

    except Exception as e:
        print(e)

    return None


def normalize_link(link, region):

    if not link:
        return None

    link = link.strip()

    link = re.sub(r'^[^a-zA-Z0-9]+', '', link)

    link = re.sub(r'[\s<>"`]+$', '', link)

    link = re.sub(r'[0XJ]+$', '', link)

    if link.startswith("http"):
        return link

    if re.match(r'^OB\d+', link, re.IGNORECASE):

        base = BASE_LINKS["ind"] if region == "ind" else BASE_LINKS["default"]

        return base + link

    return None


@app.route("/run_script")
def run_script():

    try:

        server = request.args.get("server")
        endpoint = request.args.get("name")

        if not server or not endpoint:
            return jsonify({"error": "Missing parameters"})

        token = get_token(server)

        if not token:
            return jsonify({"error": "Failed to get token"})

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "UnityPlayer/2022.3.47f1",
            "ReleaseVersion": "OB53",
            "X-Unity-Version": "2022.3.47f1"
        }

        payload = binascii.unhexlify("8533b7e1d34a5dfd9a830ee5cc36664e")

        url = API_DOMAINS[server].rstrip("/") + "/" + endpoint.lstrip("/")

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=20
        )

        content = response.content

        try:
            if content[:2] == b'\x1f\x8b':
                content = gzip.decompress(content)
        except:
            pass

        raw_strings = re.findall(rb"[ -~]{4,}", content)

        final_links = []

        for item in raw_strings:

            try:

                decoded = item.decode("utf-8", errors="ignore")

                fixed = normalize_link(decoded, server)

                if not fixed:
                    continue

                if any(ext in fixed.lower() for ext in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp",
                    ".ktx",
                    ".html",
                    ".json",
                    ".ff_extend"
                ]):
                    final_links.append(fixed)

            except:
                pass

        final_links = list(dict.fromkeys(final_links))

        return jsonify({
            "success": True,
            "count": len(final_links),
            "strings": final_links
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(debug=True)