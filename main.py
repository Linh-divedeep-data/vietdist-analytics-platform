import uuid

from src import extract, gdrive_connector
from src.logger import get_logger


def main():
    batch_id = str(uuid.uuid4())
    logger = get_logger(batch_id)
    logger.info("Pipeline run started")

    results = extract.download_all_sources(gdrive_connector.FOLDER_ID, batch_id)
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count
    logger.info(f"Extract done: {success_count} success, {failed_count} failed")

    logger.info("Pipeline run finished")
    return batch_id


if __name__ == "__main__":
    main()
