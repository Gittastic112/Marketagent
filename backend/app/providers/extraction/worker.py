"""Trusted optional parsers in a credential-free child; input remains untrusted.

seccomp denies outbound socket operations, including native library calls.
Resource limits bound parsing; this is not a general filesystem sandbox.
"""
import ctypes
from contextlib import redirect_stdout
import errno
import json
import resource
import sys

MAX_OUTPUT = 12 * 1024 * 1024


def deny_network() -> None:
    """Install irreversible child-process seccomp rules; fail closed if unavailable."""
    library = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    library.seccomp_init.argtypes = [ctypes.c_uint32]
    library.seccomp_init.restype = ctypes.c_void_p
    library.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    library.seccomp_syscall_resolve_name.restype = ctypes.c_int
    library.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    library.seccomp_load.argtypes = [ctypes.c_void_p]
    library.seccomp_release.argtypes = [ctypes.c_void_p]
    context = library.seccomp_init(0x7FFF0000)
    if not context:
        raise OSError
    try:
        for name in (b"socket", b"connect", b"sendto", b"sendmsg", b"sendmmsg"):
            syscall = library.seccomp_syscall_resolve_name(name)
            if syscall < 0 or library.seccomp_rule_add(context, 0x00050000 | errno.EPERM, syscall, 0) != 0:
                raise OSError
        if library.seccomp_load(context) != 0:
            raise OSError
    finally:
        library.seccomp_release(context)


def isolate() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (45, 46))
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    # Parsers materialize the input in a temporary file. The JSON result keeps
    # its separate smaller bound; allow the full accepted input to be written.
    resource.setrlimit(resource.RLIMIT_FSIZE, (40 * 1024 * 1024, 40 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (96, 96))
    deny_network()


def main() -> None:
    try:
        isolate()
    except (OSError, ValueError):
        print(json.dumps({"error": "isolation"}))
        return
    try:
        header = sys.stdin.buffer.readline(4098)
        if len(header) > 4097 or not header.endswith(b"\n"):
            raise ValueError
        job = json.loads(header)
        content = sys.stdin.buffer.read(40 * 1024 * 1024 + 1)
        if len(content) > 40 * 1024 * 1024:
            raise ValueError
        with redirect_stdout(sys.stderr):
            if job["adapter"] == "edgartools":
                from app.providers.extraction.edgar import parse_company_facts
                result = parse_company_facts(json.loads(content), **job["options"])
            else:
                from app.providers.extraction.pdf import parse_pdf
                result = parse_pdf(job["adapter"], content, job["pages"], job.get("model_dir"), **job["options"])
        encoded = json.dumps({"data": result}, allow_nan=False).encode()
        if len(encoded) > MAX_OUTPUT:
            raise MemoryError
        sys.stdout.buffer.write(encoded)
    except (ImportError, FileNotFoundError):
        print(json.dumps({"error": "dependency"}))
    except MemoryError:
        print(json.dumps({"error": "limits"}))
    except Exception:
        print(json.dumps({"error": "invalid"}))


if __name__ == "__main__":
    main()
