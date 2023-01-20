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

        std::map<std::string, std::string> m = usrp->get_usrp_rx_info();

        std::string serial = m["mboard_serial"];

        std::cout << "Serial number: " << serial << std::endl;

        uhd::stream_args_t stream_args("fc32"); // complex shorts (uint16_t)
        stream_args.channels = {0,1};
        uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

        // just check if we indeed have a PPS signal present
        /*
        const uhd::time_spec_t last_pps_time = usrp->get_time_last_pps();
        while (last_pps_time == usrp->get_time_last_pps())
        {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }*/

        std::string file = "../usrp_samples_" + serial + "_0.dat";
        std::ofstream outfile_0;
        outfile_0.open(file.c_str(), std::ofstream::binary | std::ios::trunc);

        file = "../usrp_samples_" + serial + "_1.dat";
        std::ofstream outfile_1;
        outfile_1.open(file.c_str(), std::ofstream::binary | std::ios::trunc);

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

        usrp->set_rx_gain(0.7);

        usrp->clear_command_time();
        double rate = 500e3;
        // set the rx sample rate
        std::cout << boost::format("Setting RX Rate: %f Msps...") % (rate / 1e6) << std::endl;
        cmd_time += 2.0;
        usrp->set_command_time(uhd::time_spec_t(cmd_time));
        usrp->set_rx_rate(rate);
        usrp->clear_command_time();

        // busy waiting to be sure setting is done
        cmd_time += 2.0;
        while(usrp->get_time_now() < uhd::time_spec_t(cmd_time)){}

        rate = usrp->get_rx_rate();
        std::cout << boost::format("Actual RX Rate: %f Msps...") % (rate / 1e6)
                  << std::endl
                  << std::endl;


        usrp->clear_command_time();
        double freq = 400e6;

        // set the rx center frequency
        std::cout << boost::format("Setting RX Freq: %f MHz...") % (freq / 1e6) << std::endl;
       
        uhd::tune_request_t::policy_t policy = uhd::tune_request_t::POLICY_MANUAL;
        uhd::tune_request_t tune_request(freq);
        //tune_request.dsp_freq_policy = policy;
        tune_request.rf_freq_policy = policy;
        tune_request.rf_freq = freq;
        tune_request.args = uhd::device_addr_t("mode_n=integer");
        //tune_request.dsp_freq = freq + 80e6; // target_freq = rf_freq + sign * dsp_freq TX = - and RX = + 

        cmd_time += 2.0;
        usrp->set_command_time(uhd::time_spec_t(cmd_time));
        usrp->set_rx_freq(tune_request, 0);
        usrp->set_rx_freq(tune_request, 1);
        usrp->clear_command_time();

        // busy waiting to be sure setting is done
        cmd_time += 2.0;
        while(usrp->get_time_now() < uhd::time_spec_t(cmd_time)){}


        std::cout << boost::format("Actual RX Freq: %f MHz...") % (usrp->get_rx_freq() / 1e6)
                  << std::endl
                  << std::endl;


        /********************************************/
        /*********** begin gpio operations **********/
        /********************************************/

        // usrp->clear_command_time();
        // time_t GPIO_time = 10.0;
        // usrp->set_command_time(uhd::time_spec_t(GPIO_time));
        // usrp->set_gpio_attr("FP0", "OUT", all_one, gpio_line, 0);
        // usrp->clear_command_time();

        // while(usrp->get_time_now() < uhd::time_spec_t(GPIO_time + 10.0)){}


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

        size_t num_requested_samples = rate * 20;
        size_t nsamps_per_buff = rx_stream->get_max_num_samps();
        // std::vector<std::vector<std::complex<float>>> buff(usrp->get_rx_num_channels(), std::vector<std::complex<float>>(nsamps_per_buff));     
        /* Allocate large buffer to store all samples */

        std::vector<std::vector<std::complex<float>>> buff(usrp->get_rx_num_channels(), std::vector<std::complex<float>>(num_requested_samples));

        std::vector<std::complex<float> *> buff_ptrs;
	for (size_t i = 0; i < buff.size(); i++)
		buff_ptrs.push_back(&buff[i].front());
        uhd::rx_metadata_t md;
        // setup streaming
        //uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS);
        uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);

        // process IQ samples
        // zmq::socket_t zmq_send_socket = zmq::socket_t(context, ZMQ_PUSH);
        // std::cout << port
        //           << std::endl;
        // zmq_send_socket.bind("tcp://*:" + port);


        stream_cmd.stream_now = false;
        stream_cmd.num_samps = num_requested_samples;
        std::cout << num_requested_samples << std::endl;
        cmd_time += 10.0;
        // std::cout << usrp->get_time_now().get_real_secs() << std::endl;
        stream_cmd.time_spec = uhd::time_spec_t(cmd_time);
        rx_stream->issue_stream_cmd(stream_cmd);

        // uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS);
        // stream_cmd.stream_now = false;
        // stream_cmd.time_spec = uhd::time_spec_t(usrp->get_time_now() + uhd::time_spec_t(1.0));
        // rx_stream->issue_stream_cmd(stream_cmd);

        usrp->clear_command_time();

        // std::cout << rx_stream->get_max_num_samps() << std::endl;

        size_t num_total_samps = 0;

        double timeout = cmd_time + 4.0f;

        std::cout << "Locked: " << usrp->get_rx_sensor("lo_locked").to_bool() << std::endl;
        std::cout << "RX channels: " << rx_stream->get_num_channels() << std::endl;
        
        uhd::time_spec_t rx_starts_in =  uhd::time_spec_t(cmd_time) - usrp->get_time_now();
        
       	std::cout << "Rx starting in " << rx_starts_in.get_full_secs() << " seconds" << std::endl;

        // Run this loop until either time expired (if a duration was given), until
        // the requested number of samples were collected (if such a number was
        // given), or until Ctrl-C was pressed.
        while (num_requested_samples > num_total_samps)
        {
                size_t num_rx_samps =
                    rx_stream->recv(buff_ptrs, nsamps_per_buff, md, timeout); // wait long enough bcs we initiated a timed cmd
                timeout = 0.5f;                                               // small timeout for subsequent recv


                // increase the pointers by the number of samples received
                buff_ptrs[0]+=num_rx_samps;
                buff_ptrs[1]+=num_rx_samps;


                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT)
                {
                        std::cout << boost::format("Timeout while streaming after %d rx samples") %num_total_samps << std::endl;
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

                //zmq::message_t send_message(buff[0]);

                //zmq_send_socket.send(send_message, zmq::send_flags::dontwait);

                
        }

        stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
        rx_stream->issue_stream_cmd(stream_cmd);


        if (outfile_0.is_open())
        {
                outfile_0.write((const char *)&buff[0].front(), num_requested_samples * sizeof(std::complex<float>));
        }
        if (outfile_1.is_open())
        {
                outfile_1.write((const char *)&buff[1].front(), num_requested_samples * sizeof(std::complex<float>));
        }

        if (outfile_0.is_open())
        {
                outfile_0.close();
        }

        if (outfile_1.is_open())
        {
                outfile_1.close();
        }

        

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
