"""Regression coverage for the isolated Academy environment adapter."""

import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase


class AcademySettingsTests(TestCase):
    def read_setting(self, expression, values):
        command = f"from core import academy_settings as s; print({expression})"
        result = subprocess.run(
            [sys.executable, "-c", command],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, **values}, capture_output=True, text=True,
            check=True,
        )
        return result.stdout.strip()

    def test_official_cache_variable_takes_precedence(self):
        result = self.read_setting("s.CACHES['default']['LOCATION']", {
            "REDIS_LOCATION": "redis://academy-cache:6380/4",
            "CACHE_URL": "redis://legacy-cache:6379/1",
        })
        self.assertEqual(result, "redis://academy-cache:6380/4")

    def test_official_csrf_variable_takes_precedence(self):
        result = self.read_setting("','.join(s.CSRF_TRUSTED_ORIGINS)", {
            "CSRF_TRUSTED_ORIGINS": "http://localhost:5500,http://localhost:4200",
            "FRONTEND_ORIGINS": "http://127.0.0.1:5500",
        })
        self.assertEqual(result, "http://localhost:5500,http://localhost:4200")

    def test_static_volume_path_and_ssl_setting(self):
        result = self.read_setting(
            "str(s.STATIC_ROOT.name) + ':' + str(s.EMAIL_USE_SSL)",
            {"EMAIL_USE_SSL": "True", "EMAIL_USE_TLS": "False"},
        )
        self.assertEqual(result, "static:True")
