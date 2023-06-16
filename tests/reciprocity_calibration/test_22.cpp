// requires to first run the script on the same machine: NI-B210-Sync/tests/reciprocity_calibration/python3 ZMQ-server.py
// it is a ZMQ server to compute the phase offsets

// requires to first run the script on the same machine: NI-B210-Sync/tests/reciprocity_calibration/python3 test_22.py
// it is a ZMQ server to compute the phase offsets


#include <zmq.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <boost/algorithm/string.hpp>
#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <thread>
#include <cmath>
#include <csignal>
#include <filesystem>
#include <climits> // for SHRT_MAX

#define FMT_HEADER_ONLY
#include <fmt/format.h>
#include <fmt/ranges.h>

namespace po = boost::program_options;


using sample_dt = short;

using sample_t = std::complex<sample_dt>;

using sample_fc32 = std::complex<float>;

zmq::context_t context(1);

// Create a publisher socket
zmq::socket_t publisher(context, zmq::socket_type::push);

zmq::socket_t socket(context, zmq::socket_type::req);

/***********************************************************************
 * Signal handlers
 **********************************************************************/
static bool stop_signal_called = false;
void sig_int_handler(int)
{
        stop_signal_called = true;
}



void ready_to_go(std::string id, std::string server_ip)
{
        // REQ RES pattern
        // let server now that you are ready and waiting for a SYNC command
        //  Socket to receive messages on
        //  Prepare our context and socket
        zmq::socket_t _socket(context, zmq::socket_type::req);

        std::cout << "Connecting to server..." << std::endl;
        _socket.connect((boost::format("tcp://%s:5556") % server_ip).str());

        zmq::message_t request(id.size());
        memcpy(request.data(), id.data(), id.size());
        std::cout << "Sending ID "
                  << id
                  << "..." << std::endl;
        _socket.send(request, zmq::send_flags::none);

        //  Get the reply.
        zmq::message_t reply;
        auto res = _socket.recv(reply, zmq::recv_flags::none);
        // std::cout << "Received: " << res << std::endl;
}

void wait_till_go_from_server(std::string server_ip)
{
        // TODO check if received message is SYNC
        //   Socket to receive messages on
        zmq::socket_t subscriber(context, ZMQ_SUB);
        subscriber.connect((boost::format("tcp://%s:5557") %server_ip).str());
        zmq_setsockopt(subscriber, ZMQ_SUBSCRIBE, "", 0);

        zmq::message_t msg;
        auto res = subscriber.recv(&msg);
        // std::string msg_str = std::string(static_cast<char *>(msg.data()), msg.size());
        // std::cout << "Received '" << msg_str << "'" << std::endl;
}

void sync(std::string serial, std::string server_ip, uhd::usrp::multi_usrp::sptr usrp)
{
                //ready_to_go(serial, server_ip);      // non-blocking
                //wait_till_go_from_server(server_ip); // blocking till SYNC message received
                // This command will be processed fairly soon after the last PPS edge:
                usrp->set_time_next_pps(uhd::time_spec_t(0.0));
                std::cout << "[SYNC] Resetting time." << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(2000));
}


void transmit_worker(size_t nsamps_per_buff, uhd::tx_streamer::sptr tx_stream,
                     size_t timeout, size_t num_channels, uhd::tx_metadata_t md, size_t num_requested_samples, sample_fc32 a)
{
        std::vector<sample_fc32 *> buffs;

        std::vector<sample_fc32> seq_ch1(nsamps_per_buff, a);
        buffs.push_back(&seq_ch1.front());

        std::vector<sample_fc32> seq_ch2(nsamps_per_buff, a);
        buffs.push_back(&seq_ch2.front());
        size_t num_total_samps = 0;

        while (num_requested_samples > num_total_samps && !stop_signal_called)  
        {
                // send a single packet
                size_t num_tx_samps = tx_stream->send(buffs, nsamps_per_buff, md, timeout);

                // do not use time spec for subsequent packets
                md.has_time_spec = false;

                if (num_tx_samps < nsamps_per_buff)
                        std::cerr << "Send timeout..." << std::endl;

                num_total_samps += num_tx_samps;
        }

        // send a mini EOB packet
        md.end_of_burst = true;
        tx_stream->send("", 0, md);

        std::cout << std::endl
                  << "Waiting for async burst ACK... " << std::flush;
        uhd::async_metadata_t async_md;
        bool got_async_burst_ack = false;
        // loop through all messages for the ACK packet (may have underflow messages in queue)
        while (not got_async_burst_ack and tx_stream->recv_async_msg(async_md, timeout))
        {
                got_async_burst_ack =
                    (async_md.event_code == uhd::async_metadata_t::EVENT_CODE_BURST_ACK);
        }
        std::cout << (got_async_burst_ack ? "success" : "fail") << std::endl;
}

