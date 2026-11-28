import { mkdir, writeFile } from 'node:fs/promises';
import { registerHooks } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Use the same pinned Three.js geometry and the same dimensions as the viewer.
const three = new URL('../../site/vendor/three.module.js', import.meta.url).href;
registerHooks({
  resolve(specifier, context, next) {
    return next(specifier === 'three' ? three : specifier, context);
  },
});

const { buildModel, slabOutlines } = await import('../../site/model.js');
const { mats } = await import('../../site/geometry.js');
const plan = await import('../../site/plan.js');
const model = buildModel();
const nodeNames = new Map([
  [model.root, 'Villa'],
  [model.roof, 'Roof'],
  [model.site, 'Yard'],
  [model.proposal, 'YardDesign'],
  [model.present, 'YardExisting'],
]);
for (const [floor, prefix] of [['ground', 'Ground'], ['upper', 'Upper']]) {
  const layer = model.building[floor];
  nodeNames.set(layer.layer, `${prefix}Floor`);
  nodeNames.set(layer.full, `${prefix}Shell`);
  nodeNames.set(layer.cut, `${prefix}Slice`);
  nodeNames.set(layer.contents, `${prefix}Furniture`);
  nodeNames.set(layer.contents.children.find(child => child.name === '固定设施'), `${prefix}Fixtures`);
}
for (const [id, object] of model.furniture) nodeNames.set(object, id);

const materialNames = new Map(Object.entries(mats).map(([key, material]) => [material, key]));
const materials = {};
const geometryIds = new Map();
const geometries = [];

function serializeMaterial(material) {
  const key = materialNames.get(material) ?? `custom-${materialNames.size}`;
  materialNames.set(material, key);
  materials[key] ??= {
    color: material.color.toArray(), roughness: material.roughness, metalness: material.metalness,
    opacity: material.transparent ? material.opacity : 1, vertexColors: material.vertexColors,
    doubleSided: material.side === 2, flat: material.flatShading,
  };
  return key;
}

function serializeGeometry(geometry) {
  if (geometryIds.has(geometry)) return geometryIds.get(geometry);
  const id = geometries.length;
  const values = (key) => geometry.getAttribute(key) && Array.from(geometry.getAttribute(key).array);
  geometries.push({
    position: values('position'), normal: values('normal'), color: values('color'), uv: values('uv'),
    indices: geometry.index ? Array.from(geometry.index.array) : null,
  });
  geometryIds.set(geometry, id);
  return id;
}

function serializeNode(object) {
  const node = {
    id: nodeNames.get(object), label: object.name,
    position: object.position.toArray(), rotation: object.quaternion.toArray(), scale: object.scale.toArray(),
    children: object.children.map(serializeNode),
  };
  if (object.isMesh) {
    if (!object.material?.color || ![...node.position, ...node.rotation, ...node.scale].every(Number.isFinite)) {
      throw new Error(`Invalid source mesh in ${object.parent.name}`);
    }
    node.mesh = serializeGeometry(object.geometry);
    node.material = serializeMaterial(object.material);
    node.castShadow = object.castShadow;
    node.receiveShadow = object.receiveShadow;
  }
  return node;
}

const scene = serializeNode(model.root);
const out = resolve(process.argv[2] ?? fileURLToPath(new URL('../../.work/blender/geometry.json', import.meta.url)));
await mkdir(dirname(out), { recursive: true });
await writeFile(out, JSON.stringify({ schema: 1, plan: { ...plan, slabOutlines }, scene, materials, geometries }));
console.log(`Blender input: ${geometries.length} mesh definitions, ${Object.keys(materials).length} materials`);
