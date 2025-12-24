import pygame
import math
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *


R1, R2 = 0.8, 0.25
stacks, slices = 24, 24 #сегменты по бол/ мал кр

pygame.init()
screen = pygame.display.set_mode((1000, 700), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Тор")
pygame.event.set_grab(True)

#настройки OpenGL
glClearColor(0.0, 0.0, 0.0, 1)
glEnable(GL_DEPTH_TEST)
glEnable(GL_CULL_FACE)
glCullFace(GL_BACK)
glFrontFace(GL_CW)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(50, 1000 / 700, 0.1, 50)
glMatrixMode(GL_MODELVIEW)

glDisable(GL_LIGHTING)

clock = pygame.time.Clock()
angle_x, angle_y = 45, 30

#Прожектор
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
LIGHT_CENTER_X = SCREEN_WIDTH // 2
LIGHT_WIDTH = 300
SCREEN_LIGHT_MIN = LIGHT_CENTER_X - LIGHT_WIDTH // 2
SCREEN_LIGHT_MAX = LIGHT_CENTER_X + LIGHT_WIDTH // 2
MAX_DISTANCE = LIGHT_WIDTH // 2

#Параметры освещения
AMBIENT = 0.4
LIGHT_INTENSITY = 0.6

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            running = False
    keys = pygame.key.get_pressed()
    if keys[K_a]:  angle_y -= 2
    if keys[K_d]:  angle_y += 2
    if keys[K_w]:  angle_x -= 2
    if keys[K_s]:  angle_x += 2

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    gluLookAt(0, 0, 3.0, 0, 0, 0, 0, 1, 0)

    glRotatef(angle_x, 1, 0, 0)
    glRotatef(angle_y, 0, 1, 0)

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    #Треугольники
    glBegin(GL_TRIANGLES)
    #выч-е углов для параметр.коор-т тора
    for i in range(stacks):
        for j in range(slices):
            phi1 = 2 * math.pi * i / stacks #угол по бол кр
            phi2 = 2 * math.pi * (i + 1) / stacks
            theta1 = 2 * math.pi * j / slices #угол по мал кр
            theta2 = 2 * math.pi * (j + 1) / slices

            #Вер-ы 1 треуг(для пол-я парам-о ур-я тора)
            v1 = (
                (R1 + R2 * math.cos(theta1)) * math.cos(phi1),
                (R1 + R2 * math.cos(theta1)) * math.sin(phi1),
                R2 * math.sin(theta1)
            )

            v2 = (
                (R1 + R2 * math.cos(theta2)) * math.cos(phi1),
                (R1 + R2 * math.cos(theta2)) * math.sin(phi1),
                R2 * math.sin(theta2)
            )

            v3 = (
                (R1 + R2 * math.cos(theta1)) * math.cos(phi2),
                (R1 + R2 * math.cos(theta1)) * math.sin(phi2),
                R2 * math.sin(theta1)
            )

            #Вер-ы 2 треуг
            v4 = (
                (R1 + R2 * math.cos(theta2)) * math.cos(phi2),
                (R1 + R2 * math.cos(theta2)) * math.sin(phi2),
                R2 * math.sin(theta2)
            )

            #Пол-м четыр-к
            triangles = [
                [v1, v2, v3],  # 1 треуг
                [v2, v4, v3]  # 2 треуг
            ]

            #Рас-м освещение для треуг
            for tri_idx, triangle in enumerate(triangles):
                #Прое-я в экранные коор
                screen_points = []

                for vertex in triangle:
                    #Выч-я для матр-ы вращ-я
                    cos_x = math.cos(math.radians(angle_x))
                    sin_x = math.sin(math.radians(angle_x))
                    cos_y = math.cos(math.radians(angle_y))
                    sin_y = math.sin(math.radians(angle_y))

                    x, y, z = vertex

                    #Вращ-е по Y
                    x_rot_y = x * cos_y - z * sin_y
                    z_rot_y = x * sin_y + z * cos_y
                    y_rot_y = y

                    # Вращение по X
                    x_rot = x_rot_y
                    y_rot = y_rot_y * cos_x - z_rot_y * sin_x
                    z_rot = y_rot_y * sin_x + z_rot_y * cos_x

                    # Преобр-е в 2D
                    perspective = 3.0 / (3.0 - z_rot)

                    # Экранные коор-ты (центр 500, 350)
                    screen_x = 500 + x_rot * perspective * 300
                    screen_y = 350 - y_rot * perspective * 300

                    screen_points.append((screen_x, screen_y))

                #Центр треуг по X
                screen_center_x = (screen_points[0][0] + screen_points[1][0] + screen_points[2][0]) / 3

               #Пров-а освещ-я
                if screen_center_x < SCREEN_LIGHT_MIN or screen_center_x > SCREEN_LIGHT_MAX:
                    #Если ВНЕ световой полосы
                    intensity = AMBIENT
                else:
                    #Если ВНУТРИ световой полосы
                    distance_from_center = abs(screen_center_x - LIGHT_CENTER_X)
                    gradient = max(0.0, 1.0 - distance_from_center / MAX_DISTANCE)

                    intensity = AMBIENT + LIGHT_INTENSITY * gradient
                    intensity = min(1.0, intensity)

                dark_color = (0.4, 0.1, 0.1)
                light_color = (1.0, 0.2, 0.2)

                #Интерполяция 0 = ambient, 1 = полный свет
                if intensity <= AMBIENT:
                    factor = 0.0
                else:
                    factor = (intensity - AMBIENT) / LIGHT_INTENSITY

                r = dark_color[0] + (light_color[0] - dark_color[0]) * factor
                g = dark_color[1] + (light_color[1] - dark_color[1]) * factor
                b = dark_color[2] + (light_color[2] - dark_color[2]) * factor

                glColor3f(r, g, b)

                #Рисуем треуг
                if tri_idx == 0:
                    glVertex3f(v1[0], v1[1], v1[2])
                    glVertex3f(v2[0], v2[1], v2[2])
                    glVertex3f(v3[0], v3[1], v3[2])
                else:
                    glVertex3f(v2[0], v2[1], v2[2])
                    glVertex3f(v4[0], v4[1], v4[2])
                    glVertex3f(v3[0], v3[1], v3[2])

    glEnd()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
