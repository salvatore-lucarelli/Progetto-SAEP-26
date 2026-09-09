import socket
import json

NAMING_SERVER_HOST = "naming_server"
NAMING_SERVER_PORT = 5000


# ==========================
# INVIO RICHIESTE AL NAMING
# ==========================

def send_to_naming(payload):

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        print(
            f"Connecting to {NAMING_SERVER_HOST}:{NAMING_SERVER_PORT}"
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

        return response

    except Exception as e:

        print(
            f"Connection error: {e}"
        )

        return {
            "status": "ERROR",
            "message": str(e)
        }


# ==========================
# LIST
# ==========================

def list_workers():

    payload = {
        "action": "LIST"
    }

    response = send_to_naming(payload)

    if response["status"] == "OK":

        workers = response["workers"]

        print("\nRegistered workers:")

        for w in workers:
            print(f" - {w}")

    else:
        print(response)


# ==========================
# LOOKUP
# ==========================

def lookup_worker(worker_name):

    payload = {
        "action": "LOOKUP",
        "worker_name": worker_name
    }

    response = send_to_naming(payload)

    if response["status"] != "OK":
        print(response)
        return None

    return response


# ==========================
# PRINT
# ==========================

def print_document():

    worker_name = input(
        "Worker name: "
    )

    # solo qui verrà usata la funzione di LOOKUP
    
    worker_info = lookup_worker(
        worker_name
    )

    if worker_info is None:
        return

    ip = worker_info["ip"]
    port = worker_info["port"]

    document = input(
        "Document text: "
    )

    payload = {
        "action": "PRINT",
        "document": document
    }

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.connect(
            (
                ip,
                port
            )
        )

        sock.send(
            json.dumps(payload).encode()
        )

        response = json.loads(
            sock.recv(4096).decode()
        )

        sock.close()

        print("\nResponse:")
        print(response)

    except Exception as e:

        print(
            "Print error:",
            str(e)
        )


# ==========================
# MENU
# ==========================

def menu():

    while True:

        print("\n===== CLIENT =====")
        print("1 - LIST")
        print("2 - PRINT")
        print("3 - EXIT")

        choice = input("> ")

        if choice == "1":
            list_workers()

        elif choice == "2":
            print_document()

        elif choice == "3":
            break

        else:
            print("Invalid option")


if __name__ == "__main__":
    menu()