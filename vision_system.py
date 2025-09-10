import cv2
import numpy as np
from utils import pipe

# GLOBALS
HSV_dict = {
    "outlines": (np.array([166, 64, 74]), np.array([179, 110, 105])),
    "pipes": (np.array([33, 90, 106]), np.array([48, 200, 255]))
}
floor_y = None

def segment_frame(frame, target):
    global HSV_dict
    if target not in HSV_dict:
        raise ValueError(f"Target '{target}' not found in HSV_dict")

    kernel = np.ones((5, 5), np.uint8)
    #frame = cv2.erode(frame, kernel, iterations=1)
    #frame = cv2.dilate(frame, kernel, iterations=1)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_dict[target][0], HSV_dict[target][1])
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.erode(mask, kernel, iterations=2)

    return mask


def draw_screen_info(frame, floor_y, pipes, bird=None):
    for p in pipes:
        x, y, w, h = p.x, p.y, p.w, p.h
        # Draw bounding boxes
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 4)
        cv2.putText(frame, f"({x},{p.syb})", (x, p.syb - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        # Draw safe zones
        cv2.line(frame, (x, p.syt), (x + w, p.syt), (0, 0, 255), 4)
        cv2.line(frame, (x, p.syb), (x + w, p.syb), (0, 0, 255), 4)

    # Draw the floor square
    if floor_y is not None:
        cv2.rectangle(frame, (0, floor_y), (frame.shape[1], frame.shape[0]), (0, 0, 255), 2)

    # Draw the bird
    if bird is not None:
        x, y, w, h = bird
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 4)
        cv2.putText(frame, f"({x},{y})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return frame


def detect_floor_y_position(screen, screen_w):
    mask = segment_frame(screen, "outlines")

    # Put bounding box around the detected area
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_w_contour = None
    max_w = -1
    if contours:
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > max_w:
                max_w = w
                max_w_contour = contour
        if max_w_contour is not None:
            x, y, w, h = cv2.boundingRect(max_w_contour)
            if screen_w - w < 100:   # Floor width should be close to screen width
                return y + h - 5
    else:
        return None


def detect_pipes(screen, floor_y):
    mask = segment_frame(screen, "pipes")

    # Make everything under the floor black
    mask[floor_y:, :] = 0

    # Make the mast a little bigger
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    #cv2.rectangle(mask, (200, 150), (400, 280), 0, thickness=-1)  #DEBUG

    # Find contours of the pipes
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pipe_positions = [] 
    if contours:
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 20:  # Filter out small noise
                pipe_positions.append((x, y, w, h))

    return pipe_positions, mask


def group_pipes_by_x(pipes, x_tolerance=20):
    if not pipes:
        return []

    # Sort pipes left to right
    pipes.sort(key=lambda p: p[0])  # sort by x

    groups = []
    current_group = [pipes[0]]

    for i in range(1, len(pipes)):
        x, y, w, h = pipes[i]
        prev_x, prev_y, prev_w, prev_h = pipes[i - 1]

        # If this pipe is close in X to the previous one, group them
        if abs(x - prev_x) < x_tolerance:
            current_group.append(pipes[i])
        else:
            # Start a new group
            groups.append(current_group)
            current_group = [pipes[i]]

    groups.append(current_group)  # add the last group
    return groups


# Create a list of pipes by detecting and connecting segments
def process_pipes(screen, floor_y, safety_margin=1):
    pipes, mask = detect_pipes(screen, floor_y)
    if not pipes:
        return [], mask
    
    # Connect pipe segments that are above each other on the Y axis
    connected_pipes = []
    pipe_groups = group_pipes_by_x(pipes)
    for group in pipe_groups:
        if len(group) < 2:
            pass

        # Pick top and bottom segments in the group
        lst = sorted(group, key=lambda p: p[1], reverse=True)
        bottom = lst[0]
        top = lst[1] if len(lst) > 1 else lst[0]

        x1, y1, w1, h1 = top
        x2, y2, w2, h2 = bottom

        # Make sure top extends to the top of the screen
        # When score becomes big, it might cut top part in half
        h1 += y1
        y1 = 0

        # Safe zones
        syt = y1 + h1 + safety_margin
        syb = y2 - safety_margin

        # Create pipe object
        connected_pipes.append(pipe(x1, y1, w1, (y2 + h2) - y1, syt, syb))


    return connected_pipes, mask


def detect_bird(screen):
    global HSV_dict, floor_y

    mask = segment_frame(screen, "outlines")
    kernel = np.ones((7, 7), np.uint8)

    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=5)
    mask = cv2.erode(mask, kernel, iterations=3)

    # Crop the sides because pipe outlines might ruin if they are partially visble
    # The bird will never be there anyway
    h, w = mask.shape[:2]
    cut = int(0.1 * w)
    mask[:, :cut] = 0
    mask[:, w-cut:] = 0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, mask

    # Assume the bird is the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)

    return (x, y, w, h), mask


def process_frame(frame, safety_margin=0):
    global HSV_dict, floor_y

    # Detect floor y-position if not already detected
    if floor_y is None:
        floor_y = detect_floor_y_position(frame, frame.shape[1])
        if floor_y is not None:
            print(f"Detected floor y-position: {floor_y}")
        else:
            print("Floor y-position not detected yet.")
            return None, None
        
    pipes, pipe_mask = process_pipes(frame, floor_y, safety_margin)
    bird, bird_mask = detect_bird(frame)

    return (floor_y, pipes, bird), (pipe_mask, bird_mask)
