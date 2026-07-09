import sys
import socket
import hashlib

def obter_hardware_id() -> str:
    """
    Gera um ID estável da máquina baseado no volume serial do disco C:
    (via ctypes nativo no Windows) e no hostname da máquina.
    Aplica hash SHA-256 para anonimizar os dados físicos.
    """
    hostname = socket.gethostname()
    serial = "MOCK-SERIAL-12345"

    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            volumeSerialNumber = ctypes.c_ulong(0)
            rc = kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p("C:\\"),
                None, 0,
                ctypes.byref(volumeSerialNumber),
                None, None,
                None, 0
            )
            if rc:
                serial = str(volumeSerialNumber.value)
        except Exception:
            pass

    combined = f"{serial}-{hostname}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest().upper()
