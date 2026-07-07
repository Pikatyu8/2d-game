# config.py
import os
import json

LEVELS_DIR = "levels"
ENEMIES_DIR = "enemies"
TEMPLATES_FILE = "templates.json"

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 600
CANVAS_OFFSET_X = 200
CANVAS_WIDTH = 1000

# Цветовая палитра
ENEMY_BODY_COLOR = (110, 110, 125)
ENEMY_HEAD_COLOR = (80, 80, 95)
PANEL_BG_COLOR = (25, 25, 30)
BORDER_COLOR = (50, 50, 60)

# Шаблоны по умолчанию
DEFAULT_TEMPLATES = {
    "forms": {
        "rect": {"type": "rectangle", "w": "$w", "h": "$h"},
        "circle": {"type": "circle", "r": "$r"}
    },
    "detections": {
        "front_view": {
            "shape": "$shape",
            "offset_x": "$offset_x",
            "offset_y": "$offset_y",
            "type": "following"
        },
        "radius_view": {
            "shape": "$shape",
            "offset_x": "$offset_x",
            "offset_y": "$offset_y",
            "type": "stationary"
        }
    }
}

# Враги по умолчанию (Новая структура с шаблонами, кейфреймами и шаблонами снарядов)
HEAVY_KNIGHT_PRESET = {
    "hp": 5,
    "body": { "template": "forms.rect", "w": 40, "h": 60 },
    "movement_config": { "type_move": "walking", "speed": 1.2, "range_x": 120 },
    "detection": {
        "template": "detections.front_view",
        "shape": { "template": "forms.rect", "w": 220, "h": 70 },
        "offset_x": 0, "offset_y": -10
    },
    "projectiles": [
        { "name": "Heavy Axe", "speed": 8.0, "angle": 0.0, "gravity": 0.05, "damage": 2, "radius": 10 }
    ],
    "attacks": [
        {
            "name": "Heavy Combo",
            "cooldown": 75,
            "windup": 35,
            "shapes": [
                {
                    "shape": { "template": "forms.rect", "w": 70, "h": 50 },
                    "offset_x": 65, "offset_y": -5, "angle": 0,
                    "delay": 0, "duration": 10, "damage": 1
                },
                {
                    "shape": { "template": "forms.rect", "w": 95, "h": 60 },
                    "offset_x": 88, "offset_y": -5, "angle": 0,
                    "delay": 16, "duration": 14, "damage": 2
                }
            ]
        },
        {
            "name": "Quick Jab",
            "cooldown": 40,
            "windup": 15,
            "shapes": [
                {
                    "shape": { "template": "forms.rect", "w": 50, "h": 30 },
                    "offset_x": 55, "offset_y": -5, "angle": 0,
                    "delay": 0, "duration": 8, "damage": 1
                }
            ]
        }
    ],
    "movements": [
        {
            "name": "Heavy Dash",
            "phases": [
                {
                    "direction": "forward",
                    "curve": "fade_out",
                    "force_x": 6.0,
                    "force_y": 0.0,
                    "delay": 0,
                    "duration": 20
                }
            ]
        },
        {
            "name": "Back Leap",
            "phases": [
                {
                    "direction": "away_from_player",
                    "curve": "fade_out",
                    "force_x": 4.0,
                    "force_y": 8.0,
                    "delay": 0,
                    "duration": 25
                }
            ]
        }
    ],
    "sequences": [
        {
            "name": "Slash & Retreat",
            "chance": 0.7,
            "cooldown": 120,
            "trigger_zone": {
                "shape": { "template": "forms.rect", "w": 90, "h": 50 },
                "offset_x": 10, "offset_y": 0, "type": "following"
            },
            "steps": [
                { "type": "attack", "idx": 0, "delay": 0, "trigger": "time" },
                { "type": "movement", "idx": 1, "delay": 35 }
            ]
        },
        {
            "name": "Surge Strike",
            "chance": 0.5,
            "cooldown": 100,
            "trigger_zone": {
                "shape": { "template": "forms.rect", "w": 180, "h": 60 },
                "offset_x": 10, "offset_y": 0, "type": "following"
            },
            "steps": [
                { "type": "movement", "idx": 0, "delay": 0 },
                { "type": "attack", "idx": 1, "delay": 20, "trigger": "time" }
            ]
        }
    ]
}

