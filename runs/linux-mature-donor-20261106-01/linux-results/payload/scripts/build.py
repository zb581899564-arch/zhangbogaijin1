"""Compile only isolated capture/probe classes against the accepted Linux anchor."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def build(anchor, source, output, javac):
    assert platform.system() == 'Linux'
    output.mkdir(parents=True, exist_ok=False)
    derived = output / 'source'
    classes = output / 'classes'
    derived.mkdir(); classes.mkdir()
    original = anchor / 'build-01/source/CanonicalHmopso.java'
    text = original.read_text()
    text = once(text, '            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);',
                '            DonorCapture.pre(groups);\n            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);')
    text = once(text, '            List<Particle> globallyUpdated = flatten(updated);',
                '            List<Particle> globallyUpdated = flatten(updated);\n            DonorCapture.post();')
    text = once(text, '            state.evaluate(child, "global", direction);',
                '            state.evaluate(child, "global", direction);\n            DonorCapture.paid(child, composed, direction);')
    (derived / original.name).write_text(text)
    for path in source.glob('*.java'):
        (derived / path.name).write_bytes(path.read_bytes())
    base = (anchor / 'build-01/classpath.txt').read_text().strip()
    command = [str(javac), '-encoding', 'UTF-8', '--release', '8', '-cp', base,
               '-d', str(classes), *map(str, sorted(derived.glob('*.java')))]
    write(output / 'build-command.json', command)
    result = subprocess.run(command, capture_output=True, text=True)
    (output / 'build.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Preserved failed build: ' + str(output / 'build.log'))
    (output / 'classpath.txt').write_text(str(classes) + ':' + base)
    write(output / 'identity.json', {'sourceAnchor': str(original), 'sourceAnchorSHA256': sha(original),
          'sources': {p.name: sha(p) for p in derived.glob('*.java')},
          'classes': {p.relative_to(classes).as_posix(): sha(p) for p in classes.rglob('*.class')},
          'javaVersion': subprocess.check_output([str(javac), '-version'], text=True).strip()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('anchor', 'source', 'output', 'javac'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    build(args.anchor, args.source, args.output, args.javac)
