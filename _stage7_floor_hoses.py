# Generic set-dressing hoses and closed storage drums, for the game scene.
COL_FLOOR_HOSES = ensure_collection('ENV_FLOOR_HOSES', ROOT)
COL_STORAGE_DRUMS = ensure_collection('ENV_STORAGE_DRUMS', ROOT)
MAT_DRUM_BODY = make_simple_material('MAT_Storage_Drum', (0.23, 0.25, 0.22), 0.52)
MAT_DRUM_LABEL = make_simple_material('MAT_Storage_Drum_Label', (0.67, 0.65, 0.55), 0.88)


def create_floor_hoses():
    for side, label in ((-1, 'LEFT'), (1, 'RIGHT')):
        drum_x, drum_y = side * 3.10, 3.91
        trunk_x = side * 1.075
        prefix = f'FLOOR_HOSE_{label}'
        # Closed, unbranded containers; visual props only.
        create_cylinder(f'STORAGE_DRUM_{label}_BODY', (drum_x, drum_y, 0.47), 0.29, 0.88,
                        COL_STORAGE_DRUMS, MAT_DRUM_BODY, vertices=32, bevel=0.035)
        for ring, zz in enumerate((0.08, 0.29, 0.65, 0.88)):
            create_hoop(f'STORAGE_DRUM_{label}_RIB_{ring}', (drum_x, drum_y, zz),
                        0.293, 0.014, COL_STORAGE_DRUMS, MAT_DARK_METAL)
        create_cylinder(f'STORAGE_DRUM_{label}_LID', (drum_x, drum_y, 0.925), 0.285, 0.04,
                        COL_STORAGE_DRUMS, MAT_DARK_METAL, vertices=32, bevel=0.012)
        create_cylinder(f'STORAGE_DRUM_{label}_CAP', (drum_x + side * 0.12, drum_y, 0.960),
                        0.052, 0.035, COL_STORAGE_DRUMS, MAT_STRUCTURAL, vertices=16, bevel=0.005)
        create_box(f'STORAGE_DRUM_{label}_LABEL', (drum_x, drum_y - 0.288, 0.52),
                   (0.19, 0.012, 0.22), COL_STORAGE_DRUMS, MAT_DRUM_LABEL, 0.008)
        create_cylinder_between(f'STORAGE_DRUM_{label}_PORT',
                                (drum_x, drum_y - 0.25, 0.22), (drum_x, drum_y - 0.36, 0.22),
                                0.046, COL_STORAGE_DRUMS, MAT_DARK_METAL, vertices=16)
        # A compact closed connection box sits beside each drum.
        box_x = side * 2.52
        create_box(f'STORAGE_DRUM_{label}_CONNECTION_BOX', (box_x, 3.78, 0.15),
                   (0.40, 0.30, 0.27), COL_STORAGE_DRUMS, MAT_STRUCTURAL, 0.035)
        create_box(f'STORAGE_DRUM_{label}_BOX_LID', (box_x, 3.78, 0.296),
                   (0.36, 0.26, 0.025), COL_STORAGE_DRUMS, MAT_GALV, 0.008)
        create_bezier_curve(prefix + '_DRUM_LINK',
                            [(drum_x, drum_y - 0.36, 0.22), (drum_x - side * 0.10, 3.43, 0.13),
                             (box_x + side * 0.28, 3.47, 0.075), (box_x, 3.62, 0.16)],
                            COL_FLOOR_HOSES, MAT_RUBBER, 0.034, bevel_resolution=2)
        # Main run hugs the inner rack edge. The central drain remains clear.
        create_bezier_curve(prefix + '_MAIN',
                            [(box_x - side * 0.20, 3.78, 0.15), (side * 2.07, 3.66, 0.085),
                             (side * 1.36, 3.39, 0.052), (trunk_x, 2.87, 0.043),
                             (trunk_x + side * 0.025, 1.55, 0.043),
                             (trunk_x - side * 0.018, -0.70, 0.043),
                             (trunk_x + side * 0.018, -3.02, 0.043),
                             (trunk_x, -4.56, 0.043)],
                            COL_FLOOR_HOSES, MAT_RUBBER, 0.029, bevel_resolution=2)
        # A thinner companion cable has a little slack, rather than a ruler-straight path.
        create_bezier_curve(prefix + '_FLOOR_CABLE',
                            [(box_x, 3.93, 0.12), (side * 2.0, 3.97, 0.027),
                             (side * 1.43, 3.57, 0.027), (side * 1.54, 3.29, 0.027),
                             (side * 1.30, 3.15, 0.027), (side * 0.98, 2.55, 0.027),
                             (side * 1.01, 0.45, 0.027), (side * 0.96, -1.65, 0.027),
                             (side * 1.00, -4.40, 0.027)],
                            COL_FLOOR_HOSES, MAT_DARK_METAL, 0.012, bevel_resolution=2)

        rack_x = RACK_X_POSITIONS[0 if side < 0 else 1]
        for bay, yy in enumerate(LIGHT_Y_POSITIONS):
            for index, (dx, dy) in enumerate(module_placeholder_offsets(PLACEHOLDERS_PER_MODULE)):
                px, py = rack_x + dx, yy + dy
                name = f'{prefix}_POT_{bay:02d}_{index:02d}'
                floor_y = yy - 0.66 + index * 0.095
                approach_y = py - 0.47 - index * 0.075
                crest_z = PLATFORM_TOP_Z + POT_HEIGHT + 0.15 + index * 0.025
                # Rise outside the rack; cross its frame above the platform, not through it.
                points = [(trunk_x, floor_y, 0.062),
                          (side * 1.12, approach_y, 0.20),
                          (side * 1.12, approach_y, 0.54),
                          (side * 1.15, approach_y, crest_z),
                          (px, approach_y, crest_z + 0.025),
                          (px, py - 0.26, crest_z),
                          (px, py - 0.18, PLATFORM_TOP_Z + POT_HEIGHT + 0.015)]
                hose = create_bezier_curve(name, points, COL_FLOOR_HOSES, MAT_RUBBER,
                                           0.021, bevel_resolution=2)
                # Keep the short ribbed rise straight so its ribs stay attached.
                spline_points = hose.data.splines[0].bezier_points
                spline_points[1].handle_right_type = 'VECTOR'
                spline_points[2].handle_left_type = 'VECTOR'
                # Short corrugated section around the vertical rise.
                for rib in range(8):
                    zz = 0.29 + rib * 0.024
                    create_hoop(f'{name}_RIB_{rib:02d}',
                                (side * 1.12, approach_y, zz), 0.025, 0.004,
                                COL_FLOOR_HOSES, MAT_RUBBER)
                endpoint = points[-1]
                start = Vector(endpoint) + (Vector(points[-2]) - Vector(endpoint)).normalized() * 0.085
                create_cylinder_between(name + '_RIM_COUPLING', start, endpoint,
                                        0.032, COL_FLOOR_HOSES, MAT_DARK_METAL, vertices=16)
                create_cylinder_between(name + '_FLOOR_COUPLING',
                                        (trunk_x, floor_y - 0.032, 0.05),
                                        (trunk_x, floor_y + 0.032, 0.05),
                                        0.036, COL_FLOOR_HOSES, MAT_DARK_METAL, vertices=16)


create_floor_hoses()
