"""Pruebas del boton de panico. Usan una carpeta temporal, nunca la real."""
from faro.panico import panico


def test_panico_borra_direccion_y_llaves(tmp_path):
    """El panico debe borrar los tres archivos sensibles."""
    (tmp_path / "direccion.bin").write_bytes(b"\xaa\xbb\xcc\xdd")
    (tmp_path / "firma.key").write_bytes(b"F" * 32)
    (tmp_path / "cifrado.key").write_bytes(b"C" * 32)

    borrados = panico(tmp_path)

    assert set(borrados) == {"direccion.bin", "firma.key", "cifrado.key"}
    assert list(tmp_path.glob("*")) == []


def test_panico_sobrescribe_antes_de_borrar(tmp_path, monkeypatch):
    """Comprueba que el contenido se sobrescribe antes de que unlink lo borre."""
    objetivo = tmp_path / "firma.key"
    objetivo.write_bytes(b"secreto")

    # Espiamos el momento previo al unlink: leemos el archivo justo antes de borrarlo.
    contenido_capturado = {}

    def falso_unlink(self):
        contenido_capturado["contenido"] = self.read_bytes()
        # Ahora si, borramos de verdad.
        original_unlink(self)

    from pathlib import Path
    original_unlink = Path.unlink
    monkeypatch.setattr(Path, "unlink", falso_unlink)

    panico(tmp_path)

    # El contenido que habia antes del unlink debe ser todo ceros.
    assert contenido_capturado["contenido"] == b"\x00" * len(b"secreto")


def test_panico_sin_carpeta_no_falla(tmp_path):
    """Si la carpeta no existe, el panico no debe lanzar excepcion."""
    fantasma = tmp_path / "no-existe"
    assert panico(fantasma) == []