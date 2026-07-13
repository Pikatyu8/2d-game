# core/physics.py
import pygame
import math
import colorsys  # Добавлен импорт для работы с цветовыми пространствами

def apply_movement_and_collisions(rect, vx, vy, platforms):
    collided_x = False
    rect.x += vx
    for plat in platforms:
        if rect.colliderect(plat.rect):
            collided_x = True
            if vx > 0: rect.right = plat.rect.left
            elif vx < 0: rect.left = plat.rect.right
                
    rect.y += vy
    on_ground = False
    for plat in platforms:
        if rect.colliderect(plat.rect):
            if vy > 0:
                rect.bottom = plat.rect.top
                vy = 0
                on_ground = True
            elif vy < 0:
                rect.top = plat.rect.bottom
                vy = 0
                
    return on_ground, vy, collided_x


# --- Математические функции для теоремы разделяющей оси (SAT) при повернутых хитбоксах ---
def get_axes(poly):
    axes = []
    for i in range(len(poly)):
        p1 = poly[i]
        p2 = poly[(i + 1) % len(poly)]
        edge = (p2[0] - p1[0], p2[1] - p1[1])
        normal = (-edge[1], edge[0])
        length = (normal[0]**2 + normal[1]**2) ** 0.5
        if length != 0:
            axes.append((normal[0] / length, normal[1] / length))
    return axes

def project(poly, axis):
    dots = [p[0] * axis[0] + p[1] * axis[1] for p in poly]
    return min(dots), max(dots)

def overlap(proj1, proj2):
    return proj1[1] >= proj2[0] and proj2[1] >= proj1[0]

def collides_polygon_polygon(poly_a, poly_b):
    axes = get_axes(poly_a) + get_axes(poly_b)
    for axis in axes:
        min_a, max_a = project(poly_a, axis)
        min_b, max_b = project(poly_b, axis)
        if not overlap((min_a, max_a), (min_b, max_b)):
            return False
    return True

def get_polygon_from_shape(stype, val):
    if stype == "rectangle":
        rect, angle = val
        w, h = rect.width, rect.height
        cx, cy = rect.centerx, rect.centery
        rad = math.radians(-angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        dx, dy = w / 2, h / 2
        poly = []
        for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
            rx = px * cos_a - py * sin_a + cx
            ry = px * sin_a + py * cos_a + cy
            poly.append((rx, ry))
        return poly
    elif stype == "circle":
        cx, cy, r = val
        poly = []
        for i in range(12):
            angle_rad = math.radians(i * 30)
            poly.append((cx + r * math.cos(angle_rad), cy + r * math.sin(angle_rad)))
        return poly
    return []

def get_bounding_circle(poly):
    if not poly:
        return (0, 0, 0)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    r_sq = max((p[0] - cx)**2 + (p[1] - cy)**2 for p in poly)
    return (cx, cy, r_sq ** 0.5)

def shapes_intersect(type_a, val_a, type_b, val_b):
    if type_a == "circle" and type_b == "circle":
        cx1, cy1, r1 = val_a
        cx2, cy2, r2 = val_b
        return ((cx1 - cx2)**2 + (cy1 - cy2)**2) <= (r1 + r2)**2
    
    poly_a = get_polygon_from_shape(type_a, val_a)
    poly_b = get_polygon_from_shape(type_b, val_b)
    
    cx_a, cy_a, r_a = get_bounding_circle(poly_a)
    cx_b, cy_b, r_b = get_bounding_circle(poly_b)
    dist_sq = (cx_a - cx_b)**2 + (cy_a - cy_b)**2
    if dist_sq > (r_a + r_b)**2:
        return False
        
    return collides_polygon_polygon(poly_a, poly_b)


# --- Функции парсинга и расчета гармонических (аналогичных) цветов ---
def parse_hex_color(hex_str):
    if not hex_str:
        return None
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    if len(hex_str) == 6:
        try:
            return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]
        except ValueError:
            return None
    return None

def get_analogous_colors(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # Смещение Hue на цветовом колесе (влево и вправо на 30 градусов)
    h_left = (h - 30.0 / 360.0) % 1.0
    h_right = (h + 30.0 / 360.0) % 1.0
    
    rgb_left = colorsys.hsv_to_rgb(h_left, s, v)
    rgb_right = colorsys.hsv_to_rgb(h_right, s, v)
    
    return (
        tuple(int(x * 255) for x in rgb_left),
        tuple(rgb),
        tuple(int(x * 255) for x in rgb_right)
    )