void recv_to_file(std::string id, uhd::rx_streamer::sptr rx_stream,
                  size_t samps_per_buff,
                  int num_requested_samples,
                  double start_time,
                  std::vector<size_t> rx_channel_nums)
{
        int num_total_samps = 0;
        

        // Prepare buffers for received samples and metadata
        uhd::rx_metadata_t md;
        std::vector<std::vector<sample_t>> buffs(
            rx_channel_nums.size(), std::vector<sample_t>(samps_per_buff));
        // create a vector of pointers to point to each of the channel buffers
        std::vector<sample_t *> buff_ptrs;
        for (size_t i = 0; i < buffs.size(); i++)
        {
                buff_ptrs.push_back(&buffs[i].front());
        }

        // Create one ofstream object per channel
        // (use shared_ptr because ofstream is non-copyable)
        // std::vector<std::shared_ptr<std::ofstream>> outfiles;
        // for (size_t i = 0; i < buffs.size(); i++)
        // {
        //         const std::string this_filename = str(boost::format("out-%02d-%s.dat") % i % id);
        //         outfiles.push_back(std::shared_ptr<std::ofstream>(
        //             new std::ofstream(this_filename.c_str(), std::ofstream::binary)));
        // }
        // UHD_ASSERT_THROW(outfiles.size() == buffs.size());
        UHD_ASSERT_THROW(buffs.size() == rx_channel_nums.size());
        bool overflow_message = true;
        // We increase the first timeout to cover for the delay between now + the
        // command time, plus 500ms of buffer. In the loop, we will then reduce the
        // timeout for subsequent receives.
        double timeout = start_time + 0.5f;

        // setup streaming
        uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
        stream_cmd.num_samps = num_requested_samples;
        stream_cmd.stream_now = false;
        stream_cmd.time_spec = uhd::time_spec_t(start_time);
        rx_stream->issue_stream_cmd(stream_cmd);

        while (not stop_signal_called and (num_requested_samples > num_total_samps or num_requested_samples == 0))
        {
                size_t num_rx_samps = rx_stream->recv(buff_ptrs, samps_per_buff, md, timeout);
                timeout = 0.1f; // small timeout for subsequent recv

                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT)
                {
                        std::cout << "Timeout while streaming" << std::endl;
                        break;
                }
                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW)
                {
                        if (overflow_message)
                        {
                                overflow_message = false;
                                std::cerr
                                    << boost::format(
                                           "Got an overflow indication. Please consider the following:\n"
                                           "  Your write medium must sustain a rate of %fMB/s.\n"
                                           "  Dropped samples will not be written to the file.\n"
                                           "  Please modify this example for your purposes.\n"
                                           "  This message will not appear again.\n") %
                                           (250e3 * sizeof(sample_t) / 1e6);
                        }
                        continue;
                }
                if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE)
                {
                        throw std::runtime_error("Receiver error " + md.strerror());
                }

                num_total_samps += num_rx_samps;

                unsigned int num_bytes = num_rx_samps * sizeof(sample_t);
                zmq::message_t message(num_bytes);
                std::memcpy(message.data(), (const char *)buff_ptrs[0], num_bytes);

                publisher.send(message);

                // for (size_t i = 0; i < outfiles.size(); i++)
                // {
                //     outfiles[i]->write(
                //         (const char *)buff_ptrs[i], num_rx_samps * sizeof(sample_t));
                // }
        }

        // Shut down receiver
        stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
        rx_stream->issue_stream_cmd(stream_cmd);

        // Close files
        // for (size_t i = 0; i < outfiles.size(); i++)
        // {
        //         outfiles[i]->close();
        // }
}

