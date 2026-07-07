# entities/enemy_parts/ai_combat_handler.py
import math

class AICombatMixin:
    def _resolve_hitbox_parry(self, player, s_data, s_idx, act, selected_attack):
        dmg = s_data.get("damage", selected_attack.get("damage", 1))
        
        # Считываем настройки отдачи при ПАРИРОВАНИИ
        kb_angle = s_data.get("kb_angle_parry", s_data.get("kb_angle", 0))
        kb_force = s_data.get("kb_force_parry", s_data.get("kb_force", 12.0) * 0.5)
        
        player_is_on_right = player.rect.centerx > self.rect.centerx
        clamped_angle = max(-90, min(90, kb_angle))
        
        if player_is_on_right:
            theta_kb = clamped_angle
        else:
            theta_kb = 180 - clamped_angle
            
        rad = math.radians(theta_kb)
        force_x = math.cos(rad) * kb_force
        force_y = -math.sin(rad) * kb_force
        
        self.parry_accumulated_damage += dmg
        player.parry_success_flash_timer = 15
        player.parry_timer = 0
        
        # Применяем полученную силу парирования напрямую
        player.knockback_vx = force_x
        player.vy = force_y
        self.knockback_vx = 0
        
        act["hitbox_damaged_flags"][s_idx] = True
        act["hitbox_contact_timers"][s_idx] = -1

    def _resolve_hitbox_damage(self, player, s_data, s_idx, act, selected_attack):
        dmg = s_data.get("damage", selected_attack.get("damage", 1))
        
        # Считываем настройки отдачи при ПРЯМОМ ПОПАДАНИИ
        kb_angle = s_data.get("kb_angle_hit", s_data.get("kb_angle", 0))
        kb_force = s_data.get("kb_force_hit", s_data.get("kb_force", 12.0))
        
        player_is_on_right = player.rect.centerx > self.rect.centerx
        clamped_angle = max(-90, min(90, kb_angle))
        
        if player_is_on_right:
            theta_kb = clamped_angle
        else:
            theta_kb = 180 - clamped_angle
            
        rad = math.radians(theta_kb)
        force_x = math.cos(rad) * kb_force
        force_y = -math.sin(rad) * kb_force
        
        self.last_attack_hit_registered = True
        player.take_damage(dmg, force_x, force_y)
        
        act["hitbox_damaged_flags"][s_idx] = True
        act["hitbox_contact_timers"][s_idx] = -1