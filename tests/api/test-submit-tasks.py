import io
import time
import requests
import argparse
import sys
import os
import logging
import datetime
import base64
from multiprocessing import Process

from functools import partial

E_OK = 0
E_ERR = 1

PRE_POLL_DELAY = 2


def submit_and_wait(host, max_retries, delay, no_ssl):

    pid = os.getpid()

    if no_ssl:
        url_base = f"http://{host}/"
    else:
        url_base = f"https://{host}/"

    url_execution = url_base + "request_stats"
    url_status    = url_base + "check_stats?key="
    url_download  = url_base + "get_stats?key="

    logging.info(f"Base url: {url_base}")

    try:
        response = requests.get(url_execution)
    except Exception as e:
        logging.error(f"Problem invoking URL {url_execution}")
        logging.error(f"Please check typos, DNS and connectivity.")
        print(e)
        exit(E_ERR)

    if response.status_code != 200:
        logging.error(f"Error invoking URL {url_execution}")
        logging.error(f"Response code was {response.status_code}")

        try:
            json_response = response.json()
            logging.error(f"Response JSON content:\n\n{json_response}")
        except Exception as ex:
            logging.error(f"The response does not include JSON content")

        response.close()
        exit(E_ERR)

    try:
        uuid = response.json()["key"]
    except Exception as ex:
        logging.error(f"Response does not contain an UUID:\n\n{json_response}")
        exit(E_ERR)

    # Looping until the task is finished
    is_task_not_finished = True
    loops = 0

    logging.info(f"Task UUID is {uuid}")

    # the task is initially not found
    # it needs sometime to be recognized by the scheduler
    time.sleep(PRE_POLL_DELAY)

    while is_task_not_finished:
        if loops == max_retries:
            waiting_time = max_retries * delay
            logging.error(f"Giving up after {waiting_time} seconds of waiting.")
            exit(E_ERR)

        try:
            response_status = requests.get(url_status + uuid)
            status = response_status.json()["status"]
        except Exception as e:
            logging.error(f"Problem checking execution the status")
            exit(E_ERR)

        if status in ["processing", "queued"]:
            time.sleep(delay)
            loops += 1
        elif status == "not found":
            is_task_not_finished = False
        else:
            # this is a catch-all case so that we become aware rather than ignoring unexpected responses
            logging.error(f"Unexpected response: {status}")
            logging.error(f"Exiting")
            response.close()
            exit(E_ERR)

    response.close()

    # Downloading the result
    try:
        response_download = requests.get(url_download + uuid)
    except Exception as e:
        logging.error(f"Problem downloading the results")

    # Saving the downloaded file to the specified destination path
    if response_download.ok:

        try:

            result = str(response_download.content.decode("utf-8"))
            logging.info(f"Result for {uuid} was: {result}")
        except Exception as e:
            logging.error(f"Problem reviewing download results")
            exit(E_ERR)

        logging.info(f"Execution results downloaded successfully")
        logging.info(f"")

    else:
        logging.error(f"Download error: {response_download.status_code}")

    exit(E_OK)


def main():

    parser = argparse.ArgumentParser(description='Test task submission via API')

    custom_formatter = partial(argparse.HelpFormatter, max_help_position=80)
    parser.formatter_class = custom_formatter

    # arguments of type string
    parser.add_argument( '-H',  '--host',             help='Hostname or IP, optionally :PORT',    default=None, required=True)

    # arguments of type int
    parser.add_argument( '-mr', '--max-retries',      help='Number of times to poll',                  default=60, type=int)
    parser.add_argument( '-pd', '--poll-delay',       help='Number of seconds to sleep between polls', default=5,  type=int)
    parser.add_argument( '-np', '--nr-procs',         help='Number of equal requests to submit',       default=1,  type=int)
    parser.add_argument( '-sd', '--submission-delay', help='Number seconds between submissions',       default=0,  type=float)

    # flags
    parser.add_argument( '-q',  '--quiet',            help='Whether to execute silently',                         default=None, action='store_true')
    parser.add_argument( '-ns', '--no-ssl',           help='Whether to connect without SSL',                      default=None, action='store_true')

    # get all the arguments as a dictionary
    args = parser.parse_args()

    host     = args.host
    max_retries      = args.max_retries
    delay            = args.poll_delay
    nr_procs         = args.nr_procs
    submission_delay = args.submission_delay
    quiet            = args.quiet
    no_ssl           = args.no_ssl

    if quiet:
        logging.basicConfig(level=logging.ERROR, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    # now let's handle the multi processing

    worker_functions = [ submit_and_wait ] * nr_procs

    worker_args = [ (host, max_retries, delay, no_ssl) ] * nr_procs

    procs = []

    initial_time = datetime.datetime.now()

    # instantiating the process with its arguments
    for function, arg_list in zip(worker_functions, worker_args):

        proc = Process(target=function, args=arg_list)
        proc.daemon = True
        procs.append(proc)
        proc.start()
        time.sleep(submission_delay)
        pid = proc.pid

    submission_time = (datetime.datetime.now() - initial_time).total_seconds()
    # wait for completion - the join call only returns immediatly if the process is done
    # and waits for completion if the process is still running
    # since we call it for all of them we are in the loop until all of them are done
    for proc in procs:
        proc.join()

    logging.info('\nNow we will check the process exit codes of our processes:\n')

    # get the exit codes
    nr_errors = 0
    for proc in procs:
        pid = proc.pid
        exit_code = proc.exitcode
        if exit_code != 0:
            nr_errors = nr_errors + 1

        # review each processe's exit code
        logging.info(f"process {pid} returned: {exit_code}")

    if nr_errors > 0:
        status_OK = False
    else:
        status_OK = True

    # check if all processes returned 0
    if status_OK is not True:
        # in a real world situation we would want to react to this with more than a simple message
        logging.error('\nERROR: At least one process exited with an error')

    total_time = (datetime.datetime.now() - initial_time).total_seconds()

    # this gets printed regardless of the log level
    print('')
    print('Requests sent:',    nr_procs)
    print(f'Number of errors: {nr_errors} ({round(nr_errors / nr_procs * 100, 2)}%)')
    print('Local submission time:',         round(submission_time, 2))
    print('Total processing time:',         round(total_time, 2))
    print('Submitted requests per second:', round(nr_procs / submission_time, 2))
    print('Processed requests per second:', round(nr_procs / total_time, 2))
    print('Seconds per processed request:', round(total_time / nr_procs, 2))
    print('Status OK:', status_OK)

    logging.info('')
    if status_OK:
        logging.info('Tasks executed successfuly')
        exit(E_OK)
    else:
        logging.info('Problem executing tasks')
        exit(E_ERR)


if __name__ == "__main__":
    main()
