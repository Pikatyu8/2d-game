# entities/enemy_parts/ai_action_processor.py
import pygame
import math
import copy

class AIActionProcessorMixin:
    def process_active_actions(self, player, game):
        movement_vx_bonus = 0
        movement_vy_bonus = 0
        movement_applied_any = False

        for act in self.running_actions:
            if act["type"] == "movement":
                act["timeline_timer"] += 1
                
                for p in act["phases"]:
                    if p.get("delay", 0) == act["timeline_timer"] - 1:
                        if p.get("direction") == "teleport":
                            dx = p.get("force_x", 0.0)
                            dy = p.get("force_y", 0.0)
                            
                            if player is not None:
                                dir_to_player = 1 if player.rect.centerx >= self.rect.centerx else -1
                            else:
                                dir_to_player = self.direction
                            
                            old_x, old_y = self.rect.x, self.rect.y
                            self.rect.centerx += int(dx * dir_to_player)
                            self.rect.centery += int(dy)
                            
                            for plat in game.platforms:
                                if self.rect.colliderect(plat.rect):
                                    self.rect.x, self.rect.y = old_x, old_y 
                                    break
                            
                            if player is not None:
                                self.direction = 1 if self.rect.centerx < player.rect.centerx else -1
                        else:
                            act["active_phases"].append({
                                "direction": p.get("direction", "forward"),
                                "curve": p.get("curve", "fade_out"),
                                "force_x": p.get("force_x", 8.0),
                                "force_y": p.get("force_y", 0.0),
                                "duration": p.get("duration", 15),
                                "elapsed_frames": 0,
                                "triggered_force": False  
                            })
                
                for p_act in act["active_phases"]:
                    duration = max(1, p_act["duration"])
                    t = p_act["elapsed_frames"] / duration
                    
                    curr_curve = p_act.get("curve", "fade_out")
                    if curr_curve == "fade_out":
                        m = 1.0 - t
                    elif curr_curve == "fade_in":
                        m = t
                    elif curr_curve == "ease_in_out":
                        m = math.sin(t * math.pi)
                    else:
                        m = 1.0
                    
                    if not p_act["triggered_force"]:
                        p_act["triggered_force"] = True
                        to_player_dir = 1 if player.rect.centerx > self.rect.centerx else -1
                        fx = p_act["force_x"]
                        fy = p_act["force_y"]
                        m_type = p_act["direction"]
                        
                        if m_type == "forward":
                            s = self.direction
                        elif m_type == "backward":
                            s = -self.direction
                        elif m_type == "to_player":
                            s = to_player_dir
                        else:
                            s = -to_player_dir
                        
                        p_act["direction_sign"] = s
                        
                        if fy > 0 and self.movement_type != "flying":
                            self.vy = -fy
                    
                    s_x = p_act.get("direction_sign", self.direction)
                    fx = p_act["force_x"]
                    
                    stop_dist = 0
                    move_idx = act.get("idx", 0)
                    if move_idx < len(self.movements):
                        stop_dist = self.movements[move_idx].get("stop_dist", 0)
                    
                    distance = abs(player.rect.centerx - self.rect.centerx)
                    
                    if self.movement_type == "flying":
                        target = p_act["direction"]
                        if target in ("to_player", "away_from_player"):
                            dx = player.rect.centerx - self.rect.centerx
                            dy = player.rect.centery - self.rect.centery
                            dist = math.hypot(dx, dy)
                            if dist > 0:
                                s_x_fly = dx / dist
                                s_y_fly = dy / dist
                                if target == "away_from_player":
                                    s_x_fly = -s_x_fly
                                    s_y_fly = -s_y_fly
                                
                                moving_towards_player_fly = (s_x_fly > 0 and player.rect.centerx > self.rect.centerx) or (s_x_fly < 0 and player.rect.centerx < self.rect.centerx)
                                desired_vx_fly = s_x_fly * fx * m * 1.5
                                
                                if moving_towards_player_fly and stop_dist > 0:
                                    if distance <= stop_dist:
                                        vx_fly = 0
                                    else:
                                        max_allowed_vx = (distance - stop_dist) * (1 if s_x_fly > 0 else -1)
                                        if abs(desired_vx_fly) > abs(max_allowed_vx):
                                            vx_fly = max_allowed_vx
                                        else:
                                            vx_fly = desired_vx_fly
                                else:
                                    vx_fly = desired_vx_fly
                                
                                movement_vx_bonus += vx_fly
                                movement_vy_bonus += s_y_fly * fx * m * 1.5
                            else:
                                movement_vx_bonus += s_x * fx * m
                        else:
                            movement_vx_bonus += s_x * fx * m
                    else:
                        moving_towards_player = (s_x > 0 and player.rect.centerx > self.rect.centerx) or (s_x < 0 and player.rect.centerx < self.rect.centerx)
                        desired_vx = s_x * fx * m
                        
                        if moving_towards_player and stop_dist > 0:
                            if distance <= stop_dist:
                                vx_phase = 0
                            else:
                                max_allowed_vx = (distance - stop_dist) * s_x
                                if abs(desired_vx) > abs(max_allowed_vx):
                                    vx_phase = max_allowed_vx
                                else:
                                    vx_phase = desired_vx
                        else:
                            vx_phase = desired_vx
                        
                        movement_vx_bonus += vx_phase
                        
                    p_act["elapsed_frames"] += 1
                    movement_applied_any = True
                
                act["active_phases"] = [p for p in act["active_phases"] if p["elapsed_frames"] < p["duration"]]
                
            elif act["type"] == "attack":
                selected_attack = self.attacks[act["idx"]]
                shapes = selected_attack["shapes"]
                
                if act["is_winding_up"]:
                    act["windup_timer"] -= 1
                    progress = max(0.0, min(1.0, (act["windup_max"] - act["windup_timer"]) / act["windup_max"]))
                    blink_speed = 0.08 + (progress ** 2.0) * 0.42
                    act["windup_phase"] += blink_speed
                    
                    if act["windup_timer"] <= 0:
                        act["is_winding_up"] = False
                        act["is_swinging"] = True
                        
                        selected_attack["_cooldown_timer"] = selected_attack.get("cooldown", 45)
                        self.attack_cooldown_timer = selected_attack.get("cooldown", 45)
                        
                elif act["is_swinging"]:
                    act["timeline_timer"] += 1
                    
                    if "hitbox_contact_timers" not in act:
                        act["hitbox_contact_timers"] = [-1] * len(shapes)
                    
                    for s_idx, s_data in enumerate(shapes):
                        delay = s_data.get("delay", 0)
                        duration = s_data.get("duration", 10)
                        is_active_frame = (delay <= act["timeline_timer"] <= (delay + duration))
                        
                        if not act["hitbox_damaged_flags"][s_idx]:
                            is_colliding = self.check_specific_hitbox_collision(player, s_data) if is_active_frame else False
                            c_timer = act["hitbox_contact_timers"][s_idx]
                            
                            is_airborne = not player.on_ground
                            enemy_is_on_right = self.rect.centerx > player.rect.centerx
                            correct_direction = (enemy_is_on_right and player.facing == 1) or (not enemy_is_on_right and player.facing == -1)
                            is_parry_successful = player.parry_timer > 0 and (is_airborne or correct_direction)
                            
                            if is_colliding and c_timer == -1:
                                if is_parry_successful:
                                    self._resolve_hitbox_parry(player, s_data, s_idx, act, selected_attack, game)
                                else:
                                    act["hitbox_contact_timers"][s_idx] = 5
                            
                            elif c_timer > 0:
                                if is_parry_successful:
                                    self._resolve_hitbox_parry(player, s_data, s_idx, act, selected_attack, game)
                                else:
                                    act["hitbox_contact_timers"][s_idx] -= 1
                                    if act["hitbox_contact_timers"][s_idx] == 0:
                                        self._resolve_hitbox_damage(player, s_data, s_idx, act, selected_attack, game)
                                        
        return movement_vx_bonus, movement_vy_bonus, movement_applied_any

    def _start_action_from_step(self, step, game, execution_color=None):
        if step["type"] == "attack":
            atk_idx = step.get("idx", 0)
            if atk_idx < len(self.attacks):
                selected_attack = self.attacks[atk_idx]
                windup = selected_attack.get("windup", 35)
                shapes = selected_attack["shapes"]
                total_dur = max([s.get("delay", 0) + s.get("duration", 10) for s in shapes]) if shapes else 15
                
                self.running_actions.append({
                    "type": "attack",
                    "idx": atk_idx,
                    "is_winding_up": True,
                    "windup_timer": windup,
                    "windup_max": windup,
                    "windup_phase": 0.0,
                    "is_swinging": False,
                    "timeline_timer": 0,
                    "total_duration": total_dur,
                    "hitbox_damaged_flags": [False] * len(shapes),
                    "hitbox_contact_timers": [-1] * len(shapes),
                    "execution_color": execution_color # Связываем цвет с действием
                })
        elif step["type"] == "movement":
            m_idx = step.get("idx", 0)
            if m_idx < len(self.movements):
                m_template = self.movements[m_idx]
                phases = m_template.get("phases", [])
                
                durations = []
                for p in phases:
                    p_dur = 1 if p.get("direction") == "teleport" else p.get("duration", 15)
                    durations.append(p.get("delay", 0) + p_dur)
                total_dur = max(durations) if durations else 15
                
                self.running_actions.append({
                    "type": "movement",
                    "idx": m_idx,
                    "timeline_timer": 0,
                    "total_duration": total_dur,
                    "phases": copy.deepcopy(phases),
                    "active_phases": []
                })
        elif step["type"] == "projectile":
            if game is not None:
                proj_templates = getattr(self, "projectiles", [])
                proj_idx = step.get("idx", 0)
                
                p_cooldown = 30
                if proj_templates and proj_idx < len(proj_templates):
                    tpl = proj_templates[proj_idx]
                    p_cooldown = tpl.get("shoot_cooldown", 30)
                else:
                    p_cooldown = step.get("shoot_cooldown", 30)

                if not hasattr(self, "projectile_cooldowns"):
                    self.projectile_cooldowns = {}
                if self.projectile_cooldowns.get(proj_idx, 0) > 0:
                    return

                if p_cooldown > 0:
                    self.projectile_cooldowns[proj_idx] = p_cooldown

                p_dir = self.direction
                spawn_x = self.rect.centerx + p_dir * (self.rect.width // 2 + 5)
                spawn_y = self.rect.centery
                
                p_speed = 10.0
                p_angle = 0.0
                p_grav = 0.0
                p_dmg = 1
                p_rad = 8
                aim_at_player = False
                homing = 0.0
                
                if proj_templates and proj_idx < len(proj_templates):
                    tpl = proj_templates[proj_idx]
                    p_speed = tpl.get("speed", 10.0)
                    p_angle = tpl.get("angle", 0.0)
                    p_grav = tpl.get("gravity", 0.0)
                    p_dmg = tpl.get("damage", 1)
                    p_rad = tpl.get("radius", 8)
                    aim_at_player = tpl.get("aim_at_player", False)
                    homing = tpl.get("homing", 0.0)
                else:
                    p_speed = step.get("proj_speed", 10.0)
                    p_angle = step.get("proj_angle", 0.0)
                    p_grav = step.get("proj_gravity", 0.0)
                    p_dmg = step.get("damage", 1)
                    p_rad = step.get("radius", 8)
                    aim_at_player = step.get("aim_at_player", False)
                    homing = step.get("homing", 0.0)
                
                if aim_at_player and game.player:
                    dx = game.player.rect.centerx - spawn_x
                    dy = game.player.rect.centery - spawn_y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        vx_p = (dx / dist) * p_speed
                        vy_p = (dy / dist) * p_speed
                    else:
                        rad = math.radians(p_angle)
                        vx_p = p_dir * p_speed * math.cos(rad)
                        vy_p = -p_speed * math.sin(rad)
                else:
                    rad = math.radians(p_angle)
                    vx_p = p_dir * p_speed * math.cos(rad)
                    vy_p = -p_speed * math.sin(rad)
                
                game.spawn_projectile(spawn_x, spawn_y, vx_p, vy_p, p_dmg, p_rad, p_grav, homing)