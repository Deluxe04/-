import pygame
import math
import sys


def normalize(v):
    x, y, z = v
    l = math.sqrt(x*x + y*y + z*z)
    if l == 0:
        return (0.0, 0.0, 0.0)
    return (x/l, y/l, z/l)

def add(a, b):
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])

def mul(v, s):
    return (v[0]*s, v[1]*s, v[2]*s)

def midpoint(a, b):
    return ((a[0]+b[0]) * 0.5, (a[1]+b[1]) * 0.5, (a[2]+b[2]) * 0.5)

def rotate_y(v, angle):
    x, y, z = v
    c, s = math.cos(angle), math.sin(angle)
    return (x * c + z * s, y, -x * s + z * c)

def rotate_x(v, angle):
    x, y, z = v
    c, s = math.cos(angle), math.sin(angle)
    return (x, y * c - z * s, y * s + z * c)

#Созд-е икосаэдра
def create_icosahedron(radius=1.0):
    t = (1.0 + math.sqrt(5.0)) / 2.0  #золотое сеч-е

    verts = [
        (-1,  t,  0),
        ( 1,  t,  0),
        (-1, -t,  0),
        ( 1, -t,  0),

        ( 0, -1,  t),
        ( 0,  1,  t),
        ( 0, -1, -t),
        ( 0,  1, -t),

        ( t,  0, -1),
        ( t,  0,  1),
        (-t,  0, -1),
        (-t,  0,  1),
    ]
    #проец-е на сферу
    verts = [mul(normalize(v), radius) for v in verts]
    #треуг грани
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7,10), (0,10,11),
        (1, 5, 9), (5,11, 4), (11,10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4,11), (6, 2,10), (8, 6, 7), (9, 8, 1)
    ]

    return verts, faces

def subdivide_icosphere(verts, faces, radius=1.0, levels=1):
    for _ in range(levels): #разб-е для детализ-и
        new_faces = []
        #чтобы не вычитать дважды
        midpoint_cache = {}

        #поиск и соз-е серед ребра
        def get_midpoint(i1, i2):
            key = tuple(sorted((i1, i2)))
            if key in midpoint_cache:
                return midpoint_cache[key]
            v1 = verts[i1]
            v2 = verts[i2]
            m = midpoint(v1, v2)
            m = mul(normalize(m), radius)
            verts.append(m)
            idx = len(verts) - 1
            midpoint_cache[key] = idx
            return idx

        #серед 3 рёбер
        for a, b, c in faces:
            ab = get_midpoint(a, b)
            bc = get_midpoint(b, c)
            ca = get_midpoint(c, a)

            #раз-м на 4 треуг
            new_faces.append((a, ab, ca))
            new_faces.append((b, bc, ab))
            new_faces.append((c, ca, bc))
            new_faces.append((ab, bc, ca))

        faces = new_faces

    return verts, faces
#нор-и из центра
def compute_vertex_normals(verts):
    return [normalize(v) for v in verts]

#прое-я в 2D
def project_ortho(v, width, height, scale=200):
    x, y, z = v
    sx = int(x * scale + width / 2)
    sy = int(-y * scale + height / 2)
    return (sx, sy)


pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

RADIUS = 1.0
verts, faces = create_icosahedron(RADIUS)
verts, faces = subdivide_icosphere(verts, faces, radius=RADIUS, levels=2)
normals = compute_vertex_normals(verts)

CAMERA_POS = (0.0, 0.0, 0.0)

SPOT_DIR = (0.0, 0.0, 1.0)
SPOT_DIR = normalize(SPOT_DIR)
SPOT_COS_ANGLE = math.cos(math.radians(40))
ATTENUATION = 0.5

angle_y = 0.0
angle_x = 0.0

running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    angle_y += 0.7 * dt
    angle_x += 0.4 * dt

    screen.fill((5, 5, 10))
#преоб-я и прое-я
    transformed = []
    transformed_normals = []
    for v, n in zip(verts, normals):
        v_rot = rotate_y(v, angle_y)
        v_rot = rotate_x(v_rot, angle_x)
        n_rot = normalize(rotate_y(n, angle_y))
        n_rot = normalize(rotate_x(n_rot, angle_x))

        v_rot = (v_rot[0], v_rot[1], v_rot[2] + 3.0)
        transformed.append(v_rot)
        transformed_normals.append(n_rot)
    #сорт граней
    face_depths = []
    for idx, (a, b, c) in enumerate(faces):
        z_avg = (transformed[a][2] + transformed[b][2] + transformed[c][2]) / 3.0
        face_depths.append((z_avg, idx))
    face_depths.sort(reverse=True)
    #свет
    for s, fi in face_depths:
        a, b, c = faces[fi]
        v1 = transformed[a]
        v2 = transformed[b]
        v3 = transformed[c]

        mx = (v1[0] + v2[0] + v3[0]) / 3.0
        my = (v1[1] + v2[1] + v3[1]) / 3.0
        mz = (v1[2] + v2[2] + v3[2]) / 3.0
        m = (mx, my, mz)
    #вектор от центра гр к камере
        L = (CAMERA_POS[0] - m[0],
             CAMERA_POS[1] - m[1],
             CAMERA_POS[2] - m[2])

        dist = math.sqrt(L[0]*L[0] + L[1]*L[1] + L[2]*L[2])
        if dist == 0:
            continue
        L_dir = (L[0]/dist, L[1]/dist, L[2]/dist)

        spot_dot = -(L_dir[0]*SPOT_DIR[0] + L_dir[1]*SPOT_DIR[1] + L_dir[2]*SPOT_DIR[2])
        #пров-а освещ-и
        if spot_dot < SPOT_COS_ANGLE:
            base = 10
            color = (base, base, base)
        else:
            n1 = transformed_normals[a]
            n2 = transformed_normals[b]
            n3 = transformed_normals[c]
            nx = (n1[0] + n2[0] + n3[0]) / 3.0
            ny = (n1[1] + n2[1] + n3[1]) / 3.0
            nz = (n1[2] + n2[2] + n3[2]) / 3.0
            n_avg = normalize((nx, ny, nz))
            #закон Ламберта
            ndotl = max(0.0, n_avg[0]*L_dir[0] + n_avg[1]*L_dir[1] + n_avg[2]*L_dir[2])
            #затух-е с рас-м
            attenuation = 1.0 / (1.0 + ATTENUATION * dist * dist)

            spot_intensity = (spot_dot - SPOT_COS_ANGLE) / (1.0 - SPOT_COS_ANGLE)
            spot_intensity = max(0.0, min(1.0, spot_intensity))

            intensity = ndotl * attenuation * spot_intensity
            #параметры цвета
            base = 15
            max_add = 240
            val = base + int(max_add * intensity)
            val = max(0, min(255, val))
            color = (val, val, val)
#пр-я отри-и треуг
        p1 = project_ortho(v1, WIDTH, HEIGHT)
        p2 = project_ortho(v2, WIDTH, HEIGHT)
        p3 = project_ortho(v3, WIDTH, HEIGHT)
        pygame.draw.polygon(screen, color, (p1, p2, p3))

    pygame.display.flip()

pygame.quit()
sys.exit()
