# Embedded into the standalone Stage 6 script. Generic environment dressing.
def create_wall_services():
    # Three metal pipe runs, upper ladder trays, bundled cables and vertical drops.
    # All longitudinal runs clear the enlarged fan housings and door headers.
    for side, label in ((-1, 'LEFT'), (1, 'RIGHT')):
        wall_x = side * (ROOM_WIDTH / 2.0 - 0.085)
        for run, (zz, radius) in enumerate(((3.16, 0.038), (3.30, 0.028), (3.43, 0.020))):
            create_cylinder_between(f'SERVICE_{label}_MAIN_PIPE_{run}',
                                    (wall_x, -5.30, zz), (wall_x, 5.38, zz),
                                    radius, COL_WALL_SERVICES, MAT_GALV, vertices=16)
            for clamp, yy in enumerate((-5.15, -2.65, -0.15, 2.35, 4.85)):
                create_ring_collar(f'SERVICE_{label}_PIPE_CLAMP_{run}_{clamp}',
                                   (wall_x, yy, zz), 'Y', radius + 0.014, 0.038,
                                   COL_WALL_SERVICES, MAT_STRUCTURAL)
                create_box(f'SERVICE_{label}_PIPE_STANDOFF_{run}_{clamp}',
                           (side * 3.97, yy, zz), (0.05, 0.055, 0.08),
                           COL_WALL_SERVICES, MAT_GALV, 0.003)

        # Ladder tray above the fans, spaced inward from the pipe runs.
        tray_x = side * 3.62
        for rail, dx in enumerate((-0.10, 0.10)):
            create_box(f'SERVICE_{label}_TRAY_RAIL_{rail}', (tray_x + dx, 0, 3.37),
                       (0.018, 10.90, 0.06), COL_WALL_SERVICES, MAT_GALV, 0.003)
        for rung in range(28):
            yy = -5.35 + rung * 10.70 / 27
            create_box(f'SERVICE_{label}_TRAY_RUNG_{rung:02d}', (tray_x, yy, 3.35),
                       (0.20, 0.022, 0.018), COL_WALL_SERVICES, MAT_GALV, 0.002)
        for cable, dx in enumerate((-0.061, -0.030, 0.0, 0.030, 0.061)):
            points = [(tray_x + dx, yy, 3.37 + 0.006 * math.sin(index * 1.8 + cable))
                      for index, yy in enumerate((-5.35, -3.3, -1.25, 0.8, 2.9, 5.30))]
            create_bezier_curve(f'SERVICE_{label}_CABLE_BUNDLE_{cable}', points,
                                COL_WALL_SERVICES, MAT_CABLE_ACCENT if cable == 0 else MAT_RUBBER,
                                0.009, bevel_resolution=1)

        for drop, yy in enumerate((-4.82, -0.20, 3.85)):
            # Drops avoid the side door and are kept in the 25 cm wall clearance.
            for run, offset in enumerate((-0.07, 0.07)):
                create_poly_curve(f'SERVICE_{label}_VERTICAL_PIPE_{drop}_{run}',
                                  [(wall_x, yy + offset + 0.12, 3.16),
                                   (wall_x, yy + offset, 3.04),
                                   (wall_x, yy + offset, 0.52)],
                                  COL_WALL_SERVICES, MAT_GALV, 0.026, bevel_resolution=2)
                for clamp, zz in enumerate((0.70, 1.45, 2.20, 2.87)):
                    create_ring_collar(f'SERVICE_{label}_DROP_CLAMP_{drop}_{run}_{clamp}',
                                       (wall_x, yy + offset, zz), 'Z', 0.038, 0.036,
                                       COL_WALL_SERVICES, MAT_STRUCTURAL)
            create_box(f'SERVICE_{label}_JUNCTION_{drop}', (side * 3.92, yy + 0.28, 2.36),
                       (0.12, 0.22, 0.30), COL_WALL_SERVICES, MAT_ELECTRICAL, 0.014)
            create_box(f'SERVICE_{label}_JUNCTION_FACE_{drop}', (side * 3.852, yy + 0.28, 2.36),
                       (0.015, 0.19, 0.265), COL_WALL_SERVICES, MAT_GALV, 0.005)
            create_bezier_curve(f'SERVICE_{label}_CABLE_DROP_{drop}',
                                [(tray_x, yy + 0.30, 3.37), (side * 3.83, yy + 0.32, 3.12),
                                 (side * 3.84, yy + 0.32, 2.69), (side * 3.88, yy + 0.28, 2.51)],
                                COL_WALL_SERVICES, MAT_RUBBER, 0.014, bevel_resolution=2)

    # Rear services bridge above the door rather than across its opening.
    for run, zz in enumerate((2.55, 2.70)):
        create_poly_curve(f'SERVICE_BACK_PIPE_{run}',
                          [(-3.87, 5.45, zz), (-3.75, 5.85, zz),
                           (3.75, 5.85, zz), (3.87, 5.45, zz)],
                          COL_WALL_SERVICES, MAT_GALV, 0.028, bevel_resolution=2)
    for cable in range(3):
        zz = 2.38 + cable * 0.032
        create_bezier_curve(f'SERVICE_BACK_CABLE_{cable}',
                            [(-3.78, 5.91, zz), (-1.95, 5.89, zz - 0.018),
                             (0, 5.91, zz), (1.95, 5.89, zz - 0.018), (3.78, 5.91, zz)],
                            COL_WALL_SERVICES, MAT_RUBBER, 0.010, bevel_resolution=1)