BAT_SCOUT_PRESET = {
    "hp": 3,
    "body": { "template": "forms.rect", "w": 30, "h": 30 },
    "movement_config": { "type_move": "flying", "speed": 2.2, "range_x": 70 },
    "detection": {
        "template": "detections.radius_view",
        "shape": { "template": "forms.circle", "r": 130 },
        "offset_x": 0, "offset_y": 0
    },
    "projectiles": [
        { "name": "Acid Spit", "speed": 10.0, "angle": 0.0, "gravity": 0.0, "damage": 1, "radius": 6 }
    ],
    "attacks": [
        {
            "name": "Triple Bite",
            "cooldown": 50,
            "windup": 20,
            "shapes": [
                {"shape": { "template": "forms.rect", "w": 40, "h": 40 }, "offset_x": 40, "offset_y": 0, "angle": 0, "delay": 0, "duration": 6, "damage": 1},
                {"shape": { "template": "forms.rect", "w": 40, "h": 40 }, "offset_x": 45, "offset_y": 0, "angle": 0, "delay": 12, "duration": 6, "damage": 1},
                {"shape": { "template": "forms.rect", "w": 45, "h": 45 }, "offset_x": 53, "offset_y": 3, "angle": 0, "delay": 24, "duration": 10, "damage": 1}
            ]
        }
    ],
    "movements": [
        {
            "name": "Swoop Forward",
            "phases": [
                {
                    "direction": "forward",
                    "curve": "fade_out",
                    "force_x": 8.0,
                    "force_y": 2.0,
                    "delay": 0,
                    "duration": 15
                }
            ]
        }
    ],
    "sequences": [
        {
            "name": "Swoop Combo",
            "chance": 1.0,
            "cooldown": 50,
            "trigger_zone": {
                "shape": { "template": "forms.rect", "w": 80, "h": 50 },
                "offset_x": 10, "offset_y": 0, "type": "following"
            },
            "steps": [
                { "type": "movement", "idx": 0, "delay": 0 },
                { "type": "attack", "idx": 0, "delay": 15, "trigger": "time" }
            ]
        }
    ]
}

GORGON_BOSS_PRESET = {
    "hp": 25,
    "body": { "template": "forms.rect", "w": 65, "h": 90 },
    "movement_config": { "type_move": "walking", "speed": 0.8, "range_x": 60 },
    "detection": {
        "template": "detections.front_view",
        "shape": { "template": "forms.rect", "w": 350, "h": 100 },
        "offset_x": 0, "offset_y": -15
    },
    "projectiles": [
        { "name": "Stone Arrow", "speed": 12.0, "angle": 0.0, "gravity": 0.0, "damage": 2, "radius": 8 }
    ],
    "attacks": [
        {
            "name": "Stomp & Cleave",
            "cooldown": 90,
            "windup": 45,
            "shapes": [
                {"shape": { "template": "forms.rect", "w": 80, "h": 60 }, "offset_x": 78, "offset_y": -5, "angle": 0, "delay": 0, "duration": 15, "damage": 1},
                {"shape": { "template": "forms.rect", "w": 140, "h": 80 }, "offset_x": 128, "offset_y": -15, "angle": 15, "delay": 25, "duration": 20, "damage": 3}
            ]
        },
        {
            "name": "Stone Gaze",
            "cooldown": 120,
            "windup": 50,
            "shapes": [
                {"shape": { "template": "forms.rect", "w": 300, "h": 40 }, "offset_x": 203, "offset_y": -45, "angle": 0, "delay": 0, "duration": 12, "damage": 2}
            ]
        }
    ],
    "movements": [
        {
            "name": "Boss Leap",
            "phases": [
                {
                    "direction": "to_player",
                    "curve": "fade_out",
                    "force_x": 5.0,
                    "force_y": 12.0,
                    "delay": 0,
                    "duration": 30
                }
            ]
        }
    ],
    "sequences": [
        {
            "name": "Boss Cleave Combo",
            "chance": 0.6,
            "cooldown": 90,
            "trigger_zone": {
                "shape": { "template": "forms.rect", "w": 130, "h": 90 },
                "offset_x": 10, "offset_y": 0, "type": "following"
            },
            "steps": [
                { "type": "attack", "idx": 0, "delay": 0, "trigger": "time" }
            ]
        },
        {
            "name": "Gaze Attack",
            "chance": 0.4,
            "cooldown": 120,
            "trigger_zone": {
                "shape": { "template": "forms.rect", "w": 300, "h": 60 },
                "offset_x": 20, "offset_y": -20, "type": "following"
            },
            "steps": [
                { "type": "attack", "idx": 1, "delay": 0, "trigger": "time" }
            ]
        }
    ]
}

DEFAULT_LEVEL_DATA = {
    "presets": {
        "Heavy Knight": HEAVY_KNIGHT_PRESET,
        "Bat Scout": BAT_SCOUT_PRESET
    }
}

