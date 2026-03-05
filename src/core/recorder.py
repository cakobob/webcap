import cv2
import threading
import time
import sounddevice as sd
import soundfile as sf
import numpy as np
import imageio_ffmpeg
import subprocess
import os
import tempfile
import uuid

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.cap = None
        self.out = None
        self.audio_stream = None
        self.audio_frames = []
        
        # Use a unique session ID so that multiple instances don't share temp files
        session_id = uuid.uuid4().hex[:8]
        self.temp_dir = tempfile.gettempdir()
        self.temp_video = os.path.join(self.temp_dir, f"webcap_{session_id}_video.mp4")
        self.temp_audio = os.path.join(self.temp_dir, f"webcap_{session_id}_audio.wav")
        
        self.final_filename = ""
        self.sample_rate = 44100
        self.channels = 1 # Mono mic usually
        
        self.target_aspect_ratio = None # (width, height) tuple or None
        self.crop_rect = None # (x, y, w, h)

    @staticmethod
    def get_available_cameras():
        """Check for available cameras without requiring a Recorder instance.

        Returns:
            List of tuples (index, name).
        """
        available_cameras = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                backend = cap.getBackendName()
                available_cameras.append((i, f"Camera {i} ({backend})"))
                cap.release()
        return available_cameras

    @staticmethod
    def get_available_microphones():
        """List input audio devices without requiring a Recorder instance.

        Returns:
            List of tuples (index, name).
        """
        devices = []
        try:
            all_devices = sd.query_devices()
            for i, dev in enumerate(all_devices):
                if dev['max_input_channels'] > 0:
                    devices.append((i, dev['name']))
        except Exception as e:
            print(f"Error listing microphones: {e}")
        return devices

    def start_camera(self, camera_index=0, resolution="1280x720", aspect_ratio="Default"):
        if self.cap:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {camera_index}.")
            return False
            
        # Parse resolution
        try:
            w, h = map(int, resolution.split('x'))
        except (ValueError, AttributeError):
            w, h = 1280, 720
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        
        # Calculate crop rect based on aspect ratio
        actual_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        self.crop_rect = None
        if aspect_ratio != "Default":
            try:
                target_w_ratio, target_h_ratio = map(int, aspect_ratio.split(':'))
                
                # Determine target dimensions based on height (keep height, crop width) 
                # or width (keep width, crop height)
                
                # Try matching height first
                new_w = int(actual_h * (target_w_ratio / target_h_ratio))
                new_h = int(actual_h)
                
                if new_w > actual_w:
                    # If new width is too big, match width instead
                    new_w = int(actual_w)
                    new_h = int(actual_w * (target_h_ratio / target_w_ratio))
                
                # Center crop
                x = int((actual_w - new_w) / 2)
                y = int((actual_h - new_h) / 2)
                
                self.crop_rect = (x, y, new_w, new_h)
                print(f"Aspect Ratio {aspect_ratio}: Cropping to {new_w}x{new_h} at ({x},{y})")
            except Exception as e:
                print(f"Error calculating aspect ratio: {e}")
                self.crop_rect = None
        
        return True

    def get_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Apply crop if needed
                if self.crop_rect:
                    x, y, w, h = self.crop_rect
                    frame = frame[y:y+h, x:x+w]
                
                if self.is_recording and self.out:
                    self.out.write(frame)
                return frame
        return None

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_frames.append(indata.copy())

    def start_recording(self, filename="output.mp4", mic_index=None):
        if not self.cap:
            return
        
        self.final_filename = filename
        
        # Video Setup
        # Use 'avc1' for H.264 which is standard on Mac and widely supported
        fourcc = cv2.VideoWriter_fourcc(*'avc1') 
        
        if self.crop_rect:
            width = self.crop_rect[2]
            height = self.crop_rect[3]
        else:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
        fps = 30.0 
        
        self.out = cv2.VideoWriter(self.temp_video, fourcc, fps, (width, height))
        
        # Audio Setup
        self.audio_frames = []
        try:
            device = mic_index if mic_index is not None else None
            self.audio_stream = sd.InputStream(
                device=device,
                samplerate=self.sample_rate, 
                channels=self.channels, 
                callback=self.audio_callback
            )
            self.audio_stream.start()
        except Exception as e:
            print(f"Audio error: {e}")
            self.audio_stream = None

        self.is_recording = True
        print(f"Recording started: {filename}")

    def stop_recording(self, on_finished=None):
        self.is_recording = False
        
        # Stop Video
        if self.out:
            self.out.release()
            self.out = None
            
        # Stop Audio
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
            
            # Save Audio
            if self.audio_frames:
                audio_data = np.concatenate(self.audio_frames, axis=0)
                sf.write(self.temp_audio, audio_data, self.sample_rate)
            else:
                # Create silent audio if no frames
                print("Warning: No audio frames recorded")
                sf.write(self.temp_audio, np.zeros((self.sample_rate, self.channels)), self.sample_rate)

        print("Recording stopped. Muxing in background...")
        
        # Run muxing in a separate thread to avoid blocking UI
        mux_thread = threading.Thread(target=self.mux_audio_video, args=(on_finished,))
        mux_thread.start()

    def mux_audio_video(self, on_finished=None):
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        # Check if files exist before attempting mux
        if not os.path.exists(self.temp_video):
            print("Error: Temp video not found")
            if on_finished:
                on_finished(None)
            return

        if not os.path.exists(self.temp_audio):
            print("Error: Temp audio not found")
            if on_finished:
                on_finished(None)
            return

        cmd = [
            ffmpeg_exe,
            '-y',
            '-i', self.temp_video,
            '-i', self.temp_audio,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            self.final_filename
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Muxing complete: {self.final_filename}")
        except subprocess.CalledProcessError as e:
            print(f"Muxing failed: {e}")
            # Cleanup temp files and signal failure
            if os.path.exists(self.temp_video):
                os.remove(self.temp_video)
            if os.path.exists(self.temp_audio):
                os.remove(self.temp_audio)
            if on_finished:
                on_finished(None)
            return

        # Cleanup temp files
        if os.path.exists(self.temp_video):
            os.remove(self.temp_video)
        if os.path.exists(self.temp_audio):
            os.remove(self.temp_audio)

        if on_finished:
            if os.path.exists(self.final_filename):
                on_finished(self.final_filename)
            else:
                on_finished(None)

    def stop_camera(self):
        if self.is_recording:
            self.stop_recording()
        if self.cap:
            self.cap.release()

