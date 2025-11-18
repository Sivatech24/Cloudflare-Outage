import subprocess
import ipaddress
import datetime
import geoip2.database

import matplotlib.pyplot as plt
from matplotlib import cm
import folium

# ---------- CLOUDFLARE IP RANGES ----------
ipv4_ranges = [
    "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "104.16.0.0/13", "104.24.0.0/14", "108.162.192.0/18",
    "131.0.72.0/22", "141.101.64.0/18", "162.158.0.0/15",
    "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
    "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17"
]

ipv6_ranges = [
    "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32",
    "2405:b500::/32", "2405:8100::/32", "2a06:98c0::/29",
    "2c0f:f248::/32"
]

# get single IP per block (first usable)
def get_test_ips(cidr_list):
    ips = []
    for block in cidr_list:
        net = ipaddress.ip_network(block)
        ip = net.network_address + 1  # first host
        ips.append(str(ip))
    return ips

ipv4_test_ips = get_test_ips(ipv4_ranges)
ipv6_test_ips = get_test_ips(ipv6_ranges)
test_ips = ipv4_test_ips + ipv6_test_ips

# ---------- PING FUNCTION ----------
def ping(ip):
    """Ping once, return status + latency in ms (or None)."""
    try:
        # For Windows. If Linux/Mac, change to `["ping", "-c", "1", "-W", "1", ip]`
        cmd = ["ping", "-n", "1", "-w", "1000", ip]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out = result.stdout
        # parse
        if "Reply from" in out:
            latency = None
            for line in out.splitlines():
                if "time=" in line:
                    # Windows style: "time=XXms"
                    part = line.split("time=")[1]
                    if "ms" in part:
                        latency = float(part.split("ms")[0])
                    else:
                        latency = float(part)
                    break
            return "Success", latency
        else:
            return "Fail", None
    except Exception as e:
        return "Error", None

# ---------- GEOLOCATION ----------
# Path to your downloaded GeoLite2-City.mmdb file
GEOIP_DB_PATH = "GeoLite2-City.mmdb"

reader = geoip2.database.Reader(GEOIP_DB_PATH)

locations = {}  # ip -> (lat, lon, country)
for ip in test_ips:
    try:
        resp = reader.city(ip)
        lat = resp.location.latitude
        lon = resp.location.longitude
        country = resp.country.name
        locations[ip] = (lat, lon, country)
    except Exception as e:
        locations[ip] = (None, None, None)

reader.close()

# ---------- COLLECT PING + GEO DATA ----------
data = []
for ip in test_ips:
    status, latency = ping(ip)
    lat, lon, country = locations.get(ip, (None, None, None))
    data.append({
        "ip": ip,
        "status": status,
        "latency": latency,
        "lat": lat,
        "lon": lon,
        "country": country
    })
    print(f"IP: {ip}, Status: {status}, Latency: {latency}, Loc: {lat},{lon} ({country})")

# ---------- PLOT LATENCY BAR GRAPH ----------
ips = [d["ip"] for d in data]
latencies = [d["latency"] if d["latency"] is not None else 0 for d in data]

plt.figure(figsize=(12, 6))
bars = plt.bar(ips, latencies, color=cm.viridis([ (l or 0)/ (max(latencies) + 1) for l in latencies ]))
plt.xticks(rotation=45, ha="right")
plt.ylabel("Latency (ms)")
plt.title("Ping Latency to Cloudflare IPs")
plt.tight_layout()
plt.savefig("cloudflare_latency_graph.png")
print("Saved latency graph: cloudflare_latency_graph.png")

# ---------- DRAW WORLD MAP WITH Folium ----------
# Center map roughly in middle of all points
valid_locs = [(d["lat"], d["lon"]) for d in data if d["lat"] is not None and d["lon"] is not None]
if valid_locs:
    avg_lat = sum(lat for lat,lon in valid_locs) / len(valid_locs)
    avg_lon = sum(lon for lat,lon in valid_locs) / len(valid_locs)
else:
    avg_lat, avg_lon = 0, 0

m = folium.Map(location=[avg_lat, avg_lon], zoom_start=2)

for d in data:
    if d["lat"] is None or d["lon"] is None:
        continue
    color = "green" if d["status"] == "Success" else "red"
    folium.CircleMarker(
        location=[d["lat"], d["lon"]],
        radius=7,
        popup=f"{d['ip']} ({d['country']}): {d['status']} {d['latency']} ms",
        color=color,
        fill=True,
        fill_color=color
    ).add_to(m)

map_file = "cloudflare_ip_map.html"
m.save(map_file)
print("Saved world map (interactive):", map_file)

# Also save map as PNG (screenshot) using selenium, or save static image via other tools
# Optionally: you can use `selenium + headless browser` to render the HTML and take a screenshot,
# or use `pyppeteer` etc.

