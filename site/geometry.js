import * as THREE from 'three';
import { RoundedBoxGeometry } from './vendor/RoundedBoxGeometry.js';

const cube = new THREE.BoxGeometry(1, 1, 1);
const sphere = new THREE.SphereGeometry(1, 12, 8);
const cylinder = new THREE.CylinderGeometry(1, 1, 1, 16);
const standard = (color, roughness = 0.82) => new THREE.MeshStandardMaterial({ color, roughness });

export const mats = {
  plaster: standard('#c5bbae'), trim: standard('#d9cfc0'), wall: standard('#f1e8d9'),
  wallCut: standard('#f7f0df'), footer: standard('#5b6065'), cement: standard('#c2bdb1'),
  frame: standard('#282c30', 0.52), sill: standard('#c2b6a5'),
  window: new THREE.MeshStandardMaterial({ color: '#8bacb4', roughness: 0.2, metalness: 0.25, transparent: true, opacity: 0.46, depthWrite: false }),
  roof: new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.63, side: THREE.DoubleSide }),
  roofEdge: standard('#292d34'), timber: standard('#9d7356'), wood: standard('#bc9368'), oak: standard('#96704e'),
  tile: standard('#ddd1bc'), stone: standard('#bdb8a8'), bath: standard('#aeb9b4'),
  cloth: standard('#eee4d2'), linen: standard('#e6dcc8'), accent: standard('#93997d'),
  sofa: standard('#d5c5ab'), pillow: standard('#b48b65'), ceramic: standard('#f3eee0', 0.32),
  dustyBlue: standard('#a0afbf'), taupe: standard('#beb4aa'),
  toyClay: standard('#ae604b', 0.5), toyOchre: standard('#c99449', 0.5), toyBlue: standard('#507498', 0.5),
  steel: new THREE.MeshStandardMaterial({ color: '#5e635d', roughness: 0.38, metalness: 0.64 }),
  stairRail: standard('#202225', 0.51),
  plant: standard('#59684b'), soil: standard('#a38c68'), mulch: standard('#706654'),
  lawn: standard('#78865b'), rock: standard('#8b8777'), brick: standard('#8e6654'),
  paving: standard('#c8b797'), slatePaving: standard('#6d7175', 0.79), pavingJoint: standard('#a0a5a8'),
  darkStone: standard('#57594d'), water: standard('#8aaca6', 0.34),
};

export function addMesh(parent, geometry, material) {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}

export function box(parent, material, x, y, z, width, height, depth) {
  const mesh = addMesh(parent, cube, material);
  mesh.position.set(x, y, z);
  mesh.scale.set(width, height, depth);
  return mesh;
}

export function cushion(parent, material, x, y, z, width, height, depth, radius = 0.045) {
  const mesh = addMesh(parent, new RoundedBoxGeometry(width, height, depth, 2, radius), material);
  mesh.position.set(x, y, z);
  return mesh;
}

export function round(parent, material, x, y, z, rx, ry, rz = rx) {
  const mesh = addMesh(parent, sphere, material);
  mesh.position.set(x, y, z);
  mesh.scale.set(rx, ry, rz);
  return mesh;
}

export function post(parent, material, x, y, z, radius, height) {
  const mesh = addMesh(parent, cylinder, material);
  mesh.position.set(x, y, z);
  mesh.scale.set(radius, height, radius);
  return mesh;
}

export function beam(parent, material, a, b, width, depth = width) {
  const start = new THREE.Vector3(...a);
  const end = new THREE.Vector3(...b);
  const dir = end.clone().sub(start);
  const mesh = box(parent, material, ...start.lerp(end, 0.5).toArray(), width, dir.length(), depth);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  return mesh;
}

export function outline(points) {
  return new THREE.Shape(points.map(([x, y]) => new THREE.Vector2(x, y)));
}

export function plate(parent, material, poly, top, depth) {
  const shape = outline(poly.map(([x, z]) => [x, -z]));
  const mesh = addMesh(parent, new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false }), material);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = top - depth;
  return mesh;
}

export function group(parent, name, x = 0, y = 0, z = 0) {
  const node = new THREE.Group();
  node.name = name;
  node.position.set(x, y, z);
  parent.add(node);
  return node;
}

export function plant(parent, x, z, base = 0, size = 1) {
  post(parent, mats.soil, x, base + 0.11 * size, z, 0.11 * size, 0.22 * size);
  for (let i = 0; i < 6; i++) {
    const angle = i * Math.PI / 3;
    const dx = Math.cos(angle) * 0.13 * size;
    const dz = Math.sin(angle) * 0.13 * size;
    const leaf = round(parent, mats.plant, x + dx, base + (0.41 + 0.03 * (i % 3)) * size, z + dz, 0.065 * size, 0.18 * size, 0.07 * size);
    leaf.rotation.set(dz * 3, angle, -dx * 3);
  }
}
