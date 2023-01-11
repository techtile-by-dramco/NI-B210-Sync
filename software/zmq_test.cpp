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

void ready_to_go(std::string id)
{
        // REQ RES pattern
        // let server now that you are ready and waiting for a SYNC command
        //  Socket to receive messages on
        //  Prepare our context and socket
        zmq::socket_t socket(context, zmq::socket_type::req);

        std::cout << "Connecting to server..." << std::endl;
        socket.connect("tcp://localhost:5555");

        zmq::message_t request(sizeof(id));
        memcpy(request.data(), &id, sizeof(id));
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
        ("args", po::value<std::string>(&str_args)->default_value("type=b200"), "give device arguments here")
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

        double rate = 250e3;
        // set the rx sample rate
        std::cout << boost::format("Setting RX Rate: %f Msps...") % (rate / 1e6) << std::endl;
        usrp->set_rx_rate(rate);
        std::cout << boost::format("Actual RX Rate: %f Msps...") % (usrp->get_rx_rate() / 1e6)
                  << std::endl
                  << std::endl;

        double freq = 400e6;

        // set the rx center frequency
        std::cout << boost::format("Setting RX Freq: %f MHz...") % (freq / 1e6) << std::endl;
        uhd::tune_request_t tune_request(freq);
        usrp->set_rx_freq(tune_request);
        std::cout << boost::format("Actual RX Freq: %f MHz...") % (usrp->get_rx_freq() / 1e6)
                  << std::endl
                  << std::endl;

        usrp->set_rx_gain(0.7);

        uhd::stream_args_t stream_args("fc32"); // complex floats
        stream_args.channels = {0};
        uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

        // just check if we indeed have a PPS signal present
        /*
        const uhd::time_spec_t last_pps_time = usrp->get_time_last_pps();
        while (last_pps_time == usrp->get_time_last_pps())
        {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }*/

        std::string file = "usrp_samples_" + serial + ".dat";
        std::ofstream outfile;
        outfile.open(file.c_str(), std::ofstream::binary | std::ios::trunc);

        if (!ignore_sync)
        {
                ready_to_go(serial);        // non-blocking
                wait_till_go_from_server(); // blocking till SYNC message received
        }else{
                std::cout << "Ignoring waiting for server" << std::endl;
        }

        // This command will be processed fairly soon after the last PPS edge:
        usrp->set_time_next_pps(uhd::time_spec_t(0.0));
        std::cout << "Resetting time." << std::endl;

        // wait to be sure new time is set
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));

        /********************************************/
        /**************** start tuning **************/
        /********************************************/


        /********************************************/
        /*********** begin gpio operations **********/
        /********************************************/

        usrp->clear_command_time();

        usrp->set_command_time(uhd::time_spec_t(3.0));
        usrp->set_gpio_attr("FP0", "OUT", all_one, gpio_line, 0);

        // // set all gpio lines to output 0
        // usrp->clear_command_time();
        // usrp->set_command_time(uhd::time_spec_t(6.0));
        // usrp->set_gpio_attr("FP0", "OUT", all_zero, gpio_line, 0); // set LOW @ t=2

        // // set all gpio lines to output 1
        // usrp->clear_command_time();
        // usrp->set_command_time(uhd::time_spec_t(8.0));
        // usrp->set_gpio_attr("FP0", "OUT", all_one, gpio_line, 0); // set HIGH @ t=4

        // // set all gpio lines to output 0
        // usrp->clear_command_time();
        // usrp->set_command_time(uhd::time_spec_t(10.0));
        // usrp->set_gpio_attr("FP0", "OUT", all_zero, gpio_line, 0); // set LOW @ t=6

        usrp->clear_command_time();

        // std::this_thread::sleep_for(std::chrono::seconds(20));

        // /********************************************/
        // /*********** quit gpio operations ***********/
        // /********************************************/

        size_t num_requested_samples = rate * 10;
        std::vector<std::complex<float>> buff(rx_stream->get_max_num_samps());
        uhd::rx_metadata_t md;
        // setup streaming
        //uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS);
        uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
        stream_cmd.stream_now = false;
        stream_cmd.num_samps = size_t(num_requested_samples);
        double start_time = 5.0f;
        // std::cout << usrp->get_time_now().get_real_secs() << std::endl;
        stream_cmd.time_spec = uhd::time_spec_t(uhd::time_spec_t(start_time));
        rx_stream->issue_stream_cmd(stream_cmd);

        // uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS);
        // stream_cmd.stream_now = false;
        // stream_cmd.time_spec = uhd::time_spec_t(usrp->get_time_now() + uhd::time_spec_t(1.0));
        // rx_stream->issue_stream_cmd(stream_cmd);

        usrp->clear_command_time();

        // std::cout << rx_stream->get_max_num_samps() << std::endl;

        size_t num_total_samps = 0;

        double timeout = start_time + 0.5f;

        // Run this loop until either time expired (if a duration was given), until
        // the requested number of samples were collected (if such a number was
        // given), or until Ctrl-C was pressed.
        while (num_requested_samples > num_total_samps)
        {
                size_t num_rx_samps =
                    rx_stream->recv(&buff.front(), buff.size(), md, timeout); // wait long enough bcs we initiated a timed cmd
                timeout = 0.1f;                                               // small timeout for subsequent recv

                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT)
                {
                        std::cout << boost::format("Timeout while streaming") << std::endl;
                        break;
                }
                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW)
                {
                        std::cout << "O";
                }
                if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE)
                {
                        std::string error = str(boost::format("Receiver error: %s") % md.strerror());
                }
                num_total_samps += num_rx_samps;
                //std::cout << num_total_samps;

                if (outfile.is_open())
                {
                        outfile.write((const char *)&buff.front(), num_rx_samps * sizeof(std::complex<float>));
                }
        }

        stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
        rx_stream->issue_stream_cmd(stream_cmd);

        if (outfile.is_open())
        {
                outfile.close();
        }

        // // process IQ samples
        // zmq::socket_t zmq_send_socket = zmq::socket_t(context, ZMQ_PUSH);
        // std::cout << port
        //           << std::endl;
        // zmq_send_socket.bind("tcp://*:" + port);

        // std::vector<std::complex<float>> buff(rx_stream->get_max_num_samps());
        // uhd::rx_metadata_t md;

        // std::cout << "Receiving now..."
        //           << std::endl
        //           << std::endl;

        // while (1)
        // {
        //         size_t num_rx_samps = rx_stream->recv(&buff.front(), buff.size(), md);

        //         zmq::message_t send_message(buff);
        //         zmq_send_socket.send(send_message, zmq::send_flags::dontwait);
        // }

        return EXIT_SUCCESS;
}
