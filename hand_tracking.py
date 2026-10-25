
import cv2
import mediapipe as mp

# Initialize MediaPipe hand tracking
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam.")
    exit()

while True:
    success, frame = cap.read()

    if not success:
        print("Could not read camera frame.")
        break

    # Mirror the camera like a selfie
    frame = cv2.flip(frame, 1)

    # Convert BGR (OpenCV) to RGB (MediaPipe)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect hand landmarks
    results = hands.process(rgb)

    height, width, _ = frame.shape

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            # Draw all 21 landmarks and their connections
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Landmark 8 is the index fingertip
            tip = hand_landmarks.landmark[8]

            # Convert normalized coordinates to pixels
            x = int(tip.x * width)
            y = int(tip.y * height)

            # Highlight the fingertip
            cv2.circle(frame, (x, y), 12, (0, 255, 0), -1)

            # Display position
            cv2.putText(
                frame,
                f"Index: ({x}, {y})",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Normalized coordinates: 0 to 1
            cv2.putText(
                frame,
                f"Normalized: ({tip.x:.2f}, {tip.y:.2f})",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

    else:
        cv2.putText(
            frame,
            "No hand detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow("Hand Tracking", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()
