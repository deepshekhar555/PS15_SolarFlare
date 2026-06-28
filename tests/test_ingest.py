import unittest
from fastapi.testclient import TestClient
from data_ingest.main import app, _goes_xray_to_cps, _kp_to_geostorm, _safe_float

class TestIngestService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_safe_float(self):
        self.assertEqual(_safe_float("1.23"), 1.23)
        self.assertEqual(_safe_float("abc", 5.0), 5.0)
        self.assertEqual(_safe_float(None, 0.0), 0.0)
        self.assertEqual(_safe_float("nan", 1.0), 1.0)

    def test_kp_to_geostorm(self):
        self.assertEqual(_kp_to_geostorm(1.0), "G0 Quiet")
        self.assertEqual(_kp_to_geostorm(5.0), "G1 Minor")
        self.assertEqual(_kp_to_geostorm(9.0), "G5 Extreme")

    def test_goes_xray_to_cps(self):
        # B-class peak (~1e-6 W/m^2)
        cps_solexs = _goes_xray_to_cps(1e-6, "solexs")
        self.assertGreater(cps_solexs, 0)
        
        # X-class peak (~1e-4 W/m^2)
        cps_hel1os = _goes_xray_to_cps(1e-4, "hel1os")
        self.assertGreater(cps_hel1os, 0)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("data_source", data)

    def test_telemetry_endpoint(self):
        response = self.client.get("/telemetry")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("solexs", data)
        self.assertIn("hel1os", data)
        self.assertIn("windSpd", data)
        self.assertIn("bz", data)
        self.assertIn("flareLon", data)
        self.assertIn("latestCME", data)

if __name__ == "__main__":
    unittest.main()
