
# entities/projectile.py
import pygame
import math
from config import CANVAS_OFFSET_X

class Projectile:
    def __init__(self, x, y, vx, vy, damage=1, radius=8, gravity=0.0, homing=0.0):
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.radius = radius
        self.gravity = gravity
        self.homing = homing  
        self.friendly = False  

    def update(self, platforms, player, game):
        self.vy += self.gravity
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        # Столкновение с игроком
        if not self.friendly:
            if self.rect.colliderect(player.rect):
                # Направленное парирование снаряда
                is_airborne = not player.on_ground
                proj_is_on_right = self.rect.centerx > player.rect.centerx
                correct_direction = (proj_is_on_right and player.facing == 1) or (not proj_is_on_right and player.facing == -1)
                is_parry_successful = player.parry_timer > 0 and (is_airborne or correct_direction)

                if is_parry_successful:
                    self.friendly = True
                    player.parry_success_flash_timer = 15
                    player.parry_timer = 0

                    # Наведение отраженного снаряда на ближайшего живого врага
                    if game and game.enemies:
                        closest_enemy = min(
                            game.enemies, 
                            key=lambda e: math.hypot(e.rect.centerx - self.rect.centerx, e.rect.centery - self.rect.centery)
                        )
                        dx = closest_enemy.rect.centerx - self.rect.centerx
                        dy = closest_enemy.rect.centery - self.rect.centery
                        dist = math.hypot(dx, dy)
                        if dist > 0:
                            speed = max(8.0, math.hypot(self.vx, self.vy) * 1.3)
                            self.vx = (dx / dist) * speed
                            self.vy = (dy / dist) * speed
                    else:
                        self.vx = -self.vx * 1.5
                        self.vy = -self.vy * 0.5

                    # Хитстоп и звук парирования
                    if game:
                        game.hitstop_timer = 3
                        game.play_sound("parry")
                else:
                    player.take_damage(self.damage, 6.0 if self.vx > 0 else -6.0, -4.0, game)
                    return True  
            
            # Активное автонаведение в воздухе по вектору направления на игрока
            elif self.homing > 0.0 and player:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    current_speed = math.hypot(self.vx, self.vy)
                    if current_speed > 0:
                        target_vx = (dx / dist) * current_speed
                        target_vy = (dy / dist) * current_speed
                        self.vx += (target_vx - self.vx) * self.homing
                        self.vy += (target_vy - self.vy) * self.homing
                        
                        new_speed = math.hypot(self.vx, self.vy)
                        if new_speed > 0:
                            self.vx = (self.vx / new_speed) * current_speed
                            self.vy = (self.vy / new_speed) * current_speed
        else:
            # Столкновение с врагами (если отражен игроком)
            for enemy in game.enemies:
                if self.rect.colliderect(enemy.rect):
                    enemy.hp -= self.damage
                    enemy.knockback_vx = 7.0 if self.vx > 0 else -7.0
                    enemy.vy = -3.0
                    return True  

        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                return True

        if self.rect.x < -1000 or self.rect.x > 3000 or self.rect.y < -1000 or self.rect.y > 2000:
            return True

        return False

    def draw(self, surface, camera_x, camera_y, zoom):
        sx = CANVAS_OFFSET_X + (self.rect.centerx - camera_x) * zoom
        sy = (self.rect.centery - camera_y) * zoom
        sr = max(2.0, self.radius * zoom)
        
        color = (50, 255, 100) if self.friendly else (255, 120, 50)
        pygame.draw.circle(surface, color, (int(sx), int(sy)), int(sr))
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), int(sr * 0.4))