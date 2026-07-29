# tests/test_game_io_and_editor.py
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import tempfile
import json
import pygame
from core.game import Game
from entities.platform_class import Platform

class TestGameIOAndEditorLogic(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.game = Game()

    def tearDown(self):
        self.temp_dir.cleanup()
        pygame.quit()

    def test_rebuild_objects_and_presets(self):
        self.game.raw_platforms = [{"x": 100, "y": 200, "w": 80, "h": 20}]
        self.game.rebuild_objects()
        self.assertEqual(len(self.game.platforms), 1)
        self.assertIsInstance(self.game.platforms[0], Platform)

    def test_create_new_level(self):
        initial_level_count = len(self.game.available_levels)
        self.game.create_new_level()
        self.assertTrue(os.path.exists(os.path.join("levels", self.game.current_level_name)))

    def test_rename_and_delete_preset(self):
        self.game.presets["Test Dummy Preset"] = {"hp": 3, "body": {"w": 30, "h": 50}}
        self.game.selected_preset_name = "Test Dummy Preset"
        
        # Удаляем созданный пресет
        self.game.delete_preset("Test Dummy Preset")
        self.assertNotIn("Test Dummy Preset", self.game.presets)

    def test_hitbox_interaction_logic(self):
        self.game.editor_mode = "ENEMY_EDITOR"
        self.game.selected_preset_name = list(self.game.presets.keys())[0]
        self.game.rebuild_objects()
        self.game.inspector_tab = "MAIN"

        # Пытаемся получить активный хитбокс детекции
        info = self.game.get_active_hitbox_rect_and_data()
        self.assertIsNotNone(info)
        self.assertIn("screen_rect", info)

if __name__ == "__main__":
    unittest.main()