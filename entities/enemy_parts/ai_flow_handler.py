# entities/enemy_parts/ai_flow_handler.py
import random
import copy

class AIFlowMixin:
    def update_flow_selection(self, player):
        # Если идет animation атаки, движения или КД, прерываем выбор
        if self.running_actions or self.attack_cooldown_timer > 0 or self.state == "post_action" or self.active_flow is not None:
            return

        if not hasattr(self, "consecutive_triggers"):
            self.consecutive_triggers = {}

        # Единый пул кандидатов
        candidates = []
        any_satisfied = False

        # 1. Сбор кандидатов из AI Flows
        for f_idx, flow in enumerate(self.flows):
            flow.setdefault("_cooldown_timer", 0)
            if flow["_cooldown_timer"] == 0:
                if self.check_player_in_flow_zone(player.rect, f_idx):
                    trig_zone = flow.get("trigger_zone", {})
                    req_hold = trig_zone.get("hold_time", 0)
                    key = f"flow_{f_idx}"
                    current_hold = self.trigger_hold_timers.get(key, 0)
                    
                    is_satisfied = (current_hold >= req_hold)
                    if is_satisfied:
                        any_satisfied = True
                        
                    hold_factor = min(1.0, current_hold / req_hold) if req_hold > 0 else 1.0
                    base_chance = flow.get("chance", 0.5)
                    weight = base_chance * hold_factor
                    
                    if weight > 0:
                        candidates.append({
                            "type": "flow",
                            "idx": f_idx,
                            "ref": flow,
                            "weight": weight,
                            "key": key,
                            "satisfied": is_satisfied
                        })

        # 2. Сбор кандидатов из Sequences (исключая те, что заняты внутри Flows и их пулов)
        for seq_idx, seq in enumerate(self.sequences):
            is_in_flow = any(
                (step.get("is_random", False) and seq_idx in step.get("seq_pool", [])) or
                (not step.get("is_random", False) and seq_idx == step.get("seq_idx", 0))
                for flow in self.flows 
                for step in flow.get("steps", [])
            )
            if is_in_flow:
                continue

            seq.setdefault("_cooldown_timer", 0)
            if seq["_cooldown_timer"] == 0:
                if self.check_player_in_zone(player.rect, seq_idx):
                    trig_zone = seq.get("trigger_zone", {})
                    req_hold = trig_zone.get("hold_time", 0)
                    key = f"seq_{seq_idx}"
                    current_hold = self.trigger_hold_timers.get(key, 0)
                    
                    is_satisfied = (current_hold >= req_hold)
                    if is_satisfied:
                        any_satisfied = True
                        
                    hold_factor = min(1.0, current_hold / req_hold) if req_hold > 0 else 1.0
                    base_chance = seq.get("chance", 0.5)
                    weight = base_chance * hold_factor
                    
                    if weight > 0:
                        candidates.append({
                            "type": "sequence",
                            "idx": seq_idx,
                            "ref": seq,
                            "weight": weight,
                            "key": key,
                            "satisfied": is_satisfied
                        })

        if not any_satisfied:
            return

        if candidates:
            total_weight = sum(c["weight"] for c in candidates)
            if total_weight > 0:
                r = random.uniform(0, total_weight)
                cumulative = 0
                chosen = candidates[0]
                for c in candidates:
                    cumulative += c["weight"]
                    if r <= cumulative:
                        chosen = c
                        break
                
                target = chosen["ref"]
                key = chosen["key"]
                trig_zone = target.get("trigger_zone", {})
                limit = trig_zone.get("consecutive_limit", 3)
                accumulate = trig_zone.get("accumulate_hold", True)

                self.consecutive_triggers[key] = self.consecutive_triggers.get(key, 0) + 1
                
                if self.consecutive_triggers[key] >= limit:
                    self.consecutive_triggers[key] = 0
                    self.trigger_hold_timers[key] = 0
                else:
                    if accumulate:
                        req_hold = trig_zone.get("hold_time", 0)
                        self.trigger_hold_timers[key] = max(self.trigger_hold_timers.get(key, 0), req_hold)

                if chosen["type"] == "flow":
                    self.active_flow = target
                    self.active_flow_timer = 0
                    self.running_actions = []
                else:
                    self.running_sequences.append({
                        "sequence": copy.deepcopy(target),
                        "timer": 0,
                        "color": target.get("color")
                    })
                    target["_cooldown_timer"] = target.get("cooldown", 120)
                    self.attack_cooldown_timer = target.get("post_cooldown", 30)