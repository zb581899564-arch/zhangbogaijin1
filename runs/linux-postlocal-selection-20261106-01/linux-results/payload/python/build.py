"""Compile new isolated classes only, against immutable donor/anchor classpath."""
import argparse
from pathlib import Path
import platform
import subprocess
from prepare import sha, write


def build(source, anchor, output, javac):
    assert platform.system() == 'Linux'
    output.mkdir(parents=True, exist_ok=False)
    classes = output / 'classes'; classes.mkdir()
    files = sorted(source.glob('*.java'))
    assert files, source
    inherited = (anchor / 'build-01/classpath.txt').read_text().strip()
    command = [str(javac), '-encoding', 'UTF-8', '--release', '8', '-cp', inherited,
               '-d', str(classes), *map(str, files)]
    write(output / 'command.json', command)
    process = subprocess.run(command, text=True, capture_output=True)
    (output / 'build.log').write_text(process.stdout + process.stderr)
    assert process.returncode == 0, 'Preserved failed build: ' + str(output)
    (output / 'classpath.txt').write_text(str(classes) + ':' + inherited)
    write(output / 'identity.json', dict(sources={str(p): sha(p) for p in files},
          classes={str(p.relative_to(classes)): sha(p) for p in classes.rglob('*.class')},
          inheritedClasspath=inherited, anchor=str(anchor),
          inheritedReceiptSHA256=sha(anchor / 'delivery-acceptance.json'),
          javac=subprocess.check_output([str(javac), '-version'], text=True).strip()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'anchor', 'output', 'javac'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args(); build(args.source, args.anchor, args.output, args.javac)
