# Embedded in the standalone Stage 6 script by _build_stage6.py.
def create_hollow_transition(name, radius_back, radius_front, z_back, z_front,
                             collection, material, parent=None, wall=0.014):
    """Open sheet-metal sleeve/bell in local Z; no disk obscures the fan blades."""
    existing = bpy.data.objects.get(name)
    if existing:
        return existing
    segments = 40
    vertices = []
    for radius, zz in ((radius_back, z_back), (radius_front, z_front),
                       (radius_back - wall, z_back), (radius_front - wall, z_front)):
        vertices.extend((radius * math.cos(i * math.tau / segments),
                         radius * math.sin(i * math.tau / segments), zz)
                        for i in range(segments))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.extend(((i, j, segments + j, segments + i),
                      (2 * segments + i, 3 * segments + i, 3 * segments + j, 2 * segments + j),
                      (i, 2 * segments + i, 2 * segments + j, j),
                      (segments + i, segments + j, 3 * segments + j, 3 * segments + i)))
    mesh = bpy.data.meshes.new(name + '_DATA')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    obj.parent = parent
    shade_smooth(obj)
    return obj


def create_axial_rotor(name, radius, collection, parent, face_z=0.0):
    # Local +Z is the visible/air-facing side of the assembly.
    for blade_index in range(7):
        angle = blade_index * math.tau / 7.0
        radial = radius * 0.53
        blade = create_box(f'{name}_BLADE_{blade_index:02d}',
                           (radial * math.cos(angle), radial * math.sin(angle), face_z - 0.065),
                           (radius * 0.73, radius * 0.24, 0.023),
                           collection, MAT_GALV, 0.022, parent)
        blade.rotation_euler = (0.0, math.radians(13.0), angle + 0.20)
    create_cylinder(name + '_HUB', (0.0, 0.0, face_z - 0.030), radius * 0.20, 0.095,
                    collection, MAT_STRUCTURAL, vertices=24, bevel=0.008, parent=parent)
    for ring, factor in enumerate((0.30, 0.47, 0.65, 0.82, 0.97)):
        create_hoop(f'{name}_GRILLE_RING_{ring:02d}', (0, 0, face_z + 0.018),
                    radius * factor, 0.006, collection, MAT_DARK_METAL, parent)
    for spoke in range(12):
        angle = spoke * math.tau / 12
        create_cylinder_between(f'{name}_GRILLE_SPOKE_{spoke:02d}',
                                (0, 0, face_z + 0.028),
                                (radius * math.cos(angle), radius * math.sin(angle), face_z + 0.008),
                                0.005, collection, MAT_GALV, vertices=6, parent=parent)
    create_cylinder(name + '_CENTER_BADGE', (0, 0, face_z + 0.039), radius * 0.115, 0.012,
                    collection, MAT_GALV, vertices=20, bevel=0.003, parent=parent)


def create_side_fan(name, side, yy):
    # The front-left fan stays clear of the side door opening and its trim.
    if side < 0 and abs(yy - SIDE_DOOR_Y) < 0.85:
        yy = SIDE_DOOR_Y + SIDE_DOOR_WIDTH / 2.0 + 0.65
    root = ensure_empty(name + '_ROOT', COL_SIDE_FANS,
                        (side * (ROOM_WIDTH / 2.0 - 0.17), yy, SIDE_FAN_Z), size=0.09)
    root.rotation_euler = (0, -side * math.pi / 2.0, 0)
    root['face_direction'] = 'inward toward racks'
    root['nominal_diameter_m'] = SIDE_FAN_DIAMETER
    radius = SIDE_FAN_DIAMETER / 2.0
    frame_width = SIDE_FAN_DIAMETER + 0.14
    half_frame = (frame_width - 0.065) / 2
    for index, offset in enumerate((-half_frame, half_frame)):
        create_box(f'{name}_FRAME_H_{index}', (0, offset, -0.035),
                   (frame_width, 0.065, 0.18), COL_SIDE_FANS, MAT_STRUCTURAL, 0.007, root)
        create_box(f'{name}_FRAME_V_{index}', (offset, 0, -0.035),
                   (0.065, frame_width, 0.18), COL_SIDE_FANS, MAT_STRUCTURAL, 0.007, root)
    create_hollow_transition(name + '_CASING', radius + 0.018, radius + 0.018,
                             -0.12, 0.070, COL_SIDE_FANS, MAT_GALV, root)
    create_hoop(name + '_FRONT_FLANGE', (0, 0, 0.070), radius + 0.019, 0.015,
                COL_SIDE_FANS, MAT_STRUCTURAL, root)
    create_axial_rotor(name, radius, COL_SIDE_FANS, root, face_z=0.074)
    for index, (xx, yy_local) in enumerate(((-half_frame, -half_frame), (-half_frame, half_frame),
                                           (half_frame, -half_frame), (half_frame, half_frame))):
        create_hex_bolt(f'{name}_BOLT_{index}', (xx, yy_local, 0.062), axis='Z',
                        radius=0.018, depth=0.020, collection=COL_SIDE_FANS,
                        material=MAT_GALV, parent=root)
    create_bezier_curve(name + '_POWER_CABLE',
                        [(0.15, half_frame, -0.09), (0.16, half_frame + 0.10, -0.07),
                         (0.37, half_frame + 0.14, -0.12)],
                        COL_SIDE_FANS, MAT_RUBBER, 0.009, bevel_resolution=1, parent=root)
