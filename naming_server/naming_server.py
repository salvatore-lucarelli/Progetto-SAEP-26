import socket
import threading
import json
import os
from datetime import datetime, timedelta

HOST = "0.0.0.0"
PORT = 5000

SECRET_TOKEN = "DistributedSystems2026"

REGISTRY_FILE = "registry.json"
AUTHORIZED_FILE = "authorized_workers.json"

registry_lock = threading.Lock()


# ==========================
# Utility JSON
# ==========================

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {}

    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)


def save_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_authorized_workers():
    with open(AUTHORIZED_FILE, "r") as f:
        return json.load(f)["workers"]


# ==========================
# REGISTER
# ==========================

def register_worker(request):

    token = request.get("token")
    worker_name = request.get("worker_name")

    if token != SECRET_TOKEN:
        return {"status": "ERROR", "message": "Unauthorized - Invalid token"}

    with registry_lock:

        registry = load_registry()

        registry[worker_name] = {
            "pid": request["pid"],
            "ip": request["ip"],
            "port": request["port"],
            "last_heartbeat": datetime.now().isoformat()
        }

        save_registry(registry)

    print(f"[REGISTER] {worker_name}")

    return {"status": "OK"}


# ==========================
# HEARTBEAT
# ==========================

def heartbeat_worker(request):

    worker_name = request.get("worker_name")

    with registry_lock:

        registry = load_registry()

        if worker_name not in registry:
            return {
                "status": "ERROR",
                "message": "Worker not registered"
            }

        registry[worker_name]["last_heartbeat"] = (
            datetime.now().isoformat()
        )

        save_registry(registry)

    return {"status": "OK"}


# ==========================
# LIST
# ==========================

def list_workers():

    with registry_lock:

        registry = load_registry()

        return {
            "status": "OK",
            "workers": list(registry.keys())
        }


# ==========================
# LOOKUP
# ==========================

def lookup_worker(request):

    worker_name = request.get("worker_name")

    with registry_lock:

        registry = load_registry()

        if worker_name not in registry:

            return {
                "status": "ERROR",
                "message": "Worker not found"
            }

        worker = registry[worker_name]

    return {
        "status": "OK",
        "worker_name": worker_name,
        "ip": worker["ip"],
        "port": worker["port"]
    }


# ==========================
# REMOVE DEAD WORKERS
# ==========================

def cleanup_workers():

    while True:

        with registry_lock:

            registry = load_registry()

            now = datetime.now()

            dead_workers = []

            for worker_name, info in registry.items():

                last_hb = datetime.fromisoformat(
                    info["last_heartbeat"]
                )

                if now - last_hb > timedelta(seconds=10):
                    dead_workers.append(worker_name)

            for worker in dead_workers:
                print(f"[TIMEOUT] Removing {worker}")
                del registry[worker]

            if dead_workers:
                save_registry(registry)

        threading.Event().wait(5)


# ==========================
# CLIENT HANDLER
# ==========================

def handle_client(conn, addr):

    try:

        data = conn.recv(4096).decode()

        request = json.loads(data)

        action = request.get("action")

        if action == "REGISTER":
            response = register_worker(request)

        elif action == "HEARTBEAT":
            response = heartbeat_worker(request)

        elif action == "LIST":
            response = list_workers()

        elif action == "LOOKUP":
            response = lookup_worker(request)

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
# MAIN
# ==========================

def main():

    cleanup_thread = threading.Thread(
        target=cleanup_workers,
        daemon=True
    )

    cleanup_thread.start()

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.bind((HOST, PORT))
    server.listen()

    print(f"Naming Server listening on {HOST}:{PORT}")

    while True:

        conn, addr = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr)
        )

        thread.start()


if __name__ == "__main__":
    main()