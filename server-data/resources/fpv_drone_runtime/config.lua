Config = {
    mass = 1.8, gravity = 9.81, com = {0.0, 0.0, 0.005},
    linearDamping = 0.10, angularDamping = 0.20,
    response = 5.0, speed = 16.0, boostSpeed = 28.0, climb = 7.0,
    acceleration = 3.5, braking = 5.0, tilt = 32.0,
    mouseSensitivity = 12.0, lookResponse = 18.0,
    cameraResponse = 12.0,
    cameras = {
        {name='Perto', distance=1.8, height=0.50, fov=75.0},
        {name='Media', distance=3.5, height=0.85, fov=78.0},
        {name='Longe', distance=6.0, height=1.30, fov=82.0},
        {name='Primeira pessoa', distance=-0.30, height=0.05, fov=90.0, firstPerson=true}
    },
    rpm = { off=0, idle=1000, low=3000, cruise=6000, high=9000, max=12000 },
    blurStart = 1500, blurFull = 4000,
    sweepGuard = true,
    -- Local development prototype. Multiplayer ownership/synchronization needs a server layer.
    networked = false,
    motors = {
        {id='FL', model='fpv_prop_fl', x=-0.105, y=0.092, z=0.043, sign=-1},
        {id='FR', model='fpv_prop_fr', x=0.105, y=0.092, z=0.043, sign=1},
        {id='RL', model='fpv_prop_rl', x=-0.105, y=-0.092, z=0.043, sign=1},
        {id='RR', model='fpv_prop_rr', x=0.105, y=-0.092, z=0.043, sign=-1}
    }
}
