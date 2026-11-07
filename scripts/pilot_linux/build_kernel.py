"""Linux-only Java 17 build of phase gates and passive pilot observation hooks."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile

from build_sources import prepare_sources


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def providers(payload):
    records = json.loads((payload / 'classpath-providers.json').read_text('utf-8-sig'))
    if not records or [row['position'] for row in records] != list(range(len(records))):
        raise ValueError('Classpath provider order is not contiguous')
    paths = []
    for row in records:
        relative = Path(row['relative'])
        path = (payload / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(payload) or not path.exists():
            raise ValueError('Missing or unsafe classpath provider: ' + str(relative))
        paths.append(path)
    return paths


def class_identity(paths, name, payload):
    resource = name.replace('.', '/') + '.class'
    for entry in paths:
        if entry.is_dir():
            path = entry / resource
            if not path.is_file():
                continue
            data = path.read_bytes()
        elif entry.suffix.lower() in ('.jar', '.zip'):
            with zipfile.ZipFile(entry) as archive:
                try:
                    data = archive.read(resource)
                except KeyError:
                    continue
        else:
            continue
        return {'name': name, 'provider': entry.relative_to(payload).as_posix(),
                'resource': resource, 'sha256': hashlib.sha256(data).hexdigest()}
    raise ValueError('Frozen class missing: ' + name)


def run_logged(command, path):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding='utf-8', errors='replace', check=False)
    path.write_text(result.stdout, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Command failed; see ' + str(path))
    return result.stdout


def build(payload, output, javac):
    if sys.platform != 'linux':
        raise RuntimeError('This build is authorized for the Linux host only')
    payload, output = payload.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError('Build output already exists: ' + str(output))
    paths = providers(payload)
    output.mkdir(parents=True)
    source, classes = output / 'source', output / 'classes'
    source.mkdir()
    classes.mkdir()
    identities, extra = prepare_sources(payload, source)
    critical = [class_identity(paths, 'org.uma.jmetal.util.research.search.' + name, payload)
                for name in ('CanonicalHmopso', 'SearchState', 'GomLocalProgram')]
    search_state = next(item for item in critical if item['name'].endswith('.SearchState'))
    if search_state['sha256'] != extra['classSHA256'] or search_state['provider'] != extra['provider']:
        raise ValueError('SearchState class differs from its frozen source/provider identity')
    write_json(output / 'source-identities.json', {
        'sources': identities, 'frozenProviders': critical,
        'extraSourceIdentity': extra,
        'observerMode': 'Runtime OBS_OFF affects PilotTrace observations only; phase gates remain active',
    })
    version = run_logged([javac, '-version'], output / 'javac-version.log')
    if not re.search(r'\bjavac\s+17(?:\.|\s|$)', version):
        raise RuntimeError('Expected Java 17 javac, received: ' + version.strip())
    base = os.pathsep.join(str(path) for path in paths)
    command = [javac, '-encoding', 'UTF-8', '--release', '8', '-cp', base,
               '-d', str(classes), *[str(path) for path in sorted(source.rglob('*.java'))]]
    write_json(output / 'compile-command.json', command)
    run_logged(command, output / 'compile.log')
    for item in critical:
        if not (classes / item['resource']).is_file():
            raise RuntimeError('Override missing after compile: ' + item['name'])
    (output / 'base-classpath.txt').write_text(base + '\n', encoding='utf-8')
    (output / 'classpath.txt').write_text(str(classes) + os.pathsep + base + '\n', encoding='utf-8')
    write_json(output / 'class-identities.json', {
        path.relative_to(classes).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(classes.rglob('*.class'))
    })
    return {'output': str(output), 'classpath': str(output / 'classpath.txt'),
            'sources': len(identities), 'compiled': True, 'searchExecuted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--javac', default='javac')
    args = parser.parse_args()
    print(json.dumps(build(args.payload, args.output or args.payload / 'build', args.javac),
                     ensure_ascii=False))
