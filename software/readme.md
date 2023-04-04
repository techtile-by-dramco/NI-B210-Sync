## How to run the Zadoff-Chu RX test

1. Install the necessary packages and libs via `software/tx-test/setup.sh` (as sudo)
2. Start the (two) receivers `software/rx-test/zadoff-chu/RX/`.
3. Start the transmitter `software/rx-test/zadoff-chu/TX/`.
4. Start the server `software/rx-test/zadoff-chu/server-sync.py`. Currently, it listens to two incoming start messages (originating from the RX nodes). After reception of these two messages, it sends a SYNC signal back to the RXs.

You can now inspect the stored data via the `xcorr_files_ZC.py` file.
