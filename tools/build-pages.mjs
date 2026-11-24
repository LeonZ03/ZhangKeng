import { cp, mkdir, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';

const source = new URL('../site/', import.meta.url);
const output = new URL('../dist/', import.meta.url);
await mkdir(output, { recursive: true });
await cp(source, output, { recursive: true });
let revision = process.env.CF_PAGES_COMMIT_SHA || 'local';
try {
  if (revision === 'local') revision = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
} catch {
  // A plain directory or the initial uncommitted checkout can still be built.
}
await writeFile(new URL('version.json', output), JSON.stringify({ revision }) + '\n');
console.log(`Pages output: dist/ (${revision.slice(0, 12)})`);
