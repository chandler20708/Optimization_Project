library(polars)
library(tibble)
library(ggplot2)
library(leaflet)
library(dplyr)

polars_envvars()

CSV_FILE = './data/dft_traffic_counts_raw_counts.csv'
PRIMARY_ROADS   <- c("A20", "A2", "M20")
SECONDARY_ROADS <- c("A256", "A259")

q <- (
  pl
  $scan_csv(CSV_FILE, null_values='NULL', try_parse_dates=TRUE)
  $filter(
    # --- Geographic scope ---
    pl$col("local_authority_name")$str$contains("Kent") &
      pl$col("latitude")$is_between(51.0891, 51.13) &
      pl$col("longitude")$is_between(1.13, 1.33) &
      
      # --- Road inclusion ---
      pl$col("road_name")$is_in(pl$lit(c(PRIMARY_ROADS, SECONDARY_ROADS))) &
      
      # --- Direction logic ---
      (
        # Primary roads: inbound only
        (
          pl$col("road_name")$is_in(pl$lit(PRIMARY_ROADS)) &
            pl$col("direction_of_travel")$is_in(pl$lit(c("E", "S")))
        ) |
          # Secondary roads: keep all directions
          (
            pl$col("road_name")$is_in(pl$lit(SECONDARY_ROADS))
          )
      ) &
      
      # --- Exclude known irrelevant sensors ---
      pl$col("count_point_id")$is_in(pl$lit(c(99222, 89097, 89317, 89096)))$not()
  )
  $with_columns(
    date_time = pl$datetime(
      year = pl$col('year'),
      month = pl$col('count_date')$dt$month(),
      day = pl$col('count_date')$dt$day(),
      hour = pl$col('hour')
    )
  )
  $sort('date_time', 'road_name')
  $select(c("date_time", "count_point_id", "road_name", "direction_of_travel", "longitude", "latitude", "pedal_cycles", "two_wheeled_motor_vehicles", "cars_and_taxis", "buses_and_coaches", "LGVs", "all_HGVs", "all_motor_vehicles"))
)

withr::with_envvar(
  list(POLARS_FMT_MAX_COLS = 13, POLARS_MAX_THREADS=16, POLARS_TABLE_WIDTH=90, POLARS_FMT_MAX_ROWS=126, POLARS_WARN_UNSTABLE=2),
  print(df <- q$collect())
)

pts <- as_tibble(df$unique('date_time')$unique('count_point_id')$select('longitude', 'latitude', pl$col('count_point_id')$alias('label')))

leaflet(pts) |>
  addProviderTiles(providers$CartoDB.Positron) |>
  addCircleMarkers(
    lng = ~longitude,
    lat = ~latitude,
    radius = 6,
    color = "red",
    label = ~label
  )

df$write_csv("./data/port_of_dover.csv")
