import subprocess
import csv
import ipaddress
import datetime

ipv4_ranges = [
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "108.162.192.0/18",
    "131.0.72.0/22",
    "141.101.64.0/18",
    "162.158.0.0/15",
    "172.64.0.0/13",
    "173.245.48.0/20",
    "188.114.96.0/20",
    "190.93.240.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17"
]

ipv6_ranges = [
    "2400:cb00::/32",
    "2606:4700::/32",
    "2803:f800::/32",
    "2405:b500::/32",
    "2405:8100::/32",
    "2a06:98c0::/29",
    "2c0f:f248::/32",
]

def get_test_ip(cidr_list):
    test_ips = []
    for block in cidr_list:
        net = ipaddress.ip_network(block)
        first_ip = net.network_address + 1     # NO EXPANSION
        test_ips.append(str(first_ip))
    return test_ips

ipv4_test_ips = get_test_ip(ipv4_ranges)
ipv6_test_ips = get_test_ip(ipv6_ranges)

def ping(ip):
    cmd = ["ping", "-n", "1", "-w", "1000", ip]  # Windows ping
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout

        if "Reply from" in output:
            latency = "N/A"
            for line in output.split("\n"):
                if "time=" in line:
                    latency = line.split("time=")[1].split("ms")[0]
                    break
            return "Success", latency
        return "Fail", "N/A"
    except:
        return "Error", "N/A"

report_file = "cloudflare_ping_report.csv"

with open(report_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["IP Address", "Version", "Status", "Latency (ms)", "Timestamp"])

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for ip in ipv4_test_ips:
        status, latency = ping(ip)
        writer.writerow([ip, "IPv4", status, latency, timestamp])

    for ip in ipv6_test_ips:
        status, latency = ping(ip)
        writer.writerow([ip, "IPv6", status, latency, timestamp])

print("Done! Report saved:", report_file)
