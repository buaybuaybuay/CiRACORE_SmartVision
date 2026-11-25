import importlib.util
import os
import unittest


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_SPEC = importlib.util.spec_from_file_location(
    "cira_receiver_detection_audio",
    os.path.join(PROJECT_DIR, "cira_receiver.py"),
)
receiver = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(receiver)


class DetectionAudioTests(unittest.TestCase):
    def candidate_for(self, class_name):
        detection = {"im_w": 1000, "im_h": 1000}
        objects = [{
            "name": class_name,
            "x": 500,
            "y": 500,
            "w": 300,
            "h": 300,
            "confidence": 0.95,
        }]
        filter_reasons = []
        candidates = receiver.get_candidates(
            detection, objects, 100.0, filter_reasons
        )
        self.assertFalse(filter_reasons)
        self.assertEqual(len(candidates), 1)
        return candidates[0]

    def test_keyboard_and_tvmonitor_are_announced_in_thai(self):
        keyboard = self.candidate_for("keyboard")
        television = self.candidate_for("tvmonitor")

        self.assertIn("แป้นพิมพ์", keyboard["speech_text"])
        self.assertIn("จอโทรทัศน์", television["speech_text"])

    def test_unmapped_detected_class_is_not_silently_discarded(self):
        candidate = self.candidate_for("custom_object")

        self.assertIn("custom object", candidate["speech_text"])


if __name__ == "__main__":
    unittest.main()
