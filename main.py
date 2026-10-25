
import pygame
import cv2
import mediapipe as mp

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Platformer")
clock = pygame.time.Clock()

# Webcam and MediaPipe
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# Player
player = pygame.Rect(100, 450, 40, 50)
velocity_y = 0
speed = 5
gravity = 0.6
jump_power = -13
on_ground = False

platforms = [
    pygame.Rect(0, 550, 900, 50),
    pygame.Rect(200, 440, 150, 20),
    pygame.Rect(420, 350, 150, 20),
    pygame.Rect(650, 260, 150, 20),
]
coins = [
    pygame.Rect(260, 400, 20, 20),
    pygame.Rect(470, 310, 20, 20),
    pygame.Rect(700, 220, 20, 20),
]

score = 0
font = pygame.font.SysFont(None, 28)
running = True

# Track jump gesture transitions
jump_frames = 0
release_frames = 0
jump_cooldown = 0
jump_latched = False

JUMP_CONFIRM_FRAMES = 4
JUMP_RELEASE_FRAMES = 5
JUMP_COOLDOWN_FRAMES = 15

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Read webcam frame
    success, frame = cap.read()

    hand_x = None
    index_up = False

    if success:
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(
                frame, hand, mp_hands.HAND_CONNECTIONS
            )

            # Use index fingertip for horizontal control
            tip = hand.landmark[8]
            hand_x = tip.x

            # Detect index finger raised, other fingers folded
            index_tip = hand.landmark[8]
            index_joint = hand.landmark[6]
            middle_tip = hand.landmark[12]
            middle_joint = hand.landmark[10]
            ring_tip = hand.landmark[16]
            ring_joint = hand.landmark[14]
            pinky_tip = hand.landmark[20]
            pinky_joint = hand.landmark[18]

            index_up = (
                index_tip.y < index_joint.y
                and middle_tip.y > middle_joint.y
                and ring_tip.y > ring_joint.y
                and pinky_tip.y > pinky_joint.y
            )

        cv2.imshow("Hand Camera", frame)

    # Keyboard fallback
    keys = pygame.key.get_pressed()
    moving = False

    if hand_x is not None:
        # Map camera position to game screen
        target_x = int(hand_x * WIDTH) - player.width // 2
        player.x += int((target_x - player.x) * 0.2)
        moving = True
    else:
        if keys[pygame.K_LEFT]:
            player.x -= speed
        if keys[pygame.K_RIGHT]:
            player.x += speed

    # Jump on the gesture's rising edge
        
    # Stabilize jump gesture
    if jump_cooldown > 0:
        jump_cooldown -= 1

    if index_up:
        jump_frames += 1
        release_frames = 0
    else:
        jump_frames = 0
        release_frames += 1

    # Unlock jumping only after the gesture is released
    if release_frames >= JUMP_RELEASE_FRAMES:
        jump_latched = False

    # Jump after the gesture is detected consistently
    if (
        jump_frames >= JUMP_CONFIRM_FRAMES
        and not jump_latched
        and jump_cooldown == 0
        and on_ground
    ):
        velocity_y = jump_power
        on_ground = False
        jump_latched = True
        jump_cooldown = JUMP_COOLDOWN_FRAMES

    # Keyboard jump fallback
    if keys[pygame.K_SPACE] and on_ground:
        velocity_y = jump_power
        on_ground = False

    # Keyboard jump fallback
    if keys[pygame.K_SPACE] and on_ground:
        velocity_y = jump_power
        on_ground = False

    # Gravity and vertical movement
    velocity_y += gravity
    player.y += int(velocity_y)

    # Platform collision when falling
    on_ground = False

    for platform in platforms:
        if (
            player.colliderect(platform)
            and velocity_y >= 0
            and player.bottom - velocity_y <= platform.top + 2
        ):
            player.bottom = platform.top
            velocity_y = 0
            on_ground = True

    player.left = max(0, min(player.left, WIDTH - player.width))

    if player.top > HEIGHT:
        player.x = 100
        player.y = 450
        velocity_y = 0
    # Collect coins
    for coin in coins[:]:
        if player.colliderect(coin):
            coins.remove(coin)
            score += 1
    # Draw game
    screen.fill((25, 30, 55))

    for platform in platforms:
        pygame.draw.rect(screen, (80, 200, 130), platform)
    # Draw coins
    for coin in coins:
        pygame.draw.circle(
            screen,
            (255, 215, 0),
            coin.center,
            10
        )

    pygame.draw.rect(screen, (255, 190, 70), player)

    instructions = font.render(
        "Move hand: Move | Raise index finger: Jump | Space: Jump",
        True, (255, 255, 255)
    )
    score_text = font.render(
        f"Coins: {score}/{3}",
        True,
        (255, 215, 0)
    )
    screen.blit(score_text, (20, 90))
    screen.blit(instructions, (20, 20))

    status = "Hand detected" if hand_x is not None else "No hand - use arrow keys"
    screen.blit(font.render(status, True, (255, 255, 255)), (20, 55))

    pygame.display.flip()

# Cleanup
cap.release()
hands.close()
cv2.destroyAllWindows()
pygame.quit()
