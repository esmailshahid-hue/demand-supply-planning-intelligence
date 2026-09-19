import type { components } from './contracts.generated';

export type Review = components['schemas']['ReviewView'];

export type ReviewRecovery = {
  previousReference: string;
  operation: 'regenerate' | 'new-draft';
  review: Review;
};

export type ReviewGate = {
  blocked: boolean;
  reason: string;
};