def create_ceiling_ducts():
    radius = CEILING_DUCT_DIAMETER / 2.0
    y_start, y_end = -5.10, DUCT_CENTER_Y
    sections = 10
    for segment in range(sections):
        a = y_start + (y_end - y_start) * segment / sections
        b = y_start + (y_end - y_start) * (segment + 1) / sections
        create_cylinder_between(f'CEILING_DUCT_MAIN_{segment:02d}',
                                (0, a, CEILING_DUCT_Z), (0, b, CEILING_DUCT_Z),
                                radius, COL_CEILING_DUCTS, MAT_GALV, vertices=40, bevel=0.004)
        create_ring_collar(f'CEILING_DUCT_JOINT_{segment:02d}',
                           (0, a, CEILING_DUCT_Z), 'Y', radius + 0.023, 0.048,
                           COL_CEILING_DUCTS, MAT_GALV)
        # Fine seam around each segment, giving the sheet metal a readable scale.
        create_ring_collar(f'CEILING_DUCT_SEAM_{segment:02d}',
                           (0, (a + b) / 2.0, CEILING_DUCT_Z), 'Y', radius + 0.005, 0.014,
                           COL_CEILING_DUCTS, MAT_DARK_METAL)
    create_ring_collar('CEILING_DUCT_REAR_JOIN', (0, y_end, CEILING_DUCT_Z),
                       'Y', radius + 0.025, 0.075, COL_CEILING_DUCTS, MAT_GALV)
    # The transverse rear duct and this trunk meet at a short vertical adapter.
    create_cylinder_between('CEILING_DUCT_REAR_ADAPTER', (0, y_end, DUCT_HEIGHT),
                            (0, y_end, CEILING_DUCT_Z), radius * 0.80,
                            COL_CEILING_DUCTS, MAT_GALV, vertices=32)
    create_cylinder_between('CEILING_DUCT_FRONT_CAP', (0, y_start - 0.025, CEILING_DUCT_Z),
                            (0, y_start, CEILING_DUCT_Z), radius + 0.006,
                            COL_CEILING_DUCTS, MAT_GALV, vertices=40)

    for mount, yy in enumerate((-4.55, -1.90, 0.60, 3.15, 5.20)):
        # Slender transverse channels at slab level; a suspended cradle below.
        create_box(f'CEILING_DUCT_CROSS_RAIL_{mount}', (0, yy, 3.555),
                   (ROOM_WIDTH - 0.20, 0.065, 0.055), COL_CEILING_DUCTS, MAT_GALV, 0.003)
        create_box(f'CEILING_DUCT_CRADLE_{mount}', (0, yy, 2.79),
                   (1.16, 0.055, 0.050), COL_CEILING_DUCTS, MAT_STRUCTURAL, 0.004)
        for side, xx in enumerate((-0.54, 0.54)):
            create_cylinder_between(f'CEILING_DUCT_HANGER_{mount}_{side}',
                                    (xx, yy, 2.79), (xx, yy, 3.54),
                                    0.009, COL_CEILING_DUCTS, MAT_GALV, vertices=8)
            create_hex_bolt(f'CEILING_DUCT_HANGER_NUT_{mount}_{side}',
                            (xx, yy, 2.755), axis='Z', radius=0.018, depth=0.020,
                            collection=COL_CEILING_DUCTS, material=MAT_GALV)
        create_ring_collar(f'CEILING_DUCT_STRAP_{mount}', (0, yy, CEILING_DUCT_Z),
                           'Y', radius + 0.014, 0.055, COL_CEILING_DUCTS, MAT_STRUCTURAL)

    for vent, yy in enumerate(LIGHT_Y_POSITIONS):
        name = f'CEILING_VENT_{vent:02d}'
        root = ensure_empty(name + '_ROOT', COL_CEILING_DUCTS,
                            (0, yy, CEILING_VENT_FACE_Z), size=0.10)
        root.rotation_euler = (math.pi, 0, 0)
        root['face_direction'] = 'vertically downward'
        root['nominal_diameter_m'] = CEILING_VENT_DIAMETER
        r = CEILING_VENT_DIAMETER / 2.0
        create_hollow_transition(name + '_NECK', 0.27, 0.27, -0.64, -0.27,
                                 COL_CEILING_DUCTS, MAT_GALV, root)
        create_hollow_transition(name + '_BELL', 0.27, r, -0.27, 0.0,
                                 COL_CEILING_DUCTS, MAT_GALV, root)
        create_hoop(name + '_NECK_COLLAR', (0, 0, -0.29), 0.283, 0.017,
                    COL_CEILING_DUCTS, MAT_STRUCTURAL, root)
        create_hoop(name + '_FRONT_FLANGE', (0, 0, 0), r + 0.010, 0.019,
                    COL_CEILING_DUCTS, MAT_STRUCTURAL, root)
        create_axial_rotor(name, r - 0.025, COL_CEILING_DUCTS, root, face_z=0.008)
        for bolt in range(8):
            angle = bolt * math.tau / 8
            create_hex_bolt(f'{name}_FLANGE_BOLT_{bolt}',
                            ((r + 0.008) * math.cos(angle), (r + 0.008) * math.sin(angle), 0.024),
                            axis='Z', radius=0.012, depth=0.018,
                            collection=COL_CEILING_DUCTS, material=MAT_GALV, parent=root)


if CREATE_WALL_SERVICES:
    create_wall_services()
if CREATE_CEILING_DUCTS:
    create_ceiling_ducts()

# The roof stays renderable from inside and can be shown in the viewport when needed.
if CREATE_CEILING:
    roof = bpy.data.objects.get('CEILING_SLAB')
    if roof:
        roof.hide_set(True)
        roof['viewport_note'] = 'Hidden for interior editing; enable the eye icon to show the roof.'

