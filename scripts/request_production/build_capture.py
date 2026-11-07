"""Build isolated real-request observation classes on Linux; never runs an experiment.

The sole inherited source override is CooperationSupport.observeRequest's first
statement. CanonicalHmopso and every other inherited class remain resolved from
the mature-donor anchor. Use the emitted classpath in an independently authorized
source replay, with these required JVM properties:
  -Dresearch.request.capture=/new/output/folder
  -Dresearch.request.sourceBefore=255880 -Dresearch.request.sourceAfter=260880
For the 100-job source use 273560 and 278560. This script only compiles and invokes
the class-resource identity probe; it cannot launch that source replay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
from urllib.parse import unquote, urlparse


SUPPORT = 'org.uma.jmetal.util.research.cooperation.CooperationSupport'
BRIDGE = 'org.uma.jmetal.util.research.search.RequestCaptureBridge'
CAPTURE = 'org.uma.jmetal.util.research.cooperation.RequestCapture'
SOURCE_NAMES = ('RequestCapture.java', 'RequestCaptureBridge.java')
HOOK_ANCHOR = ('    private void observeRequest(PermutationSolution<Integer> parent, int family, '
               'int cycle, double cap, double eta, String outcome) {\n')
HOOK = ('        RequestCapture.observe(pools[family], parent, '
        '(DynamicSchedule) parent.getAttribute(DynamicEvaluation.KEY),\n'
        '                family, cycle, cap, eta, energyScale, wageScale, generation, outcome);\n')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def derive_support(original):
    text = original.read_text(encoding='utf-8')
    if text.count(HOOK_ANCHOR) != 1 or 'RequestCapture.' in text:
        raise ValueError('Expected exactly one uninstrumented observeRequest entry')
    following = text.split(HOOK_ANCHOR, 1)[1]
    if not following.startswith('        if (evidence == null) return;\n'):
        raise ValueError('observeRequest entry changed; refusing to guess a hook')
    return text.replace(HOOK_ANCHOR, HOOK_ANCHOR + HOOK, 1)


def dependency_identity(classpath):
    result = []
    for entry in classpath.split(':'):
        path = Path(entry)
        if not path.is_absolute() or not path.exists():
            raise ValueError('Missing or relative inherited classpath entry: ' + entry)
        files = sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else [path]
        records = [{'path': p.relative_to(path).as_posix() if path.is_dir() else p.name,
                    'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files]
        result.append({'path': str(path), 'kind': 'directory' if path.is_dir() else 'file',
                       'files': records})
    return result


def run_logged(command, log):
    process = subprocess.run(command, text=True, capture_output=True)
    with log.open('x', encoding='utf-8') as stream:
        stream.write(process.stdout + process.stderr)
    if process.returncode:
        raise RuntimeError('Preserved failed command output: ' + str(log))
    return process.stdout


def identity_probe(java, classpath, output, label, inherited=False):
    command = [str(java), '-cp', classpath, BRIDGE]
    if inherited:
        command.append('--inherited-only')
    write_json(output / (label + '-command.json'), command)
    value = json.loads(run_logged(command, output / (label + '.log')))
    write_json(output / (label + '.json'), value)
    return value


def verify_resolution(before, after, classes):
    for name, identity in before.items():
        if isinstance(identity, dict) and name != SUPPORT and after[name] != identity:
            raise ValueError('Unexpected inherited class override: ' + name)
    for name in (SUPPORT, CAPTURE, BRIDGE):
        resource = urlparse(after[name]['resource'])
        expected = (classes / (name.replace('.', '/') + '.class')).resolve()
        if resource.scheme != 'file' or Path(unquote(resource.path)).resolve() != expected:
            raise ValueError('Capture class resolved from unexpected resource: ' + name)


def build(anchor, source, cooperation_source, output, javac, java):
    if platform.system() != 'Linux':
        raise RuntimeError('This isolated build is Linux-only; no local scientific execution')
    anchor, source = anchor.resolve(), source.resolve()
    cooperation_source, output = cooperation_source.resolve(), output.resolve()
    javac = Path(shutil.which(str(javac)) or str(javac)).resolve()
    java = Path(shutil.which(str(java)) or str(java)).resolve() if java else javac.with_name('java')
    inherited_path = anchor / 'build-01/classpath.txt'
    inherited = inherited_path.read_text(encoding='utf-8').strip()
    if Path(inherited.split(':')[0]).resolve() != anchor / 'build-01/classes':
        raise ValueError('Expected mature-donor build-01/classes first in anchor classpath')
    derived_text = derive_support(cooperation_source)
    source_files = [source / name for name in SOURCE_NAMES]
    if any(not p.is_file() for p in source_files):
        raise FileNotFoundError('Both request capture source files are required')
    output.mkdir(parents=True, exist_ok=False)
    derived, classes = output / 'source', output / 'classes'
    derived.mkdir()
    classes.mkdir()
    (derived / 'CooperationSupport.java').write_text(derived_text, encoding='utf-8')
    for path in source_files:
        shutil.copyfile(path, derived / path.name)
    shutil.copyfile(Path(__file__).resolve(), output / 'build_capture.py')
    write_json(output / 'dependencies.json', dependency_identity(inherited))
    command = [str(javac), '-encoding', 'UTF-8', '--release', '8', '-implicit:none',
               '-sourcepath', str(derived), '-cp', inherited, '-d', str(classes),
               *map(str, sorted(derived.glob('*.java')))]
    write_json(output / 'build-command.json', command)
    run_logged(command, output / 'build.log')
    expected_classes = {name.replace('.', '/') + '.class' for name in (SUPPORT, CAPTURE, BRIDGE)}
    actual_classes = {p.relative_to(classes).as_posix() for p in classes.rglob('*.class')}
    if actual_classes != expected_classes:
        raise ValueError('Unexpected generated classes: ' + repr(actual_classes))
    classpath = str(classes) + ':' + inherited
    before = identity_probe(java, inherited + ':' + str(classes), output, 'inherited-loaded', True)
    after = identity_probe(java, classpath, output, 'capture-loaded')
    verify_resolution(before, after, classes)
    with (output / 'classpath.txt').open('x', encoding='utf-8') as stream:
        stream.write(classpath + '\n')
    write_json(output / 'identity.json', {
        'passed': True, 'buildOnly': True, 'experimentsStarted': 0,
        'sourceAnchor': str(cooperation_source), 'sourceAnchorSHA256': sha(cooperation_source),
        'sourceChange': 'Exactly one observeRequest entry hook before evidence-null return',
        'anchor': str(anchor), 'inheritedClasspath': inherited,
        'inheritedClasspathSHA256': sha(inherited_path),
        'dependencyIdentitySHA256': sha(output / 'dependencies.json'),
        'sources': {p.name: sha(p) for p in sorted(derived.glob('*.java'))},
        'classes': {p.relative_to(classes).as_posix(): sha(p) for p in sorted(classes.rglob('*.class'))},
        'buildScriptSHA256': sha(output / 'build_capture.py'),
        'inheritedLoadedSHA256': sha(output / 'inherited-loaded.json'),
        'captureLoadedSHA256': sha(output / 'capture-loaded.json'),
        'javacVersion': run_logged([str(javac), '-version'], output / 'javac-version.log').strip(),
        'javaVersion': after['javaVersion'], 'javaHome': after['javaHome'],
        'canonicalHmopsoOverridden': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('anchor', 'source', 'cooperation-source', 'output', 'javac'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--java', type=Path, help='Defaults to javac sibling; load-only identity probe')
    args = parser.parse_args()
    build(args.anchor, args.source, args.cooperation_source, args.output, args.javac, args.java)
