"""Explicit in-process diagnostics. Disabled by default; never a public trace endpoint."""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

_sink=ContextVar('scamshield_diagnostic_sink',default=None)

@contextmanager
def capture_traces():
    records=[];token=_sink.set(records)
    try:yield records
    finally:_sink.reset(token)

def record(request_id,extracted,response):
    sink=_sink.get()
    if sink is None:return
    if not hasattr(extracted,'annotations'):return
    # This is the same provider result used to build the HTTP response, after support.
    sink.append(deepcopy({'request_id':request_id,'versions':extracted.versions,
      'analysis_status':extracted.analysis_status,'annotations':extracted.annotations.model_dump(mode='json'),
      'assessment':extracted.assessment.model_dump(mode='json'),
      'response':response.model_dump(mode='json'),'core_timings_ms':extracted.core_timings_ms}))

def record_cached(request_id,response):
    sink=_sink.get()
    if sink is not None:sink.append({'request_id':request_id,'cache_hit':True,'annotations':None,'note':'No new extraction or policy execution on this request.','response':response.model_dump(mode='json')})
