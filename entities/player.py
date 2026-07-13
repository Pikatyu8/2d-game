# entities/player.py
import pygame
from config import SCREEN_HEIGHT, CANVAS_OFFSET_X, CANVAS_WIDTH
from core.physics import apply_movement_and_collisions

class Player:
    def __init__(self, config):
        self.rect = pygame.Rect(config.get("start_x", 100), config.get("start_y", 300), 30, 50)
        self.vx = 0
        self.vy = 0
        self.knockback_vx = 0  
        self.on_ground = False
        self.facing = 1
        self.hp = 5
        self.damage_flash_timer = 0
        
        self.speed = config.get("speed", 5)
        self.jump_force = config.get("jump_force", 14)
        self.gravity = config.get("gravity", 0.6)
        self.attack_range = config.get("attack_range", 65)
        self.attack_cooldown_max = config.get("attack_cooldown", 45)
        
        self.attack_duration = 15
        self.attack_timer = 0
        self.is_attacking = False
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.hit_enemies = set()

        self.parry_timer = 0
        self.parry_duration = 7
        self.parry_cooldown_timer = 0
        self.parry_cooldown_max = 20  
        self.parry_success_flash_timer = 0
        
        self.parry_was_pressed = False
        self.attack_was_pressed = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vx = 0
        
        if self.damage_flash_timer > 0:
            return
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -self.speed
            self.facing = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = self.speed
            self.facing = 1
            
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = -self.jump_force
            self.on_ground = False

        parry_is_pressed = keys[pygame.K_LSHIFT] or pygame.mouse.get_pressed()[2]
        if parry_is_pressed and not self.parry_was_pressed:
            if self.parry_cooldown_timer == 0 and self.parry_timer == 0 and not self.is_attacking:
                self.parry_timer = self.parry_duration
                self.parry_cooldown_timer = self.parry_cooldown_max
        self.parry_was_pressed = parry_is_pressed

        mouse_click = pygame.mouse.get_pressed()[0]
        m_x, _ = pygame.mouse.get_pos()
        attack_is_pressed = (mouse_click and CANVAS_OFFSET_X <= m_x <= CANVAS_OFFSET_X + CANVAS_WIDTH) or keys[pygame.K_f]
        
        if attack_is_pressed and not self.attack_was_pressed:
            if self.attack_timer == 0 and self.parry_timer == 0:
                self.is_attacking = True
                self.attack_timer = self.attack_cooldown_max
                self.hit_enemies.clear()
        self.attack_was_pressed = attack_is_pressed

    def take_damage(self, amount, force_x, force_y=None, game=None):
        if self.damage_flash_timer == 0 and self.parry_success_flash_timer == 0:
            self.hp -= amount
            self.damage_flash_timer = 15
            self.knockback_vx = force_x  
            
            if force_y is not None:
                self.vy = force_y
            else:
                self.vy = -5
            
            # Воспроизведение процедурного / физического звука урона
            if game:
                game.play_sound("damage")
                
            if self.hp <= 0:
                self.respawn(game)

    def respawn(self, game=None):
        self.hp = 5
        self.rect.x = game.raw_player_cfg.get("start_x", 100) if game else 100
        self.rect.y = game.raw_player_cfg.get("start_y", 300) if game else 300
        self.vy = 0
        self.knockback_vx = 0
        if game:
            game.camera_x = max(0, self.rect.centerx - CANVAS_WIDTH // 2)
            game.camera_y = self.rect.centery - SCREEN_HEIGHT // 2

    def update(self, platforms, enemies, game=None):
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer < self.attack_cooldown_max - self.attack_duration:
                self.is_attacking = False
                
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1
        
        if self.parry_timer > 0:
            self.parry_timer -= 1
            
        if self.parry_cooldown_timer > 0:
            self.parry_cooldown_timer -= 1
            
        if self.parry_success_flash_timer > 0:
            self.parry_success_flash_timer -= 1
        
        if abs(self.knockback_vx) > 0.1:
            self.knockback_vx *= 0.85
        else:
            self.knockback_vx = 0

        self.vy += self.gravity
        
        # Оригинальная физика движения игрока
        total_vx = self.vx + self.knockback_vx
        self.on_ground, self.vy, _ = apply_movement_and_collisions(self.rect, total_vx, self.vy, platforms)

        if self.is_attacking:
            if self.facing == 1:
                self.attack_rect = pygame.Rect(self.rect.right, self.rect.y + 10, self.attack_range, 30)
            else:
                self.attack_rect = pygame.Rect(self.rect.left - self.attack_range, self.rect.y + 10, self.attack_range, 30)
            
            for enemy in enemies:
                if enemy not in self.hit_enemies and self.attack_rect.colliderect(enemy.rect):
                    damage_to_deal = 1
                    if enemy.parry_accumulated_damage > 0:
                        damage_to_deal += enemy.parry_accumulated_damage
                        enemy.parry_accumulated_damage = 0
                    
                    enemy.hp -= damage_to_deal
                    self.hit_enemies.add(enemy)
                    
                    enemy.knockback_vx = self.facing * 7.0
                    enemy.vy = -4.0  
        else:
            self.attack_rect = pygame.Rect(0, 0, 0, 0)

        lowest_y = max([p.rect.bottom for p in platforms]) if platforms else SCREEN_HEIGHT
        if self.rect.y > lowest_y + 300:
            self.respawn(game)

    def draw(self, surface, camera_x=0, camera_y=0, zoom=1.0):
        sx = CANVAS_OFFSET_X + (self.rect.x - camera_x) * zoom
        sy = (self.rect.y - camera_y) * zoom
        sw = max(1.0, self.rect.width * zoom)
        sh = max(1.0, self.rect.height * zoom)
        draw_rect = pygame.Rect(sx, sy, sw, sh)
        
        if self.parry_success_flash_timer > 0:
            color = (255, 255, 255) 
        elif self.parry_timer > 0:
            color = (0, 240, 255)   
        elif self.damage_flash_timer > 0:
            color = (255, 100, 100) 
        else:
            color = (50, 100, 255)  
            
        pygame.draw.rect(surface, color, draw_rect)
        
        eye_w = max(1.0, 4 * zoom)
        eye_x = draw_rect.right - 8 * zoom if self.facing == 1 else draw_rect.left + 4 * zoom
        eye_y = draw_rect.y + 10 * zoom
        pygame.draw.rect(surface, (255, 255, 255), (eye_x, eye_y, eye_w, eye_w))
        
        if self.parry_timer > 0:
            pygame.draw.circle(surface, (0, 240, 255), (int(draw_rect.centerx), int(draw_rect.centery)), int(32 * zoom), max(1, int(2 * zoom)))
        
        if self.is_attacking:
            asx = CANVAS_OFFSET_X + (self.attack_rect.x - camera_x) * zoom
            asy = (self.attack_rect.y - camera_y) * zoom
            asw = self.attack_rect.width * zoom
            ash = self.attack_rect.height * zoom
            pygame.draw.rect(surface, (230, 240, 255), (asx, asy, asw, ash))