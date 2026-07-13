# core/game_parts/game_io.py
import os
import json
import copy
from config import (
    LEVELS_DIR, ENEMIES_DIR, TEMPLATES_FILE, resolve_json, ensure_level_file
)
from entities.platform_class import Platform
from entities.enemy import Enemy
from editor.editor_ui import PlayerStart

class GameIOMixin:
    def normalize_enemy_raw(self, raw_e):
        raw_e.setdefault("attacks", [])
        raw_e.setdefault("movements", [])
        raw_e.setdefault("sequences", [])
        raw_e.setdefault("flows", [])
        raw_e.setdefault("projectiles", []) 

        if "attack_zones" in raw_e:
            if not raw_e["attacks"]:
                for zone in raw_e["attack_zones"]:
                    if "attacks" in zone:
                        raw_e["attacks"].extend(zone["attacks"])
            raw_e.pop("attack_zones", None)
            
        raw_e.pop("attack_zone", None)

        for att in raw_e["attacks"]:
            shapes = att.setdefault("shapes", [])
            if not shapes:
                shapes.append({
                    "shape": {"template": "forms.rect", "w": 50, "h": 40},
                    "offset_x": att.get("offset_x", 10),
                    "offset_y": att.get("offset_y", 0),
                    "angle": att.get("angle", 0),
                    "delay": 0,
                    "duration": 10,
                    "damage": att.get("damage", 1),
                    "kb_angle": 0,
                    "kb_force": 12.0
                })
            for s in shapes:
                s.setdefault("delay", 0)
                s.setdefault("duration", 10)
                s.setdefault("damage", s.get("damage", att.get("damage", 1)))
                s.setdefault("kb_angle", 0)
                s.setdefault("kb_force", 12.0)
                s.setdefault("kb_angle_hit", s.get("kb_angle_hit", s.get("kb_angle", 0)))
                s.setdefault("kb_force_hit", s.get("kb_force_hit", s.get("kb_force", 12.0)))
                s.setdefault("kb_angle_parry", s.get("kb_angle_parry", s.get("kb_angle", 0)))
                s.setdefault("kb_force_parry", s.get("kb_force_parry", s.get("kb_force", 12.0) * 0.5))

        for m in raw_e["movements"]:
            phases = m.setdefault("phases", [])
            if not phases:
                phases.append({
                    "direction": "forward",
                    "curve": "fade_out",
                    "force_x": 8.0,
                    "force_y": 0.0,
                    "delay": 0,
                    "duration": 15
                })
            
            for p in phases:
                p.setdefault("direction", "forward")
                p.setdefault("curve", "fade_out")
                p.setdefault("force_x", 8.0)
                p.setdefault("force_y", 0.0)
                p.setdefault("delay", 0)
                p.setdefault("duration", 15)

        for proj in raw_e["projectiles"]:
            proj.setdefault("name", "Fireball")
            proj.setdefault("speed", 10.0)
            proj.setdefault("angle", 0.0)
            proj.setdefault("gravity", 0.0)
            proj.setdefault("damage", 1)
            proj.setdefault("radius", 8)
            proj.setdefault("shoot_cooldown", 30) # Частота стрельбы по умолчанию (кулдаун в кадрах)

        for seq in raw_e["sequences"]:
            seq.setdefault("chance", 0.5)
            seq.setdefault("post_cooldown", 30) # Наш новый параметр восстановления по умолчанию
            tz = seq.setdefault("trigger_zone", {})
            tz.setdefault("hold_time", 0)
            tz.setdefault("consecutive_limit", 3)
            tz.setdefault("accumulate_hold", True)

        for flow in raw_e["flows"]:
            flow.setdefault("chance", 0.5)
            flow.setdefault("post_cooldown", 30) # Добавляем нормализацию Post CD для потоков
            tz = flow.setdefault("trigger_zone", {})
            tz.setdefault("hold_time", 0)
            tz.setdefault("consecutive_limit", 3)
            tz.setdefault("accumulate_hold", True)

        raw_flows = raw_e.setdefault("flows", [])
        for flow in raw_flows:
            steps = flow.setdefault("steps", [])
            for step in steps:
                step.setdefault("is_random", False)
                step.setdefault("seq_pool", [step.get("seq_idx", 0)])

    def load_level(self):
        try:
            self.camera_x = 0  
            self.camera_y = 0
            self.zoom = 1.0  
            self.projectiles = []
            
            with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                self.templates = json.load(f)
                
            if os.path.exists(LEVELS_DIR):
                self.available_levels = sorted([
                    f for f in os.listdir(LEVELS_DIR) if f.endswith(".json")
                ])
                
            self.presets = {}
            self.preset_filepaths = {}
            for root, _, files in os.walk(ENEMIES_DIR):
                for file in files:
                    if file.endswith(".json"):
                        filepath = os.path.join(root, file)
                        preset_name = os.path.splitext(file)[0].replace("_", " ").title()
                        try:
                            with open(filepath, "r", encoding="utf-8") as pf:
                                p_data = json.load(pf)
                            self.normalize_enemy_raw(p_data)
                            self.presets[preset_name] = p_data
                            self.preset_filepaths[preset_name] = filepath
                        except Exception as e:
                            print(f"Ошибка загрузки пресета {filepath}: {e}")
            
            level_path = os.path.join(LEVELS_DIR, self.current_level_name)
            with open(level_path, "r", encoding="utf-8") as f:
                level_data = json.load(f)
            
            self.raw_platforms = level_data.get("platforms", [])
            self.raw_enemies = level_data.get("enemies", [])
            self.raw_player_cfg = level_data.get("player", {})
            
            for raw_e in self.raw_enemies:
                self.normalize_enemy_raw(raw_e)
            
            if "start_x" not in self.raw_player_cfg: self.raw_player_cfg["start_x"] = 100
            if "start_y" not in self.raw_player_cfg: self.raw_player_cfg["start_y"] = 300
            
            self.rebuild_objects()
            
            self.gravity = self.raw_player_cfg.get("gravity", 0.6)
            from entities.player import Player
            self.player = Player(self.raw_player_cfg)
            
            if self.presets:
                sorted_presets = sorted(list(self.presets.keys()))
                self.selected_preset_name = sorted_presets[0]
                
            self.flash_timer = 5
            print(f"Загружен уровень: {self.current_level_name}")
        except Exception as e:
            self.player = None
            print(f"Ошибка чтения конфигураций игры: {e}")

    def save_level(self):
        try:
            level_path = os.path.join(LEVELS_DIR, self.current_level_name)
            level_data = {
                "player": self.raw_player_cfg,
                "platforms": self.raw_platforms,
                "enemies": self.raw_enemies
            }
            with open(level_path, "w", encoding="utf-8") as f:
                json.dump(level_data, f, indent=4)
                
            for preset_name, preset_data in self.presets.items():
                filepath = self.preset_filepaths.get(preset_name)
                if not filepath:
                    filename = preset_name.lower().replace(" ", "_") + ".json"
                    filepath = os.path.join(ENEMIES_DIR, "common", filename)
                    self.preset_filepaths[preset_name] = filepath
                    
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(preset_data, f, indent=4)
                    
            print("Уровни и пресеты монстров сохранены!")
        except Exception as e:
            print(f"Ошибка сохранения JSON: {e}")

    def create_new_level(self):
        try:
            existing_numbers = []
            for f in os.listdir(LEVELS_DIR):
                if f.startswith("level_") and f.endswith(".json"):
                    try:
                        num = int(f.replace("level_", "").replace(".json", ""))
                        existing_numbers.append(num)
                    except ValueError:
                        pass
            next_num = max(existing_numbers) + 1 if existing_numbers else 1
            new_filename = f"level_{next_num}.json"
            
            new_level_data = {
                "player": {
                    "start_x": 100,
                    "start_y": 300,
                    "speed": 5,
                    "jump_force": 14,
                    "gravity": 0.6,
                    "attack_range": 65,
                    "attack_cooldown": 45
                },
                "platforms": [
                    {"x": 0, "y": 550, "w": 1000, "h": 50, "color": [80, 80, 80]},
                    {"x": 300, "y": 420, "w": 250, "h": 20, "color": [100, 150, 100]}
                ],
                "enemies": []
            }
            
            new_level_path = os.path.join(LEVELS_DIR, new_filename)
            with open(new_level_path, "w", encoding="utf-8") as f:
                json.dump(new_level_data, f, indent=4)
            
            print(f"Успешно создан новый уровень: {new_filename}")
            self.current_level_name = new_filename
            self.selected_instance = None
            self.load_level()
        except Exception as e:
            print(f"Ошибка создания нового файла уровня: {e}")

    def rebuild_objects(self):
        if self.selected_brush not in ("Selection", "Platform") and self.selected_brush not in self.presets:
            self.selected_brush = "Selection"

        self.raw_enemies = [
            raw_e for raw_e in self.raw_enemies 
            if (raw_e.get("preset") or raw_e.get("name")) in self.presets
        ]

        selected_raw = self.selected_instance.raw_data if self.selected_instance else None
        self.platforms = [Platform(p, p) for p in self.raw_platforms]
        
        for raw_e in self.raw_enemies:
            preset_name = raw_e.get("preset") or raw_e.get("name")
            if preset_name in self.presets:
                retained_keys = {}
                for k in ("x", "y", "name", "preset"):
                    if k in raw_e:
                        retained_keys[k] = raw_e[k]
                retained_keys["preset"] = preset_name
                
                raw_e.clear()
                
                template = self.presets[preset_name]
                for key, val in template.items():
                    if key not in ("x", "y", "name"):
                        raw_e[key] = copy.deepcopy(val)
                
                for k, v in retained_keys.items():
                    raw_e[k] = v

        self.enemies = []
        for raw_e in self.raw_enemies:
            resolved = resolve_json(raw_e, self.templates)
            resolved["x"] = raw_e.get("x", 200)
            resolved["y"] = raw_e.get("y", 200)
            self.enemies.append(Enemy(resolved, raw_e))
            
        self.player_start_obj = PlayerStart(self.raw_player_cfg)
            
        if self.selected_preset_name and self.selected_preset_name in self.presets:
            preset_raw = self.presets[self.selected_preset_name]
            resolved_preset = resolve_json(preset_raw, self.templates)
            resolved_preset["x"] = 480
            body_h = resolved_preset.get("body", {}).get("h", 60)
            resolved_preset["y"] = 400 - body_h
            self.dummy_enemy = Enemy(resolved_preset, preset_raw)
        else:
            self.dummy_enemy = None
            
        self.selected_instance = None
        if selected_raw:
            if self.player_start_obj.raw_data is selected_raw:
                self.selected_instance = self.player_start_obj
            for plat in self.platforms:
                if plat.raw_data is selected_raw:
                    self.selected_instance = plat
            for enemy in self.enemies:
                if enemy.raw_data is selected_raw:
                    self.selected_instance = enemy

    def rename_current_preset(self):
        old_name = self.selected_preset_name
        if not old_name:
            return
        new_name = self.prompt_text_input("Rename Preset", "Enter new name for the preset template:", old_name)
        if new_name and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            
            p_data = self.presets.pop(old_name)
            p_data["name"] = new_name
            self.presets[new_name] = p_data
            
            old_path = self.preset_filepaths.pop(old_name, None)
            if old_path:
                folder = os.path.dirname(old_path)
                filename = new_name.lower().replace(" ", "_") + ".json"
                new_path = os.path.join(folder, filename)
                try:
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                    self.preset_filepaths[new_name] = new_path
                except Exception as e:
                    print(f"Error renaming physical file: {e}")
                    self.preset_filepaths[new_name] = old_path
            else:
                self.preset_filepaths[new_name] = os.path.join(ENEMIES_DIR, "common", new_name.lower().replace(" ", "_") + ".json")
            
            self.selected_preset_name = new_name
            self.rebuild_objects()
            print(f"Preset renamed to: {new_name}")

    def delete_preset(self, preset_name):
        if preset_name in self.presets:
            self.presets.pop(preset_name)
            filepath = self.preset_filepaths.pop(preset_name, None)
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Preset file deleted: {filepath}")
                except Exception as e:
                    print(f"Error physically deleting preset file {filepath}: {e}")
            
            if self.selected_preset_name == preset_name:
                if self.presets:
                    sorted_presets = sorted(list(self.presets.keys()))
                    self.selected_preset_name = sorted_presets[0]
                else:
                    self.selected_preset_name = None

            if self.selected_brush == preset_name:
                self.selected_brush = "Selection"

            self.selected_trigger_idx = 0
            self.selected_attack_edit_idx = 0
            self.selected_box_idx = 0
            self.selected_move_edit_idx = 0
            self.selected_seq_idx = 0
            self.selected_step_idx = 0
            self.right_panel_scroll = 0
            
            self.rebuild_objects()

    def rename_selected_instance(self):
        if not self.selected_instance or not hasattr(self.selected_instance, "raw_data"):
            return
        raw_data = self.selected_instance.raw_data
        old_name = raw_data.get("name", "Enemy")
        new_name = self.prompt_text_input("Rename Instance", "Enter custom name for this specific instance:", old_name)
        if new_name and new_name.strip():
            raw_data["name"] = new_name.strip()
            self.rebuild_objects()
            print(f"Enemy instance renamed to: {raw_data['name']}")