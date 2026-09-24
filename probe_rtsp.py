"""Diagnose a camera: walk DESCRIBE -> SETUP -> PLAY and print each status.

Usage: uv run probe_rtsp.py <ip> <user> <password> stream1
"""
import hashlib, re, socket, sys


class Rtsp:
    def __init__(self, ip, user, password, port=554):
        self.ip, self.user, self.password, self.port = ip, user, password, port
        self.s = socket.create_connection((ip, port), timeout=5)
        self.s.settimeout(5)
        self.cseq = 0
        self.realm = self.nonce = None
        self.session = None

    def _auth(self, method, url):
        if not self.realm:
            return ""
        h = lambda x: hashlib.md5(x.encode()).hexdigest()
        ha1 = h(f"{self.user}:{self.realm}:{self.password}")
        ha2 = h(f"{method}:{url}")
        resp = h(f"{ha1}:{self.nonce}:{ha2}")
        return (f'Authorization: Digest username="{self.user}", realm="{self.realm}", '
                f'nonce="{self.nonce}", uri="{url}", response="{resp}"\r\n')

    def request(self, method, url, extra=""):
        self.cseq += 1
        req = f"{method} {url} RTSP/1.0\r\nCSeq: {self.cseq}\r\n"
        req += self._auth(method, url)
        if self.session:
            req += f"Session: {self.session}\r\n"
        req += extra + "\r\n"
        self.s.sendall(req.encode())
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = self.s.recv(4096)
            if not chunk:
                break
            data += chunk
        text = data.decode(errors="replace")

        if "401" in text.split("\r\n")[0] and not self.realm:
            m = re.search(r'Digest realm="([^"]*)".*?nonce="([^"]*)"', text, re.S)
            if m:
                self.realm, self.nonce = m.groups()
                return self.request(method, url, extra)

        m = re.search(r"Session:\s*([^;\r\n]+)", text)
        if m:
            self.session = m.group(1).strip()
        return text


if __name__ == "__main__":
    ip, user, password, stream = sys.argv[1:5]
    base = f"rtsp://{ip}:554/{stream}"
    c = Rtsp(ip, user, password)

    for method, url, extra in [
        ("DESCRIBE", base, "Accept: application/sdp\r\n"),
        ("SETUP", f"{base}/track1", "Transport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n"),
        ("PLAY", base, "Range: npt=0.000-\r\n"),
    ]:
        reply = c.request(method, url, extra)
        if not reply.strip():
            print(f"{method:9} -> (empty reply - camera closed the connection)")
            break
        print(f"{method:9} -> {reply.splitlines()[0]}")
        if not reply.startswith("RTSP/1.0 200"):
            print("   full reply:")
            print("   " + reply.replace("\r\n", "\n   ")[:600])
            break
    else:
        data = c.s.recv(4096)
        print(f"\nRTP data flowing: {len(data)} bytes received")
