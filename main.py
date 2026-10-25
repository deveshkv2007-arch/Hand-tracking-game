
import pygame

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Platformer")

clock = pygame.time.Clock()

# Player
player = pygame.Rect(100, 450, 40, 50)
velocity_y = 0
speed = 5
gravity = 0.6
jump_power = -13
on_ground = False

# Platforms
platforms = [
    pygame.Rect(0, 550, 900, 50),
    pygame.Rect(200, 440, 150, 20),
    pygame.Rect(420, 350, 150, 20),
    pygame.Rect(650, 260, 150, 20),
]

running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Horizontal movement
    if keys[pygame.K_LEFT]:
        player.x -= speed
    if keys[pygame.K_RIGHT]:
        player.x += speed

    # Jump
    if keys[pygame.K_SPACE] and on_ground:
        velocity_y = jump_power
        on_ground = False

    # Gravity
    velocity_y += gravity
    player.y += int(velocity_y)

    # Platform collision
    on_ground = False

    for platform in platforms:
        if player.colliderect(platform) and velocity_y >= 0:
            if player.bottom - velocity_y <= platform.top + 2:
                player.bottom = platform.top
                velocity_y = 0
                on_ground = True

    # Screen boundaries
    player.left = max(0, player.left)
    player.right = min(WIDTH, player.right)

    if player.top > HEIGHT:
        player.x = 100
        player.y = 450
        velocity_y = 0

    # Draw
    screen.fill((25, 30, 55))

    for platform in platforms:
        pygame.draw.rect(screen, (80, 200, 130), platform)

    pygame.draw.rect(screen, (255, 190, 70), player)

    font = pygame.font.SysFont(None, 28)
    text = font.render(
        "Arrow keys: Move | Space: Jump",
        True,
        (255, 255, 255)
    )
    screen.blit(text, (20, 20))

    pygame.display.flip()

pygame.quit()
