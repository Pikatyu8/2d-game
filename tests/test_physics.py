# tests/test_physics.py
import unittest
import pygame
from core.physics import (
    apply_movement_and_collisions,
    collides_polygon_polygon,
    shapes_intersect
)
from config import resolve_json

class TestPhysicsAndResolution(unittest.TestCase):
    def setUp(self):
        # Настраиваем фиктивную платформу для проверки столкновений
        # В Pygame Rect работает без инициализации дисплея
        self.platform = pygame.Rect(0, 100, 200, 20)
        class MockPlatform:
            def __init__(self, rect):
                self.rect = rect
        self.platforms = [MockPlatform(self.platform)]

    def test_apply_movement_no_collision(self):
        # Персонаж находится в воздухе (координата y=50) и падает вниз
        rect = pygame.Rect(10, 50, 20, 20)
        on_ground, vy, collided_x = apply_movement_and_collisions(
            rect, vx=0, vy=10, platforms=self.platforms
        )
        self.assertFalse(on_ground)
        self.assertEqual(vy, 10)
        self.assertFalse(collided_x)
        self.assertEqual(rect.y, 60)

    def test_apply_movement_vertical_collision(self):
        # Персонаж касается платформы сверху
        rect = pygame.Rect(10, 90, 20, 20)
        on_ground, vy, collided_x = apply_movement_and_collisions(
            rect, vx=0, vy=15, platforms=self.platforms
        )
        # Ожидаем приземление на поверхность платформы (y=100 - height=20 = 80)
        self.assertTrue(on_ground)
        self.assertEqual(vy, 0)
        self.assertEqual(rect.bottom, 100)

    def test_polygon_polygon_collision_sat(self):
        # Два пересекающихся квадрата
        poly_a = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly_b = [(5, 5), (15, 5), (15, 15), (5, 15)]
        self.assertTrue(collides_polygon_polygon(poly_a, poly_b))

        # Два непересекающихся квадрата
        poly_c = [(20, 20), (30, 20), (30, 30), (20, 30)]
        self.assertFalse(collides_polygon_polygon(poly_a, poly_c))

    def test_shapes_intersect_circles(self):
        # Пересекающиеся круги
        circle_a = ("circle", (0, 0, 10))
        circle_b = ("circle", (15, 0, 10))
        self.assertTrue(shapes_intersect(circle_a[0], circle_a[1], circle_b[0], circle_b[1]))

        # Непересекающиеся круги
        circle_c = ("circle", (30, 0, 5))
        self.assertFalse(shapes_intersect(circle_a[0], circle_a[1], circle_c[0], circle_c[1]))

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