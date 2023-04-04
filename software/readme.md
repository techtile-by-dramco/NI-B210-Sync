## How to run the Zadoff-Chu RX test


[git clone ](https://github.com/techtile-by-dramco/NI-B210-Sync.git)


1. Install the necessary packages and libs via `software/tx-test/setup.sh` (as sudo)
2. Start the (two) receivers `software/rx-test/zadoff-chu/RX/`. Assuming you are in the working dir:
```sh
# in a new terminal
cd software/rx-test/zadoff-chu/RX/
mkdir build
cd build
cmake ../
make

./init_usrp --ignore-server # arg to ignore the sync server, used for testing purposes
```
4. Start the transmitter `software/rx-test/zadoff-chu/TX/`.
```sh
# in a new terminal
cd software/rx-test/zadoff-chu/TX/
mkdir build
cd build
cmake ../
make

./init_usrp --ignore-server # arg to ignore the sync server, used for testing purposes
```
6. Start the server `software/rx-test/zadoff-chu/server-sync.py`. Currently, it listens to two incoming start messages (originating from the RX nodes). After reception of these two messages, it sends a SYNC signal back to the RXs.
```sh
# in a new terminal
cd software/rx-test/zadoff-chu/
./server-sync.py
```

You can now inspect the stored data via the `xcorr_files_ZC.py` file.
