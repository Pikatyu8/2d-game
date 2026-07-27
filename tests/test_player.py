# tests/test_player.py
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame
from entities.player import Player

class TestPlayerMechanics(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.config = {
            "start_x": 100,
            "start_y": 300,
            "speed": 5,
            "jump_force": 14,
            "gravity": 0.6
        }
        self.player = Player(self.config)

    def tearDown(self):
        pygame.quit()

    def test_initialization(self):
        self.assertEqual(self.player.rect.x, 100)
        self.assertEqual(self.player.rect.y, 300)
        self.assertEqual(self.player.hp, 5)
        self.assertFalse(self.player.is_attacking)

    def test_take_damage_normal(self):
        self.player.take_damage(amount=2, force_x=5.0)
        # HP должно уменьшиться с 5 до 3
        self.assertEqual(self.player.hp, 3)
        # Должен включиться таймер неуязвимости/мигания
        self.assertEqual(self.player.damage_flash_timer, 15)
        self.assertEqual(self.player.knockback_vx, 5.0)

    def test_take_damage_during_invulnerability(self):
        self.player.take_damage(amount=1, force_x=2.0)
        self.assertEqual(self.player.hp, 4)
        # Пока активен таймер мигания, урон не должен наноситься
        self.player.take_damage(amount=2, force_x=10.0)
        self.assertEqual(self.player.hp, 4)

    def test_parry_timing(self):
        # Имитируем успешное прожатие парирования
        self.player.parry_timer = self.player.parry_duration
        self.player.update(platforms=[], enemies=[])
        # Таймер парирования должен уменьшиться на 1 кадр
        self.assertEqual(self.player.parry_timer, self.player.parry_duration - 1)

    def test_respawn(self):
        self.player.take_damage(amount=10, force_x=0.0) # Смертельный урон
        # Должен сработать автоматический респаун в начальные координаты
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(self.player.rect.x, 100)
        self.assertEqual(self.player.rect.y, 300)

if __name__ == "__main__":
    unittest.main()