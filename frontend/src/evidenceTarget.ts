import type { components } from './contracts.generated';

type EvidenceTarget = components['schemas']['EvidenceTarget'];
type WithEvidenceTargets = { evidence_targets: EvidenceTarget[] };

export const purchaseEvidenceTarget = (policy: WithEvidenceTargets, actionId: string) =>
  policy.evidence_targets.find(target => target.action_id === actionId);

export const evidenceTargetSummary = (target: EvidenceTarget | undefined) => {
  if (!target?.location_id) return 'No defensible store demand context is available for this pooled-DC purchase.';
  if (target.basis === 'earliest_shortage') {
    return `${target.location_id} demand context · earliest reachable shortage ${target.shortage_date} · ${target.affected_units} units.`;
  }
  return `${target.location_id} demand context · greatest replay-backed replenishment need · ${target.affected_units} units.`;
};
