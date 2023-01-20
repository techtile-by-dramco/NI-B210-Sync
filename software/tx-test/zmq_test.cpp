#include <zmq.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <thread>

namespace po = boost::program_options;

zmq::context_t context(1);

static const size_t wave_table_len = 8192;
std::vector<std::complex<float>> _wave_table(wave_table_len, {0.0, 0.0});

/***********************************************************************
 * Signal handlers
 **********************************************************************/
static bool stop_signal_called = false;
void sig_int_handler(int)
{
    stop_signal_called = true;
}



void ready_to_go(std::string id)
{
        // REQ RES pattern
        // let server now that you are ready and waiting for a SYNC command
        //  Socket to receive messages on
        //  Prepare our context and socket
        zmq::socket_t socket(context, zmq::socket_type::req);

        std::cout << "Connecting to server..." << std::endl;
        socket.connect("tcp://localhost:5555");

        zmq::message_t request(id.size());
        memcpy(request.data(), id.data(), id.size());
        std::cout << "Sending ID "
                  << id
                  << "..." << std::endl;
        socket.send(request, zmq::send_flags::none);

        //  Get the reply.
        zmq::message_t reply;
        auto res = socket.recv(reply, zmq::recv_flags::none);
        // std::cout << "Received: " << res << std::endl;
}

void wait_till_go_from_server(void)
{
        // TODO check if received message is SYNC
        //   Socket to receive messages on
        zmq::socket_t subscriber(context, ZMQ_SUB);
        subscriber.connect("tcp://localhost:5557");
        zmq_setsockopt(subscriber, ZMQ_SUBSCRIBE, "", 0);

        zmq::message_t msg;
        auto res = subscriber.recv(&msg);
        // std::string msg_str = std::string(static_cast<char *>(msg.data()), msg.size());
        // std::cout << "Received '" << msg_str << "'" << std::endl;
}

