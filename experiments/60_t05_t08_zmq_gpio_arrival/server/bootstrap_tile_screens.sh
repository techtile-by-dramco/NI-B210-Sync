#!/usr/bin/env bash
# Bootstrap T04--T08 in detached screen sessions from the Experiment 60 server.

set -euo pipefail

readonly REPOSITORY_URL="https://github.com/techtile-by-dramco/NI-B210-Sync.git"
readonly REMOTE_REPOSITORY_DIR='${HOME}/NI-B210-Sync'
readonly REQUIREMENTS_PATH="experiments/60_t05_t08_zmq_gpio_arrival/requirements-pi.txt"
readonly SCREEN_COMMAND_WRAPPER='"$@"
status=$?
printf "\nProcess exited with status %d; this Screen session is being kept open for inspection.\n" "${status}"
exec bash -i'

if ! command -v screen >/dev/null 2>&1; then
    echo "GNU screen is required on the server." >&2
    exit 1
fi

for tile_number in {04..08}; do
    tile="T${tile_number}"
    host="pi@rpi-t${tile_number}.local"

    if screen -ls 2>/dev/null | grep -Eq "[[:space:]][0-9]+\.${tile}[[:space:]]"; then
        echo "Skipping ${tile}: a screen session with that name already exists." >&2
        continue
    fi

    remote_command="set -e; repo_dir=\"${REMOTE_REPOSITORY_DIR}\"; \
if [ ! -e \"\${repo_dir}\" ]; then \
git clone \"${REPOSITORY_URL}\" \"\${repo_dir}\"; \
elif [ ! -d \"\${repo_dir}/.git\" ]; then \
echo \"Cannot use \${repo_dir}: it exists but is not a Git repository.\" >&2; exit 1; \
else git -C \"\${repo_dir}\" pull --ff-only; fi; \
cd \"\${repo_dir}\"; \
python3 -m venv .venv; \
. .venv/bin/activate; \
python3 -m pip install -r \"${REQUIREMENTS_PATH}\"; \
echo \"${tile} is ready in \${repo_dir}; virtual environment: \${VIRTUAL_ENV}\"; \
exec bash -i"

    # Pass SSH and its remote command as positional arguments to the wrapper.
    # This avoids local expansion of remote variables and preserves failures for
    # inspection after SSH exits.
    screen -dmS "${tile}" bash -c "${SCREEN_COMMAND_WRAPPER}" bash \
        ssh -tt "${host}" "${remote_command}"
    echo "Started ${tile}: ${host}"
done

echo "Use 'screen -ls' to list sessions and 'screen -r T05' to attach."
