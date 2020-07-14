import threading

import av
from PIL import Image

import sys

sys.path.append("..")
import config


class ScreenshotThread(threading.Thread):
    """
    Uses opencv-python for capturing rtsp stream and taking screenshots.
    """

    def __init__(self, screenshot_queue):
        threading.Thread.__init__(self)
        self.screenshot_queue = screenshot_queue

    def run(self):
        while True:
            creds, ip, path = self.screenshot_queue.get()
            self.get_screenshot(creds, ip, path)
            config.update_bar(__class__)
            self.screenshot_queue.task_done()

    def get_screenshot(self, creds, ip, path):
        try:
            video = av.open(
                f"rtsp://{creds}@{ip}{path}?tcp",
                options={"rtsp_transport": "tcp"},
                timeout=60.0,
            )
            video.streams.video[0].thread_type = "AUTO"
            frame = next(video.decode(video=0))
            img = frame.to_rgb().to_ndarray()
            Image.fromarray(img).save(f"pics/{ip}.jpg")
        except (av.ExitError, av.InvalidDataError):
            # Server isn't responding
            pass
        except ValueError:
            # Some bug in av.logging
            pass
        finally:
            video.close()
