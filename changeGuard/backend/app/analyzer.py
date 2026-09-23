import re
from typing import Dict, List, Any

class GitDiffAnalyzer:
    def __init__(self, diff_text: str):
        self.diff_text = diff_text

    def parse(self) -> Dict[str, Any]:
        files_changed = []
        lines_added = 0
        lines_deleted = 0

        current_file = None
        for line in self.diff_text.splitlines():
            if line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    current_file = parts[3].replace("b/", "")
                    files_changed.append(current_file)
            elif line.startswith("+") and not line.startswith("+++"):
                lines_added += 1
            elif line.startswith("-") and not line.startswith("---"):
                lines_deleted += 1

        rule_flags = self._evaluate_rules(files_changed, self.diff_text)

        return {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "rule_flags": rule_flags
        }

    def _evaluate_rules(self, files: List[str], diff: str) -> List[str]:
        flags = []
        for f in files:
            if any(f.endswith(ext) for ext in [".sql", ".migration.py", "/migrations/"]):
                flags.append("DATABASE_MIGRATION_DETECTED")
            if "payment" in f.lower() or "billing" in f.lower():
                flags.append("CRITICAL_PAYMENT_LOGIC_MODIFIED")
            if "auth" in f.lower() or "security" in f.lower():
                flags.append("SECURITY_AUTH_MODIFIED")
            if f.endswith(".yaml") or f.endswith(".yml"):
                flags.append("INFRASTRUCTURE_OR_CI_MODIFIED")

        if re.search(r"(DROP\s+TABLE|ALTER\s+TABLE|CASCADE)", diff, re.IGNORECASE):
            flags.append("DESTRUCTIVE_SQL_KEYWORDS")

        return list(set(flags))