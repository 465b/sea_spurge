from oceantracker.main import OceanTracker

def run_AU_to_NZ_model(
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
):
    ot = OceanTracker()

    ot.settings(
        output_file_base=run_name,
        root_output_dir=chunk_output_dir,
        processors=number_of_threads,
        max_run_duration=3600 * 24 * durationDays,
        time_step=timeStep,
        restart_interval=30 * 24 * 3600,
        use_open_boundary=True,
        time_buffer_size=3,
        write_tracks=False,
    )

    ot.add_class(
        "nested_readers",
        class_name="oceantracker.reader.SCHISM_reader.SCHISMreader",
        input_dir=hindcast_dir_nz,
        file_mask=hindcast_mask_nz,
        grid_variable_map=dict(x="longitude", y="latitude"),  # remap x to long lat
        field_variable_map=dict(
            water_velocity=["vsurf"]
        ),  # remap vel to surf values in file
        hgrid_file_name=hgrid_file_name,
        # to convert the NZTM grid to LON LAT
        EPSG_code=2193,
    )

    ot.add_class(
        "reader",
        class_name="oceantracker.reader.GLORYS_reader.GLORYSreader",
        input_dir=hindcast_dir_au,
        file_mask=hindcast_mask_au,
        grid_variable_map=dict(x="longitude", y="latitude"),  # remap x to long lat
        field_variable_map=dict(
            water_velocity_depth_averaged=["u", "v"]
        ),  # remap vel to surf values in file
    )

    ot.add_class("solver", RK_order=2)

    # Add release groups for each polygon in
    for poly in polygons_to_process:
        ot.add_class(
            "release_groups",
            class_name="oceantracker.release_groups.polygon_release.PolygonRelease",
            name=poly["name"],
            points=poly["points"],
            release_interval=releaseInterval,
            pulse_size=pulseSize,
            release_at_surface=True,
            start=releaseStartDate,
            duration=durationDays * 24 * 3600,
            max_cycles_to_find_release_points=5,
            max_age=6 * 365 * 24 * 3600,
        )

    ot.add_class(
        "particle_statistics",
        class_name="oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased",
        name="shore_to_shore_poly_monthly",
        update_interval=statsInterval,
        polygon_list=nz_coastal_polygons,
        min_age_to_bin=0 * 365 * 24 * 3600,
        age_bin_size=30 * 24 * 3600,
        max_age_to_bin=6 * 365 * 24 * 3600,
    )

    ot.add_class("dispersion", A_H=0.1)

    case_info = ot.run()

    return case_info