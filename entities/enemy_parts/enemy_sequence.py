# entities/enemy_parts/enemy_sequence.py
import math

class EnemySequenceMixin:
    def _advance_sequence_step(self, player):
        # Метод оставлен для обратной совместимости, но больше не используется таймлайн-движком
        pass

    def _terminate_sequence(self):
        if self.active_sequence:
            self.active_sequence["_cooldown_timer"] = self.active_sequence.get("cooldown", 120)
            self.attack_cooldown_timer = 25
        self.active_sequence = None
        self.active_seq_step_idx = 0
        self.active_seq_timer = 0
        self.seq_timer = 0
        self.running_actions = []
        self.state = "chase"

    def get_stopping_distance(self, z_idx=0):
        if not self.trigger_zones or z_idx >= len(self.trigger_zones):
            return 5
            
        zone = self.trigger_zones[z_idx]
        shape = zone.get("shape", {})
        ox = zone.get("offset_x", 0)
        stype = shape.get("type", "rectangle")
        
        if stype == "circle":
            r = shape.get("r", 40)
            body_w = self.rect.width
            return max(5, ox + r - body_w // 2)
        else:
            w = shape.get("w", 80)
            return max(5, ox + w)

    def get_flow_stopping_distance(self, f_idx=0):
        if not self.flows or f_idx >= len(self.flows):
            return 5
            
        flow = self.flows[f_idx]
        zone = flow.get("trigger_zone", {})
        shape = zone.get("shape", {})
        ox = zone.get("offset_x", 0)
        stype = shape.get("type", "rectangle")
        
        if stype == "circle":
            r = shape.get("r", 40)
            body_w = self.rect.width
            return max(5, ox + r - body_w // 2)
        else:
            w = shape.get("w", 80)
            return max(5, ox + w)
