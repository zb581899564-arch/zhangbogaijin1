"""Derive three isolated overrides from the exact frozen capability sources."""
from pathlib import Path
import hashlib
import json
import shutil


OVERRIDES = {
    'CanonicalHmopso': 'anchor/overrides/CanonicalHmopso.java',
    'SearchState': 'anchor/extra/SearchState.java',
    'GomLocalProgram': 'anchor/source/GomLocalProgram.java',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Frozen patch anchor must occur once: ' + old[:100])
    return text.replace(old, new, 1)


def region(text, start, end, transform):
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Frozen region boundaries must occur once')
    first, last = text.index(start), text.index(end)
    if last <= first:
        raise ValueError('Frozen region boundaries reversed')
    return once(text, text[first:last], transform(text[first:last]))


def indent(text):
    return ''.join('    ' + line if line.strip() else line
                   for line in text.splitlines(keepends=True))


def global_gate(body):
    return ('            if (PilotTrace.globalEnabled()) {\n'
            '                PilotTrace.phase("GLOBAL");\n' + indent(body) +
            '            } else {\n'
            '                updated.putAll(groups);\n'
            '            }\n')


def local_gate(body):
    declaration = '            List<Particle> offspring = new ArrayList<>();\n'
    body = once(body, declaration, '')
    return (declaration + '            if (PilotTrace.localEnabled()) {\n'
            '                PilotTrace.phase("LOCAL");\n' + indent(body) +
            '            }\n')


def patch_canonical(text):
    text = region(text,
                  '            for (Direction direction : globalUpdateOrder()) {\n',
                  '            List<Particle> globallyUpdated = flatten(updated);',
                  global_gate)
    text = region(text,
                  '            if (GomRunScope.enabled()) GomRunScope.begin(reference, gomInstance);\n',
                  '            // JMS Algorithm 1 explicitly uses parents union final local-search offspring.',
                  local_gate)
    patches = [
        ('        if (audit != null) audit.feedbackInitialized();',
         '        if (audit != null) audit.feedbackInitialized();\n'
         '        PilotTrace.population("INITIAL", population);'),
        ('            if (audit != null) audit.feedbackBegin();',
         '            PilotTrace.phase("LIFECYCLE");\n'
         '            if (audit != null) audit.feedbackBegin();'),
        ('            renewContexts(population);',
         '            renewContexts(population);\n'
         '            PilotTrace.population("PRE_GLOBAL", population);'),
        ('            List<Particle> globallyUpdated = flatten(updated);',
         '            List<Particle> globallyUpdated = flatten(updated);\n'
         '            PilotTrace.population("POST_GLOBAL", globallyUpdated);\n'
         '            PilotTrace.phase("LIFECYCLE");'),
        ('            if (chapter == 3) offspring.addAll(population);',
         '            PilotTrace.population("POST_LOCAL", offspring);\n'
         '            PilotTrace.phase("LIFECYCLE");\n'
         '            if (chapter == 3) offspring.addAll(population);'),
        ('                population = selected.survivors();',
         '                PilotTrace.selection(candidates, selected);\n'
         '                population = selected.survivors();'),
        ('            if (audit != null) audit.feedbackEnd();',
         '            PilotTrace.population("SURVIVORS", population);\n'
         '            if (audit != null) audit.feedbackEnd();'),
        ('            state.evaluate(child, "global", direction);',
         '            PilotTrace.composed(composed);\n'
         '            state.evaluate(child, "global", direction);'),
    ]
    for old, new in patches:
        text = once(text, old, new)
    return text


def patch_search_state(text):
    return once(text,
                '        if (observationGroup != null) direction = observationGroup;',
                '        if (observationGroup != null) direction = observationGroup;\n'
                '        PilotTrace.context(stage, direction);')


def patch_local(text):
    return once(text,
                '            if (keep) w.values.set(slot, state);',
                '            if (keep) w.values.set(slot, state);\n'
                '            PilotTrace.acceptedLocal(keep, child);')


def prepare_sources(payload, destination):
    """Copy only explicit overrides and supplied pilot modules; preserve all bases."""
    manifest = json.loads((payload / 'transfer-manifest.json').read_text('utf-8-sig'))
    extra = json.loads((payload / 'anchor/extra/source-identity.json').read_text('utf-8-sig'))
    transforms = {'CanonicalHmopso': patch_canonical,
                  'SearchState': patch_search_state, 'GomLocalProgram': patch_local}
    identities = []
    for name, relative in OVERRIDES.items():
        original = payload / relative
        expected = extra['sourceSHA256'] if name == 'SearchState' else manifest[relative]['sha256']
        if sha(original) != expected:
            raise ValueError('Frozen source identity mismatch: ' + relative)
        output = destination / (name + '.java')
        output.write_text(transforms[name](original.read_text('utf-8-sig')), encoding='utf-8')
        identities.append({'name': name, 'original': relative,
                           'originalSHA256': expected, 'output': output.name,
                           'outputSHA256': sha(output), 'kind': 'isolated_override'})
    additions = sorted((payload / 'new-java').rglob('*.java'))
    if not additions:
        raise ValueError('No supplied Java pilot modules under payload/new-java')
    for original in additions:
        relative = original.relative_to(payload / 'new-java')
        if original.stem in OVERRIDES:
            raise ValueError('Pilot module shadows a controlled override: ' + str(relative))
        output = destination / 'new' / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, output)
        identities.append({'name': original.stem, 'original': original.relative_to(payload).as_posix(),
                           'originalSHA256': sha(original),
                           'output': output.relative_to(destination).as_posix(),
                           'outputSHA256': sha(output), 'kind': 'supplied_pilot'})
    return identities, extra
