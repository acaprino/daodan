"""Which files the Codebase Map never reads.

The obvious credential files are recognized by name. Any other name that speaks of secrets
is read unless its content holds a generated value, in every language and format.
"""

import base64
from pathlib import Path
import random
import shutil
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import snapshot  # noqa: E402

# Generated at run time, so this file holds no generated value of its own.
_RANDOM = random.Random(2026)
KEY_BODY = base64.b64encode(_RANDOM.randbytes(48)).decode()
HEX_KEY = _RANDOM.randbytes(32).hex()
TOKEN = base64.urlsafe_b64encode(_RANDOM.randbytes(30)).decode()


class SecretFilesTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_obvious_credential_files_are_never_read(self):
        for name in (".env", ".env.local", "secrets.yaml", "credentials.json", "credentials.py",
                     "server.pem", "tls.key", "id_rsa", ".npmrc", "main.tfstate", "app.jks"):
            with self.subTest(name=name):
                self.assertTrue(snapshot.is_forbidden(name, self.write(name, "harmless\n")))

    def test_other_secret_names_are_read_in_every_language_and_format(self):
        sources = {
            "secretCipher.js": "export function encrypt(text) { return text; }\n",
            "secret_manager.py": "def rotate(key):\n    return key\n",
            "SecretService.java": "class SecretService { String name() { return \"vault\"; } }\n",
            "SecretStore.kt": "class SecretStore { fun size() = 0 }\n",
            "secret_store.go": "package vault\nfunc Size() int { return 0 }\n",
            "SecretVault.cs": "class SecretVault { int Size() => 0; }\n",
            "secret-form.vue": "<template><form></form></template>\n",
            "secret.example.yaml": "stringData:\n  SESSION_SECRET: change-me\n",
            "client_secret.txt": "Ask the administrator.\n",
            "secrets-management.md": "# Secrets\n\nSee https://docs.python.org/3/library/secrets.html#module-secrets\n",
        }
        for name, text in sources.items():
            with self.subTest(name=name):
                self.assertFalse(snapshot.is_forbidden(name, self.write(name, text)))

    def test_other_secret_names_holding_a_generated_value_are_not_read(self):
        sources = {
            "secretCipher.js": f"const key = `-----BEGIN PRIVATE KEY-----\n{KEY_BODY}\n-----END PRIVATE KEY-----`;\n",
            "secret_store.go": f'const id = "{HEX_KEY}"\n',
            "client_secret.txt": f"{TOKEN}\n",
            "secrets-management.md": f"Use `{TOKEN}` in production.\n",
        }
        for name, text in sources.items():
            with self.subTest(name=name):
                self.assertTrue(snapshot.is_forbidden(name, self.write(name, text)))

    def test_written_values_and_placeholders_do_not_hide_a_file(self):
        sources = {
            "secret.test.js": "login({ password: 'password123' });\n",
            "secret_config.ts": 'const apiKey = process.env.API_KEY ?? "YOUR_API_KEY_HERE_0000";\n'
                                'const url = "postgres://user:pass@localhost:5432/app";\n',
            "SecretService.java": "String token = generateSecretTokenForTheSession();\n",
        }
        for name, text in sources.items():
            with self.subTest(name=name):
                self.assertFalse(snapshot.is_forbidden(name, self.write(name, text)))

    def test_without_a_path_only_obvious_names_are_forbidden(self):
        self.assertFalse(snapshot.is_forbidden("secretCipher.js"))
        self.assertTrue(snapshot.is_forbidden(".env"))
        self.assertTrue(snapshot.is_forbidden("secrets.yaml"))

    def test_the_walk_keeps_secret_named_code_and_leaves_out_credentials(self):
        self.write("app.js", "export const app = 1;\n")
        self.write("secretCipher.js", "export function encrypt(text) { return text; }\n")
        self.write("secret_keys.py", f'ACCESS_KEY = "{TOKEN}"\n')
        self.write("secrets.yaml", "password: hunter2\n")
        self.write(".env", "TOKEN=1\n")
        names = sorted(path.name for path in snapshot.iter_files(self.root))
        self.assertEqual(names, ["app.js", "secretCipher.js"])


if __name__ == "__main__":
    unittest.main()
