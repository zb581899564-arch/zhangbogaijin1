"""Download the author thesis from its institutional portal for private method audit only."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path

import requests

from run_long_budget_bridge import ROOT, write_once

PORTAL = 'https://research.vu.nl/en/publications/model-based-optimization-in-home-healthcare/'
PDF = 'https://research.vu.nl/ws/portalfiles/portal/360510178/proefschriftyoramclapper%20-%2066fdb0c4047b7.pdf'
CAP = 20_000_000  # Institutional landing page advertises14.6MB, well below the authorized500MB/file limit.


def main():
    root = ROOT / 'research/gomea_reference_audit' / datetime.now().strftime('private-publications-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('PAGOMEA_REFERENCE_ROOT', root, flush=True)
    count = 0
    try:
        target = root / 'clapper-thesis-2024.pdf'
        with requests.get(PDF, stream=True, timeout=(15, 60)) as response:
            response.raise_for_status()
            metadata = {'requestedURL': PDF, 'resolvedURL': response.url, 'statusCode': response.status_code,
                        'contentType': response.headers.get('Content-Type'), 'contentLength': response.headers.get('Content-Length')}
            assert 'application/pdf' in metadata['contentType']
            with target.open('xb') as output:
                for chunk in response.iter_content(65536):
                    count += len(chunk)
                    if count > CAP:
                        raise RuntimeError('Institutional14.6MB source exceeded local20MB cap; retained partial, not retried')
                    output.write(chunk)
        assert target.read_bytes()[:5] == b'%PDF-'
        import fitz
        with fitz.open(target) as document:
            text = '\n\n'.join(f'=== PDF PAGE {p + 1} ===\n' + page.get_text() for p, page in enumerate(document))
            (root / 'extracted-text.txt').write_text(text, encoding='utf-8')
            pages = len(document)
        write_once(root / 'manifest.json', {'landingPage': PORTAL, 'advertisedSize': '14.6MB',
            'actualBytes': count, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), **metadata,
            'downloadedAtUTC': datetime.now(timezone.utc).isoformat(), 'pdfPages': pages,
            'version': 'Author2024dissertation, Chapter3 based on COR2023paper; not assumed identical typesetting/version',
            'purpose': 'Private research, no public redistribution', 'uploadedBytes': 0,
            'networkConfigurationChanged': False, 'directRouteVerified': False, 'optimizationFE': 0})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), 'downloadedBytes': count})
        raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'downloadedBytes': count, 'uploadedBytes': 0, 'optimizationFE': 0})
    print('PAGOMEA_REFERENCE_COMPLETE', count, pages, flush=True)


if __name__ == '__main__':
    main()
