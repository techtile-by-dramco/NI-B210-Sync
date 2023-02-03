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
#include <cmath>
#include <filesystem>

#define FMT_HEADER_ONLY
#include <fmt/format.h>
#include <fmt/ranges.h>

namespace po = boost::program_options;

#define RATE    1e6
#define FREQ    400e6

zmq::context_t context(1);

using sample_t = std::complex<float>;

std::vector<sample_t> read_ZC_seq(int min_samples)
{
        // adapted from https://wiki.gnuradio.org/index.php/File_Sink
        std::string filename = "../zc-sequence.dat";
        // check whether file exists
        if (!std::filesystem::exists(filename.data()))
        {
                fmt::print(stderr, "file '{:s}' not found\n", filename);
        }

        // calculate how many samples to read
        auto file_size = std::filesystem::file_size(std::filesystem::path(filename));
        auto samples_in_file = file_size / sizeof(sample_t);

        int num_repetitions = std::ceil(static_cast<float>(min_samples) / samples_in_file);

        std::vector<sample_t> samples;
        samples.resize(samples_in_file * num_repetitions);

        fmt::print(stderr, "Reading {:d} times...\n", num_repetitions);

        std::ifstream input_file(filename.data(), std::ios_base::binary);
        if (!input_file)
        {
                fmt::print(stderr, "error opening '{:s}'\n", filename);
        }

        fmt::print(stderr, "Reading {:d} samples...\n", samples_in_file);

        sample_t *buff_ptr = &samples.front();
        // read-out the same file "num_repetitions" times
        for (int i = 0; i < num_repetitions; i++)
        {
                input_file.read(reinterpret_cast<char *>(buff_ptr), samples_in_file * sizeof(sample_t));
                buff_ptr += samples_in_file;
        }

        return samples;

        /*
        LEGACY
        std::vector<std::complex<float>> seq(353*10);
        std::complex<float> seq_length(353,0);
        std::complex<float> u(7,0);
        std::complex<float> cf(53%2,0);
        std::complex<float> q(2*0,0);
        std::complex<float> min_j(0,-1);

        std::complex<float> pi = M_PI;


        std::complex<float> n = 0;
        for(uint16_t i=0;i<353*10;i++){
                n = i%353;
                std::complex<float> s = exp(min_j*pi*u*n*(n+cf+q) / seq_length); // i defined q = 2*q, so i dont need to cast 2 to a complex number
                seq.push_back(s);
        }
        */
}


    void ready_to_go(std::string id)
{
        // REQ RES pattern
        // let server now that you are ready and waiting for a SYNC command
        //  Socket to receive messages on
        //  Prepare our context and socket
        zmq::socket_t socket(context, zmq::socket_type::req);

        std::cout << "Connecting to server..." << std::endl;
        socket.connect("tcp://10.128.48.4:5555");

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
        subscriber.connect("tcp://10.128.48.4:5557");
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

        std::map<std::string, std::string> m = usrp->get_usrp_tx_info();

        std::string serial = m["mboard_serial"];

        std::cout << "Serial number: " << serial << std::endl;

        uhd::stream_args_t stream_args("fc32"); // complex shorts (uint16_t)
        stream_args.channels = {0};
        uhd::tx_streamer::sptr tx_stream = usrp->get_tx_stream(stream_args);

        size_t nsamps_per_buff = tx_stream->get_max_num_samps();
        std::vector<sample_t> seq = read_ZC_seq(nsamps_per_buff);

        if (!ignore_sync)
        {
                ready_to_go(serial);        // non-blocking
                wait_till_go_from_server(); // blocking till SYNC message received
        }
        else
        {
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

        usrp->set_normalized_tx_gain(0.5);

        usrp->clear_command_time();
        double rate = RATE;
        // set the tx sample rate
        std::cout << boost::format("Setting TX Rate: %f Msps...") % (rate / 1e6) << std::endl;
        cmd_time += 2.0; //7
        usrp->set_command_time(uhd::time_spec_t(cmd_time));
        usrp->set_tx_rate(rate);
        usrp->clear_command_time();

        // busy waiting to be sure setting is done
        cmd_time += 2.0; //9
        while(usrp->get_time_now() < uhd::time_spec_t(cmd_time)){}

        rate = usrp->get_tx_rate();
        std::cout << boost::format("Actual TX Rate: %f Msps...") % (rate / 1e6)
                  << std::endl
                  << std::endl;


        usrp->clear_command_time();
        double freq = FREQ;

        // set the tx center frequency
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
        usrp->clear_command_time();

        // busy waiting to be sure setting is done
        cmd_time += 2.0; //11
        while(usrp->get_time_now() < uhd::time_spec_t(cmd_time)){}


        std::cout << boost::format("Actual TX Freq: %f MHz...") % (usrp->get_tx_freq() / 1e6)
                  << std::endl
                  << std::endl;


        usrp->clear_command_time();

        uhd::tx_metadata_t md;
        md.start_of_burst = false;
        md.end_of_burst = false;
        md.has_time_spec = true;

        cmd_time += 5.0; //16
        md.time_spec = uhd::time_spec_t(cmd_time);

        size_t num_requested_samples = rate*15;

        size_t num_total_samps = 0;
        

        double timeout = cmd_time + 4.0f;

        std::cout << "Locked: " << usrp->get_tx_sensor("lo_locked").to_bool() << std::endl;

        
        uhd::time_spec_t tx_starts_in =  uhd::time_spec_t(cmd_time) - usrp->get_time_now();
        
       	std::cout << "Tx starting in " << tx_starts_in.get_full_secs() << " seconds" << std::endl;

        // Run this loop until either time expired (if a duration was given), until
        // the requested number of samples were collected (if such a number was
        // given), or until Ctrl-C was pressed.

        std::vector<sample_t> buff(nsamps_per_buff);
        std::string filename = "../zc-sequence.dat";
        // check whether file exists
        if (!std::filesystem::exists(filename.data()))
        {
                fmt::print(stderr, "file '{:s}' not found\n", filename);
        }

        // calculate how many samples to read
        auto file_size = std::filesystem::file_size(std::filesystem::path(filename));
        auto samples_in_file = file_size / sizeof(sample_t);

        std::ifstream infile(filename.data(), std::ios_base::binary);
        if (!infile)
        {
                fmt::print(stderr, "error opening '{:s}'\n", filename);
        }


        // while (num_requested_samples > num_total_samps)
        // {

        //         infile.read((char *)&buff.front(), buff.size() * sizeof(sample_t));
        //         size_t num_tx_samps = infile.gcount() / sizeof(sample_t);

        //         sample_t *start_pos = &buff.front();
        //          for (int i = 0; i < num_tx_samps; i++)
        //         {
        //                 std::cout << std::arg(*start_pos) << " ";
        //                 start_pos++;
        //         }
        //         std::cout << std::endl;

        //         if(infile.eof()){
        //                 // reset to beginning
        //                 infile.clear();
        //                 infile.seekg(0, std::ios::beg);
        //         }

        //         tx_stream->send(&buff.front(), num_tx_samps, md, timeout);
        //         md.has_time_spec = false;

        //         if (num_tx_samps < nsamps_per_buff)
        //                 std::cerr << "Send timeout..." << std::endl;
        //         num_total_samps += num_tx_samps;
        // }

        while (num_requested_samples > num_total_samps)
        {
        
                //send a single packet
                size_t num_tx_samps = tx_stream->send(&seq.front(), nsamps_per_buff, md, timeout);

                //do not use time spec for subsequent packets
                md.has_time_spec = false;

                if (num_tx_samps < nsamps_per_buff)
                        std::cerr << "Send timeout..." << std::endl;

                num_total_samps += num_tx_samps;
        }



        // send a mini EOB packet
        md.end_of_burst = true;
        tx_stream->send("", 0, md);

        std::cout << std::endl << "Waiting for async burst ACK... " << std::flush;
        uhd::async_metadata_t async_md;
        bool got_async_burst_ack = false;
        // loop through all messages for the ACK packet (may have underflow messages in queue)
        while (not got_async_burst_ack and tx_stream->recv_async_msg(async_md, timeout)) {
                got_async_burst_ack =
                (async_md.event_code == uhd::async_metadata_t::EVENT_CODE_BURST_ACK);
        }
        std::cout << (got_async_burst_ack ? "success" : "fail") << std::endl;

        // finished
        std::cout << std::endl << "Done!" << std::endl << std::endl;


        return EXIT_SUCCESS;
}
