# Methods to synchronise NI B210s for MIMO operation

## Relevant sources
- [Synchronizing multiple AD9361 devices](https://wiki.analog.com/resources/eval/user-guides/ad-fmcomms5-ebz/multi-chip-sync?force_rev=1)
- [AD9361 Register Map Reference Manual](https://usermanual.wiki/Document/AD9361RegisterMapReferenceManualUG671.1082447504)
- [Schematic B210](https://files.ettus.com/schematics/b200/b210.pdf)
- [Ettus Research USRP FPGA HDL Source](https://github.com/EttusResearch/fpga)
- [AD community question related to phase diff](https://ez.analog.com/wide-band-rf-transceivers/design-support/f/q-a/543540/phase-difference-in-ad9361-multichip-synchronization)
- [Fractional/Integer-N PLL Basics](https://www.ti.com/lit/an/swra029/swra029.pdf)
- [FMComms5 Phase Synchronization](https://wiki.analog.com/resources/eval/user-guides/ad-fmcomms5-ebz/phase-sync)
- [Phase Difference in AD9361 Multichip Synchronization](https://ez.analog.com/wide-band-rf-transceivers/design-support/f/q-a/543540/phase-difference-in-ad9361-multichip-synchronization)
- [UHD Device synchronisation](https://files.ettus.com/manual/page_sync.html)
- [Timed commands in UHD](https://kb.ettus.com/index.php?title=Synchronizing_USRP_Events_Using_Timed_Commands_in_UHD)

## What needs to be synchronised for MIMO applications

At the RF transceiver:
- ADC/DAC sample clock
- RF mixer 
- Baseband digital clocks

At the FPGA:
- DSP (CORDICs)

Between FPGA and host:
- USB (to be checked)

At the host:


## Maintaining phase coherency at different PLLs

From [ref](https://ez.analog.com/cfs-file/__key/telligent-evolution-components-attachments/00-333-01-00-00-24-69-46/attachment.pdf):
Phase coherence is defined as the state in which two signals maintain a fixed phase relationship
between each other and is typically required for evaluating the performance of phased-array antennas
as well as for test and measurement equipment.
For integer-N PLLs, it is relatively straightforward to achieve phase coherence between multiple PLLs
by using the same reference for each PLL and updating each device at the same time to ensure the
PLL counters are aligned. This is often achieved by updating the PLL register contents with the new
frequency word while holding the device in reset. To ensure both parts get updated at the same time,
the reset signal is made common and so is cleared internally in the PLLs at exactly the same time.
This ensures the internal dividers in the PLL start counting from the same start-point. See here for a
good reference on achieving integer-N PLL phase coherence using this method. If the output
frequencies on both parts are updated at the same time then the consistent output phase will be
maintained between the multiple PLLs. To achieve absolute phase consistency with respect to the
reference input requires you to update the PLLs at a rate equal to an integer multiple of N-divide (PLL
feedback divider) times REFIN cycles. This would mean the reset signal would need to be
synchronized with the reference and a count done internally in a microcontroller to keep
synchronization. In many cases the absolute phase consistency is not required just that the relative
phase between the PLL outputs is kept constant. In this case LE can be asynchronous to the reference
input.

## B210

Sync input:
- pulse per second input: PPS_IN_EXT (see schematic)
- 20MHz reference input (as no GPS option to our B210): REFIN (see schematic)

The REFIN is connected to the [ADF4001](https://www.analog.com/en/products/adf4001.html) (200MHz Clock Generator PLL) which generates vcxo_tune which is connected to Voltage Controlled Temperature Compensated Crystal Oscillator (VCTCXO), which is than connected to a fan-out buffer to distribute it to xo_out (going to the AD9361) and xo_to_pll (to PLL RF in).

PPS_IN_EXT is connected to the Spartan6 IO_L34P_GCLK19_0.

PLL bring-up:
1. VCTCXO starts up
2. FX3 brings up transceiver, sets CLKOUT to FPGA
3. FX3 programs FPGA
4. FPGA writes to PLL, initializes PLL
5. PLL locks to external ref if avail.
6. If no ref, PLL tristated via SPI

![clock connections](images/clock-connections-fpga.png)

## AD9361 - RF transceiver

### XTALN
The on-board 40MHz clock signal generated from the [ADF4001](https://www.analog.com/en/products/adf4001.html) is coherent:

![scope-40MHz-XTALN](images/scope-40MHz-input-XTALN.png)

### Synchronise ADC/DAC clocks
The ADC and DAC clocks can not be perfectly synchronised due to the divider, both clocks are derived from the same BBPLL.

$$ADC_{rate} = BBPLL_{rate} / 2^{div}$$

witd $div$ between 1 through 6. The value for $div$ is [determined so the the VCO rate is between 672MHz and 1430MHz](https://github.com/EttusResearch/uhd/blob/197cdc4f665cbd4e6394a7eeb44b405f67ab10b1/host/lib/usrp/common/ad9361_driver/ad9361_device.cpp#L1202).

![AD9361](images/ad9361.svg)

The device utilizes a fractional-N synthesizer in the baseband PLL block to generate the desired sample rate for a given system. This synthesizer generates the ADC sample clock, DAC sample clock, and baseband digital clocks from any reference clock in the frequency range specified for the reference clock input.


## Sync BBPLLs and Digital CLK [AD9361 Register Map Reference Manual](https://usermanual.wiki/Document/AD9361RegisterMapReferenceManualUG671.1082447504)
  - SPI Register 0x001—Multichip Sync and Tx Monitor Control
  - D2—MCS BBPLL EnableTo synchronize the BBPLLs of multiple devices, write this bit high and then provide a sync pulse to SYNC_IN.
  - D1—MCS Digital CLK Enable To synchronize the digital clocks of multiple AD9361 devices, first synchronize the BBPLLs, then write this bit high and provide a sync pulse to the `SYNC_IN` pin. 
  - D0—MCS BB Enable Setting this bit enables the capability of baseband multichip digital synchronization. See also 0x001[D2:D1]. 


### Clock input options (from AD9361 datasheet)
The AD9361 operates using a reference clock that can be provided
by two different sources. The first option is to use a dedicated
crystal with a frequency between 19 MHz and 50 MHz connected
between the XTALP and XTALN pins. The second option is to
connect an external oscillator or clock distribution device (such as
the AD9548) to the XTALN pin (with the XTALP pin remaining
unconnected). If an external oscillator is used, the frequency
can vary between 10 MHz and 80 MHz. This reference clock
is used to supply the synthesizer blocks that generate all data
clocks, sample clocks, and local oscillators inside the device.
Errors in the crystal frequency can be removed by using the
digitally programmable digitally controlled crystal oscillator
(DCXO) function to adjust the on-chip variable capacitor. This
capacitor can tune the crystal frequency variance out of the
system, resulting in a more accurate reference clock from which
all other frequency signals are generated. This function can also
be used with on-chip temperature sensing to provide oscillator
frequency temperature compensation during normal operation.

### RF PLLs (from AD9361 datasheet)
The AD9361 contains two identical synthesizers to generate the
required LO signals for the RF signal paths:—one for the receiver
and one for the transmitter. Phase-locked loop (PLL) synthesizers
are fractional-N designs incorporating completely integrated
voltage controlled oscillators (VCOs) and loop filters. In TDD
operation, the synthesizers turn on and off as appropriate for the
RX and TX frames. In FDD mode, the TX PLL and the RX PLL
can be activated simultaneously. These PLLs require no external
components

### BB PLL (from AD9361 datasheet)
The AD9361 also contains a baseband PLL synthesizer that is
used to generate all baseband related clock signals. These include
the ADC and DAC sampling clocks, the DATA_CLK signal (see
the Digital Data Interface section), and all data framing signals.
This PLL is programmed from 700 MHz to 1400 MHz based on
the data rate and sample rate requirements of the system. 


## FPGA

From [here](https://www.ni.com/nl-nl/shop/wireless-design-test/what-is-a-usrp-software-defined-radio/global-synchronization-and-clock-disciplining-with-ni-usrp-293x-.html):
- The USRP hardware OSP interpolates and up-converts the synthesized signals to 400 MS/s using a digital up conversion process, and uses the CORDIC algorithm to apply minor frequency offset corrections to achieve the requested RF center frequency. 
- The digitized I and Q data flow through parallel onboard signal processing (OSP) processes that applies DC offset correction and digital down conversion using the CORDIC algorithm.

[How to sync the CORDICs](https://files.ettus.com/manual/page_sync.html)


## UHD and GNURadio

There are four key elements required for phase coherent operation of resync-capable USRPs:

1. All USRPs share a common reference clock (10MHz Ref)
2. All USRPs share a common sense of time (PPS)
3. LO and DSP tuning is synchronous
4. Streaming is started synchronously

### Enable external PPS and 10MHz
```cpp
usrp->set_clock_source("external");
usrp->set_time_source("external");
```

### Defining a common absolute reference clock
The time can be 're'-set once a new PPS has occured:
```cpp
const uhd::time_spec_t last_pps_time = usrp->get_time_last_pps();
while (last_pps_time == usrp->get_time_last_pps()){
    //sleep 100 milliseconds (give or take)
}
// This command will be processed fairly soon after the last PPS edge:
usrp->set_time_next_pps(uhd::time_spec_t(0.0));

std::this_thread::sleep_for(std::chrono::milliseconds(1000));
```
After we reset the USRP's sense of time, we wait 1 second to ensure a PPS rising edge occurs and latches the 0.000s value to both USRPs. At this point, both USRPs should have a shared sense of time.  We've now satisfied the first and second requirements for phase coherent USRP operation. 

**TODO**: Send a command from the server to the RPIs to start resetting their time reference on next PPS. Or only start transmitting PPS signals from the octoclocks once all devices are operational (not sure the latter is supported by the Octoclock). 


### Timed commands for predicatable and repeatable phase offsets
```cp
usrp->clear_command_time();

usrp->set_command_time(usrp->get_time_now() + uhd::time_spec_t(0.1)); //set cmd time for .1s in the future

uhd::tune_request_t tune_request(freq);
usrp->set_rx_freq(tune_request);
std::this_thread::sleep_for(std::chrono::milliseconds(110)); //sleep 110ms (~10ms after retune occurs) to allow LO to lock

usrp->clear_command_time();
```
With the above code block, we are able to set a command time equal to the current time + 0.1s. Any commands that are called after `set_command_time()` will be sent to the USRP with a timestamp corresponding to the argument passed to `set_command_time()`. Because of this timestamp, the USRP will wait until the command time passes to execute the tune request. This will ensure that the LO and DSP chain of our USRPs are retuned synchronously (on the same clock cycle), satisfying the third requirement for phase coherent operation, i.e., LO and DSP tuning is synchronous.

Modern USRPs pass packets using the CHDR protocol. These packets can be used to issue commands to the USRP and may have an associated timestamp. A command with an included timestamp is called a timed command and it's important to understand how the USRP handles these timed commands. All blocks in a USRP's FPGA have a command queue and maintain a sense of time, however the Radio Core has the unique ability to store an absolute sense of time known as the vita_time. When timed commands are issued to the USRP, they are added to a command FIFO of finite depth and are executed when the timestamp in the header of the command packet is >= the RFNoC block's sense of time. Utilizing these timed commands correctly allows for various USRP functionality to be executed with nanosecond precision, enabling time and phase coherent operation across multiple devices.


#### Command Queue
As commands are passed from host to USRP, they are added to a FIFO on the USRP's FPGA. This FIFO is called the command queue and all commands that are sent to the USRP must pass through a command queue. Each block in the FPGA that handles data also has its own command queue. The command queue FIFO is not to be confused with the data FIFOs used to buffer data between blocks (pictured in Figure 3).

Every command queue maintains a sense of time. The mechanism for acquiring this sense of time is different between the Radio Core and other IP cores (including custom RFNoC blocks) and will be explored later in this application note. When commands enter the command queue, their timestamp is compared against the command queue's sense of time and the commands are executed when Queue Time >= Command Time. Commands without timestamps are executed immediately when they're at the front of the queue. Command queues in the USRP do not support on-the-fly reordering, meaning a command at the front of the queue will block subsequent commands from executing even if their timestamp has passed.

Every IP core on a USRP, including the Radio Core, DDC, DUC, and custom blocks, includes one command queue per data stream (certain blocks are designed to pass multiple data streams). The depth of this command queue varies from device to device is determined at FPGA compilation time based on user settings and available resources. An overflow of the command queue will result in a system halt and often requires a physical reset of the FPGA.

The B210 (Xilinx Spartan 6 XC6SLX150) has by default a depth of 8 (radio core) and 5 (IP cores).


### Phase-aligned DSP
In order to achieve phase alignment between USRP devices, the CORDICS in both devices must be aligned with respect to each other. This is easily achieved by issuing stream commands with a time spec property, which instructs the streaming to begin at a specified time. Since the devices are already synchronized via the 10 MHz and PPS inputs, the streaming will start at exactly the same time on both devices. The CORDICs are reset at each start-of-burst command, so users should ensure that every start-of-burst also has a time spec set.

#### Receive example

##### One burst
```cpp
uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE); 
stream_cmd.num_samps = samps_to_recv;
stream_cmd.stream_now = false;
stream_cmd.time_spec = uhd::time_spec_t(usrp->get_time_now() + uhd::time_spec_t(1.0));
usrp->issue_stream_cmd(stream_cmd);
```

##### Streaming
```cpp
// create a receive streamer
uhd::stream_args_t stream_args("fc32", wire); // complex floats
stream_args.channels             = "0,1,2,3";
uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

// setup streaming
uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS);
stream_cmd.stream_now = false;
stream_cmd.time_spec  = uhd::time_spec_t(usrp->get_time_now() + uhd::time_spec_t(1.0));
rx_stream->issue_stream_cmd(stream_cmd);
```

Our system will begin to stream data 1s after the time returned by usrp->get_time_now(). Data sent to the host will be phase coherent between the 4 RX channels in this system. 
**TODO**: Check if the signal maintains a known phase relationship between both i) the channels and ii) the devices, across runs of code and system power cycles.


#### Transmit example
```cpp
uhd::tx_metadata_t md; //the metadata incl. the time spec
md.start_of_burst = true;
md.end_of_burst = false;
md.has_time_spec = true;
md.time_spec = time_to_send;
//send a single packet
size_t num_tx_samps = tx_streamer->send(buffs, samps_to_send, md);
```


