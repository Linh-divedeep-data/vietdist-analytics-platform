import argparse
import uuid

from src import extract, gdrive_connector
from src.logger import get_logger


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VDAP pipeline CLI — chạy Bronze/Silver/Gold theo layer + run-date."
    )
    parser.add_argument(
        "--layer",
        choices=["bronze", "silver", "gold", "all"],
        required=True,
        help="Layer cần chạy: bronze|silver|gold|all",
    )
    parser.add_argument("--run-date", required=True, help="Ngày chạy pipeline, định dạng YYYY-MM-DD")
    return parser


def main(argv: list[str] | None = None) -> str:
    args = build_arg_parser().parse_args(argv)
    batch_id = str(uuid.uuid4())
    logger = get_logger(batch_id)
    logger.info(f"Pipeline run started (layer={args.layer}, run_date={args.run_date})")

    if args.layer in ("bronze", "all"):
        download_results = extract.download_all_sources(gdrive_connector.FOLDER_ID, batch_id)
        success_count = sum(1 for r in download_results if r["status"] == "success")
        failed_count = len(download_results) - success_count
        logger.info(f"Download done: {success_count} success, {failed_count} failed")

        ingest_records = extract.run_bronze_ingestion(run_date=args.run_date, batch_id=batch_id)
        bronze_success = sum(1 for r in ingest_records if r["status"] == "success")
        logger.info(f"Bronze ingestion done: {bronze_success}/{len(ingest_records)} nguồn")

    if args.layer in ("silver", "all"):
        logger.info("Silver layer chưa implement — bỏ qua (Phase 2)")

    if args.layer in ("gold", "all"):
        logger.info("Gold layer chưa implement — bỏ qua (Phase 3)")

    logger.info("Pipeline run finished")
    return batch_id


if __name__ == "__main__":
    main()
