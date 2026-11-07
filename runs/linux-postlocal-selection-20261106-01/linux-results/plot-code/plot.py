"""Linux-only paired effects for the registered post-local selection probe."""
import argparse
import json
from pathlib import Path
import platform
import time
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


LABELS = {'RAW_ROLE': 'R', 'POST_ROLE': 'P', 'POST_PARETO': 'U'}
ENDPOINTS = ('finalArchive', 'workingPopulation')
CONTRACT = {
    'claim': 'Expose every paired metric agreement or disagreement under equal three-pass FE.',
    'archetype': 'quantitative grid', 'backend': 'Python matplotlib',
    'panels': 'Final all-paid archive and working population: HV, IGDplus, C difference',
    'mapping': 'All three comparisons, all three registered reused source seeds; black median marks',
    'statistics': 'Descriptive paired values only; no confidence intervals, EAF or significance test',
    'reuse': 'Style-only inheritance of accepted pilot plots; new hypothesis and comparison labels',
    'exclusions': '2B explanatory endpoints are in source tables; no seed omitted in final panels',
    'formats': ['SVG editable text', 'PDF TrueType', 'PNG 600dpi', 'preview PNG 300dpi'],
    'widthMM': 183, 'heightMM': 118,
    'limits': 'Reused development states; not a full-algorithm trial; sampled first batches contain no shared proposals',
}


def effects(pair):
    return [pair['HVEffectPct']['1.5'], pair['IGDplusSymmetricImprovementPct'], 100 * pair['Cdelta']]


def configure():
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans'], 'font.size': 7,
                         'axes.titlesize': 8, 'axes.labelsize': 7, 'legend.fontsize': 6.5,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42, 'axes.spines.right': False,
                         'axes.spines.top': False, 'axes.linewidth': 0.7, 'legend.frameon': False})


def draw_panel(axis, records, column, row, maximum):
    colors, markers = ['#4477AA', '#CC9955', '#55A899'], ['o', 's', '^']
    titles = ['HV relative change (%)', 'IGD+ symmetric\nimprovement (%)',
              'C(A,B) - C(B,A)\n(percentage points)']
    axis.axvline(0, color='#777777', linewidth=0.6)
    for i, comp in enumerate(records):
        points = np.asarray([effects(p) for p in comp['pairs']])[:, column]
        for j, value in enumerate(points):
            axis.plot(value, i + (j - 1) * 0.15, marker=markers[j], color=colors[j], markersize=3.5,
                      linestyle='none', label=str(comp['pairs'][j]['seed']) if row == column == i == 0 else None)
        axis.plot(float(np.median(points)), i, marker='|', color='black', markersize=9, linestyle='none')
    axis.set(xlim=(-maximum, maximum), ylim=(len(records) - 0.5, -0.5), yticks=range(len(records)))
    axis.set_yticklabels([LABELS[c['candidate']] + ' / ' + LABELS[c['control']] for c in records]
                        if column == 0 else [''] * len(records))
    axis.set_title(titles[column], pad=13)
    axis.locator_params(axis='x', nbins=4)
    axis.grid(axis='x', alpha=0.15, linewidth=0.5)
    axis.text(-0.08, 1.22, chr(ord('a') + row * 3 + column), transform=axis.transAxes,
              fontsize=8, fontweight='bold')


def draw_case(case, out, maxima):
    fig, axes = plt.subplots(2, 3, figsize=(7.204724409448819, 4.645669291338583))
    fig.subplots_adjust(left=0.12, right=0.98, top=0.82, bottom=0.18, wspace=0.32, hspace=0.65)
    for row, endpoint in enumerate(ENDPOINTS):
        records = [c for c in case['comparisons'] if c['endpoint'] == endpoint]
        assert len(records) == 3 and all(len(c['pairs']) == 3 for c in records)
        for column in range(3):
            draw_panel(axes[row, column], records, column, row, maxima[column])
        axes[row, 0].set_ylabel('All-paid archive' if row == 0 else 'Working population', labelpad=5)
    fig.suptitle(case['instance'] + ' | equal three-pass FE | all paired effects', y=0.985, fontsize=9)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.55, 0.95), ncol=3)
    fig.text(0.5, 0.065, 'Positive values favour A. All three source seeds shown; black marks: medians. No confidence intervals.',
              ha='center', fontsize=6)
    fig.text(0.5, 0.025, 'R: raw role selection; P: post-local role selection; U: post-local Pareto selection. Not a full-algorithm trial.',
              ha='center', fontsize=6)
    stem = out / ('paired-effects-' + case['instance'])
    fig.savefig(str(stem) + '.svg')
    fig.savefig(str(stem) + '.pdf')
    fig.savefig(str(stem) + '.png', dpi=600)
    fig.savefig(str(stem) + '-preview.png', dpi=300)
    text_count = len(ET.parse(str(stem) + '.svg').findall('.//{http://www.w3.org/2000/svg}text'))
    assert text_count > 0
    plt.close(fig)
    return dict(stem=stem.name, svgTextElements=text_count, widthMM=183, heightMM=118,
                pairedComparisons=6, rawEffectPoints=54, visualInspection='PENDING')


def main():
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); start = time.perf_counter()
    result = json.loads(args.analysis.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'figure-contract.json').write_text(json.dumps(CONTRACT, indent=2))
    values = np.asarray([effects(p) for case in result['instances'] for c in case['comparisons']
                         if c['endpoint'] in ENDPOINTS for p in c['pairs']])
    assert values.shape == (36, 3) and np.isfinite(values).all()
    maxima = np.maximum(np.abs(values).max(axis=0), 1e-5) * 1.15
    configure()
    exports = [draw_case(case, args.output, maxima) for case in result['instances']]
    (args.output / 'figure-export.json').write_text(json.dumps(dict(exports=exports,
        source=str(args.analysis), seconds=time.perf_counter() - start), indent=2))
    print('PLOT_COMPLETE', args.output, flush=True)


if __name__ == '__main__':
    main()
