"""Policy input ontology only; this does not resize or relabel learned heads."""
from .schema import ATTRS
VERSION='graph-policy-2.0-experimental'
EXTRA_ACTIONS=['read_terms','promise_income','conceal_terms','misstate_information','sign_obligation','grant_authority','pressure_relationship','claim_entitlement','change_work','control_income','confirm_completion','receive_service','trade_off_platform','collect_identity','purpose_mismatch','claim_organization','payee_mismatch','unspecified_step','offer_service','free_exit']
POLICY_ATTRS={**ATTRS,'action_type':ATTRS['action_type']+EXTRA_ACTIONS,'object_type':ATTRS['object_type']+['ownership_right','contract','service_confirmation','employment']}
