import * as THREE from 'three';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';
import { furnishings } from './plan.js';

const assetUrl = new URL('./assets/zhangkeng.glb', import.meta.url);

function requireDescendant(parent, name) {
  const node = parent.getObjectByName(name);
  if (!node || node === parent) throw new Error(`Villa model is missing ${name} inside ${parent.name}.`);
  return node;
}

export async function loadAssetModel() {
  const { scene } = await new GLTFLoader().loadAsync(assetUrl.href);
  const root = requireDescendant(scene, 'Villa');
  const building = Object.fromEntries([['ground', 'Ground'], ['upper', 'Upper']].map(([id, name]) => {
    const layer = requireDescendant(root, `${name}Floor`);
    return [id, {
      layer,
      full: requireDescendant(layer, `${name}Shell`),
      cut: requireDescendant(layer, `${name}Slice`),
      contents: requireDescendant(layer, `${name}Furniture`),
    }];
  }));
  const roof = requireDescendant(root, 'Roof');
  const site = requireDescendant(root, 'Yard');
  const proposal = requireDescendant(site, 'YardDesign');
  const present = requireDescendant(site, 'YardExisting');
  const furniture = new Map();
  const tagged = Object.fromEntries(Object.entries(building).map(([id, { contents }]) => {
    const pivots = new Map();
    contents.traverse(node => {
      if (node.userData.itemId) pivots.set(node.userData.itemId, node);
    });
    return [id, pivots];
  }));
  for (const { id, floor } of furnishings) {
    const { contents } = building[floor];
    const item = contents.getObjectByName(id) ?? tagged[floor].get(id);
    if (!item) throw new Error(`Villa model is missing furniture ${id}.`);
    item.userData.itemId = id;
    furniture.set(id, item);
  }
  root.traverse(object => {
    if (!object.isMesh) return;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    const opaque = materials.some(material => !material.transparent && !material.transmission);
    object.userData.castShadow ??= opaque;
    object.castShadow = object.userData.castShadow;
    object.receiveShadow = object.userData.receiveShadow ?? opaque;
  });
  return { root, building, roof, site, proposal, present, furniture };
}

export function makeDaylightEnvironment() {
  const width = 256, height = 128;
  const data = new Uint16Array(width * height * 4);
  const sky = new THREE.Color('#9eb6d0');
  const horizon = new THREE.Color('#e9eef4');
  const ground = new THREE.Color('#8c887a');
  const color = new THREE.Color();
  const direction = new THREE.Vector3();
  const softbox = new THREE.Vector3(-0.45, 0.6, 0.65).normalize();
  const half = THREE.DataUtils.toHalfFloat;
  for (let y = 0; y < height; y++) {
    const latitude = Math.PI * ((y + 0.5) / height - 0.5);
    const up = Math.sin(latitude);
    const horizontal = Math.cos(latitude);
    for (let x = 0; x < width; x++) {
      const longitude = Math.PI * (2 * (x + 0.5) / width - 1);
      direction.set(horizontal * Math.cos(longitude), up, horizontal * Math.sin(longitude));
      color.copy(horizon).lerp(up >= 0 ? sky : ground, Math.pow(Math.abs(up), 0.45));
      const cloud = Math.max(0, direction.dot(softbox)) ** 14 * 1.65;
      color.addScalar(cloud);
      const index = (y * width + x) * 4;
      data[index] = half(color.r);
      data[index + 1] = half(color.g);
      data[index + 2] = half(color.b);
      data[index + 3] = half(1);
    }
  }
  const environment = new THREE.DataTexture(data, width, height, THREE.RGBAFormat, THREE.HalfFloatType);
  environment.mapping = THREE.EquirectangularReflectionMapping;
  environment.colorSpace = THREE.LinearSRGBColorSpace;
  environment.minFilter = environment.magFilter = THREE.LinearFilter;
  environment.needsUpdate = true;
  return environment;
}
