import { cp, mkdir, readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';

const source = new URL('../site/', import.meta.url);
const output = new URL('../dist/', import.meta.url);
const model = await readFile(new URL('assets/zhangkeng.glb', source));
if (model.length === 0 || model.length > 25 * 1024 * 1024) throw new Error('The Blender GLB must fit within the Cloudflare Pages file size limit.');
const compressed = gzipSync(model, { level: 9 });
const digest = createHash('sha256').update(compressed).digest('hex').slice(0, 16);
const packedPath = `assets/models/${digest}.glb.gz`;
const index = await readFile(new URL('index.html', source), 'utf8');
const marker = 'data-packed-model="" data-packed-bytes=""';
if (!index.includes(marker)) throw new Error('Missing model download configuration on the stage.');
await mkdir(output, { recursive: true });
await cp(source, output, { recursive: true });
await mkdir(new URL('assets/models/', output), { recursive: true });
await writeFile(new URL(packedPath, output), compressed);
await writeFile(new URL('index.html', output), index.replace(marker, `data-packed-model="./${packedPath}" data-packed-bytes="${compressed.length}"`));
let revision = process.env.CF_PAGES_COMMIT_SHA || 'local';
try {
  if (revision === 'local') revision = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
} catch {
  // A plain directory or the initial uncommitted checkout can still be built.
}
await writeFile(new URL('version.json', output), JSON.stringify({ revision, packedModel: packedPath }) + '\n');
console.log(`Pages output: dist/ (${revision.slice(0, 12)}), model download ${(compressed.length / 1048576).toFixed(2)} MiB`);
