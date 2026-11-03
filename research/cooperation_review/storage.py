"""Small IO helpers that track source metadata and refuse output overwrite."""
import csv
import json
from pathlib import Path


class Sources:
    def __init__(self):
        self.files = {}

    def text(self, path):
        path = Path(path).resolve()
        stat = path.stat()
        self.files[str(path)] = (stat.st_size, stat.st_mtime_ns)
        return path.read_text(encoding="utf-8-sig")

    def json(self, path):
        return json.loads(self.text(path))

    def lines(self, path):
        return [json.loads(line) for line in self.text(path).splitlines() if line]

    def unchanged(self):
        for path, signature in self.files.items():
            stat = Path(path).stat()
            if signature != (stat.st_size, stat.st_mtime_ns):
                raise ValueError("Source metadata changed: " + path)
        return [{"source": path, "bytes": size, "mtimeNs": mtime}
                for path, (size, mtime) in sorted(self.files.items())]


def json_write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def csv_write(path, rows):
    if not rows:
        raise ValueError("Refusing empty table: " + str(path))
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def means_by(rows, keys, fields):
    from statistics import mean
    groups = {}
    for row in rows:
        groups.setdefault(tuple(row[key] for key in keys), []).append(row)
    return [dict(zip(keys, key)) | {"runs": len(group)} |
            {field: mean(row[field] for row in group if row[field] is not None)
             if any(row[field] is not None for row in group) else None for field in fields}
            for key, group in sorted(groups.items())]
