# core/physics.py
import pygame
import math

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
        # Аппроксимация круга 12-угольником для SAT
        for i in range(12):
            angle_rad = math.radians(i * 30)
            poly.append((cx + r * math.cos(angle_rad), cy + r * math.sin(angle_rad)))
        return poly
    return []

def shapes_intersect(type_a, val_a, type_b, val_b):
    if type_a == "circle" and type_b == "circle":
        cx1, cy1, r1 = val_a
        cx2, cy2, r2 = val_b
        return ((cx1 - cx2)**2 + (cy1 - cy2)**2) <= (r1 + r2)**2
    
    poly_a = get_polygon_from_shape(type_a, val_a)
    poly_b = get_polygon_from_shape(type_b, val_b)
    return collides_polygon_polygon(poly_a, poly_b)