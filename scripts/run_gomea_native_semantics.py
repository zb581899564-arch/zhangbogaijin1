"""Compile isolated, unchanged author predicate/model functions; no original optimizer or scheduling FE."""
import csv
from datetime import datetime
import hashlib
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from research.semantic_repair.evidence import digest
from gomea_native_fixtures import predicate_input, predicate_cases, expected_predicates, dependency_input, expected_dependency

SOURCE = ROOT / 'research/gomea_reference_audit/author-sources-20261105-144447-843551'
MO = SOURCE / 'MO-GOMEA/MO_GOMEA/MO_GOMEA.c'
PERMUTATION = SOURCE / 'PermutationGOMEA/PermutationGOMEA.c'


def extract(path, names):
    text = path.read_text('utf-8');result = {};anchors = {}
    for name in names:
        match = re.search(r'(?m)^(?:char|short|double|void|int)\s+\*?\s*' + re.escape(name) + r'\s*\([^;]*?\)\s*\{', text)
        if match is None: raise ValueError(f'Missing source definition: {name}')
        opening = text.index('{', match.start());depth = 1;end = opening + 1
        while depth:
            if text[end] == '{': depth += 1
            elif text[end] == '}': depth -= 1
            end += 1
        body = text[match.start():end];result[name] = body
        anchors[name] = {'path': str(path.relative_to(ROOT)), 'startLine': text.count('\n', 0, match.start()) + 1,
            'endLine': text.count('\n', 0, end) + 1, 'normalizedFunctionSHA256': hashlib.sha256(body.encode()).hexdigest()}
    return result, anchors


def run(root, command, log):
    write_once(root / (log + '.command.json'), command)
    with (root / log).open('x', encoding='utf-8') as output:
        completed = subprocess.run(command, cwd=root, stdout=output, stderr=subprocess.STDOUT, timeout=60)
    if completed.returncode: raise RuntimeError(f'Native audit command failed: {log}')


def native_sources(root):
    names = ('betterFitness', 'equalFitness', 'constraintParetoDominates', 'constraintWeaklyParetoDominates', 'paretoDominates', 'weaklyParetoDominates')
    functions, mo_anchors = extract(MO, names)
    macros = '\n'.join(re.findall(r'(?m)^#define (?:FALSE|TRUE|MINIMIZATION|MAXIMIZATION)\s+\d+.*$', MO.read_text('utf-8')))
    declarations = '\n'.join(body[:body.index('{')].strip() + ';' for body in functions.values())
    header = '/* Author-derived functions for private local semantic audit. See source manifest and original notice. */\n#include <stdio.h>\n#include <math.h>\n'
    prefix = header + macros + '\nint number_of_objectives; int *optimization;\n' + declarations + '\n'
    main = r'''
int main(int argc, char **argv) {
    FILE *input=fopen(argv[1],"r");long id;int mask,d,directions[3];double cx,cy,x[3],y[3];
    if(!input)return 2;number_of_objectives=3;optimization=directions;
    while(fscanf(input,"%ld%d%lf%lf%lf%lf%lf%lf%lf%lf",&id,&mask,&cx,&cy,&x[0],&x[1],&x[2],&y[0],&y[1],&y[2])==10) {
        for(d=0;d<3;d++)directions[d]=(mask&(1<<d))?MINIMIZATION:MAXIMIZATION;
        printf("%ld,%d,%d",id,constraintParetoDominates(x,cx,y,cy),constraintWeaklyParetoDominates(x,cx,y,cy));
        for(d=0;d<3;d++)printf(",%d,%d",betterFitness(x,cx,y,cy,d),equalFitness(x,cx,y,cy,d));
        printf("\n");
    }
    fclose(input);return 0;
}
'''
    (root / 'native-predicates.c').write_text(prefix + '\n'.join(functions.values()) + main, encoding='utf-8')
    functions, permutation_anchors = extract(PERMUTATION, ('log2', 'computeDependencyMatrixSpecificGOMEA'))
    globals_text = '\n#include <stdlib.h>\nint number_of_parameters;int *population_sizes;double ***populations,***dependency_matrices;double math_log_two;\n'
    dependency_main = r'''
int main(int argc,char **argv) {
    FILE *input=fopen(argv[1],"r");int id,n,p,i,j,k;if(!input)return 2;
    math_log_two=log(2.0);
    population_sizes=(int*)malloc(sizeof(int));populations=(double***)malloc(sizeof(double**));dependency_matrices=(double***)malloc(sizeof(double**));
    while(fscanf(input,"%d%d%d",&id,&n,&p)==3) {
        number_of_parameters=n;population_sizes[0]=p;populations[0]=(double**)malloc(p*sizeof(double*));dependency_matrices[0]=(double**)malloc(n*sizeof(double*));
        for(k=0;k<p;k++){populations[0][k]=(double*)malloc(n*sizeof(double));for(i=0;i<n;i++)if(fscanf(input,"%lf",&populations[0][k][i])!=1)return 3;}
        for(i=0;i<n;i++)dependency_matrices[0][i]=(double*)calloc(n,sizeof(double));
        computeDependencyMatrixSpecificGOMEA(0);
        for(i=0;i<n;i++)for(j=i+1;j<n;j++)printf("%d,%d,%d,%.17g\n",id,i,j,dependency_matrices[0][i][j]);
        for(k=0;k<p;k++)free(populations[0][k]);free(populations[0]);for(i=0;i<n;i++)free(dependency_matrices[0][i]);free(dependency_matrices[0]);
    }
    free(population_sizes);free(populations);free(dependency_matrices);fclose(input);return 0;
}
'''
    (root / 'native-dependency.c').write_text(header + globals_text + '\n'.join(functions.values()) + dependency_main, encoding='utf-8')
    write_once(root / 'source-anchors.json', {'multiobjective': mo_anchors, 'permutation': permutation_anchors,
        'lineEndingsNormalizedToLF': True, 'functionBodiesOtherwiseUnchanged': True,
        'dependencyExternalConstant': {'name': 'math_log_two', 'valueExpression': 'log(2.0)',
            'sourceLine': 2720, 'initializedByHarnessBeforeCalls': True}})