int UHD_SAFE_MAIN(int argc, char *argv[])
{

        std::string str_args;
        std::string port;
        bool ignore_sync = false;



        po::options_description desc("Allowed options");
        desc.add_options()("help", "produce help message")
        ("args", po::value<std::string>(&str_args)->default_value("type=b200,mode_n=integer"), "give device arguments here")
        ("iq_port", po::value<std::string>(&port)->default_value("8888"), "Port to stream IQ samples to")
        ("ignore-server", po::bool_switch(&ignore_sync), "Discard waiting till SYNC server");

        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);

        if (vm.count("help"))
        {
                std::cout << desc << "\n";
                return 0;
        }

        uhd::device_addr_t args(str_args);
        uhd::usrp::multi_usrp::sptr usrp = uhd::usrp::multi_usrp::make(args);
        // std::cout << "Hello World"
        //           << std::endl;

        // // set up some catch-all masks
        uint32_t gpio_line = 0xF; // only the bottom 4 lines: 0xF = 00001111 = Pin 0, 1, 2, 3
        uint32_t all_one = 0xFF;
        uint32_t all_zero = 0x00;

        // // set gpio pins up for output
        std::cout << "Setting up GPIO" << std::endl;
        usrp->set_gpio_attr("FP0", "DDR", all_one, gpio_line, 0);
        usrp->set_gpio_attr("FP0", "CTRL", all_zero, gpio_line, 0);
        usrp->set_gpio_attr("FP0", "OUT", all_zero, gpio_line, 0); // reset LOW (async)

        // initialise
        std::cout << "Setting up PPS + 10MHz" << std::endl;
        usrp->set_clock_source("external");
        usrp->set_time_source("external");

        std::map<std::string, std::string> m = usrp->get_usrp_rx_info();

        std::string serial = m["mboard_serial"];

        std::cout << "Serial number: " << serial << std::endl;

        uhd::stream_args_t stream_args("fc32"); // complex shorts (uint16_t)
        stream_args.channels = {0,1};
        uhd::tx_streamer::sptr tx_stream = usrp->get_tx_stream(stream_args);
                // TX waveform I=1 Q=0 -> just the carrier

        // allocate buffer with data to send
        const size_t spb = tx_stream->get_max_num_samps();

        std::vector<std::complex<float>> buff(spb, std::complex<float>(0.5, 0.0));
        std::vector<std::complex<float>*> buffs(channel_nums.size(), &buff.front());


        size_t channel_nums = tx_stream->get_num_channels();
         // allocate a buffer which we re-use for each channel
        size_t spb = tx_stream->get_max_num_samps() * 10;
        std::vector<std::complex<float>> buff(spb);
        std::vector<std::complex<float>*> buffs(channel_nums.size(), &buff.front());

        // just check if we indeed have a PPS signal present
        /*
        const uhd::time_spec_t last_pps_time = usrp->get_time_last_pps();
        while (last_pps_time == usrp->get_time_last_pps())
        {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }*/


        if (!ignore_sync)
        {
                ready_to_go(serial);        // non-blocking
                wait_till_go_from_server(); // blocking till SYNC message received
        }else{
                std::cout << "Ignoring waiting for server" << std::endl;
        }

        // This command will be processed fairly soon after the last PPS edge:
        usrp->set_time_next_pps(uhd::time_spec_t(0.0));
        std::cout << "[SYNC] Resetting time." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(2000));

        

        /********************************************/
        /**************** start tuning **************/
        /********************************************/

        time_t cmd_time = 5.0;

        usrp->set_tx_gain(0.7);

        usrp->clear_command_time();
        double rate = 100e3;
        // set the rx sample rate
        std::cout << boost::format("Setting TX Rate: %f Msps...") % (rate / 1e6) << std::endl;
        cmd_time += 2.0;
        usrp->set_command_time(uhd::time_spec_t(cmd_time));
        usrp->set_tx_rate(rate);
        usrp->clear_command_time();

        // busy waiting to be sure setting is done
        cmd_time += 2.0;
        while(usrp->get_time_now() < uhd::time_spec_t(cmd_time)){}

        rate = usrp->get_tx_rate();
        std::cout << boost::format("Actual TX Rate: %f Msps...") % (rate / 1e6)
                  << std::endl
                  << std::endl;


        usrp->clear_command_time();
        double freq = 400e6;

        // set the rx center frequency
        std::cout << boost::format("Setting TX Freq: %f MHz...") % (freq / 1e6) << std::endl;
       
        uhd::tune_request_t::policy_t policy = uhd::tune_request_t::POLICY_MANUAL;
        uhd::tune_request_t tune_request(freq);
        //tune_request.dsp_freq_policy = policy;
        tune_request.rf_freq_policy = policy;
        tune_request.rf_freq = freq;
        tune_request.args = uhd::device_addr_t("mode_n=integer");
        //tune_request.dsp_freq = freq + 80e6; // target_freq = rf_freq + sign * dsp_freq TX = - and RX = + 

        cmd_time += 2.0;
        usrp->set_command_time(uhd::time_spec_t(cmd_time));
        usrp->set_tx_freq(tune_request, 0);
        usrp->set_tx_freq(tune_request, 1);
        usrp->clear_command_time();

        // busy waiting to be sure setting is done
        cmd_time += 2.0;
        while(usrp->get_time_now() < uhd::time_spec_t(cmd_time)){}


        std::cout << boost::format("Actual TX Freq: %f MHz...") % (usrp->get_tx_freq() / 1e6)
                  << std::endl
                  << std::endl;


        usrp->clear_command_time();

       
        uhd::rx_metadata_t md;
        md.start_of_burst = true;
        md.end_of_burst   = false;
        md.has_time_spec  = true;
        cmd_time += 10.0;
        md.time_spec      = uhd::time_spec_t(cmd_time);

        // std::cout << rx_stream->get_max_num_samps() << std::endl;

        std::cout << "Locked: " << usrp->get_rx_sensor("lo_locked").to_bool() << std::endl;
        std::cout << "TX channels: " << channel_nums << std::endl;

        std::signal(SIGINT, &sig_int_handler);
        std::cout << "Press Ctrl + C to stop streaming..." << std::endl;
        // send data until the signal handler gets called
        // or if we accumulate the number of samples specified (unless it's 0)
        uint64_t num_acc_samps = 0;

        
        while (true) {
                // Break on the end of duration or CTRL-C
                if (stop_signal_called) {
                break;
                }

                // send a single packet
                size_t num_tx_samps = tx_stream->send(buffs, spb, md, timeout);
                // do not use time spec for subsequent packets
                md.has_time_spec  = false;
                md.start_of_burst = false;

                md.start_of_burst = false;
                md.has_time_spec  = false;
        }

        // send a mini EOB packet
        md.end_of_burst = true;
        tx_stream->send("", 0, md);

        // finished
        std::cout << std::endl << "Done!" << std::endl << std::endl;

        return EXIT_SUCCESS;
}
