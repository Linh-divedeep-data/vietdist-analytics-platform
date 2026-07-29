import uuid

from src.logger import get_logger


def main():
    batch_id = str(uuid.uuid4())
    logger = get_logger(batch_id)
    logger.info("Pipeline run started")
    logger.info("Pipeline run finished")
    return batch_id


if __name__ == "__main__":
    main()
