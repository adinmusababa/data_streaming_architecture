import subprocess, sys

py = open("graphify-out/.graphify_python", encoding="utf-8").read().strip()
r = subprocess.run([py, "-m", "graphify", "query",
    "Apakah semua komponen desain di docs sudah diimplementasikan di kode? Bandingkan rancangan dengan implementasi aktual",
    "--budget", "3000"], capture_output=True, text=True)
print(r.stdout)
print(r.stderr)