LEVEL_1_DATA = {
    "player": {
        "start_x": 100, "start_y": 300,
        "speed": 5, "jump_force": 14, "gravity": 0.6,
        "attack_range": 65, "attack_cooldown": 45
    },
    "platforms": [
        {"x": 0, "y": 550, "w": 1000, "h": 50, "color": [80, 80, 80]},
        {"x": 300, "y": 420, "w": 250, "h": 20, "color": [100, 150, 100]},
        {"x": 100, "y": 300, "w": 150, "h": 20, "color": [100, 150, 100]}
    ],
    "enemies": [
        {
            "name": "Heavy Knight",
            "x": 350, "y": 360,
            "hp": 5,
            "body": { "template": "forms.rect", "w": 40, "h": 60 },
            "movement_config": { "type_move": "walking", "speed": 1.2, "range_x": 120 },
            "detection": {
                "template": "detections.front_view",
                "shape": { "template": "forms.rect", "w": 220, "h": 70 },
                "offset_x": 0, "offset_y": -10
            },
            "projectiles": [
                { "name": "Heavy Axe", "speed": 8.0, "angle": 0.0, "gravity": 0.05, "damage": 2, "radius": 10 }
            ],
            "attacks": [
                {
                    "name": "Heavy Combo",
                    "cooldown": 75, "windup": 35,
                    "shapes": [
                        {"shape": { "template": "forms.rect", "w": 70, "h": 50 }, "offset_x": 65, "offset_y": -5, "angle": 0, "delay": 0, "duration": 10, "damage": 1},
                        {"shape": { "template": "forms.rect", "w": 95, "h": 60 }, "offset_x": 88, "offset_y": -5, "angle": 0, "delay": 16, "duration": 14, "damage": 2}
                    ]
                }
            ],
            "movements": [
                {
                    "name": "Back Leap",
                    "phases": [
                        {
                            "direction": "away_from_player",
                            "curve": "fade_out",
                            "force_x": 4.0,
                            "force_y": 8.0,
                            "delay": 0,
                            "duration": 25
                        }
                    ]
                }
            ],
            "sequences": [
                {
                    "name": "Heavy Sequence",
                    "chance": 0.6, "cooldown": 75,
                    "trigger_zone": {
                        "shape": { "template": "forms.rect", "w": 90, "h": 50 },
                        "offset_x": 10, "offset_y": 0, "type": "following"
                    },
                    "steps": [
                        {"type": "attack", "idx": 0, "delay": 0, "trigger": "time"}
                    ]
                }
            ]
        }
    ]
}

LEVEL_2_BOSS_DATA = {
    "player": {
        "start_x": 150, "start_y": 400,
        "speed": 5, "jump_force": 14, "gravity": 0.6,
        "attack_range": 65, "attack_cooldown": 45
    },
    "platforms": [
        {"x": 0, "y": 520, "w": 1000, "h": 80, "color": [60, 40, 40]},
        {"x": 150, "y": 380, "w": 150, "h": 15, "color": [120, 80, 80]},
        {"x": 700, "y": 380, "w": 150, "h": 15, "color": [120, 80, 80]}
    ],
    "enemies": [
        {
            "name": "Gorgon Boss",
            "x": 480, "y": 430,
            "hp": 25,
            "body": { "template": "forms.rect", "w": 65, "h": 90 },
            "movement_config": { "type_move": "walking", "speed": 0.8, "range_x": 60 },
            "detection": {
                "template": "detections.front_view",
                "shape": { "template": "forms.rect", "w": 350, "h": 100 },
                "offset_x": 0, "offset_y": -15
            },
            "projectiles": [
                { "name": "Stone Arrow", "speed": 12.0, "angle": 0.0, "gravity": 0.0, "damage": 2, "radius": 8 }
            ],
            "attacks": [
                {
                    "name": "Stomp & Cleave",
                    "cooldown": 90, "windup": 45,
                    "shapes": [
                        {"shape": { "template": "forms.rect", "w": 80, "h": 60 }, "offset_x": 78, "offset_y": -5, "angle": 0, "delay": 0, "duration": 15, "damage": 1},
                        {"shape": { "template": "forms.rect", "w": 140, "h": 80 }, "offset_x": 128, "offset_y": -15, "angle": 15, "delay": 25, "duration": 20, "damage": 3}
                    ]
                }
            ],
            "movements": [
                {
                    "name": "Boss Leap",
                    "phases": [
                        {
                            "direction": "to_player",
                            "curve": "fade_out",
                            "force_x": 5.0,
                            "force_y": 12.0,
                            "delay": 0,
                            "duration": 30
                        }
                    ]
                }
            ],
            "sequences": [
                {
                    "name": "Boss Cleave Combo",
                    "chance": 0.6, "cooldown": 90,
                    "trigger_zone": {
                        "shape": { "template": "forms.rect", "w": 130, "h": 90 },
                        "offset_x": 10, "offset_y": 0, "type": "following"
                    },
                    "steps": [
                        {"type": "attack", "idx": 0, "delay": 0, "trigger": "time"}
                    ]
                }
            ]
        }
    ]
}


