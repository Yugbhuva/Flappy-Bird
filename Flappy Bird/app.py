import pygame
import random
import time
from pygame.locals import *

# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Game constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
INITIAL_SPEED = 20
GRAVITY = 2.5
GAME_SPEED = 15
SLOW_GRAVITY = 1.5  # Slower gravity after restart

GROUND_WIDTH = 2 * SCREEN_WIDTH
GROUND_HEIGHT = 100
PIPE_WIDTH = 80
PIPE_HEIGHT = 500
PIPE_GAP = 150

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird')
clock = pygame.time.Clock()

# Load assets
try:
    BACKGROUND = pygame.image.load('assets/sprites/background-day.png').convert()
    BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDTH, SCREEN_HEIGHT))
    BEGIN_IMAGE = pygame.image.load('assets/sprites/message.png').convert_alpha()
    
    # Font setup
    font = pygame.font.SysFont('Arial', 30)
    game_over_font = pygame.font.SysFont('Arial', 50, bold=True)
    button_font = pygame.font.SysFont('Arial', 25)
    
    # Sound setup
    wing_sound = pygame.mixer.Sound('assets/audio/wing.wav')
    hit_sound = pygame.mixer.Sound('assets/audio/hit.wav')
except Exception as e:
    print(f"Error loading assets: {e}")
    pygame.quit()
    exit()

class Bird(pygame.sprite.Sprite):
    def __init__(self, slow_gravity=False):
        pygame.sprite.Sprite.__init__(self)
        try:
            self.images = [
                pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
                pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
                pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha()
            ]
            self.image = self.images[0]
            self.mask = pygame.mask.from_surface(self.image)
        except Exception as e:
            print(f"Error loading bird images: {e}")
            pygame.quit()
            exit()
            
        self.speed = INITIAL_SPEED
        self.current_image = 0
        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDTH / 6
        self.rect[1] = SCREEN_HEIGHT / 2
        self.slow_gravity = slow_gravity
        self.current_gravity = GRAVITY if not slow_gravity else SLOW_GRAVITY

    def update(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]
        self.speed += self.current_gravity
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -INITIAL_SPEED
        wing_sound.play()

    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]

class Pipe(pygame.sprite.Sprite):
    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)
        try:
            self.image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))
        except Exception as e:
            print(f"Error loading pipe image: {e}")
            pygame.quit()
            exit()
            
        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize
        self.mask = pygame.mask.from_surface(self.image)
        self.passed = False

    def update(self):
        self.rect[0] -= GAME_SPEED

class Ground(pygame.sprite.Sprite):
    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        try:
            self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (GROUND_WIDTH, GROUND_HEIGHT))
        except Exception as e:
            print(f"Error loading ground image: {e}")
            pygame.quit()
            exit()
            
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT
    
    def update(self):
        self.rect[0] -= GAME_SPEED

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=10)
        
        text_surface = button_font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])

def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted

def reset_game(slow_gravity=False):
    global bird, bird_group, ground_group, pipe_group, score, game_active
    
    bird_group = pygame.sprite.Group()
    bird = Bird(slow_gravity)
    bird_group.add(bird)

    ground_group = pygame.sprite.Group()
    for i in range(2):
        ground = Ground(GROUND_WIDTH * i)
        ground_group.add(ground)

    pipe_group = pygame.sprite.Group()
    for i in range(2):
        pipes = get_random_pipes(SCREEN_WIDTH * i + 800)
        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])
    
    score = 0
    game_active = True

def show_game_over_screen(final_score):
    screen.blit(BACKGROUND, (0, 0))
    
    game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
    screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 100))
    
    score_text = font.render(f"Score: {final_score}", True, (0, 0, 0))
    screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 180))
    
    replay_button = Button(SCREEN_WIDTH//2 - 100, 250, 200, 50, "Play Again", (100, 255, 100), (150, 255, 150))
    replay_button.draw(screen)
    
    # instruction_text = font.render("Press SPACE to restart", True, (0, 0, 0))
    # screen.blit(instruction_text, (SCREEN_WIDTH//2 - instruction_text.get_width()//2, 320))
    
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            
            # Space bar or button click to restart
            if (event.type == KEYDOWN and event.key == K_SPACE) or \
               (event.type == MOUSEBUTTONDOWN and replay_button.rect.collidepoint(pygame.mouse.get_pos())):
                return True
            
        mouse_pos = pygame.mouse.get_pos()
        replay_button.check_hover(mouse_pos)
        replay_button.draw(screen)
        pygame.display.update()
        clock.tick(60)

def show_start_screen():
    screen.blit(BACKGROUND, (0, 0))
    screen.blit(BEGIN_IMAGE, (120, 150))
    
    # instruction_text = font.render("Press SPACE to start", True, (0, 0, 0))
    # screen.blit(instruction_text, (SCREEN_WIDTH//2 - instruction_text.get_width()//2, 320))
    
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN and event.key == K_SPACE:
                return True
        
        clock.tick(60)

# Main game function
def main():
    global score, game_active
    
    # Initial game setup
    reset_game()
    
    # Show start screen
    if not show_start_screen():
        pygame.quit()
        return
    
    game_active = True
    bird.bump()  # Initial jump
    
    # Main game loop
    running = True
    while running:
        clock.tick(15)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if game_active:
                    bird.bump()
                elif event.key == K_SPACE:  # Allow space to restart from game over
                    pass  # Handled in show_game_over_screen
        
        screen.blit(BACKGROUND, (0, 0))
        
        if game_active:
            # Update score
            for pipe in pipe_group:
                if pipe.rect.right < bird.rect.left and not pipe.passed:
                    pipe.passed = True
                    score += 0.5
            
            score_text = font.render(f"Score: {int(score)}", True, (255, 255, 255))
            screen.blit(score_text, (20, 20))
            
            # Update sprites
            bird_group.update()
            ground_group.update()
            pipe_group.update()
            
            # Draw sprites
            bird_group.draw(screen)
            pipe_group.draw(screen)
            ground_group.draw(screen)
            
            # Check collisions
            if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
                    pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
                hit_sound.play()
                game_active = False
            
            # Recycle ground
            if is_off_screen(ground_group.sprites()[0]):
                ground_group.remove(ground_group.sprites()[0])
                new_ground = Ground(GROUND_WIDTH - 20)
                ground_group.add(new_ground)
            
            # Recycle pipes
            if is_off_screen(pipe_group.sprites()[0]):
                pipe_group.remove(pipe_group.sprites()[0])
                pipe_group.remove(pipe_group.sprites()[0])
                pipes = get_random_pipes(SCREEN_WIDTH * 2)
                pipe_group.add(pipes[0])
                pipe_group.add(pipes[1])
        else:
            # Game over - show restart screen
            if show_game_over_screen(int(score)):
                reset_game(slow_gravity=True)  # Use slower gravity after restart
            else:
                running = False
        
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()