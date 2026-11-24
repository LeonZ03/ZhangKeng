import { cp, mkdir, stat, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';

const source = new URL('../site/', import.meta.url);
const output = new URL('../dist/', import.meta.url);
const { size } = await stat(new URL('assets/zhangkeng.glb', source));
if (size === 0 || size > 25 * 1024 * 1024) throw new Error('The Blender GLB must fit within the Cloudflare Pages file size limit.');
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
