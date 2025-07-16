import cv2
import mediapipe as mp
import numpy as np
import os
import csv
import math 


# ---------------------
# Initial configuration
# ---------------------
# Thresholds related to the position of the iris in the bbox eye (0-1)
# Minimum and maximum values of x and y inside the eye considered "centered"
X_LEFT_THRESH  = 0.30
X_RIGHT_THRESH = 0.70
Y_UP_THRESH    = 0.30
Y_DOWN_THRESH  = 0.70

# Path of images
FOLDER_PATH = r'PATH_TO_DATASET'

# ---------------------
# Setup MediaPipe
# ---------------------
mp_face_mesh   = mp.solutions.face_mesh
mp_face_detect = mp.solutions.face_detection

# ---------------------
# Functions of utilities
# ---------------------
def get_face_crop(img):
    # Trim the area around the face
    with mp_face_detect.FaceDetection(model_selection=1,
                                     min_detection_confidence=0.5) as detector:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = detector.process(rgb)
        if not res.detections:
            return None
        bbox = res.detections[0].location_data.relative_bounding_box
        h, w, _ = img.shape
        x1 = max(int(bbox.xmin * w) - 20, 0)
        y1 = max(int(bbox.ymin * h) - 20, 0)
        x2 = min(x1 + int(bbox.width * w) + 40, w)
        y2 = min(y1 + int(bbox.height * h) + 40, h)
        return img[y1:y2, x1:x2]


def get_landmarks(img):
    # Return to the Face Mesh landmarks
    with mp_face_mesh.FaceMesh(static_image_mode=True,
                               max_num_faces=1,
                               refine_landmarks=True,
                               min_detection_confidence=0.5) as fmesh:
        img.flags.writeable = False
        res = fmesh.process(img)
        if not res.multi_face_landmarks:
            return None
        return res.multi_face_landmarks[0].landmark


def iris_center(landmarks, indices, w, h):
    # Calculate the iris center
    xs = [landmarks[i].x * w for i in indices]
    ys = [landmarks[i].y * h for i in indices]
    return np.mean(xs), np.mean(ys)


def eye_bbox_norm(landmarks, corner_idxs, topbot_idxs, iris_cent, w, h):
    # Normalizes the position of the iris within the eye bbox
    corner_x = [landmarks[i].x * w for i in corner_idxs]
    corner_y = [landmarks[i].y * h for i in corner_idxs]
    topbot_y = [landmarks[i].y * h for i in topbot_idxs]
    xmin, xmax = min(corner_x), max(corner_x)
    ymin, ymax = min(min(corner_y), min(topbot_y)), max(max(corner_y), max(topbot_y))
    ix, iy = iris_cent
    nx = (ix - xmin) / (xmax - xmin)
    ny = (iy - ymin) / (ymax - ymin)
    return nx, ny

# ---------------------
# Main Processing
# ---------------------
frame_list = sorted([f for f in os.listdir(FOLDER_PATH)
                     if f.lower().endswith(('.jpg', '.png'))])
results = []

