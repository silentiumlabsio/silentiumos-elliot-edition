import json
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))

from audit_public_release import audit_repository, build_manifest_entries  # noqa: E402


class PublicReleaseAuditTests(unittest.TestCase):
    def make_repository(self, directory: str) -> Path:
        root = Path(directory)
        (root / "README.md").write_text("Public source tree\n", encoding="utf-8")
        self.write_manifest(root)
        return root

    def write_manifest(self, root: Path) -> None:
        manifest = {
            "project": "SilentiumOS Elliot Edition",
            "version": "test",
            "files": build_manifest_entries(root),
        }
        (root / "PUBLIC_IMPORT_MANIFEST.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def rules(self, root: Path) -> set[str]:
        return {issue.rule for issue in audit_repository(root)}

    def test_accepts_a_minimal_safe_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.assertEqual([], audit_repository(root))

    def test_rejects_a_packaged_application(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            (root / "release.apk").write_bytes(b"not an application")
            self.write_manifest(root)
            self.assertIn("blocked-extension", self.rules(root))

    def test_detects_private_network_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            private_address = ".".join(("192", "168", "7", "42"))
            (root / "notes.txt").write_text(private_address, encoding="utf-8")
            self.write_manifest(root)
            self.assertIn("private-ipv4", self.rules(root))

    def test_detects_credential_shapes_without_fixture_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            shaped_value = "gh" + "p_" + ("a" * 24)
            (root / "config.txt").write_text(shaped_value, encoding="utf-8")
            self.write_manifest(root)
            self.assertIn("github-token", self.rules(root))

    def test_detects_manifest_size_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            (root / "README.md").write_text(
                "Public source tree changed\n", encoding="utf-8"
            )
            self.assertIn("manifest-size-mismatch", self.rules(root))


if __name__ == "__main__":
    unittest.main()
