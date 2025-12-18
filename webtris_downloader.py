"""Download 15-minute traffic flow data from the UK WebTRIS API.

This script pulls 15-minute flow data for a predefined list of Dover-area
WebTRIS site IDs (configurable via CLI flags), using short rolling windows to
avoid API instability. Results for each site are written to
``data/webtris_15min_site_<site_id>.csv`` by default, with optional Parquet
output for efficiency. Empty responses are handled gracefully, and a clear
error is raised only if all requests fail for a site.
"""
from __future__ import annotations

import argparse
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import pandas as pd
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

BASE_URL = "https://webtris.highwaysengland.co.uk/api/v1.0"
REPORT_SUBTYPE_ID = 1
PAGE_SIZE = 1000
WINDOW_DAYS = 3
DATE_FORMAT = "%d%m%Y"
DEFAULT_START_DATE = "19122015"
DEFAULT_END_DATE = "17122025"
MAX_PAGES_FALLBACK = 500

SITE_METADATA: Dict[int, Dict[str, str]] = {
    3158: {
        "Description": "MIDAS site at A20/7224A priority 1 on link 104025002; GPS Ref: 632877;141581; Eastbound",
        "Reference": "Ref: 632877;141581",
    },
    3613: {
        "Description": "MIDAS site at M20/7059A priority 1 on link 125053401; GPS Ref: 617692;137293; Eastbound",
        "Reference": "Ref: 617692;137293",
    },
    7650: {
        "Description": "TMU Site 5826/1 on link A2 eastbound between A260 and A256 near Whitfield (west); GPS Ref: 626126;146459; Eastbound",
        "Reference": "Ref: 626126;146459",
    },
    7655: {
        "Description": "TMU Site 5892/1 on A20 eastbound between A256 near Dover (east) and A2; GPS Ref: 632542;141482; Eastbound",
        "Reference": "Ref: 632542;141482",
    },
    9053: {
        "Description": "TMU Site 5993/1 on link A2 eastbound between A258 and A20; GPS Ref: 633046;141874; Eastbound",
        "Reference": "Ref: 633046;141874",
    },
    10579: {
        "Description": "TMU Site 9953/1 on link A20 eastbound between B2011 and A256 near Dover (west); GPS Ref: 631566;140595; Eastbound",
        "Reference": "Ref: 631566;140595",
    },
    10593: {
        "Description": "TMU Site 9953/4 on link A20 westbound at a minor junction between A256 near Dover (west) and B2011; GPS Ref: 631600;140521; Carriageway Connector",
        "Reference": "Ref: 631600;140521",
    },
}

DEFAULT_SITE_IDS: Sequence[int] = tuple(SITE_METADATA.keys())

DATA_DIR = Path("data")
LOGGER = logging.getLogger(__name__)


def chunk_date_range(
    start_date: datetime, end_date: datetime, window_days: int = WINDOW_DAYS
) -> Iterable[Tuple[datetime, datetime]]:
    """Yield inclusive date windows up to ``window_days`` long."""

    current = start_date
    max_delta = timedelta(days=window_days - 1)
    while current <= end_date:
        window_end = min(current + max_delta, end_date)
        yield current, window_end
        current = window_end + timedelta(days=1)


def build_endpoint(start_date: datetime, end_date: datetime) -> str:
    """Construct the API endpoint path with formatted dates."""

    return (
        f"{BASE_URL}/reports/{start_date.strftime(DATE_FORMAT)}"
        f"/to/{end_date.strftime(DATE_FORMAT)}/daily"
    )


