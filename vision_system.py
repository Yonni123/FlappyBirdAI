import cv2
import numpy as np

# GLOBALS
HSV_dict = {
    "outlines": (np.array([166, 64, 74]), np.array([179, 110, 105])),
    "pipes": (np.array([33, 90, 106]), np.array([48, 200, 255]))
}
floor_y = None


class pipe:
    def __init__(self, x, y, w, h, syt, syb):   # Safe y-top, Safe y-bottom
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.syt = syt
        self.syb = syb
        self.center = (x + w // 2, y + h // 2)


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
        cv2.putText(frame, f"({x},{y})", (x, p.syb - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
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

    # Make the mast a little bigger
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Make everything under the floor black
    mask[floor_y:, :] = 0

    # Find contours of the pipes
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pipe_positions = [] 
    if contours:
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 20:  # Filter out small noise
                pipe_positions.append((x, y, w, h))

    return pipe_positions, mask


# Create a list of pipes by detecting and connecting segments
def process_pipes(screen, floor_y, safety_margin=1):
    pipes, mask = detect_pipes(screen, floor_y)
    if not pipes:
        return [], mask
    
    # Connect pipe segments that are above each other on the Y axis
    pipes.sort(key=lambda p: p[1])  # Sort by y position so that we can connect top and bottom segments 
    connected_pipes = []
    skip_indices = set()
    for i in range(len(pipes)):
        if i in skip_indices:
            continue
        x, y, w, h = pipes[i]
        # Look for a bottom segment that is below this top segment and close in x position
        for j in range(i + 1, len(pipes)):
            if j in skip_indices:
                continue
            x2, y2, w2, h2 = pipes[j]
            if abs(x - x2) < 20 and y2 > y:  # Close in x and below in y
                # Found a matching bottom segment
                syt = y + h + safety_margin  # Safe y-top
                syb = y2 - safety_margin     # Safe y-bottom
                connected_pipes.append(pipe(x, y, w, (y2 + h2) - y, syt, syb))
                skip_indices.add(j)
                break

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


def process_frame(frame):
    global HSV_dict, floor_y

    # Detect floor y-position if not already detected
    if floor_y is None:
        floor_y = detect_floor_y_position(frame, frame.shape[1])
        if floor_y is not None:
            print(f"Detected floor y-position: {floor_y}")
        else:
            print("Floor y-position not detected yet.")
            return
        
    pipes, pipe_mask = process_pipes(frame, floor_y)
    bird, bird_mask = detect_bird(frame)

    return (floor_y, pipes, bird), (pipe_mask, bird_mask)