def ensure_level_file():
    os.makedirs(LEVELS_DIR, exist_ok=True)
    os.makedirs(os.path.join(ENEMIES_DIR, "common"), exist_ok=True)
    os.makedirs(os.path.join(ENEMIES_DIR, "boss"), exist_ok=True)
    
    old_monolith = "levels.json"
    if os.path.exists(old_monolith) and os.path.getsize(old_monolith) > 0:
        try:
            print(f"Обнаружен старый файл {old_monolith}. Запуск миграции...")
            with open(old_monolith, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            
            templates = old_data.get("templates", DEFAULT_TEMPLATES)
            with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
                json.dump(templates, f, indent=4)
                
            presets = old_data.get("presets", {})
            for p_name, p_data in presets.items():
                filename = p_name.lower().replace(" ", "_") + ".json"
                folder = "boss" if "boss" in p_name.lower() or "gorgon" in p_name.lower() else "common"
                p_path = os.path.join(ENEMIES_DIR, folder, filename)
                with open(p_path, "w", encoding="utf-8") as f:
                    json.dump(p_data, f, indent=4)
                    
            level_content = old_data.get("level", LEVEL_1_DATA)
            l1_path = os.path.join(LEVELS_DIR, "level_1.json")
            with open(l1_path, "w", encoding="utf-8") as f:
                json.dump(level_content, f, indent=4)
                
            l2_path = os.path.join(LEVELS_DIR, "level_2_boss.json")
            if not os.path.exists(l2_path) or os.path.getsize(l2_path) == 0:
                with open(l2_path, "w", encoding="utf-8") as f:
                    json.dump(LEVEL_2_BOSS_DATA, f, indent=4)
            
            gb_path = os.path.join(ENEMIES_DIR, "boss", "gorgon_boss.json")
            if not os.path.exists(gb_path) or os.path.getsize(gb_path) == 0:
                with open(gb_path, "w", encoding="utf-8") as f:
                    json.dump(GORGON_BOSS_PRESET, f, indent=4)
                    
            backup_name = old_monolith + ".backup"
            if os.path.exists(backup_name):
                os.remove(backup_name)
            os.rename(old_monolith, backup_name)
            print(f"Миграция данных успешно завершена! Создан бэкап: {backup_name}")
            return
        except Exception as e:
            print(f"Ошибка миграции: {e}. Переключаемся на стандартную генерацию.")

    if not os.path.exists(TEMPLATES_FILE) or os.path.getsize(TEMPLATES_FILE) == 0:
        with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TEMPLATES, f, indent=4)
            
    hk_path = os.path.join(ENEMIES_DIR, "common", "heavy_knight.json")
    if not os.path.exists(hk_path) or os.path.getsize(hk_path) == 0:
        with open(hk_path, "w", encoding="utf-8") as f:
            json.dump(HEAVY_KNIGHT_PRESET, f, indent=4)
            
    bs_path = os.path.join(ENEMIES_DIR, "common", "bat_scout.json")
    if not os.path.exists(bs_path) or os.path.getsize(bs_path) == 0:
        with open(bs_path, "w", encoding="utf-8") as f:
            json.dump(BAT_SCOUT_PRESET, f, indent=4)
            
    gb_path = os.path.join(ENEMIES_DIR, "boss", "gorgon_boss.json")
    if not os.path.exists(gb_path) or os.path.getsize(gb_path) == 0:
        with open(gb_path, "w", encoding="utf-8") as f:
            json.dump(GORGON_BOSS_PRESET, f, indent=4)
            
    lvl1_path = os.path.join(LEVELS_DIR, "level_1.json")
    if not os.path.exists(lvl1_path) or os.path.getsize(lvl1_path) == 0:
        with open(lvl1_path, "w", encoding="utf-8") as f:
            json.dump(LEVEL_1_DATA, f, indent=4)
            
    lvl2_path = os.path.join(LEVELS_DIR, "level_2_boss.json")
    if not os.path.exists(lvl2_path) or os.path.getsize(lvl2_path) == 0:
        with open(lvl2_path, "w", encoding="utf-8") as f:
            json.dump(LEVEL_2_BOSS_DATA, f, indent=4)

def resolve_json(node, templates, context=None):
    if context is None:
        context = {}
    if isinstance(node, dict):
        if "template" in node:
            path = node["template"].split(".")
            target_template = templates
            for key in path:
                target_template = target_template[key]
            local_context = {
                f"${k}": resolve_json(v, templates, context) 
                for k, v in node.items() if k != "template"
            }
            merged_context = {**context, **local_context}
            resolved = resolve_json(target_template, templates, merged_context)
            merged_node = {**node, **resolved}
            merged_node.pop("template", None)
            return merged_node
        else:
            return {k: resolve_json(v, templates, context) for k, v in node.items()}
    elif isinstance(node, list):
        return [resolve_json(item, templates, context) for item in node]
    elif isinstance(node, str) and node.startswith("$"):
        return context.get(node, node)
    return node