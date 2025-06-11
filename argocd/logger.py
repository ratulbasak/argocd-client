import logging
import sys


def get_logger(name="argocd_client", debug=False, log_format="text"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)

        # if log_format == "json":
        #     formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
        # else:
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
