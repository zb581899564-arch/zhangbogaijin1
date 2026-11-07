"""Small UTF-8 result I/O helpers."""
import csv
import json

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")


def csv_write(path,rows):
    with path.open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


