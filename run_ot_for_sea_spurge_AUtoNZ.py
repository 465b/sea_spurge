import datetime
from datetime import datetime, timedelta
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
hindcast_base_dir = "/data4/hindcasts/tmp"
hindcast_mask_nz = "schism_*.nc"
hindcast_mask_au = "FullData_*.nc"
glorys_static = "glorys_static.nc"
hgrid = "hgridNZ_run.gr3"
    
"""
These are the parameter we could consider tuning to improve model accuracy.
The current configuration is the bare minimum based on the sensitivity analysis
that I did.
"""
# Model configuration
max_model_duration = 14 * 365 * 24 * 3600 # seconds
model_time_step_size = 3 * 3600 # seconds

# Release settings
release_start_date = "2010-01-01T01:00:00"
# release till model stops
# calculate release based on start and max run duration and return it as iso string

release_stop_date = (datetime.fromisoformat(release_start_date) + timedelta(seconds=max_model_duration)).isoformat()
releaseInterval = 3 * 3600 # seconds
pulseSize = 30 # seconds

# Stats settings
statsInterval = 12 * 3600 # seconds

print("------------------------------ output dir setup start ------------------------")
run_output_dir = os.path.join(root_output_dir, base_run_name)
if os.path.isdir(run_output_dir):
    print(f"* run with the same name already exists: {run_output_dir}")
    print("* overwriting existing runs")
    shutil.rmtree(run_output_dir)
os.makedirs(run_output_dir,exist_ok=True)

print("------------------------------ polygon setup start ---------------------------")
nz_coastal_polygons, au_coastal_polygons = prepare_polygons()

# AU to NZ only releases in AU
release_polygons = au_coastal_polygons
print(f"* resulting in {len(release_polygons)} release polygons")


print("------------------------------ started time chunking -------------------------")
dirs = os.listdir(hindcast_base_dir)
for ii,d in enumerate(dirs):
    if ii > 1: break
    print(f"------------------------------ time chunk {ii} setup start --------------------")
    hindcast_dir = os.path.join(hindcast_base_dir,d)
    hgrid_path = os.path.join(hindcast_dir, hgrid)
    glorys_static_path = os.path.join(hindcast_dir, glorys_static)

    # for ii_time_chunk in range(number_of_time_chunks):
    current_run_name = f"{base_run_name}_chunk_{ii:04d}"
    print(f"* current run name: {current_run_name}")

    if ii > 0:
        # if ii_time_chunk > 1: break
        previous_run_name = f"{base_run_name}_chunk_{(ii-1):04d}"
        continue_from = os.path.join(root_output_dir,base_run_name,previous_run_name)

    else:
        continue_from = None

    run_AU_to_NZ_model(
        number_of_threads,
        hindcast_dir,
        hindcast_mask_nz,
        hindcast_dir,
        hindcast_mask_au,
        hgrid_path,
        max_model_duration,
        model_time_step_size,
        release_start_date,
        releaseInterval,
        pulseSize,
        statsInterval,
        nz_coastal_polygons,
        run_output_dir,
        current_run_name,
        release_polygons,
        continue_from=continue_from
    )

