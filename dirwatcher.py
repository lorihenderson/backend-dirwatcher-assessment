__author__ = "Lori Henderson with some help from KaNo and David R"

import os
import signal
import time
import argparse
import errno
import logging.handlers
import logging
import sys

exit_flag = False

files = {}

logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d &%H:%M:%S',
)
logger.setLevel(logging.DEBUG)


def scan_single_file(dir_path, start_line, magic_word):
    """Scans a file from a start position for a given word."""
    global files
    with open(dir_path) as f:
        for i, line in enumerate(f):
            if magic_word in line:
                logger.info(f"{magic_word} found at line {i + 1}")


def detect_added_files(file_list, ext):
    """Checks the directory if given file was added."""
    global files
    for file in file_list:
        if file.endswith(ext) and file not in files:
            files[file] = 0
            logger.info(f'{file} add')


def detect_removed_files(file_list):
    """Checks the directory if given file was deleted."""
    global files
    for file in list(files):
        if file not in file_list:
            logger.info(f'{file} remove')
            del files[file]


def watch_directory(args):
    """Watches a given directory for added and deleted files.  Checks for the magic word in a file."""
    file_list = os.listdir(args.directory)
    detect_added_files(file_list, args.extension)
    detect_removed_files(file_list)

    for file in files:
        files[file] = scan_single_file(os.path.join(args.directory, file), files[file], args.magic_text)



def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals can be mapped here as well (SIGHUP?)
    Basically, it just sets a global flag, and main() will exit its loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    # log the associated signal name
    logger.warning('Received ' + signal.Signals(sig_num).name)
    global exit_flag
    exit_flag = True

def create_parser():
    """Creates a parser"""
    parser = argparse.ArgumentParser(description="Watches a directory of text files for a magic string")
    parser.add_argument("directory", help="specifies the directory to watch") # specify the directory to watch (*this directory may not yet exist!*) ##positional argument
    parser.add_argument("magic_text", help="specifies the magic text to search for") # specifics the "magic text" to search for ##position argument
    parser.add_argument("-i", "--interval", help="controls the polling interval", type=float, default=1.0) # controls the polling interval (instead of hard-coding it)
    parser.add_argument("-e", "--extension", help="filters what kind of file extension to search within", type=str, default=".txt") # filters what kind of file extension to search within (i.e., `.txt`, `.log`)
    return parser


def main(args):
    """Main function is declared as a standalone."""   

    parser = create_parser()
    p_args = parser.parse_args(args)
    print("ARGS", p_args)
    polling_interval = p_args.interval
 
    logger = logging.getLogger()

    start_time = time.time()

    logger.info(
        '\n'
        '-------------------------------------------------\n'
        f'   Running {__file__}\n'
        f'   PID is {os.getpid()}\n'
        f'   Started on {start_time:.1f}\n'
        '-------------------------------------------------\n'
    )

    # Hook into these two signals from the OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Now my signal_handler will get called if OS sends
    # either of these to my process.

    while not exit_flag:
        try:
            # call my directory watching function
            watch_directory(p_args)
            
        except OSError as e:
            if e.errno == errno.ENOENT:
                logger.error(f"{p_args.directory} directory not found")
                time.sleep(2)
            else:
                logger.error(e)
        except Exception as e:
            # This is an UNHANDLED exception
            # Log an ERROR level message here
            logger.error(f'UNHANDLED EXCEPTION:{e}')

        # put a sleep inside my while loop so I don't peg the cpu usage at 100%
        time.sleep(polling_interval)
    
    end_time = time.time() - start_time
    # final exit point happens here
    # Log a message that we are shutting down
    # Include the overall uptime since program start
    logger.info(
        '\n'
        '-------------------------------------------------\n'
        f'   Stopped {__file__}\n'
        f'   Uptime was {end_time:.1f}\n'
        '-------------------------------------------------\n'
    )
    logging.shutdown()

if __name__ == "__main__":
    main(sys.argv[1:])