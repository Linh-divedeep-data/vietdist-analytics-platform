import uuid
from datetime import UTC, datetime

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

    # Placeholder tới khi --run-date CLI arg được wire (vdap-24y) — hiện dùng ngày chạy thật.
    run_date = datetime.now(UTC).strftime("%Y-%m-%d")
    sources = {**extract.read_csv_sources(), **extract.read_excel_sources()}
    for source_file, df in sources.items():
        lineage_df = extract.attach_lineage(df, source_file=source_file, run_date=run_date, batch_id=batch_id)
        extract.cast_to_string(lineage_df)
    logger.info(f"Lineage attached: {len(sources)} sources")

    logger.info("Pipeline run finished")
    return batch_id


if __name__ == "__main__":
    main()
