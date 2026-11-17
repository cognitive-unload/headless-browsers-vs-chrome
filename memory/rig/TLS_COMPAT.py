"""Auditable Python 3.12+ repair for the pinned pywebsocket3 server only."""
import hashlib

OLD='''                socket_ = ssl.wrap_socket(
                    socket_,
                    keyfile=server_options.private_key,
                    certfile=server_options.certificate,
                    ca_certs=server_options.tls_client_ca,
                    cert_reqs=client_cert_)'''
NEW='''                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.verify_mode = client_cert_
                context.load_cert_chain(server_options.certificate,
                                        server_options.private_key)
                if server_options.tls_client_ca:
                    context.load_verify_locations(server_options.tls_client_ca)
                socket_ = context.wrap_socket(socket_, server_side=True)'''

def patch(path):
    before=path.read_bytes();source=before.decode()
    if source.count(OLD)!=1:raise ValueError('pinned TLS repair source mismatch')
    after=source.replace(OLD,NEW).encode();path.write_bytes(after)
    return dict(file='pywebsocket3/websocket_server.py',
                original_sha256=hashlib.sha256(before).hexdigest(),
                modified_sha256=hashlib.sha256(after).hexdigest(),
                reason='replace removed ssl.wrap_socket with server SSLContext; same fixture certificate and client-auth policy')
