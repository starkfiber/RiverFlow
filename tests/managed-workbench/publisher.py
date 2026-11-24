"""Independent OpenSSL publisher for disposable RF2REL01 test fixtures."""
import hashlib
from pathlib import Path
import struct
import subprocess

SPKI = bytes.fromhex("3059301306072a8648ce3d020106082a8648ce3d030107034200")
DOMAIN = b"RF2 release chain signature v1".ljust(32, b"\0")


def openssl(*args, data=None):
    return subprocess.run(["/usr/bin/openssl", *args], input=data, capture_output=True,
                          check=True, timeout=20).stdout


def digest(data):
    return hashlib.sha256(data).digest()


class Publisher:
    def __init__(self, private_dir: Path, label):
        self.key = private_dir / (label + ".pem")
        openssl("genpkey", "-algorithm", "EC", "-pkeyopt", "ec_paramgen_curve:prime256v1",
                "-pkeyopt", "ec_param_enc:named_curve", "-out", self.key)
        self.public_pem = private_dir / (label + "-public.pem")
        self.public_pem.write_bytes(openssl("pkey", "-in", self.key, "-pubout"))
        encoded = openssl("pkey", "-in", self.key, "-pubout", "-outform", "DER")
        assert encoded.startswith(SPKI) and len(encoded) == len(SPKI) + 65
        self.public = encoded[len(SPKI):]

    def envelope(self, previous, artifact, provenance, target=None):
        sequence = struct.unpack_from("<Q", previous, 16)[0] + 1 if previous else 1
        selected = struct.unpack_from("<Q", target, 16)[0] if target else 0
        values = target[64:192] if target else digest(artifact) + b"".join(map(digest, provenance))
        record = (struct.pack("<8sQQQ", b"RF2REL01", 1, sequence, 2 if target else 1)
                  + (digest(previous) if previous else bytes(32)) + values
                  + (digest(target) if target else bytes(32))
                  + struct.pack("<QQQQ", selected, len(artifact), 1, 1) + digest(self.public))
        assert len(record) == 288
        message = DOMAIN + record
        signature = openssl("dgst", "-sha256", "-sign", self.key, data=message)
        signature_file = self.key.with_suffix(".signature")
        signature_file.write_bytes(signature)
        openssl("dgst", "-sha256", "-verify", self.public_pem, "-signature", signature_file, data=message)
        return record + struct.pack("<Q", len(signature)) + signature
