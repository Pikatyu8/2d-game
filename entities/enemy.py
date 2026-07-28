# entities/enemy.py
import pygame
from entities.enemy_parts.enemy_collision import EnemyCollisionMixin
from entities.enemy_parts.enemy_sequence import EnemySequenceMixin
from entities.enemy_parts.enemy_ai import EnemyAILogicMixin
from entities.enemy_parts.enemy_render import EnemyRenderMixin

class Enemy(EnemyCollisionMixin, EnemySequenceMixin, EnemyAILogicMixin, EnemyRenderMixin):
    def __init__(self, resolved_data, raw_data):
        self.config = resolved_data
        self.raw_data = raw_data
        
        body_cfg = resolved_data["body"]
        self.rect = pygame.Rect(resolved_data["x"], resolved_data["y"], body_cfg["w"], body_cfg["h"])
        
        self.name = resolved_data.get("name", "Enemy")
        self.hp = resolved_data.get("hp", 3)
        self.vy = 0
        self.knockback_vx = 0
        self.direction = 1
        
        move_cfg = resolved_data.get("movement_config", {})
        self.speed = move_cfg.get("speed", 2)
        self.start_x = resolved_data["x"]
        self.range_x = move_cfg.get("range_x", 100)
        self.min_x = self.start_x - self.range_x
        self.max_x = self.start_x + self.range_x
        
        self.movement_type = move_cfg.get("type_move", "walking")
        
        self.state = "patrol"
        self.attack_cooldown_timer = 0
        
        self.is_winding_up = False
        self.attack_windup_timer = 0
        self.attack_windup_max = 35
        self.windup_phase = 0.0
        self.is_swinging = False
        
        self.post_action_vx = 0
        self.post_action_timer = 0
        
        self.parry_accumulated_damage = 0

        self.active_attack_idx = 0
        self.attack_timeline_timer = 0  
        self.attack_total_duration = 0  
        self.hitbox_damaged_flags = []  

        self.attacks = resolved_data.get("attacks", [])
        self.movements = resolved_data.get("movements", [])
        self.sequences = resolved_data.get("sequences", [])
        self.flows = resolved_data.get("flows", [])
        self.orders = resolved_data.get("orders", [])  # Локальный реестр цепочек порядка
        self.projectiles = resolved_data.get("projectiles", []) 
        self.projectile_cooldowns = {} 

        # Инициализация списков для AI
        self.running_sequences = []
        self.running_actions = []
        self.trigger_hold_timers = {}
        self.active_flow = None
        self.active_flow_timer = 0
        self.active_order = None
        self.active_order_timer = 0
        self.active_order_step_idx = 0
        self.last_attack_hit_registered = False

        self.trigger_zones = []
        for seq in self.sequences:
            if "trigger_zone" in seq:
                self.trigger_zones.append(seq["trigger_zone"])

        self._attack_sprite_loaded = False
        self.attack_sprite = None
        self.attack_sprite_circle = None

        self.patrol_return_delay_timer = 0
        
        self.was_collided_x = False
        self.was_collided_y = False

        # Формируем кэш индексов дочерних хитбоксов для их скрытия/байпаса
        self.connected_seq_indices = set()
        self.connected_flow_indices = set()
        for order in self.orders:
            for step in order.get("steps", []):
                for conn in step.get("connections", []):
                    c_type = conn.get("type")
                    c_name = conn.get("name")
                    if c_type == "Sequence":
                        for s_idx, seq in enumerate(self.sequences):
                            if seq.get("name") == c_name:
                                self.connected_seq_indices.add(s_idx)
                    elif c_type == "Flow":
                        for f_idx, flow in enumerate(self.flows):
                            if flow.get("name") == c_name:
                                self.connected_flow_indices.add(f_idx)