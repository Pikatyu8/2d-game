# tests/test_physics.py
import unittest
import pygame
import math
from core.physics import (
    apply_movement_and_collisions,
    collides_polygon_polygon,
    shapes_intersect,
    parse_hex_color,
    get_analogous_colors,
    rotate_point,
    get_polygon_from_shape,
    get_bounding_circle
)
from config import resolve_json

class TestPhysicsAndResolution(unittest.TestCase):
    def setUp(self):
        self.platform = pygame.Rect(0, 100, 200, 20)
        class MockPlatform:
            def __init__(self, rect):
                self.rect = rect
        self.platforms = [MockPlatform(self.platform)]

    def test_apply_movement_no_collision(self):
        rect = pygame.Rect(10, 50, 20, 20)
        on_ground, vy, collided_x = apply_movement_and_collisions(
            rect, vx=0, vy=10, platforms=self.platforms
        )
        self.assertFalse(on_ground)
        self.assertEqual(vy, 10)
        self.assertFalse(collided_x)
        self.assertEqual(rect.y, 60)

    def test_apply_movement_vertical_collision(self):
        rect = pygame.Rect(10, 90, 20, 20)
        on_ground, vy, collided_x = apply_movement_and_collisions(
            rect, vx=0, vy=15, platforms=self.platforms
        )
        self.assertTrue(on_ground)
        self.assertEqual(vy, 0)
        self.assertEqual(rect.bottom, 100)

    def test_apply_movement_horizontal_collision(self):
        wall = pygame.Rect(100, 0, 20, 200)
        class MockPlatform:
            def __init__(self, rect):
                self.rect = rect
        rect = pygame.Rect(70, 50, 20, 20)
        on_ground, vy, collided_x = apply_movement_and_collisions(
            rect, vx=20, vy=0, platforms=[MockPlatform(wall)]
        )
        self.assertTrue(collided_x)
        self.assertEqual(rect.right, 100)

    def test_polygon_polygon_collision_sat(self):
        poly_a = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly_b = [(5, 5), (15, 5), (15, 15), (5, 15)]
        self.assertTrue(collides_polygon_polygon(poly_a, poly_b))

        poly_c = [(20, 20), (30, 20), (30, 30), (20, 30)]
        self.assertFalse(collides_polygon_polygon(poly_a, poly_c))

    def test_shapes_intersect_circles(self):
        circle_a = ("circle", (0, 0, 10))
        circle_b = ("circle", (15, 0, 10))
        self.assertTrue(shapes_intersect(circle_a[0], circle_a[1], circle_b[0], circle_b[1]))

        circle_c = ("circle", (30, 0, 5))
        self.assertFalse(shapes_intersect(circle_a[0], circle_a[1], circle_c[0], circle_c[1]))

    def test_parse_hex_color(self):
        self.assertEqual(parse_hex_color("#ff0000"), [255, 0, 0])
        self.assertEqual(parse_hex_color("00ff00"), [0, 255, 0])
        self.assertEqual(parse_hex_color("#f00"), [255, 0, 0])
        self.assertIsNone(parse_hex_color("invalid"))
        self.assertIsNone(parse_hex_color(None))

    def test_get_analogous_colors(self):
        color = (255, 0, 0)
        analogous = get_analogous_colors(color)
        self.assertEqual(len(analogous), 3)
        self.assertEqual(analogous[1], (255, 0, 0))

    def test_rotate_point(self):
        rx, ry = rotate_point((10, 0), (0, 0), 90)
        self.assertAlmostEqual(rx, 0, places=4)
        self.assertAlmostEqual(ry, 10, places=4)

    def test_get_polygon_from_shape(self):
        rect = pygame.Rect(0, 0, 20, 10)
        poly_rect = get_polygon_from_shape("rectangle", (rect, 0))
        self.assertEqual(len(poly_rect), 4)

        poly_circle = get_polygon_from_shape("circle", (0, 0, 10))
        self.assertEqual(len(poly_circle), 12)

        self.assertEqual(get_polygon_from_shape("unknown", None), [])

    def test_get_bounding_circle(self):
        self.assertEqual(get_bounding_circle([]), (0, 0, 0))
        poly = [(-10, -10), (10, -10), (10, 10), (-10, 10)]
        cx, cy, r = get_bounding_circle(poly)
        self.assertEqual((cx, cy), (0, 0))
        self.assertAlmostEqual(r, math.sqrt(200), places=4)

    def test_resolve_json_templates(self):
        templates = {
            "forms": {
                "rect": {"type": "rectangle", "w": "$w", "h": "$h"}
            }
        }
        node = {
            "template": "forms.rect",
            "w": 50,
            "h": 30
        }
        resolved = resolve_json(node, templates)
        self.assertEqual(resolved["type"], "rectangle")
        self.assertEqual(resolved["w"], 50)
        self.assertEqual(resolved["h"], 30)
        self.assertNotIn("template", resolved)

if __name__ == "__main__":
    unittest.main()