import socket
import threading
import json
import os
import time

# ==========================
# CONFIGURAZIONE
# ==========================

WORKER_NAME = os.getenv("WORKER_NAME", "printer-01")

WORKER_HOST = "0.0.0.0"
WORKER_PORT = int(os.getenv("WORKER_PORT", "6001"))

NAMING_SERVER_HOST = os.getenv(
    "NAMING_SERVER_HOST",
    "naming_server"
)

NAMING_SERVER_PORT = 5000

SECRET_TOKEN = os.getenv(
    "SECRET_TOKEN",
    "DistributedSystems2026"
)

PRINT_LOG = "print_jobs.log"


# ==========================
# REGISTER
# ==========================

def register():

    pid = os.getpid()

    payload = {
        "action": "REGISTER",
        "token": SECRET_TOKEN,
        "worker_name": WORKER_NAME,
        "pid": pid,
        "ip": socket.gethostbyname(socket.gethostname()),
        "port": WORKER_PORT
    }

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.connect(
            (
                NAMING_SERVER_HOST,
                NAMING_SERVER_PORT
            )
        )

        sock.send(
            json.dumps(payload).encode()
        )

        response = json.loads(
            sock.recv(4096).decode()
        )

        sock.close()

        print("[REGISTER]", response)

        return "OK"

    except Exception as e:

        print(
            "[REGISTER ERROR]",
            str(e)
        )

        return "NETWORK_ERROR"


# ==========================
# HEARTBEAT
# ==========================

def send_heartbeat():

    while True:

        try:

            payload = {
                "action": "HEARTBEAT",
                "worker_name": WORKER_NAME
            }

            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            sock.connect(
                (
                    NAMING_SERVER_HOST,
                    NAMING_SERVER_PORT
                )
            )

            sock.send(
                json.dumps(payload).encode()
            )

            response = json.loads(
                sock.recv(4096).decode()
            )

            sock.close()

            print("[HEARTBEAT]", response)

        except Exception as e:

            print(
                "[HEARTBEAT ERROR]",
                str(e)
            )

        time.sleep(5)


# ==========================
# STAMPA
# ==========================

def save_print_job(document, client_ip, client_port):

    with open(
        PRINT_LOG,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(f"\n{'='*40}\n")

        f.write(f"PID: {os.getpid()}\n")

        f.write(f"THREAD: {threading.current_thread().name}\n")

        f.write(f"WORKER: {WORKER_NAME}\n")

        f.write(f"CLIENT: {client_ip}:{client_port}\n")

        f.write(f"DOCUMENT:\n{document}\n")


# ==========================
# CLIENT HANDLER
# ==========================

def handle_client(conn, addr):

    try:

        data = conn.recv(4096).decode()

        request = json.loads(data)

        action = request.get("action")

        if action == "PRINT":

            document = request.get(
                "document",
                ""
            )

            client_ip = addr[0]
            client_port  =addr[1]
            save_print_job(document, client_ip, client_port)

            response = {
                "status": "PRINTED"
            }

        else:

            response = {
                "status": "ERROR",
                "message": "Unknown action"
            }

        conn.send(
            json.dumps(response).encode()
        )

    except Exception as e:

        conn.send(
            json.dumps({
                "status": "ERROR",
                "message": str(e)
            }).encode()
        )

    finally:

        conn.close()


# ==========================
# SERVER STAMPA
# ==========================

def start_print_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.bind(
        (
            WORKER_HOST,
            WORKER_PORT
        )
    )

    server.listen()

    print(
        f"{WORKER_NAME} listening "
        f"on port {WORKER_PORT}"
    )

    while True:

        conn, addr = server.accept()

        threading.Thread(
            target=handle_client,
            args=(conn,addr),
            daemon=True
        ).start()


# ==========================
# MAIN
# ==========================

def main():

    while True:

        response = register()

        if response == "OK":
            break

        if response == "ERROR":
            print(f"Registration failed")
            exit(1)

        print(
            "Naming Server unreachable, "
            "retry in 5 seconds..."
        )

        time.sleep(5)

    heartbeat_thread = threading.Thread(
        target=send_heartbeat,
        daemon=True
    )

    heartbeat_thread.start()

    start_print_server()


if __name__ == "__main__":
    main()