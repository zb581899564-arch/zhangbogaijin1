import sys
from .campaign import campaign

if sys.argv[1] == '--resume': campaign(resume=sys.argv[2])
else: campaign(engineering=sys.argv[1])
