import logging

import gevent
from gevent.queue import Queue

from job_runner_worker.cleanup import reset_incomplete_runs
from job_runner_worker.config import config
from job_runner_worker.enqueuer import enqueue_runs
from job_runner_worker.events import publish
from job_runner_worker.worker import execute_run


logger = logging.getLogger(__name__)


def run():
    """
    Start consuming runs and executing them.
    """
    greenlets = []
    reset_incomplete_runs()
    concurrent_jobs = config.getint('job_runner_worker', 'concurrent_jobs')

    run_queue = Queue(concurrent_jobs)
    event_queue = Queue()

    logger.info('Start enqueue loop')
    greenlets.append(gevent.spawn(enqueue_runs, run_queue, event_queue))

    logger.info('Starting {0} workers'.format(concurrent_jobs))
    for x in range(concurrent_jobs):
        greenlets.append(gevent.spawn(execute_run, run_queue, event_queue))

    logger.info('Starting event publisher')
    greenlets.append(gevent.spawn(publish, event_queue))

    for greenlet in greenlets:
        greenlet.join()