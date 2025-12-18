library(polars)
library(ggplot2)
library(dplyr)

polars_envvars()

CSV_FILE = "./data/port_of_dover.csv"
PRIMARY_ROADS   <- c("A20", "A2", "M20")
SECONDARY_ROADS <- c("A256", "A259")

q <- (
  pl
  $scan_csv(CSV_FILE, null_values='NULL', try_parse_dates=TRUE)
  $filter(
    pl$col("road_name") == "A20" &
      pl$col("direction_of_travel") == "E"
  )
  $group_by("date_time")
  $agg(lambda_t = pl$sum("all_HGVs"))
  $sort("date_time")
)

withr::with_envvar(
  list(POLARS_FMT_MAX_COLS = 13, POLARS_MAX_THREADS=16, POLARS_TABLE_WIDTH=90, POLARS_FMT_MAX_ROWS=126, POLARS_WARN_UNSTABLE=2),
  print(df <- q$collect())
)