def extract_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract row data from the API payload, supporting multiple shapes."""

    if not isinstance(payload, dict):
        return []

    row_keys = (
        "Rows",
        "rows",
        "ReportRows",
        "Records",
        "records",
        "Flow",
        "flow",
        "Report",
    )
    for key in row_keys:
        rows = payload.get(key)
        if isinstance(rows, list):
            return rows

    pagination = payload.get("Pagination")
    if isinstance(pagination, dict):
        rows = pagination.get("Rows")
        if isinstance(rows, list):
            return rows

    return []


def extract_total_pages(payload: Dict[str, Any]) -> int | None:
    """Try to determine the total page count from the payload."""

    if not isinstance(payload, dict):
        return None

    candidate_keys = (
        "TotalPages",
        "totalPages",
        "TotalNumberOfPages",
        "TotalPagesCount",
        "numberOfPages",
    )
    for key in candidate_keys:
        value = payload.get(key)
        try:
            if value is not None:
                pages = int(value)
                if pages > 0:
                    return pages
        except (TypeError, ValueError):
            continue

    pagination = payload.get("Pagination")
    if isinstance(pagination, dict):
        for key in candidate_keys:
            value = pagination.get(key)
            try:
                if value is not None:
                    pages = int(value)
                    if pages > 0:
                        return pages
            except (TypeError, ValueError):
                continue

    total_records = payload.get("TotalRecords") or payload.get("TotalCount")
    page_size = payload.get("PageSize") or payload.get("pageSize") or PAGE_SIZE
    try:
        if total_records is not None:
            pages = math.ceil(int(total_records) / int(page_size))
            if pages > 0:
                return pages
    except (TypeError, ValueError, ZeroDivisionError):
        return None

    return None


def fetch_page(
    session: Session,
    site_id: int,
    start_date: datetime,
    end_date: datetime,
    page: int,
) -> Tuple[List[Dict[str, Any]], int | None]:
    """Fetch a single paginated response for a site and date window."""

    endpoint = build_endpoint(start_date, end_date)
    params = {
        "sites": site_id,
        "page": page,
        "pageSize": PAGE_SIZE,
        "page_size": PAGE_SIZE,
        "reportSubTypeId": REPORT_SUBTYPE_ID,
        "format": "json",
    }
    response = session.get(endpoint, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    rows = extract_rows(payload)
    total_pages = extract_total_pages(payload)
    return rows or [], total_pages


def fetch_site_data(
    session: Session,
    site_id: int,
    start_date: datetime,
    end_date: datetime,
) -> pd.DataFrame:
    """Fetch all paginated rows for a site across rolling windows."""

    all_rows: List[Dict[str, Any]] = []
    successful_requests = 0

    for window_start, window_end in chunk_date_range(start_date, end_date):
        page = 1
        pages_seen = 0
        while True:
            try:
                rows, total_pages = fetch_page(
                    session, site_id, window_start, window_end, page
                )
                successful_requests += 1
            except (RequestException, ValueError) as exc:
                LOGGER.warning(
                    "Request failed for site %s (%s-%s) page %s: %s",
                    site_id,
                    window_start.strftime(DATE_FORMAT),
                    window_end.strftime(DATE_FORMAT),
                    page,
                    exc,
                )
                break

            rows_with_site = [
                {
                    **row,
                    "SiteId": row.get("SiteId", site_id),
                    "Reference": SITE_METADATA.get(site_id, {}).get("Reference"),
                    "Description": SITE_METADATA.get(site_id, {}).get("Description"),
                }
                for row in rows
            ]
            all_rows.extend(rows_with_site)

            pages_seen += 1
            page += 1

            if total_pages is not None:
                if page > total_pages:
                    break
            else:
                if not rows:
                    break
                if len(rows) < PAGE_SIZE:
                    break
                if pages_seen >= MAX_PAGES_FALLBACK:
                    LOGGER.warning(
                        "Stopping pagination early after %s pages for site %s window %s-%s",
                        MAX_PAGES_FALLBACK,
                        site_id,
                        window_start.strftime(DATE_FORMAT),
                        window_end.strftime(DATE_FORMAT),
                    )
                    break

    if successful_requests == 0:
        raise RuntimeError(f"All requests failed for site {site_id}.")

    if all_rows:
        return pd.DataFrame(all_rows)

    return pd.DataFrame(columns=["SiteId", "Reference", "Description"])


def write_outputs(
    df: pd.DataFrame, site_id: int, output_dir: Path, output_format: str
) -> None:
    csv_path = output_dir / f"webtris_15min_site_{site_id}.csv"
    parquet_path = output_dir / f"webtris_15min_site_{site_id}.parquet"

    if output_format in {"csv", "both"}:
        df.to_csv(csv_path, index=False)
        LOGGER.info("Saved CSV with %s rows for site %s to %s", len(df), site_id, csv_path)

    if output_format in {"parquet", "both"}:
        try:
            df.to_parquet(parquet_path, index=False)
            LOGGER.info(
                "Saved Parquet with %s rows for site %s to %s",
                len(df),
                site_id,
                parquet_path,
            )
        except (ImportError, ValueError) as exc:
            message = (
                f"Failed to write Parquet for site {site_id} to {parquet_path}: {exc}"
            )
            if output_format == "parquet":
                raise RuntimeError(message) from exc
            LOGGER.warning(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download 15-minute WebTRIS traffic flow data."
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help=f"Start date in {DATE_FORMAT} format (default: {DEFAULT_START_DATE}).",
    )
    parser.add_argument(
        "--end-date",
        default=DEFAULT_END_DATE,
        help=f"End date in {DATE_FORMAT} format (default: {DEFAULT_END_DATE}).",
    )
    parser.add_argument(
        "--site-id",
        dest="site_ids",
        action="append",
        type=int,
        help=(
            "WebTRIS site ID to download. "
            "Can be provided multiple times; defaults to the Dover list."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DATA_DIR),
        help="Directory to write per-site CSV files (default: data/).",
    )
    parser.add_argument(
        "--output-format",
        choices=("csv", "parquet", "both"),
        default="csv",
        help="Output format per site (default: csv).",
    )
    return parser.parse_args()


def parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}', expected format {DATE_FORMAT}") from exc


def validate_date_range(start: datetime, end: datetime) -> None:
    if start > end:
        raise ValueError(
            f"Start date {start.strftime(DATE_FORMAT)} must be on or before "
            f"end date {end.strftime(DATE_FORMAT)}."
        )


def build_session() -> Session:
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update({"User-Agent": "webtris-downloader/2.0"})
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    start_dt = parse_date(args.start_date)
    end_dt = parse_date(args.end_date)
    validate_date_range(start_dt, end_dt)

    site_ids: Sequence[int] = (
        tuple(args.site_ids) if args.site_ids else DEFAULT_SITE_IDS
    )

    with build_session() as session:
        successful_sites = 0

        for site_id in site_ids:
            LOGGER.info("Fetching data for site %s", site_id)
            try:
                df = fetch_site_data(session, site_id, start_dt, end_dt)
            except RuntimeError as exc:
                LOGGER.error("%s", exc)
                continue

            write_outputs(df, site_id, output_dir, args.output_format)
            successful_sites += 1

    if successful_sites == 0:
        raise RuntimeError("All WebTRIS requests failed; no files were written.")


if __name__ == "__main__":
    main()
