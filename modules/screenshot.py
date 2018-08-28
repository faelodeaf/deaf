import threading

from numpy import ndarray
from cv2 import VideoCapture, imwrite, redirectError

import sys
sys.path.append('..')

import config


class ScreenshotThread(threading.Thread):
    """
    Uses opencv-python for capturing rtsp stream and taking screenshots.
    """
    def __init__(self, screenshot_queue):
        threading.Thread.__init__(self)
        self.screenshot_queue = screenshot_queue

    def handle_errors(self, *args):
        """Custom handling cv2 exceptions. Doesn't work for warnings."""
        pass

    def get_screenshot(self, creds, ip, path):
        redirectError(self.handle_errors)
        try:
            video_capture = VideoCapture(f'rtsp://{creds}@{ip}{path}')
            ret, frame = video_capture.read()
            if isinstance(frame, ndarray):
                imwrite(f'pics/{ip}.jpg', frame)
        except Exception as e:
            pass
        finally:
            video_capture.release()

    def run(self):
        while True:
            creds, ip, path = self.screenshot_queue.get()
            self.get_screenshot(creds, ip, path)
            config.update_bar(__class__)
            self.screenshot_queue.task_done()
