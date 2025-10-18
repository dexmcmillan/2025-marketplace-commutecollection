# Chunked conversion of .dta to Parquet for 2024-2025 data and selected columns, with schema alignment and index reset
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

stata_path = 'alltrips_canada.dta'
parquet_path = 'alltrips_canada_2024_2025.parquet'
cols = [
    "tripid",
    "mode",
    "citycode",
    "cityname_corrected",
    "time_full_str",
    "traffic_min",
    "notraffic_min",
    "dayofweek",
    "tz",
    "trip_dist",
    "lat_dest",
    "lon_dest",
    "lat_orig",
    "lon_orig"
]

writer = None
schema = None
chunksize = 100_000
print('Converting .dta to Parquet in chunks (2024 & 2025 only)...')
for chunk in pd.read_stata(stata_path, columns=cols, chunksize=chunksize):
    # Filter for 2024 or 2025 in 'time_full_str'
    mask = chunk['time_full_str'].str.startswith('2024') | chunk['time_full_str'].str.startswith('2025')
    chunk_2024_2025 = chunk[mask].copy()
    if not chunk_2024_2025.empty:
        chunk_2024_2025 = chunk_2024_2025.reset_index(drop=True)  # Remove index to avoid __index_level_0__
        table = pa.Table.from_pandas(chunk_2024_2025, preserve_index=False)
        if writer is None:
            schema = table.schema
            writer = pq.ParquetWriter(parquet_path, schema)
        else:
            table = table.cast(schema)
        writer.write_table(table)
if writer is not None:
    writer.close()
    print(f'Done. Data saved to {parquet_path}')
else:
    print('No 2024 or 2025 data found in the .dta file.')