def verify_predicates(root, count):
    checked = 0;differences = 0
    with (root / 'predicate-results.csv').open(encoding='ascii') as source:
        observed = csv.reader(source)
        for index, case in enumerate(predicate_cases()):
            record = list(map(int, next(observed)));expected = expected_predicates(case)
            assert record == [index, *expected], f'Native predicate mismatch at case {index}'
            differences += expected[:2] != expected_predicates(case, tolerance=0.)[:2];checked += 1
        assert next(observed, None) is None and checked == count
    return {'inputCases': checked, 'numericAssertions': checked * 8, 'allNativeSourcePredicatesMatchIndependentMath': True,
        'casesWhereSourceToleranceDiffersFromExactPareto': differences}


def verify_dependency(root, cases):
    matrices = {c['case']: np.zeros((len(c['keys'][0]), len(c['keys'][0]))) for c in cases};worst = 0.;checked = 0
    with (root / 'dependency-results.csv').open(encoding='ascii') as source:
        for row in csv.reader(source):
            index,i,j = map(int,row[:3]);value=float(row[3]);expected=expected_dependency(cases[index]['keys'],i,j)
            error=abs(value-expected);worst=max(worst,error);assert error<1e-12
            matrices[index][i,j]=matrices[index][j,i]=value;checked+=1
    assert checked == sum(len(c['keys'][0])*(len(c['keys'][0])-1)//2 for c in cases)
    comparisons = []
    for offset in range(0,len(cases),2):
        first,second=matrices[offset],matrices[offset+1];indices=np.triu_indices(len(first),1);delta=abs(first[indices]-second[indices])
        comparisons.append({'stem':cases[offset]['stem'],'seed':cases[offset]['seed'],'jobPairs':len(delta),
            'changedDependencyPairs':int(np.sum(delta>1e-12)),'maximumAbsoluteDifference':float(delta.max()),
            'samePerFactoryJobMachineWorkerChains':True,'sameSortedRandomKeyMagnitudesPerIndividual':True})
    return {'independentNativeDependencyPairs':checked,'maximumIndependentFormulaError':worst,'neutralViewComparisons':comparisons}


def main():
    with controller_lock(ROOT / 'research/night_research','dispatch.lock'):
        assert read(SOURCE/'status.json')['status']=='COMPLETE';compiler=shutil.which('gcc');assert compiler
        root=ROOT/'research/gomea_reference_audit'/datetime.now().strftime('native-semantics-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('GOMEA_NATIVE_AUDIT_ROOT',root,flush=True)
        write_once(root/'protocol.json',{'source':str(SOURCE),'purpose':'Original-function numeric audit and representation boundary, not optimizer performance',
            'functionsUnchangedExceptLF':True,'predicateDirections':'All8three-objective min/max combinations, feasible/infeasible and1e-5boundaries',
            'dependencyCases':'80free real source genomes,2instances/2source seeds,raw and equal-physical neutral global interleavings with paired key magnitudes',
            'sourceAlgorithmsRun':False,'optimizationFE':0,'decoderCalls':0,'frozenFaMiProgramStopUnchanged':True})
        try:
            count=predicate_input(root);cases=dependency_input(root);native_sources(root)
            shutil.copy2(Path(__file__),root);shutil.copy2(Path(__file__).with_name('gomea_native_fixtures.py'),root)
            write_once(root/'source-hashes.json',{str(p.relative_to(ROOT)):digest(p) for p in (MO,PERMUTATION)})
            run(root,[compiler,'--version'],'compiler-version.log')
            for kind in ('predicates','dependency'):
                run(root,[compiler,'-O2','-std=c11','-mfpmath=sse','-msse2',f'native-{kind}.c','-o',f'native-{kind}.exe','-lm'],f'compile-{kind}.log')
                input_name='predicate-cases.tsv' if kind=='predicates' else 'dependency-cases.tsv'
                run(root,[str(root/f'native-{kind}.exe'),input_name],f'{"predicate" if kind=="predicates" else "dependency"}-results.csv')
            result={'predicateAudit':verify_predicates(root,count),'dependencyAudit':verify_dependency(root,cases),
                'originalOptimizerExecuted':False,'nativeSourceFunctionsExecuted':True,'optimizationFE':0,'decoderCalls':0,'goalAchieved':False}
            write_once(root/'analysis.json',result)
        except BaseException as error:
            write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','error':repr(error),'optimizationFE':0,'decoderCalls':0});raise
        write_once(root/'status.json',{'status':'COMPLETE','optimizationFE':0,'decoderCalls':0,'goalAchieved':False})
        print('GOMEA_NATIVE_AUDIT_COMPLETE',result,flush=True)


if __name__=='__main__':main()