for fname in frame_list:
    img_path = os.path.join(FOLDER_PATH, fname)
    img = cv2.imread(img_path)
    if img is None:
        continue

    face = get_face_crop(img)
    if face is None:
        results.append((fname, 'DISTRACTED'))
        continue

    # Upscale to increase the value for precise eyes.
    face = cv2.resize(face, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    h, w, _ = face.shape
    lm = get_landmarks(face)
    if lm is None:
        results.append((fname, 'DISTRACTED'))
        continue

    # Calculate iris centers and normalize for eye
    left_idx  = [469, 470, 471, 472]
    right_idx = [474, 475, 476, 477]
    left_center  = iris_center(lm, left_idx, w, h)
    right_center = iris_center(lm, right_idx, w, h)
    left_norm  = eye_bbox_norm(lm, [33,133],  [159,145], left_center,  w, h)
    right_norm = eye_bbox_norm(lm, [362,263], [386,374], right_center, w, h)

    # Check eye direction based only on eyes
    lx, ly = left_norm
    rx, ry = right_norm
    # ATTENTIVE if both irises are in the X and Y range
    if (X_LEFT_THRESH  <= lx <= X_RIGHT_THRESH and
        X_LEFT_THRESH  <= rx <= X_RIGHT_THRESH and
        Y_UP_THRESH    <= ly <= Y_DOWN_THRESH    and
        Y_UP_THRESH    <= ry <= Y_DOWN_THRESH):
        status = 'ATTENTIVE'
    else:
        status = 'DISTRACTED'

    # Debug: print normalized values and status
    print(f"DEBUG {fname}: left={left_norm}, right={right_norm}, status={status}")

    # Annotation and display
    face.flags.writeable = True
    color = (0,255,0) if status=='ATTENTIVE' else (0,0,255)
    cv2.putText(face, f"Attention: {status}", (30,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow('Frame', face)
    if cv2.waitKey(0) == 27:
        break

    results.append((fname, status))

cv2.destroyAllWindows()

# ---------------------
# Final smoothing (closest voting)
# ---------------------
window = 5
half = window // 2
sm = results.copy()
for i in range(len(results)):
    att = sum(1 for j in range(i-half, i+half+1)
              if 0<=j<len(results) and results[j][1]=='ATTENTIVE')
    dist = sum(1 for j in range(i-half, i+half+1)
               if 0<=j<len(results) and results[j][1]=='DISTRACTED')
    if att+dist >= window-1:
        sm[i] = (results[i][0], 'ATTENTIVE' if att>dist else 'DISTRACTED')

print("\n==== FINAL RESULTS AFTER SMOOTHING ====")
for f, s in sm:
    print(f, s)
    

# with open('labels_output.csv', 'w', newline='') as f:
#     writer = csv.writer(f)
#     writer.writerow(['frame', 'label'])
#     writer.writerows(results)
    
    
    
# -----------------------------------------------
# ### NEW LOGIC STARTS HERE ###
# -----------------------------------------------

# --- 1. Block Analysis ---
num_frames = len(sm)
if num_frames > 0:
    block_size = math.ceil(num_frames / 3) # Ensures we cover all frames
    
    # Define the 3 blocks based on frame indices
    block1_data = sm[0:block_size]
    block2_data = sm[block_size : 2 * block_size]
    block3_data = sm[2 * block_size : num_frames]
    
    blocks = {
        "Block 1": block1_data,
        "Block 2": block2_data,
        "Block 3": block3_data
    }
    
    block_analysis_results = []
    
    print("\n==== BLOCK-LEVEL ATTENTION ANALYSIS ====")
    for block_name, block_data in blocks.items():
        if not block_data:
            print(f"{block_name}: No data")
            continue
            
        total_in_block = len(block_data)
        attentive_in_block = sum(1 for _, label in block_data if label == 'ATTENTIVE')
        
        # Calculate percentage, handle division by zero
        attention_percentage = (attentive_in_block / total_in_block) * 100 if total_in_block > 0 else 0
        
        # Determine overall status for the block
        block_status = "ATTENTIVE" if attention_percentage >= 60.0 else "DISTRACTED"
        
        print(f"{block_name} (Frames {block_data[0][0]} to {block_data[-1][0]}):")
        print(f"  - Attention Percentage: {attention_percentage:.2f}%")
        print(f"  - Overall Status: {block_status}")
        
        block_analysis_results.append({
            "block_name": block_name,
            "start_frame": block_data[0][0],
            "end_frame": block_data[-1][0],
            "attention_percentage": f"{attention_percentage:.2f}%",
            "status": block_status
        })

# --- 2. Save the Block Analysis Report ---
# This creates a simple text file with the block summary.
with open('block_analysis_report.txt', 'w') as f:
    f.write("Attention Analysis by Block\n")
    f.write("===========================\n\n")
    for res in block_analysis_results:
        f.write(f"{res['block_name']} (Frames {res['start_frame']} to {res['end_frame']}):\n")
        f.write(f"  - Attention Percentage: {res['attention_percentage']}\n")
        f.write(f"  - Status: {res['status']}\n\n")
print("\nINFO: Block analysis report saved to 'block_analysis_report.txt'")


# --- 3. Save the Per-Frame Smoothed Results to CSV ---
# FIX: This now correctly saves the SMOOTHED `sm` results.
with open('attention_log.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['frame_filename', 'attention_label'])
    writer.writerows(sm) # <-- Use sm, not results
    
print("INFO: Per-frame smoothed attention log saved to 'attention_log.csv'")
