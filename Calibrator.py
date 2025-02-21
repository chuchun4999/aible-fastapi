import cv2
import numpy as np
import time
import mediapipe as mp

class Calibrator:
    def __init__(self, calibration_frames=1, rom_duration=1):
        self.calibration_frames = calibration_frames
        self.rom_duration = rom_duration
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        self.joint_landmark_map = {
            "hip_flexion": [self.mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                            self.mp_pose.PoseLandmark.LEFT_HIP.value,
                            self.mp_pose.PoseLandmark.LEFT_KNEE.value],
            "knee_flexion": [self.mp_pose.PoseLandmark.LEFT_HIP.value,
                             self.mp_pose.PoseLandmark.LEFT_KNEE.value,
                             self.mp_pose.PoseLandmark.LEFT_ANKLE.value],
            "ankle_dorsiflexion": [self.mp_pose.PoseLandmark.LEFT_KNEE.value,
                                   self.mp_pose.PoseLandmark.LEFT_ANKLE.value,
                                   self.mp_pose.PoseLandmark.LEFT_HEEL.value]
        }
        
        self.joints = list(self.joint_landmark_map.keys())
    
    @staticmethod
    def calculate_angle_3d(p1, p2, p3):
        a = np.array(p1)
        b = np.array(p2)
        c = np.array(p3)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        return float(angle)
    
    def process_frame(self, frame):
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)
        
        joint_angles = {}
        if results.pose_landmarks:
            for joint in self.joints:
                indices = self.joint_landmark_map[joint]
                pts = [(results.pose_landmarks.landmark[idx].x,
                        results.pose_landmarks.landmark[idx].y,
                        results.pose_landmarks.landmark[idx].z) for idx in indices]
                angle = Calibrator.calculate_angle_3d(pts[0], pts[1], pts[2])
                joint_angles[joint] = angle

        
        return frame, joint_angles

