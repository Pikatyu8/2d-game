# tests/test_acceptance.py
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame
from core.game import Game
from entities.projectile import Projectile
from entities.enemy import Enemy

class TestGameAcceptanceScenarios(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def test_level_loading_and_mode_switching(self):
        # Сценарий: Игра инициализируется в режиме геймплея, затем переключается в редактор уровней
        self.assertEqual(self.game.editor_mode, "GAMEPLAY")
        self.assertIsNotNone(self.game.player)
        self.assertTrue(len(self.game.platforms) > 0)

        # Симулируем нажатие 'E' (переключение в LEVEL_EDITOR)
        # Напрямую вызываем логику переключения для тестирования состояния
        self.game.editor_mode = "LEVEL_EDITOR"
        self.game.rebuild_objects()
        
        self.assertEqual(self.game.editor_mode, "LEVEL_EDITOR")
        # В режиме редактора у игрока должна сохраняться валидная координатная сетка
        self.assertIsNotNone(self.game.player_start_obj)

    def test_enemy_ai_chase_trigger(self):
        # Сценарий: Враг замечает приблизившегося игрока
        # Спавним врага и игрока рядом
        enemy_data = {
            "name": "Heavy Knight Test",
            "x": 100, "y": 300, "hp": 5,
            "body": {"type": "rectangle", "w": 40, "h": 60},
            # Увеличиваем range_x, чтобы враг не разворачивался влево на первом кадре
            "movement_config": {"type_move": "walking", "speed": 1.0, "range_x": 100},
            "detection": {
                "shape": {"type": "rectangle", "w": 200, "h": 100},
                "offset_x": 0, "offset_y": 0, "type": "following"
            }
        }
        test_enemy = Enemy(enemy_data, enemy_data)
        
        # Помещаем игрока вне зоны видимости (на расстоянии 500 пикселей)
        self.game.player.rect.x = 600
        self.game.player.rect.y = 300
        
        # Обновляем состояние врага
        test_enemy.update(platforms=[], gravity=0.5, player=self.game.player)
        self.assertEqual(test_enemy.state, "patrol")

        # Перемещаем игрока прямо в зону видимости врага
        self.game.player.rect.x = 150
        test_enemy.update(platforms=[], gravity=0.5, player=self.game.player)
        
        # Враг должен изменить статус на погоню
        self.assertEqual(test_enemy.state, "chase")

    def test_projectile_parry_deflection(self):
        # Сценарий: Снаряд летит в игрока, игрок активирует парирование, 
        # снаряд перенаправляется в сторону врага (меняет статус на friendly)
        
        # Спавним врага
        enemy_data = {
            "name": "Dummy Target", "x": 300, "y": 300, "hp": 5,
            "body": {"type": "rectangle", "w": 40, "h": 60}
        }
        test_enemy = Enemy(enemy_data, enemy_data)
        self.game.enemies = [test_enemy]
        
        # Настраиваем игрока
        self.game.player.rect.x = 100
        self.game.player.rect.y = 300
        self.game.player.facing = 1
        
        # Активируем у игрока щит парирования
        self.game.player.parry_timer = 5
        
        # Спавним вражеский снаряд, летящий влево в сторону игрока
        proj = Projectile(x=120, y=320, vx=-5.0, vy=0.0, damage=1, radius=8)
        self.game.projectiles = [proj]
        
        # Выполняем шаг обновления снаряда
        proj.update(platforms=[], player=self.game.player, game=self.game)
        
        # Ожидаем, что снаряд отразился (friendly = True) и летит в сторону ближайшего врага
        self.assertTrue(proj.friendly)
        self.assertTrue(proj.vx > 0) # Скорость инвертировалась в положительную сторону

if __name__ == "__main__":
    unittest.main()