import { cp, mkdir, readdir, readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
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

const sourceDirectory = fileURLToPath(source);
const sourcePath = (path) => relative(sourceDirectory, path).split(sep).join('/');
const appPaths = (await readdir(source, { recursive: true, withFileTypes: true }))
  .filter(entry => entry.isFile())
  .map(entry => sourcePath(join(entry.parentPath, entry.name)))
  .filter(path => path.startsWith('vendor/') || /\.(js|css)$/.test(path))
  .sort();
const appFiles = await Promise.all(appPaths.map(async path => ({ path, contents: await readFile(new URL(path, source)) })));
const appHash = createHash('sha256');
for (const { path, contents } of appFiles) {
  appHash.update(path).update('\0').update(contents).update('\0');
}
const appPath = `_app/${appHash.digest('hex').slice(0, 16)}/`;
const appOutput = new URL(appPath, output);

await mkdir(output, { recursive: true });
await cp(source, output, {
  recursive: true,
  filter(path) {
    const name = sourcePath(path);
    return name !== 'index.html' && name !== 'vendor' && !appPaths.includes(name);
  },
});
await Promise.all(appFiles.map(async ({ path, contents }) => {
  const target = new URL(path, appOutput);
  await mkdir(new URL('.', target), { recursive: true });
  await writeFile(target, contents);
}));
await mkdir(new URL('assets/models/', output), { recursive: true });
await writeFile(new URL(packedPath, output), compressed);
const html = index
  .replace(marker, `data-packed-model="./${packedPath}" data-packed-bytes="${compressed.length}"`)
  .replace('./style.css', `./${appPath}style.css`)
  .replace('./vendor/three.module.js', `./${appPath}vendor/three.module.js`)
  .replace('./viewer.js', `./${appPath}viewer.js`);
await writeFile(new URL('index.html', output), html);
let revision = process.env.CF_PAGES_COMMIT_SHA || 'local';
try {
  if (revision === 'local') revision = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
} catch {
  // A plain directory or the initial uncommitted checkout can still be built.
}
await writeFile(new URL('version.json', output), JSON.stringify({ revision, packedModel: packedPath }) + '\n');
console.log(`Pages output: dist/ (${revision.slice(0, 12)}), model download ${(compressed.length / 1048576).toFixed(2)} MiB`);
