import threading
from faro.medio import MedioSimUDP
from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador

A, B = b"\xaa\xaa\xaa\xaa", b"\xbb\xbb\xbb\xbb"


def test_envio_confiable_entre_dos_faros_simulados():
    ma = MedioSimUDP(50001, [("127.0.0.1", 50002)])
    mb = MedioSimUDP(50002, [("127.0.0.1", 50001)])
    faro_a, faro_b = DispositivoLuzAdaptador(ma, A), DispositivoLuzAdaptador(mb, B)
    recibido = []
    hilo = threading.Thread(target=lambda: recibido.append(faro_b.recibir(3.0)))
    hilo.start()
    assert faro_a.enviar_confiable(B, b"hola faro") is True
    hilo.join()
    assert recibido[0].payload == b"hola faro"
    ma.cerrar(); mb.cerrar()
