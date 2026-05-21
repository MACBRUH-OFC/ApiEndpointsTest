from flask import Flask, jsonify, request, Response
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

server_tokens = {}

UI_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FF API TOOL</title>

<style>

body{
background:#050505;
color:white;
font-family:Arial;
padding:20px;
}

input{
width:100%;
padding:14px;
background:#111;
border:1px solid #333;
border-radius:14px;
color:white;
margin-bottom:16px;
}

button{
padding:12px;
border:none;
border-radius:12px;
cursor:pointer;
font-weight:bold;
}

.server{
background:#111;
color:white;
margin:4px;
}

.server.active{
background:#ffde00;
color:black;
}

.run{
background:#ffde00;
color:black;
width:100%;
}

#results{
margin-top:20px;
white-space:pre-wrap;
word-break:break-word;
}

.link{
padding:10px;
margin-bottom:8px;
background:#111;
border-radius:12px;
}

a{
color:#59d0ff;
text-decoration:none;
}

</style>
</head>

<body>

<h1>FF API TOOL</h1>

<input id="api" placeholder="Enter API name">

<div id="servers"></div>

<button class="run" onclick="runAPI()">
RUN
</button>

<div id="results"></div>

<script>

const servers = [
"ind","mea","id","cis","br","latam",
"vn","tw","th","sg","eu","na","pk","bd"
]

let current = "ind"

const box = document.getElementById("servers")

servers.forEach(s=>{

const btn = document.createElement("button")

btn.innerText = s.toUpperCase()

btn.className = "server"

if(s==="ind"){
btn.classList.add("active")
}

btn.onclick=()=>{

document.querySelectorAll(".server")
.forEach(x=>x.classList.remove("active"))

btn.classList.add("active")

current=s

}

box.appendChild(btn)

})

async function runAPI(){

const api = document.getElementById("api").value

if(!api){
alert("Enter API")
return
}

document.getElementById("results").innerHTML="Loading..."

try{

const r = await fetch(
`/run_script?server=${current}&name=${encodeURIComponent(api)}`
)

const data = await r.json()

if(!data.success){

document.getElementById("results").innerHTML =
data.error

return

}

let html = ""

data.links.forEach(link=>{

html += `
<div class="link">
<a href="${link}" target="_blank">
${link}
</a>
</div>
`

})

document.getElementById("results").innerHTML =
html

}catch(e){

document.getElementById("results").innerHTML =
e

}

}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return Response(UI_HTML, mimetype="text/html")


def get_token(server):

    if server in server_tokens:
        return server_tokens[server]

    try:

        uid = UID_PASSWORDS[server]["uid"]
        password = UID_PASSWORDS[server]["password"]

        response = requests.get(
            f"{TOKEN_BASE_URL}?uid={uid}&password={password}",
            timeout=20
        )

        text = response.text

        token_match = re.search(
            r'eyJ[a-zA-Z0-9_\-\.]+',
            text
        )

        if token_match:

            token = token_match.group(0)

            server_tokens[server] = token

            return token

    except Exception as e:
        print(e)

    return None


def clean_link(link):

    link = link.strip()

    link = re.sub(r'[\x00-\x1F]+', '', link)

    link = re.sub(
        r'(\.png|\.jpg|\.jpeg|\.webp|\.gif|\.ktx|\.ktxp|\.mp4|\.html|\.json|\.ff_extend)0+$',
        r'\1',
        link
    )

    return link


def extract_links(text):

    pattern = r'https?://[^\s<>"\'\\]+'

    found = re.findall(pattern, text)

    final = []

    seen = set()

    for link in found:

        link = clean_link(link)

        if len(link) < 8:
            continue

        if link in seen:
            continue

        seen.add(link)

        final.append(link)

    return final


@app.route("/run_script")
def run_script():

    try:

        server = request.args.get("server")
        api_name = request.args.get("name")

        if server not in UID_PASSWORDS:
            return jsonify({
                "success": False,
                "error": "Invalid server"
            })

        token = get_token(server)

        if not token:
            return jsonify({
                "success": False,
                "error": "Token fetch failed"
            })

        url = API_DOMAINS[server].rstrip("/") + "/" + api_name.lstrip("/")

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "UnityPlayer/2022.3.47f1",
            "ReleaseVersion": "OB53"
        }

        payload = binascii.unhexlify(
            "8533b7e1d34a5dfd9a830ee5cc36664e"
        )

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=30
        )

        raw = response.content

        try:
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
        except:
            pass

        try:
            decoded = raw.decode(
                "utf-8",
                errors="ignore"
            )
        except:
            decoded = str(raw)

        links = extract_links(decoded)

        return jsonify({
            "success": True,
            "status": response.status_code,
            "links": links
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(debug=True)