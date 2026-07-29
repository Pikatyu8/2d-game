# tests/test_projectile.py
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame
from entities.projectile import Projectile
from entities.player import Player
from entities.enemy import Enemy

class MockGame:
    def __init__(self, enemies=None):
        self.enemies = enemies or []
        self.hitstop_timer = 0
        self.sounds_played = []

    def play_sound(self, name):
        self.sounds_played.append(name)

class TestProjectileMechanics(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.player = Player({"start_x": 100, "start_y": 100, "speed": 5, "jump_force": 14, "gravity": 0.6})
        self.game = MockGame()

    def tearDown(self):
        pygame.quit()

    def test_projectile_hits_player_no_parry(self):
        proj = Projectile(x=105, y=110, vx=-5.0, vy=0.0, damage=2)
        destroyed = proj.update(platforms=[], player=self.player, game=self.game)
        self.assertTrue(destroyed)
        self.assertEqual(self.player.hp, 3)

    def test_projectile_parried_by_player(self):
        proj = Projectile(x=120, y=110, vx=-5.0, vy=0.0, damage=2)
        enemy_data = {"name": "Boss", "x": 300, "y": 100, "hp": 10, "body": {"type": "rectangle", "w": 40, "h": 60}}
        enemy = Enemy(enemy_data, enemy_data)
        self.game.enemies = [enemy]

        self.player.parry_timer = 5
        self.player.facing = 1

        destroyed = proj.update(platforms=[], player=self.player, game=self.game)
        self.assertFalse(destroyed)
        self.assertTrue(proj.friendly)
        self.assertGreater(proj.vx, 0)
        self.assertEqual(self.game.hitstop_timer, 3)
        self.assertIn("parry", self.game.sounds_played)

    def test_friendly_projectile_hits_enemy(self):
        proj = Projectile(x=100, y=100, vx=5.0, vy=0.0, damage=3)
        proj.friendly = True
        
        enemy_data = {"name": "Target", "x": 105, "y": 95, "hp": 5, "body": {"type": "rectangle", "w": 30, "h": 30}}
        enemy = Enemy(enemy_data, enemy_data)
        self.game.enemies = [enemy]

        destroyed = proj.update(platforms=[], player=self.player, game=self.game)
        self.assertTrue(destroyed)
        self.assertEqual(enemy.hp, 2)

    def test_homing_projectile_adjusts_velocity(self):
        proj = Projectile(x=0, y=0, vx=5.0, vy=0.0, homing=0.5)
        self.player.rect.x = 0
        self.player.rect.y = 100
        proj.update(platforms=[], player=self.player, game=self.game)
        self.assertGreater(proj.vy, 0)

    def test_projectile_hits_platform(self):
        proj = Projectile(x=50, y=50, vx=5.0, vy=0.0)
        class MockPlatform:
            def __init__(self):
                self.rect = pygame.Rect(40, 40, 30, 30)
        destroyed = proj.update(platforms=[MockPlatform()], player=self.player, game=self.game)
        self.assertTrue(destroyed)

    def test_projectile_out_of_bounds(self):
        proj = Projectile(x=5000, y=5000, vx=0.0, vy=0.0)
        destroyed = proj.update(platforms=[], player=self.player, game=self.game)
        self.assertTrue(destroyed)

if __name__ == "__main__":
    unittest.main()