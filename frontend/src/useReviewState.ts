import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api';
import type { Plan } from './scenarioApi';
import type { Review, ReviewGate, ReviewMutationPhase, ReviewRecovery } from './reviewState';

// Owned by App: changing screens must never cancel review readiness.
export function useReviewState(plan: Plan | null, recovery: ReviewRecovery | null, mutation: ReviewMutationPhase) {
  const key = plan ? plan.review_id || plan.run_id : '';
  const [loaded, setLoaded] = useState<{ key: string; review: Review | null; error: string } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const request = useRef<AbortController | null>(null);
  const pending = recovery?.previousReference === plan?.review_id ? recovery : null;
  useEffect(() => {
    const controller = new AbortController();
    request.current = controller;
    setLoaded(null);
    if (pending) setLoaded({ key, review: pending.review, error: '' });
    else if (plan?.review_id) {
      api<Review>(`/api/workflow/review/${plan.review_id}`, controller.signal)
        .then(review => { if (!controller.signal.aborted) setLoaded({ key, review, error: '' }); })
        .catch((error: Error) => { if (!controller.signal.aborted) setLoaded({ key, review: null, error: error.message }); });
    }
    return () => controller.abort();
  }, [key, pending, attempt]);
  const update = useCallback((review: Review) => {
    request.current?.abort(); // An earlier GET must not overwrite a completed mutation.
    setLoaded({ key: review.reference, review, error: '' });
  }, []);
  const review = loaded?.key === key ? loaded.review : null;
  const error = loaded?.key === key ? loaded.error : '';
  const valid = !!plan?.proposed?.replay.feasible && ['feasible', 'feasible_fallback'].includes(plan.status);
  const safe = review && ['draft', 'accepted', 'read_only'].includes(review.state) && !review.failures.length;
  const reason = mutation !== 'idle' ? 'The review mutation is still being saved.'
    : pending ? 'The replacement calculation is saved, but its result has not loaded.'
    : !valid ? 'A validated current plan is required.'
    : plan?.review_id && !review ? (error ? 'Review status could not be loaded. Retry review to continue.' : 'Review state is loading.')
    : plan?.review_id && !safe ? 'Review changes or conflicts require regeneration before this plan can be used.'
    : '';
  const gate: ReviewGate = { blocked: !!reason, reason };
  const protectedPlan = !!plan?.review_id && (!review || review.decisions.length > 0 || review.state !== 'draft');
  return { review, error, gate, protectedPlan, update, retry: () => setAttempt(value => value + 1) };
}

export type ReviewState = ReturnType<typeof useReviewState>;
