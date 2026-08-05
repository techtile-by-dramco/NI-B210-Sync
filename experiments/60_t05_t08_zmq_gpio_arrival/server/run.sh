#!/usr/bin/env bash
# Start the Experiment 60 server and T05--T08 clients in GNU Screen sessions.

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly REPOSITORY_DIR="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
readonly EXPERIMENT_PATH="experiments/60_t05_t08_zmq_gpio_arrival"
readonly REMOTE_REPOSITORY_DIR='${HOME}/NI-B210-Sync'
readonly SERVER_SESSION="EXP60_SERVER"

server_ip=""
repetitions=""

usage() {
    cat <<'EOF'
Usage: run.sh [--server-ip ADDRESS] [--repetitions N]

Starts the local Experiment 60 synchronization server and the T05--T08 clients
in detached GNU Screen sessions. ADDRESS defaults to the local IPv4 address used
by the default route. Use --server-ip when the tiles reach this server through a
different interface.
EOF
}

while (($#)); do
    case "$1" in
        --server-ip)
            if (($# < 2)); then
                echo "--server-ip requires an address." >&2
                exit 2
            fi
            server_ip="$2"
            shift 2
            ;;
        --repetitions)
            if (($# < 2)); then
                echo "--repetitions requires a positive integer." >&2
                exit 2
            fi
            repetitions="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if ! command -v screen >/dev/null 2>&1; then
    echo "GNU screen is required on the server." >&2
    exit 1
fi

if [[ -n "${repetitions}" && ! "${repetitions}" =~ ^[1-9][0-9]*$ ]]; then
    echo "--repetitions must be a positive integer." >&2
    exit 2
fi

if [[ -z "${server_ip}" ]] && command -v ip >/dev/null 2>&1; then
    server_ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i == "src") {print $(i + 1); exit}}')"
fi
if [[ -z "${server_ip}" ]] && command -v hostname >/dev/null 2>&1; then
    server_ip="$(hostname -I 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i ~ /^[0-9]+\./) {print $i; exit}}')"
fi
if [[ -z "${server_ip}" ]]; then
    echo "Could not detect this server's IPv4 address; pass --server-ip ADDRESS." >&2
    exit 1
fi
if [[ ! "${server_ip}" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "Invalid server address: ${server_ip}" >&2
    exit 2
fi

screen_exists() {
    local session="$1"
    screen -ls 2>/dev/null | grep -Eq "[[:space:]][0-9]+\.${session}[[:space:]]"
}

sessions=("${SERVER_SESSION}")
for tile_number in {05..08}; do
    sessions+=("EXP60_T${tile_number}")
done
for session in "${sessions[@]}"; do
    if screen_exists "${session}"; then
        echo "Screen session ${session} already exists; leaving all sessions unchanged." >&2
        echo "Attach with: screen -r ${session}" >&2
        exit 1
    fi
done

server_python="$(command -v python3)"
if [[ -x "${REPOSITORY_DIR}/.venv/bin/python3" ]]; then
    server_python="${REPOSITORY_DIR}/.venv/bin/python3"
fi

printf -v quoted_repository_dir '%q' "${REPOSITORY_DIR}"
printf -v quoted_server_python '%q' "${server_python}"
server_command="cd ${quoted_repository_dir} && exec ${quoted_server_python} \
${EXPERIMENT_PATH}/server/zmq_sync_server.py --host 0.0.0.0"
if [[ -n "${repetitions}" ]]; then
    server_command+=" --repetitions ${repetitions}"
fi

screen -dmS "${SERVER_SESSION}" bash
screen -S "${SERVER_SESSION}" -p 0 -X stuff "${server_command}"$'\r'
echo "Started synchronization server in ${SERVER_SESSION} (advertised IP: ${server_ip})."

for tile_number in {05..08}; do
    tile="T${tile_number}"
    session="EXP60_${tile}"
    host="pi@rpi-t${tile_number}.local"
    remote_command="set -e; repo_dir=\"${REMOTE_REPOSITORY_DIR}\"; \
if [ ! -d \"\${repo_dir}/.git\" ] || [ ! -f \"\${repo_dir}/.venv/bin/activate\" ]; then \
echo \"Run ${EXPERIMENT_PATH}/server/bootstrap_tile_screens.sh first.\" >&2; exit 1; fi; \
cd \"\${repo_dir}\"; \
. .venv/bin/activate; \
python3 ${EXPERIMENT_PATH}/client/zmq_gpio_client.py \
--tile ${tile} --server \"${server_ip}\""
    if [[ -n "${repetitions}" ]]; then
        remote_command+=" --repetitions ${repetitions}"
    fi

    # The client command is part of SSH, so an SSH failure cannot cause it to
    # execute in the local Screen shell.
    screen -dmS "${session}" bash
    screen -S "${session}" -p 0 -X stuff "ssh -tt ${host} '${remote_command}'"$'\r'
    echo "Started ${tile} client in ${session}: ${host} -> ${server_ip}."
done

echo "Use 'screen -r ${SERVER_SESSION}' to watch the server and 'screen -ls' to list all sessions."