sample_fc32 start_cal(std::string id_cal, std::string serial, std::string server_ip, uhd::usrp::multi_usrp::sptr usrp, size_t num_channels, uhd::tx_streamer::sptr tx_stream, uhd::rx_streamer::sptr rx_stream, std::string otw, std::vector<size_t> rx_channel_nums, double rate, sample_fc32 bb_correction = sample_fc32(0.8))
{
        sync(serial, server_ip, usrp); // first sync to get absolute time=0
        uhd::tx_metadata_t md;
        md.start_of_burst = false;
        md.end_of_burst = false;
        md.has_time_spec = true;

        time_t cmd_time = 3.0;
        md.time_spec = uhd::time_spec_t(cmd_time);

        size_t num_requested_samples = rate * 1;

        double timeout = cmd_time + 1.0f;

        uhd::time_spec_t tx_starts_in = uhd::time_spec_t(cmd_time) - usrp->get_time_now();

        std::cout << "Tx starting in " << tx_starts_in.get_full_secs() << " seconds" << std::endl;

        size_t spb = tx_stream->get_max_num_samps();
        std::cout << "nsamps_per_buff: " << spb << std::endl;

        // start transmit worker thread
        std::thread transmit_thread([&]()
                                    { transmit_worker(spb, tx_stream, timeout, num_channels, md, num_requested_samples, bb_correction); });

        

        recv_to_file(id_cal, rx_stream, spb, num_requested_samples, cmd_time, rx_channel_nums);

        transmit_thread.join();

        // get calbration phase
        std::cout << "Connecting to receiver ..." << std::endl;
        socket.connect("tcp://localhost:5000");

        std::string id = "hello";

        zmq::message_t request(id.size());
        memcpy(request.data(), id.data(), id.size());
        std::cout << "Sending message " << id << "..." << std::endl;
        socket.send(request, zmq::send_flags::none);

        //  Get the reply.
        zmq::message_t reply;
        auto res = socket.recv(reply, zmq::recv_flags::none);
        std::string rpl = std::string(static_cast<char *>(reply.data()), reply.size());
        std::cout << rpl << std::endl;

        float phase_diff = std::stof(rpl);

        return std::polar<float>(0.8, -phase_diff);
}
int UHD_SAFE_MAIN(int argc, char *argv[])
{

        // transmit variables to be set by po
        std::string tx_args, wave_type, tx_ant, tx_subdev, ref, otw, tx_channels;
        double tx_rate, tx_freq, tx_gain, wave_freq, tx_bw;
        float ampl;

        // receive variables to be set by po
        std::string rx_args, file, type, rx_ant, rx_subdev, rx_channels;
        size_t total_num_samps, spb;
        double rx_rate, rx_freq, rx_gain, rx_bw;
        double settling;

        bool ignore_sync;
        std::string server_ip;

        // setup the program options
        po::options_description desc("Allowed options");
        // clang-format off
    desc.add_options()
        ("help", "help message")
        ("tx-args", po::value<std::string>(&tx_args)->default_value(""), "uhd transmit device address args")
        ("rx-args", po::value<std::string>(&rx_args)->default_value(""), "uhd receive device address args")
        ("file", po::value<std::string>(&file)->default_value("usrp_samples.dat"), "name of the file to write binary samples to")
        ("type", po::value<std::string>(&type)->default_value("short"), "sample type in file: double, float, or short")
        ("nsamps", po::value<size_t>(&total_num_samps)->default_value(0), "total number of samples to receive")
        ("settling", po::value<double>(&settling)->default_value(double(0.2)), "settling time (seconds) before receiving")
        ("spb", po::value<size_t>(&spb)->default_value(0), "samples per buffer, 0 for default")
        ("tx-rate", po::value<double>(&tx_rate), "rate of transmit outgoing samples")
        ("rx-rate", po::value<double>(&rx_rate), "rate of receive incoming samples")
        ("tx-freq", po::value<double>(&tx_freq), "transmit RF center frequency in Hz")
        ("rx-freq", po::value<double>(&rx_freq), "receive RF center frequency in Hz")
        ("ampl", po::value<float>(&ampl)->default_value(float(0.3)), "amplitude of the waveform [0 to 0.7]")
        ("tx-gain", po::value<double>(&tx_gain), "gain for the transmit RF chain")
        ("rx-gain", po::value<double>(&rx_gain), "gain for the receive RF chain")
        ("tx-ant", po::value<std::string>(&tx_ant), "transmit antenna selection")
        ("rx-ant", po::value<std::string>(&rx_ant), "receive antenna selection")
        ("tx-subdev", po::value<std::string>(&tx_subdev), "transmit subdevice specification")
        ("rx-subdev", po::value<std::string>(&rx_subdev), "receive subdevice specification")
        ("tx-bw", po::value<double>(&tx_bw), "analog transmit filter bandwidth in Hz")
        ("rx-bw", po::value<double>(&rx_bw), "analog receive filter bandwidth in Hz")
        ("ref", po::value<std::string>(&ref), "reference source (internal, external, gpsdo, mimo)")
        ("otw", po::value<std::string>(&otw)->default_value("sc16"), "specify the over-the-wire sample mode")
        ("tx-channels", po::value<std::string>(&tx_channels)->default_value("0"), "which TX channel(s) to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("rx-channels", po::value<std::string>(&rx_channels)->default_value("0"), "which RX channel(s) to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("tx-int-n", "tune USRP TX with integer-N tuning")
        ("rx-int-n", "tune USRP RX with integer-N tuning")
        ("ignore-server", po::bool_switch(&ignore_sync), "Discard waiting till SYNC server")
        ("server-ip", po::value<std::string>(&server_ip), "Server local IP address")
    ;
        // clang-format on
        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);

        // print the help message
        if (vm.count("help"))
        {
                std::cout << "UHD TXRX Loopback to File " << desc << std::endl;
                return ~0;
        }

        rx_freq = tx_freq;
        rx_rate = tx_rate;

        publisher.bind("tcp://*:5555");

                // create a usrp device
        std::cout << std::endl;
        std::cout << "Creating the usrp device in integer mode args..." << std::endl;
        uhd::usrp::multi_usrp::sptr usrp = uhd::usrp::multi_usrp::make(uhd::device_addr_t("mode_n=integer"));
        std::cout << std::endl;


        // detect which channels to use
        std::vector<std::string> tx_channel_strings;
        std::vector<size_t> tx_channel_nums;
        boost::split(tx_channel_strings, tx_channels, boost::is_any_of("\"',"));
        for (size_t ch = 0; ch < tx_channel_strings.size(); ch++)
        {
                size_t chan = std::stoi(tx_channel_strings[ch]);
                if (chan >= usrp->get_tx_num_channels())
                {
                        throw std::runtime_error("Invalid TX channel(s) specified.");
                }
                else
                        tx_channel_nums.push_back(std::stoi(tx_channel_strings[ch]));
        }
        std::vector<std::string> rx_channel_strings;
        std::vector<size_t> rx_channel_nums;
        boost::split(rx_channel_strings, rx_channels, boost::is_any_of("\"',"));
        for (size_t ch = 0; ch < rx_channel_strings.size(); ch++)
        {
                size_t chan = std::stoi(rx_channel_strings[ch]);
                if (chan >= usrp->get_rx_num_channels())
                {
                        throw std::runtime_error("Invalid RX channel(s) specified.");
                }
                else
                        rx_channel_nums.push_back(std::stoi(rx_channel_strings[ch]));
        }

        // initialise
        std::cout << "Setting up PPS + 10MHz" << std::endl;
        usrp->set_clock_source("external");
        usrp->set_time_source("external");

        std::cout << "Using USRP Device: " << usrp->get_pp_string() << std::endl;


        std::map<std::string, std::string> m = usrp->get_usrp_rx_info();

        std::string serial = m["mboard_serial"];

        

        // set the transmit sample rate
        if (not vm.count("tx-rate"))
        {
                std::cerr << "Please specify the transmit sample rate with --tx-rate"
                          << std::endl;
                return ~0;
        }
        std::cout << boost::format("Setting TX Rate: %f Msps...") % (tx_rate / 1e6)
                  << std::endl;
        usrp->set_tx_rate(tx_rate);
        std::cout << boost::format("Actual TX Rate: %f Msps...") % (usrp->get_tx_rate() / 1e6)
                  << std::endl
                  << std::endl;

        std::cout << boost::format("Setting RX Rate: %f Msps...") % (rx_rate / 1e6)
                  << std::endl;
        usrp->set_rx_rate(rx_rate);
        std::cout << boost::format("Actual RX Rate: %f Msps...") % (usrp->get_rx_rate() / 1e6)
                  << std::endl
                  << std::endl;

        for (size_t ch = 0; ch < tx_channel_nums.size(); ch++)
        {
                size_t channel = tx_channel_nums[ch];
                if (tx_channel_nums.size() > 1)
                {
                        std::cout << "Configuring TX Channel " << channel << std::endl;
                }
                std::cout << boost::format("Setting TX Freq: %f MHz...") % (tx_freq / 1e6)
                          << std::endl;
                uhd::tune_request_t tx_tune_request(tx_freq);
                if (vm.count("tx-int-n"))
                        tx_tune_request.args = uhd::device_addr_t("mode_n=integer");
                usrp->set_tx_freq(tx_tune_request, channel);
                std::cout << boost::format("Actual TX Freq: %f MHz...") % (usrp->get_tx_freq(channel) / 1e6)
                          << std::endl
                          << std::endl;

                // set the rf gain
                if (vm.count("tx-gain"))
                {
                        std::cout << boost::format("Setting TX Gain: %f norm ...") % tx_gain
                                  << std::endl;
                        usrp->set_normalized_tx_gain(tx_gain, channel);
                        std::cout << boost::format("Actual TX Gain: %f dB...") % usrp->get_tx_gain(channel)
                                  << std::endl
                                  << std::endl;
                }

                // set the analog frontend filter bandwidth
                if (vm.count("tx-bw"))
                {
                        std::cout << boost::format("Setting TX Bandwidth: %f MHz...") % tx_bw
                                  << std::endl;
                        usrp->set_tx_bandwidth(tx_bw, channel);
                        std::cout << boost::format("Actual TX Bandwidth: %f MHz...") % usrp->get_tx_bandwidth(channel)
                                  << std::endl
                                  << std::endl;
                }

                // set the antenna
                if (vm.count("tx-ant"))
                        usrp->set_tx_antenna(tx_ant, channel);
        }

        for (size_t ch = 0; ch < rx_channel_nums.size(); ch++)
        {
                size_t channel = rx_channel_nums[ch];
                if (rx_channel_nums.size() > 1)
                {
                        std::cout << "Configuring RX Channel " << channel << std::endl;
                }

                std::cout << boost::format("Setting RX Freq: %f MHz...") % (rx_freq / 1e6)
                          << std::endl;
                uhd::tune_request_t rx_tune_request(rx_freq);
                if (vm.count("rx-int-n"))
                        rx_tune_request.args = uhd::device_addr_t("mode_n=integer");
                usrp->set_rx_freq(rx_tune_request, channel);
                std::cout << boost::format("Actual RX Freq: %f MHz...") % (usrp->get_rx_freq(channel) / 1e6)
                          << std::endl
                          << std::endl;

                // set the receive rf gain
                if (vm.count("rx-gain"))
                {
                        std::cout << boost::format("Setting RX Gain: %f dB...") % rx_gain
                                  << std::endl;
                        usrp->set_rx_gain(rx_gain, channel);
                        std::cout << boost::format("Actual RX Gain: %f dB...") % usrp->get_rx_gain(channel)
                                  << std::endl
                                  << std::endl;
                }

                // set the receive analog frontend filter bandwidth
                if (vm.count("rx-bw"))
                {
                        std::cout << boost::format("Setting RX Bandwidth: %f MHz...") % (rx_bw / 1e6)
                                  << std::endl;
                        usrp->set_rx_bandwidth(rx_bw, channel);
                        std::cout << boost::format("Actual RX Bandwidth: %f MHz...") % (usrp->get_rx_bandwidth(channel) / 1e6)
                                  << std::endl
                                  << std::endl;
                }

                // set the receive antenna
                if (vm.count("rx-ant"))
                        usrp->set_rx_antenna(rx_ant, channel);
        }

        // create a transmit streamer
        // linearly map channels (index0 = channel0, index1 = channel1, ...)
        uhd::stream_args_t stream_args("fc32", otw);
        stream_args.channels = tx_channel_nums;
        uhd::tx_streamer::sptr tx_stream = usrp->get_tx_stream(stream_args);

        int num_channels = tx_channel_nums.size();

        // create a receive streamer
        uhd::stream_args_t rx_stream_args("sc16", otw);
        rx_stream_args.channels = rx_channel_nums;
        uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(rx_stream_args);

        // Check Ref and LO Lock detect
        std::vector<std::string> tx_sensor_names, rx_sensor_names;
        tx_sensor_names = usrp->get_tx_sensor_names(0);
        if (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "lo_locked") != tx_sensor_names.end())
        {
                uhd::sensor_value_t lo_locked = usrp->get_tx_sensor("lo_locked", 0);
                std::cout << boost::format("Checking TX: %s ...") % lo_locked.to_pp_string()
                          << std::endl;
                UHD_ASSERT_THROW(lo_locked.to_bool());
        }
        rx_sensor_names = usrp->get_rx_sensor_names(0);
        if (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "lo_locked") != rx_sensor_names.end())
        {
                uhd::sensor_value_t lo_locked = usrp->get_rx_sensor("lo_locked", 0);
                std::cout << boost::format("Checking RX: %s ...") % lo_locked.to_pp_string()
                          << std::endl;
                UHD_ASSERT_THROW(lo_locked.to_bool());
        }

        tx_sensor_names = usrp->get_mboard_sensor_names(0);
        if ((ref == "mimo") and (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "mimo_locked") != tx_sensor_names.end()))
        {
                uhd::sensor_value_t mimo_locked = usrp->get_mboard_sensor("mimo_locked", 0);
                std::cout << boost::format("Checking TX: %s ...") % mimo_locked.to_pp_string()
                          << std::endl;
                UHD_ASSERT_THROW(mimo_locked.to_bool());
        }
        if ((ref == "external") and (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "ref_locked") != tx_sensor_names.end()))
        {
                uhd::sensor_value_t ref_locked = usrp->get_mboard_sensor("ref_locked", 0);
                std::cout << boost::format("Checking TX: %s ...") % ref_locked.to_pp_string()
                          << std::endl;
                UHD_ASSERT_THROW(ref_locked.to_bool());
        }

        rx_sensor_names = usrp->get_mboard_sensor_names(0);
        if ((ref == "mimo") and (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "mimo_locked") != rx_sensor_names.end()))
        {
                uhd::sensor_value_t mimo_locked = usrp->get_mboard_sensor("mimo_locked", 0);
                std::cout << boost::format("Checking RX: %s ...") % mimo_locked.to_pp_string()
                          << std::endl;
                UHD_ASSERT_THROW(mimo_locked.to_bool());
        }
        if ((ref == "external") and (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "ref_locked") != rx_sensor_names.end()))
        {
                uhd::sensor_value_t ref_locked = usrp->get_mboard_sensor("ref_locked", 0);
                std::cout << boost::format("Checking RX: %s ...") % ref_locked.to_pp_string()
                          << std::endl;
                UHD_ASSERT_THROW(ref_locked.to_bool());
        }

        if (total_num_samps == 0)
        {
                std::signal(SIGINT, &sig_int_handler);
                std::cout << "Press Ctrl + C to stop streaming..." << std::endl;
        }

        /********************************************/
        /**************** start tuning **************/
        /********************************************/

        while (!stop_signal_called){
                sample_fc32 a = start_cal("0", serial, server_ip, usrp, num_channels, tx_stream, rx_stream, otw, rx_channel_nums, tx_rate);

                sample_fc32 b = start_cal("1", serial, server_ip, usrp, num_channels, tx_stream, rx_stream, otw, rx_channel_nums, tx_rate, a);

                rx_stream = usrp->get_rx_stream(rx_stream_args);
        }

        // b should be now close to zero

        //std::this_thread::sleep_for(std::chrono::milliseconds(2000));

        // finished
        std::cout
            << std::endl
            << "Done!" << std::endl
            << std::endl;

        return EXIT_SUCCESS;
}

