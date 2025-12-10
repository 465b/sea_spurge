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
number_of_release_groups_per_chunk = 10

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
durationDays = 14 * 365 * 24 * 3600
timeStep = 3 * 60 * 60

# Release settings
releaseStartDate = "2010-01-01T01:00:00"
releaseInterval = 3 * 60 * 60
pulseSize = 30

# Stats settiongs
statsInterval = 12 * 60 * 60


print("------------------------------ polygon setup start ---------------------------")
# prepare coastal polygons
# ------------------------
# Release and catch polies for polygon and gridded stats

nz_coastal_polygons, au_coastal_polygons = prepare_polygons()

# AU to NZ only releases in AU
release_polygons = au_coastal_polygons
print(f"* resulting in {len(release_polygons)} release polygons")


print("------------------------------ batching setup start ---------------------------")
number_of_chunks = np.ceil(
    len(release_polygons) / number_of_release_groups_per_chunk
).astype(int)
print(f"* max number of releas groups per chunk {number_of_release_groups_per_chunk}")
print(f"* number of  chunks {number_of_chunks}")

chunk_output_dir = os.path.join(root_output_dir, base_run_name)
if os.path.isdir(chunk_output_dir):
    print(f"* run with the same name already exists")
    print(f"* deleting existing run")
    shutil.rmtree(chunk_output_dir)
os.makedirs(chunk_output_dir)

for ii_chunk in range(number_of_chunks):
    # setting up output dir for chunk
    run_name = f"{base_run_name}_chunk_{ii_chunk:03d}"

    # setting up the release groups for current chunk
    n = number_of_release_groups_per_chunk
    # Determine which polygons to process in this chunk
    if len(release_polygons) > 1:
        polygons_to_process = release_polygons[ii_chunk * n : (ii_chunk + 1) * n]
    else:
        polygons_to_process = release_polygons

    # Print info about current chunk
    print(f"* processing {len(polygons_to_process)} release groups in this chunk")

    # "------------------------------ model setup  ---------------------------"
    run_AU_to_NZ_model(
        number_of_threads,
        hindcast_dir_nz,
        hindcast_mask_nz,
        hindcast_dir_au,
        hindcast_mask_au,
        hgrid_file_name,
        durationDays,
        timeStep,
        releaseStartDate,
        releaseInterval,
        pulseSize,
        statsInterval,
        nz_coastal_polygons,
        chunk_output_dir,
        run_name,
        polygons_to_process,
    )
