"""Build new probe classes against the unchanged accepted Linux anchor."""
import argparse
from pathlib import Path
import subprocess
from common import SOURCE, JAVA, JAVAC, linux, sha, write


def build(root, source, name='probe-build-01'):
    linux()
    out=root/name;out.mkdir(exist_ok=False)
    classes=out/'classes';classes.mkdir()
    files=sorted(p for p in source.glob('*.java') if p.name not in ('RequestCapture.java','RequestCaptureBridge.java'))
    assert len(files)==6, [p.name for p in files]
    inherited=(SOURCE/'build-01/classpath.txt').read_text().strip()
    command=[str(JAVAC),'-encoding','UTF-8','--release','8','-implicit:none','-cp',inherited,
             '-d',str(classes),*map(str,files)]
    write(out/'command.json',command)
    result=subprocess.run(command,text=True,capture_output=True)
    (out/'build.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0, str(out/'build.log')
    (out/'classpath.txt').write_text(str(classes)+':'+inherited)
    write(out/'identity.json',dict(sources={p.name:sha(p) for p in files},
        classes={str(p.relative_to(classes)):sha(p) for p in classes.rglob('*.class')},
        inheritedClasspath=inherited,sourceAcceptanceSHA256=sha(SOURCE/'delivery-acceptance.json'),
        java=subprocess.check_output([str(JAVA),'-version'],stderr=subprocess.STDOUT,text=True)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--name',default='probe-build-01')
    args=parser.parse_args();build(args.root,args.source,args.name)
