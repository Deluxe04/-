import pygame
import math
import sys

# Инициализация Pygame
pygame.init()

# Вершины куба
vertices = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
]

# Грани куба
faces = [
    [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
    [2, 3, 7, 6], [0, 3, 7, 4], [1, 2, 6, 5]
]

# Параметры
k = 1.0
vector = [0, 0, 8]
screen_width = 1000
screen_height = 800
fov = 400

#Свет
LIGHT_POS = [0, 0, 0]
LIGHT_DIRECTION = [0, 0, 1]
LIGHT_CONE_ANGLE = 3.14
FALLOFF_DISTANCE = 20.0
AMBIENT = 0.4

#Зона света
LIGHT_X_MIN = -0.5
LIGHT_X_MAX = 0.8
LIGHT_INTENSITY = 1.2


# Создание окна
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("3D Куб ")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)


class CubeEngine:
    def __init__(self):
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0

    def scale(self, vertex):
        return [k * v for v in vertex]
#Матрицы поворота
    def rotate_x(self, vertex, angle):
        c, s = math.cos(angle), math.sin(angle)
        x, y, z = vertex
        return [x, c * y - s * z, s * y + c * z]

    def rotate_y(self, vertex, angle):
        c, s = math.cos(angle), math.sin(angle)
        x, y, z = vertex
        return [c * x + s * z, y, -s * x + c * z]

    def rotate_z(self, vertex, angle):
        c, s = math.cos(angle), math.sin(angle)
        x, y, z = vertex
        return [c * x - s * y, s * x + c * y, z]

    def translate(self, vertex):
        return [vertex[0] + vector[0], vertex[1] + vector[1], vertex[2] + vector[2]]

    def project(self, vertex):
        x, y, z = vertex
        factor = fov / (z + fov)
        x2d = int(screen_width / 2 + x * factor * 200)
        y2d = int(screen_height / 2 - y * factor * 200)
        return (x2d, y2d)

    def get_face_normal(self, vertices_3d, face):
        v1, v2, v3 = [vertices_3d[i] for i in face[:3]]
        dx1, dy1, dz1 = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
        dx2, dy2, dz2 = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
        nx = dy1 * dz2 - dz1 * dy2
        ny = dz1 * dx2 - dx1 * dz2
        nz = dx1 * dy2 - dy1 * dx2
        return (nx, ny, nz)


    def is_face_visible(self, vertices_3d, face):
        return True

    def calculate_spotlight(self, vertices_3d, projected_vertices, face):
        #Вершины грани
        v0, v1, v2, v3 = [vertices_3d[i] for i in face]
        p0, p1, p2, p3 = [projected_vertices[i] for i in face]

        #Внутренние точки(сетка 3x3)
        mid01_3d = [(v0[0] + v1[0]) / 2, (v0[1] + v1[1]) / 2, (v0[2] + v1[2]) / 2]
        mid12_3d = [(v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2, (v1[2] + v2[2]) / 2]
        mid23_3d = [(v2[0] + v3[0]) / 2, (v2[1] + v3[1]) / 2, (v2[2] + v3[2]) / 2]
        mid30_3d = [(v3[0] + v0[0]) / 2, (v3[1] + v0[1]) / 2, (v3[2] + v0[2]) / 2]
        center_3d = [(v0[0] + v1[0] + v2[0] + v3[0]) / 4, (v0[1] + v1[1] + v2[1] + v3[1]) / 4,
                     (v0[2] + v1[2] + v2[2] + v3[2]) / 4]

        # Проекция
        p_mid01 = self.project(mid01_3d)
        p_mid12 = self.project(mid12_3d)
        p_mid23 = self.project(mid23_3d)
        p_mid30 = self.project(mid30_3d)
        p_center = self.project(center_3d)

        # Треугольники(для теней)
        triangles = [
            # Левый нижний (3 треугольника)
            [p0, p1, p_mid01], [p0, p_mid01, p_center], [p1, p_mid01, p_center],

            # Левый верхний (3 треугольника)
            [p0, p3, p_mid30], [p0, p_mid30, p_center], [p3, p_mid30, p_center],

            # Правый нижний (2 треугольника)
            [p1, p2, p_mid12], [p1, p_mid12, p_center],

            # Правый верхний (2 треугольника)
            [p2, p3, p_mid23], [p3, p_mid23, p_center]
        ]

        triangle_intensities = []

        #Проверка треугольника
        for triangle in triangles:
            screen_center_x = sum(int(p[0]) for p in triangle) / 3

            # Световой интервал
            SCREEN_LIGHT_MIN = 420
            SCREEN_LIGHT_MAX = 620
            LIGHT_CENTER = 520

            if screen_center_x < SCREEN_LIGHT_MIN or screen_center_x > SCREEN_LIGHT_MAX:
                triangle_intensities.append(AMBIENT)
            else:
                distance_from_center = abs(screen_center_x - LIGHT_CENTER)
                max_distance = (SCREEN_LIGHT_MAX - SCREEN_LIGHT_MIN) / 2
                gradient = max(0, 1.0 - distance_from_center / max_distance)
                triangle_intensities.append(AMBIENT + LIGHT_INTENSITY * gradient)

        #Сред яркость
        avg_intensity = sum(triangle_intensities) / len(triangle_intensities)
        return min(1.0, avg_intensity)

    def render(self):
        #Тран-ия вершин
        transformed_vertices = []
        projected_vertices = []

        for v in vertices:
            vs = self.scale(v)
            v1 = self.rotate_x(vs, self.angle_x)
            v2 = self.rotate_y(v1, self.angle_y)
            v3 = self.rotate_z(v2, self.angle_z)
            vt = self.translate(v3)
            proj = self.project(vt)
            transformed_vertices.append(vt)
            projected_vertices.append(proj)


        screen.fill((20, 20, 50))
        BASE_COLOR = (100, 160, 255)

        # Сорт-а граней
        face_depths = []
        for face_idx, face in enumerate(faces):
            avg_z = sum(transformed_vertices[i][2] for i in face) / 4
            face_depths.append((avg_z, face_idx, face))

        face_depths.sort(reverse=True)

        rendered_faces = 0
        for depth, face_idx, face in face_depths:
            #Проверка освещ-я
            intensity = self.calculate_spotlight(transformed_vertices, projected_vertices, face)

            r = int(BASE_COLOR[0] * intensity)
            g = int(BASE_COLOR[1] * intensity)
            b = int(BASE_COLOR[2] * intensity)
            lit_color = (r, g, b)


            points = [projected_vertices[i] for i in face]
            pygame.draw.polygon(screen, lit_color, points)

        # 6. Обновление экрана
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False

        return True


def main():
    engine = CubeEngine()

    running = True
    while running:
        engine.angle_x += 0.005
        engine.angle_y += 0.004
        engine.angle_z += 0.003

        running = engine.handle_events()
        engine.render()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()








