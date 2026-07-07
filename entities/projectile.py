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
        self.homing = homing  # Сила самонаведения (0.0 - отключено, >0.0 - активный доворот к игроку)
        self.friendly = False  # Становится True при успешном парировании игроком

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
                    # Отражение снаряда обратно во врагов
                    self.vx = -self.vx * 1.5
                    self.vy = -self.vy - 2
                    self.friendly = True
                    player.parry_success_flash_timer = 15
                    player.parry_timer = 0
                else:
                    player.take_damage(self.damage, 6.0 if self.vx > 0 else -6.0, -4.0, game)
                    return True  # Уничтожить снаряд
            
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
                        # Плавно интерполируем текущую скорость к направленной скорости к игроку
                        self.vx += (target_vx - self.vx) * self.homing
                        self.vy += (target_vy - self.vy) * self.homing
                        
                        # Сохраняем модуль скорости неизменным, чтобы автонаведение не гасило скорость
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
                    return True  # Уничтожить снаряд

        # Столкновение со стенами/платформами
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                return True

        # Выход за пределы мира
        if self.rect.x < -1000 or self.rect.x > 3000 or self.rect.y < -1000 or self.rect.y > 2000:
            return True

        return False

    def draw(self, surface, camera_x, camera_y, zoom):
        sx = CANVAS_OFFSET_X + (self.rect.centerx - camera_x) * zoom
        sy = (self.rect.centery - camera_y) * zoom
        sr = max(2.0, self.radius * zoom)
        
        # Свечение снаряда
        color = (50, 255, 100) if self.friendly else (255, 120, 50)
        pygame.draw.circle(surface, color, (int(sx), int(sy)), int(sr))
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), int(sr * 0.4))