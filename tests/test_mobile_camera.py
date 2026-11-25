import importlib.util
import json
import os
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_SPEC = importlib.util.spec_from_file_location(
    "cira_receiver_mobile_camera",
    os.path.join(PROJECT_DIR, "cira_receiver.py"),
)
receiver = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(receiver)


class MobileCameraEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), receiver.Receiver)
        cls.server_thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2)

    def setUp(self):
        receiver.stop_mobile_camera_stream()

    def post(self, path, body=b"", headers=None):
        request_headers = {"X-CIRA-Token": receiver.MOBILE_ACCESS_TOKEN}
        request_headers.update(headers or {})
        request = urllib.request.Request(
            self.base_url + path + "?token=" + receiver.MOBILE_ACCESS_TOKEN,
            data=body,
            headers=request_headers,
            method="POST",
        )
        return urllib.request.urlopen(request)

    def test_mobile_camera_requires_an_active_stream_and_valid_jpeg(self):
        jpeg = b"\xff\xd8test-frame\xff\xd9"
        self.assertFalse(receiver.store_mobile_camera_frame(jpeg, 640, 480))

        receiver.start_mobile_camera_stream()
        self.assertFalse(receiver.store_mobile_camera_frame(b"not-jpeg", 640, 480))
        self.assertTrue(receiver.store_mobile_camera_frame(jpeg, 640, 480))

        frame, _sequence, dimensions = receiver.get_mobile_camera_frame()
        self.assertEqual(frame, jpeg)
        self.assertEqual(dimensions, (640, 480))

    def test_mobile_camera_stream_expires_after_frames_stop(self):
        receiver.start_mobile_camera_stream()
        receiver.store_mobile_camera_frame(b"\xff\xd8test-frame\xff\xd9", 640, 480)
        with receiver.mobile_camera_lock:
            receiver.mobile_camera_last_frame = time.monotonic() - 10.1

        status = receiver.mobile_camera_status()
        self.assertFalse(status["camera_active"])
        self.assertIsNone(receiver.mobile_camera_frame)

    def test_authenticated_camera_endpoint_starts_receives_and_stops(self):
        origin = self.base_url
        start = self.post(
            "/api/camera/start",
            headers={"Origin": origin},
        )
        self.assertTrue(json.loads(start.read())["camera_active"])

        jpeg = b"\xff\xd8test-frame\xff\xd9"
        upload = self.post(
            "/api/camera/frame",
            jpeg,
            {
                "Origin": origin,
                "Content-Type": "image/jpeg",
                "X-CIRA-Width": "640",
                "X-CIRA-Height": "480",
            },
        )
        self.assertTrue(json.loads(upload.read())["ok"])

        frame_response = urllib.request.urlopen(
            self.base_url
            + "/api/camera/latest?token="
            + receiver.MOBILE_ACCESS_TOKEN
        )
        self.assertEqual(frame_response.read(), jpeg)

        stopped = self.post(
            "/api/camera/stop",
            headers={"Origin": origin},
        )
        self.assertFalse(json.loads(stopped.read())["camera_active"])
        latest = urllib.request.urlopen(
            self.base_url
            + "/api/camera/latest?token="
            + receiver.MOBILE_ACCESS_TOKEN
        )
        self.assertEqual(latest.status, 204)

    def test_camera_endpoint_rejects_missing_token_and_cross_origin(self):
        with self.assertRaises(urllib.error.HTTPError) as unauthorized:
            urllib.request.urlopen(self.base_url + "/api/status")
        self.assertEqual(unauthorized.exception.code, 403)

        with self.assertRaises(urllib.error.HTTPError) as cross_origin:
            self.post("/api/camera/start", headers={"Origin": "http://other"})
        self.assertEqual(cross_origin.exception.code, 403)

    def test_obs_camera_policy_allows_blob_frame_urls(self):
        response = urllib.request.urlopen(self.base_url + "/obs-camera")
        policy = response.headers["Content-Security-Policy"]
        self.assertIn("img-src 'self' blob: data:", policy)


if __name__ == "__main__":
    unittest.main()
