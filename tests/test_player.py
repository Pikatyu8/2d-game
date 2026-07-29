# tests/test_player.py
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame
from entities.player import Player
from entities.enemy import Enemy

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
        self.assertEqual(self.player.hp, 3)
        self.assertEqual(self.player.damage_flash_timer, 15)
        self.assertEqual(self.player.knockback_vx, 5.0)

    def test_take_damage_during_invulnerability(self):
        self.player.take_damage(amount=1, force_x=2.0)
        self.assertEqual(self.player.hp, 4)
        self.player.take_damage(amount=2, force_x=10.0)
        self.assertEqual(self.player.hp, 4)

    def test_parry_timing(self):
        self.player.parry_timer = self.player.parry_duration
        self.player.update(platforms=[], enemies=[])
        self.assertEqual(self.player.parry_timer, self.player.parry_duration - 1)

    def test_attack_hits_enemy(self):
        enemy_data = {
            "name": "Target", "x": 140, "y": 300, "hp": 5,
            "body": {"type": "rectangle", "w": 30, "h": 50}
        }
        enemy = Enemy(enemy_data, enemy_data)
        
        self.player.is_attacking = True
        self.player.attack_timer = 40
        self.player.facing = 1
        
        self.player.update(platforms=[], enemies=[enemy])
        self.assertEqual(enemy.hp, 4)
        self.assertIn(enemy, self.player.hit_enemies)

    def test_respawn(self):
        self.player.take_damage(amount=10, force_x=0.0)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(self.player.rect.x, 100)
        self.assertEqual(self.player.rect.y, 300)

    def test_fall_below_world_triggers_respawn(self):
        self.player.rect.y = 2000
        self.player.update(platforms=[], enemies=[])
        self.assertEqual(self.player.rect.y, 300)

    def test_draw_player_modes(self):
        screen = pygame.Surface((800, 600))
        # Проверяем отрисовку без ошибок в обычных и спец-состояниях
        self.player.draw(screen)
        self.player.parry_timer = 5
        self.player.draw(screen)
        self.player.parry_success_flash_timer = 5
        self.player.draw(screen)

if __name__ == "__main__":
    unittest.main()