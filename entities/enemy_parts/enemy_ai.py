# entities/enemy_parts/enemy_ai.py
import pygame
import math
import copy
from entities.enemy_parts.ai_combat_handler import AICombatMixin
from entities.enemy_parts.ai_flow_handler import AIFlowMixin
from entities.enemy_parts.ai_action_processor import AIActionProcessorMixin
from core.physics import apply_movement_and_collisions

class EnemyAILogicMixin(AICombatMixin, AIFlowMixin, AIActionProcessorMixin):
    def update(self, platforms, gravity, player, game=None):
        self.load_attack_sprite()
        vx = 0
        
        if not hasattr(self, "patrol_return_delay_timer"):
            self.patrol_return_delay_timer = 0

        if not hasattr(self, "projectile_cooldowns"):
            self.projectile_cooldowns = {}
        for k in list(self.projectile_cooldowns.keys()):
            if self.projectile_cooldowns[k] > 0:
                self.projectile_cooldowns[k] -= 1

        for flow in self.flows:
            flow.setdefault("_cooldown_timer", 0)
            if flow["_cooldown_timer"] > 0:
                flow["_cooldown_timer"] -= 1

        for seq in self.sequences:
            seq.setdefault("_cooldown_timer", 0)
            if seq["_cooldown_timer"] > 0:
                seq["_cooldown_timer"] -= 1

        # Обновление КД цепочек порядка
        for order in getattr(self, "orders", []):
            order.setdefault("_cooldown_timer", 0)
            if order["_cooldown_timer"] > 0:
                order["_cooldown_timer"] -= 1

        if abs(self.knockback_vx) > 0.1:
            self.knockback_vx *= 0.85
        else:
            self.knockback_vx = 0

        if self.movement_type == "flying":
            self.vy = 0
        else:
            self.vy += gravity
        
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1
            
        for att in self.attacks:
            if att.get("_cooldown_timer", 0) > 0:
                att["_cooldown_timer"] -= 1

        if not hasattr(self, "trigger_hold_timers"):
            self.trigger_hold_timers = {}
            
        is_any_action_running = len(self.running_actions) > 0 or self.active_flow is not None or self.running_sequences or getattr(self, "active_order", None) is not None
        
        # Обновление таймеров удержания Sequences
        for seq_idx, seq in enumerate(self.sequences):
            if seq_idx in getattr(self, "connected_seq_indices", set()):
                continue
            key = f"seq_{seq_idx}"
            self.trigger_hold_timers.setdefault(key, 0)
            if self.check_player_in_zone(player.rect, seq_idx):
                self.trigger_hold_timers[key] += 1
            else:
                if not is_any_action_running:
                    self.trigger_hold_timers[key] = max(0, self.trigger_hold_timers[key] - 2)

        # Обновление таймеров удержания Flows
        for flow_idx, flow in enumerate(self.flows):
            if flow_idx in getattr(self, "connected_flow_indices", set()):
                continue
            key = f"flow_{flow_idx}"
            self.trigger_hold_timers.setdefault(key, 0)
            if self.check_player_in_flow_zone(player.rect, flow_idx):
                self.trigger_hold_timers[key] += 1
            else:
                if not is_any_action_running:
                    self.trigger_hold_timers[key] = max(0, self.trigger_hold_timers[key] - 2)

        # Обновление таймеров удержания Orders
        for o_idx, order in enumerate(getattr(self, "orders", [])):
            key = f"order_{o_idx}"
            self.trigger_hold_timers.setdefault(key, 0)
            if self.check_player_in_order_zone(player.rect, o_idx):
                self.trigger_hold_timers[key] += 1
            else:
                if not is_any_action_running:
                    self.trigger_hold_timers[key] = max(0, self.trigger_hold_timers[key] - 2)

        self.update_flow_selection(player)

        # ОБНОВЛЕНИЕ АКТИВНОГО FLOW
        if self.active_flow is not None:
            flow_color = self.active_flow.get("color") 
            for step in self.active_flow.get("steps", []):
                if step.get("delay", 0) == self.active_flow_timer:
                    if step.get("is_random", False) and step.get("seq_pool"):
                        pool = step["seq_pool"]
                        weights = []
                        valid_pool = []
                        for s_idx in pool:
                            if s_idx < len(self.sequences):
                                valid_pool.append(s_idx)
                                weights.append(self.sequences[s_idx].get("chance", 0.5))
                        
                        if valid_pool:
                            import random
                            total_w = sum(weights)
                            if total_w > 0:
                                r = random.uniform(0, total_w)
                                cumulative = 0
                                chosen_idx = valid_pool[0]
                                for idx, w in zip(valid_pool, weights):
                                    cumulative += w
                                    if r <= cumulative:
                                        chosen_idx = idx
                                        break
                                s_idx = chosen_idx
                            else:
                                s_idx = random.choice(valid_pool)
                        else:
                            s_idx = 0
                    else:
                        s_idx = step.get("seq_idx", 0)
                        
                    if s_idx < len(self.sequences):
                        if not hasattr(self, "running_sequences"):
                            self.running_sequences = []
                        
                        seq_color = flow_color if flow_color is not None else self.sequences[s_idx].get("color")
                        self.running_sequences.append({
                            "sequence": copy.deepcopy(self.sequences[s_idx]),
                            "timer": 0,
                            "color": seq_color
                        })
            self.active_flow_timer += 1
            max_flow_delay = max([s.get("delay", 0) for s in self.active_flow.get("steps", [])] or [0])
            if self.active_flow_timer > max_flow_delay and len(self.running_actions) == 0:
                flow_ref = self.active_flow
                flow_cd = flow_ref.get("cooldown", 180)
                flow_ref["_cooldown_timer"] = flow_cd
                self.active_flow = None
                self.active_flow_timer = 0
                self.attack_cooldown_timer = flow_ref.get("post_cooldown", 30)

        # ОБНОВЛЕНИЕ АКТИВНОГО ORDER (МАСТЕР-ЦЕПОЧКИ)
        if getattr(self, "active_order", None) is not None:
            order_ref = self.active_order
            steps = order_ref.get("steps", [])
            
            # Следующий шаг порядка активируется только после полного завершения действий предыдущего
            if len(self.running_actions) == 0 and not self.running_sequences:
                if getattr(self, "active_order_step_idx", 0) < len(steps):
                    current_step = steps[self.active_order_step_idx]
                    connections = current_step.get("connections", [])
                    
                    if connections:
                        # Случайный выбор (branching) при наличии нескольких связей на шаге
                        import random
                        chosen_conn = random.choice(connections)
                        c_type = chosen_conn.get("type")
                        c_name = chosen_conn.get("name")
                        
                        if c_type == "Sequence":
                            for s_idx, seq in enumerate(self.sequences):
                                if seq.get("name") == c_name:
                                    self.running_sequences.append({
                                        "sequence": copy.deepcopy(seq),
                                        "timer": 0,
                                        "color": seq.get("color")
                                    })
                                    break
                        elif c_type == "Flow":
                            for f_idx, flow in enumerate(self.flows):
                                if flow.get("name") == c_name:
                                    self.active_flow = flow
                                    self.active_flow_timer = 0
                                    break
                                    
                    self.active_order_step_idx += 1
                else:
                    # Цепочка порядка завершена
                    order_cd = order_ref.get("cooldown", 120)
                    order_ref["_cooldown_timer"] = order_cd
                    self.active_order = None
                    self.attack_cooldown_timer = order_ref.get("post_cooldown", 30)

        # ОБНОВЛЕНИЕ ВСЕХ ПАРАЛЛЕЛЬНО ЗАПУЩЕННЫХ ПОСЛЕДОВАТЕЛЬНОСТЕЙ
        if not hasattr(self, "running_sequences"):
            self.running_sequences = []
            
        if hasattr(self, "active_sequence") and self.active_sequence is not None:
            self.running_sequences.append({
                "sequence": self.active_sequence,
                "timer": self.active_seq_timer,
                "color": self.active_sequence.get("color")
            })
            self.active_sequence = None
            self.active_seq_timer = 0
            
        for run_seq in self.running_sequences:
            seq = run_seq["sequence"]
            timer = run_seq["timer"]
            seq_color = run_seq.get("color") 
            
            for step in seq.get("steps", []):
                if step.get("delay", 0) == timer:
                    self._start_action_from_step(step, game, execution_color=seq_color)
            
            run_seq["timer"] += 1
            
        self.running_sequences = [
            r for r in self.running_sequences
            if r["timer"] <= max([s.get("delay", 0) for s in r["sequence"].get("steps", [])] or [0])
        ]

        # Обновляем активные действия
        movement_vx_bonus, movement_vy_bonus, movement_applied_any = self.process_active_actions(player, game)

        # Фильтруем завершенные действия
        active_remaining_actions = []
        for act in self.running_actions:
            keep = True
            if act["type"] == "movement" and act["timeline_timer"] >= act["total_duration"] and len(act["active_phases"]) == 0:
                keep = False
            elif act["type"] == "attack" and act["is_swinging"] and act["timeline_timer"] >= act["total_duration"]:
                if not any(t > 0 for t in act.get("hitbox_contact_timers", [])):
                    keep = False
            if keep:
                active_remaining_actions.append(act)
        self.running_actions = active_remaining_actions

        # Проверяем завершение активных Flow
        if self.active_flow is not None and len(self.running_actions) == 0:
            max_flow_delay = max([s.get("delay", 0) for s in self.active_flow.get("steps", [])] or [0])
            if self.active_flow_timer > max_flow_delay:
                flow_ref = self.active_flow
                flow_cd = flow_ref.get("cooldown", 180)
                flow_ref["_cooldown_timer"] = flow_cd
                self.active_flow = None
                self.active_flow_timer = 0
                self.attack_cooldown_timer = flow_ref.get("post_cooldown", 30)

        # Синхронизируем классические переменные для рендера
        active_attacks = [act for act in self.running_actions if act["type"] == "attack"]
        if active_attacks:
            first_atk = active_attacks[0]
            self.is_winding_up = first_atk["is_winding_up"]
            self.is_swinging = first_atk["is_swinging"]
            self.active_attack_idx = first_atk["idx"]
            self.attack_timeline_timer = first_atk["timeline_timer"]
            self.attack_total_duration = first_atk["total_duration"]
            self.windup_phase = first_atk.get("windup_phase", 0.0)
            self.attack_windup_timer = first_atk.get("windup_timer", 0)
            self.attack_windup_max = first_atk.get("windup_max", 35)
            self.active_execution_color = first_atk.get("execution_color")
        else:
            self.is_winding_up = False
            self.is_swinging = False
            self.attack_timeline_timer = 0
            self.attack_total_duration = 0
            self.active_execution_color = None

        # ДВИЖЕНИЕ ПАТРУЛИРОВАНИЯ И ПРЕСЛЕДОВАНИЯ
        if self.active_flow is None and not self.running_sequences and not self.running_actions and getattr(self, "active_order", None) is None:
            move_cfg = self.config.get("movement_config", {})
            global_stop_dist = move_cfg.setdefault("stop_dist", 60)
            
            if move_cfg.get("patrol_on_platform", False) and platforms:
                standing_plat = None
                min_dist = float('inf')
                for plat in platforms:
                    if self.rect.right > plat.rect.left and self.rect.left < plat.rect.right:
                        dist = plat.rect.top - self.rect.bottom
                        if 0 <= dist < 10 and dist < min_dist:
                            min_dist = dist
                            standing_plat = plat
                if standing_plat:
                    self.min_x = standing_plat.rect.left + self.rect.width // 2
                    self.max_x = standing_plat.rect.right - self.rect.width // 2
                else:
                    self.min_x = self.start_x - self.range_x
                    self.max_x = self.start_x + self.range_x
            else:
                self.min_x = self.start_x - self.range_x
                self.max_x = self.start_x + self.range_x

            if self.state == "post_action":
                self.post_action_timer -= 1
                vx = self.post_action_vx
                self.post_action_vx *= 0.92  
                if self.movement_type == "flying":
                    self.vy = 0
                if self.post_action_timer <= 0:
                    self.state = "chase"
            else:
                player_detected = self.check_player_detected(player.rect)
                if player_detected:
                    self.state = "chase"
                    self.patrol_return_delay_timer = 180  
                elif self.patrol_return_delay_timer > 0:
                    self.patrol_return_delay_timer -= 1
                    self.state = "chase"  
                else:
                    self.state = "patrol"

                if self.state == "chase":
                    if self.movement_type == "flying":
                        dx = player.rect.centerx - self.rect.centerx
                        dy = player.rect.centery - self.rect.centery
                        distance = math.hypot(dx, dy)
                        
                        stop_distances = []
                        for idx in range(len(self.trigger_zones)):
                            if idx in getattr(self, "connected_seq_indices", set()):
                                continue
                            is_in_flow = any(
                                (step.get("is_random", False) and idx in step.get("seq_pool", [])) or 
                                (not step.get("is_random", False) and idx == step.get("seq_idx", 0))
                                for flow in self.flows 
                                for step in flow.get("steps", []))
                            if not is_in_flow:
                                stop_distances.append(self.get_stopping_distance(idx))
                                
                        for f_idx in range(len(self.flows)):
                            if f_idx in getattr(self, "connected_flow_indices", set()):
                                continue
                            stop_distances.append(self.get_flow_stopping_distance(f_idx))

                        for o_idx in range(len(self.orders)):
                            stop_distances.append(self.get_order_stopping_distance(o_idx))
                            
                        raw_stop_dist = max(stop_distances) if stop_distances else 5
                        trigger_stop_dist = raw_stop_dist + self.rect.width / 2 + player.rect.width / 2
                        stop_dist = max(2.0, max(trigger_stop_dist - 5.0, global_stop_dist))
                        
                        if distance > stop_dist:
                            vx = (dx / distance) * (self.speed * 1.4)
                            self.vy = (dy / distance) * (self.speed * 1.4)
                            
                            if getattr(self, "was_collided_x", False):
                                dir_y = -1 if dy < 0 else 1 if dy > 0 else -1
                                self.vy = dir_y * (self.speed * 1.4)
                                vx = vx * 0.2
                            elif getattr(self, "was_collided_y", False):
                                dir_x = -1 if dx < 0 else 1 if dx > 0 else 1
                                vx = dir_x * (self.speed * 1.4)
                                self.vy = self.vy * 0.2
                        else:
                            vx = 0
                            self.vy = 0
                        if dx != 0:
                            self.direction = 1 if dx > 0 else -1
                    else:
                        overlapping_zones = []
                        for idx in range(len(self.trigger_zones)):
                            if idx in getattr(self, "connected_seq_indices", set()):
                                continue
                            is_in_flow = any(
                                (step.get("is_random", False) and idx in step.get("seq_pool", [])) or 
                                (not step.get("is_random", False) and idx == step.get("seq_idx", 0))
                                for flow in self.flows 
                                for step in flow.get("steps", []))
                            if is_in_flow:
                                continue
                            if self.check_zone_vertical_overlap(player.rect, idx):
                                overlapping_zones.append(("sequence", idx))
                                
                        for f_idx in range(len(self.flows)):
                            if f_idx in getattr(self, "connected_flow_indices", set()):
                                continue
                            if self.check_flow_zone_vertical_overlap(player.rect, f_idx):
                                overlapping_zones.append(("flow", f_idx))
                        
                        if overlapping_zones:
                            stop_distances = []
                            for z_type, z_idx in overlapping_zones:
                                if z_type == "sequence":
                                    stop_distances.append(self.get_stopping_distance(z_idx))
                                else:
                                    stop_distances.append(self.get_flow_stopping_distance(z_idx))
                                    
                            raw_stop_dist = max(stop_distances)
                            trigger_stop_dist = raw_stop_dist + self.rect.width / 2 + player.rect.width / 2
                            stop_dist = max(2.0, max(trigger_stop_dist - 3.0, global_stop_dist))
                            
                            distance = abs(player.rect.centerx - self.rect.centerx)
                            self.direction = 1 if player.rect.centerx > self.rect.centerx else -1
                                
                            if distance <= stop_dist:
                                vx = 0
                            else:
                                desired_vx = self.speed * 1.4
                                max_allowed_vx = distance - stop_dist
                                vx = min(desired_vx, max_allowed_vx) * self.direction
                        else:
                            distance = abs(player.rect.centerx - self.rect.centerx)
                            self.direction = 1 if player.rect.centerx > self.rect.centerx else -1
                                
                            if distance <= global_stop_dist:
                                vx = 0
                            else:
                                desired_vx = self.speed * 1.4
                                max_allowed_vx = distance - global_stop_dist
                                vx = min(desired_vx, max_allowed_vx) * self.direction
                else:  # Patrol
                    if self.rect.centerx < self.min_x:
                        self.direction = 1
                    elif self.rect.centerx > self.max_x:
                        self.direction = -1
                    
                    vx = self.speed * self.direction
                    if self.rect.x <= self.min_x and self.direction == -1:
                        self.direction = 1
                    elif self.rect.x >= self.max_x and self.direction == 1:
                        self.direction = -1
                        
                    if self.movement_type == "flying":
                        self.vy = math.sin(pygame.time.get_ticks() * 0.005) * 1.0
        else:
            if movement_applied_any:
                vx = movement_vx_bonus
                if self.movement_type == "flying":
                    self.vy = movement_vy_bonus
            else:
                vx = 0

        if self.rect.colliderect(player.rect):
            has_forced_movement = any(act["type"] == "movement" for act in self.running_actions)
            if not has_forced_movement:
                vx = 0
                if self.movement_type == "flying":
                    self.vy = 0

        if not hasattr(self, "x_remainder"):
            self.x_remainder = 0.0

        total_vx = vx + self.knockback_vx + self.x_remainder
        int_vx = int(total_vx)
        self.x_remainder = total_vx - int_vx

        intended_vy = self.vy
        on_ground, self.vy, collided_x = apply_movement_and_collisions(self.rect, int_vx, self.vy, platforms)
        
        self.was_collided_x = collided_x
        self.was_collided_y = (intended_vy != 0 and self.vy == 0)
        
        if self.state == "patrol" and collided_x:
            self.direction *= -1