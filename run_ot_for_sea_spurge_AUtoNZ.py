import os
import shutil
import numpy as np

from load_polygons import prepare_polygons
from model_wrapper import run_AU_to_NZ_model

from batching import get_next_chunk_number


# ===========================================================================
base_run_name = "2025_12_10_v01_AUtoNZ_tmp"
# ===========================================================================

# paralellization
number_of_threads = 30

# "------------------------------ batching config ---------------------------"
# Batching configuration
"""
For ~1_000_000 particles per release group, I'd recommend batching the runs into chunks
of 10 release groups each, this keeps the relative cost for reading the hindcast small
i.e. below ~10% and total runtimes at about 1 day
"""
# I/O configuration
# Model output
root_output_dir = "/data3/ls/oceantracker_output/sea_spurge_big_boy_runs"
# Model input
## Hindcast settings
hindcast_dir_nz = r"/data4/hindcasts/SCHISM/New_Zealand_global_2D_surface_only/"
hindcast_mask_nz = "*.nc"
hindcast_dir_au = r"/data4/hindcasts/GLORYS/Australia_global_2D_surface_only/"
hindcast_mask_au = "*.nc"
hgrid_file_name = (
    "/data4/hindcasts/SCHISM/New_Zealand_global_2D_surface_only/hgridNZ_run.gr3"
)
## Poylgon settings
""" These are defined relative to the repo root dir and defined in 'load_polygon' """

# "------------------------------ model setup start -----------------------------"
"""
These are the parameter we could consider tuning to improve model accuracy.
The current configuration is the bare minimum based on the sensitivity analysis
that I did.
"""
# Model configuration
max_model_duration = 14 * 365 * 24 * 3600 # seconds
model_time_step_size = 3 * 3600 # seconds
max_duration_per_time_chunk = 1 * 30 * 3600 # seconds

# Release settings
releaseStartDate = "2010-01-01T01:00:00"
releaseInterval = 3 * 3600 # seconds
pulseSize = 30 # seconds

# Stats settings
statsInterval = 12 * 3600 # seconds


print("------------------------------ polygon setup start ---------------------------")
nz_coastal_polygons, au_coastal_polygons = prepare_polygons()

# AU to NZ only releases in AU
release_polygons = au_coastal_polygons
print(f"* resulting in {len(release_polygons)} release polygons")

print("------------------------------ time batching setup start ------------")
number_of_time_chunks = np.ceil(
    max_model_duration / max_duration_per_time_chunk
).astype(int)
print(f"* max time per time chunk {max_duration_per_time_chunk}")
print(f"* number of time chunks {number_of_time_chunks}")



run_output_dir = os.path.join(root_output_dir, base_run_name)
if os.path.isdir(run_output_dir):
    print(f"* run with the same name already exists: {run_output_dir}")
    print("* assuming you would like to append to it, otherwise remove dir manually")
os.makedirs(run_output_dir,exist_ok=True)

for ii_time_chunk in range(number_of_time_chunks):
    current_run_name = f"{base_run_name}_chunk_{ii_time_chunk:04d}"
    print(f"* current run name: {current_run_name}")

    if ii_time_chunk > 0:
        if ii_time_chunk > 1: break
        previous_run_name = f"{base_run_name}_chunk_{(ii_time_chunk-1):04d}"

    else:
        previous_run_name = None

    run_AU_to_NZ_model(
        number_of_threads,
        hindcast_dir_nz,
        hindcast_mask_nz,
        hindcast_dir_au,
        hindcast_mask_au,
        hgrid_file_name,
        max_duration_per_time_chunk,
        model_time_step_size,
        releaseStartDate,
        releaseInterval,
        pulseSize,
        statsInterval,
        nz_coastal_polygons,
        run_output_dir,
        current_run_name,
        release_polygons,
    )

