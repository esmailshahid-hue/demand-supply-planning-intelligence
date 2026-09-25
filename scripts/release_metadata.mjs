// Public build identity only. Never serialize the environment or credentials.
import { writeFile } from 'node:fs/promises';
const commit = process.env.VERCEL_GIT_COMMIT_SHA || process.env.GITHUB_SHA || null;
const deployment_host = process.env.VERCEL_URL || null;
if (process.env.VERCEL_ENV === 'production' && (!/^[a-f0-9]{40}$/.test(commit || '') || !deployment_host?.endsWith('.vercel.app'))) {
  throw new Error('Production build requires VERCEL_GIT_COMMIT_SHA and VERCEL_URL for release verification');
}
await writeFile(new URL('../frontend/dist/release.json', import.meta.url), JSON.stringify({ commit, deployment_host }) + '\n');
