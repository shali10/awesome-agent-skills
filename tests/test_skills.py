import os
import re
import unittest
import yaml

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT_DIR, "skills")

SENSITIVE_PATTERNS = [
    r"sk-[a-zA-Z0-9_-]{20,}",
    r"ghp_[a-zA-Z0-9_-]{20,}",
    r"cfk_[a-zA-Z0-9_-]{20,}",
    r"-----BEGIN (OPENSSH|RSA) PRIVATE KEY-----",
    r"id_ed25519_[a-zA-Z0-9_]+",
]

def get_all_skills():
    skills = []
    if not os.path.exists(SKILLS_DIR):
        return skills
    for sdir in sorted(os.listdir(SKILLS_DIR)):
        sp = os.path.join(SKILLS_DIR, sdir)
        if os.path.isdir(sp):
            skill_file = os.path.join(sp, "SKILL.md")
            if os.path.exists(skill_file):
                skills.append((sdir, skill_file))
    return skills

class TestAwesomeAgentSkills(unittest.TestCase):

    def test_all_skills_exist(self):
        skills = get_all_skills()
        self.assertGreaterEqual(len(skills), 10, "Expected at least 10 skills")

    def test_skills_frontmatter_and_structure(self):
        skills = get_all_skills()
        for skill_name, skill_path in skills:
            with self.subTest(skill=skill_name):
                with open(skill_path, "r", encoding="utf-8") as f:
                    content = f.read()

                self.assertTrue(content.startswith("---"), f"{skill_name}: SKILL.md must start with '---'")
                parts = content.split("---", 2)
                self.assertGreaterEqual(len(parts), 3, f"{skill_name}: SKILL.md must have closing '---'")

                fm = yaml.safe_load(parts[1])
                self.assertIsInstance(fm, dict, f"{skill_name}: Frontmatter must be a YAML dict")
                self.assertIn("name", fm, f"{skill_name}: 'name' is required")
                self.assertLessEqual(len(fm["name"]), 64, f"{skill_name}: 'name' must be <= 64 chars")

                self.assertIn("description", fm, f"{skill_name}: 'description' is required")
                self.assertLessEqual(len(fm["description"]), 1024, f"{skill_name}: 'description' <= 1024 chars")
                self.assertIn("version", fm)
                self.assertIn("author", fm)
                self.assertIn("license", fm)
                self.assertIn("platforms", fm)

                body = parts[2]
                self.assertIn("## Overview", body, f"{skill_name}: Missing '## Overview'")
                self.assertIn("## When to Use", body, f"{skill_name}: Missing '## When to Use'")
                self.assertIn("## Common Pitfalls", body, f"{skill_name}: Missing '## Common Pitfalls'")
                self.assertIn("## Verification Checklist", body, f"{skill_name}: Missing '## Verification Checklist'")

    def test_zero_sensitive_data_leaks(self):
        hits = []
        for root, _, files in os.walk(ROOT_DIR):
            if ".git" in root:
                continue
            for file in files:
                fpath = os.path.join(root, file)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        for pat in SENSITIVE_PATTERNS:
                            matches = re.findall(pat, text)
                            if matches:
                                hits.append((fpath, pat, matches))
                except Exception:
                    pass
        self.assertEqual(len(hits), 0, f"Found sensitive data leaks: {hits}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
