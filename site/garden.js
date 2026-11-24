import * as THREE from 'three';
import { yard } from './plan.js';
import { box, group, mats, plate, plant, post, round } from './geometry.js';
import { chair } from './furniture.js';

const datum = -0.29;
const { west, east, north, south, radius } = yard;
const rect = (x1, z1, x2, z2) => [[x1, z1], [x2, z1], [x2, z2], [x1, z2]];

function border() {
  const points = [[west, north], [east, north]];
  for (const [x, start] of [[east - radius, 0], [west + radius, 90]]) {
    for (let i = 0; i <= 8; i++) {
      const angle = (start + 90 * i / 8) * Math.PI / 180;
      points.push([x + radius * Math.cos(angle), south - radius + radius * Math.sin(angle)]);
    }
  }
  return points;
}

function wallEdge(parent, a, b, material, y, h, thickness) {
  const dx = b[0] - a[0], dz = b[1] - a[1];
  const node = box(parent, material, (a[0] + b[0]) / 2, y, (a[1] + b[1]) / 2, Math.hypot(dx, dz) + 0.025, h, thickness);
  node.rotation.y = Math.atan2(-dz, dx);
}

function enclosure(parent, points, built) {
  const height = built ? 0.38 : 0.53;
  const segments = points.slice(1).map((b, i) => [points[i], b]);
  segments.push([points.at(-1), [west, 10.62]], [[west, 9.13], points[0]]);
  for (const [a, b] of segments) {
    wallEdge(parent, built ? mats.brick : mats.rock, a, b, datum + height / 2, height, 0.24);
    if (!built) wallEdge(parent, mats.sill, a, b, datum + height, 0.065, 0.30);
  }
  if (built) return;
  for (const z of [9.1, 10.65]) box(parent, mats.plaster, west, datum + 0.5, z, 0.33, 1, 0.33);
  for (let z = 9.28; z < 10.48; z += 0.11) box(parent, mats.steel, west, datum + 0.48, z, 0.047, 0.76, 0.035);
  for (const y of [datum + 0.18, datum + 0.85]) box(parent, mats.frame, west, y, 9.875, 0.064, 0.043, 1.24);
}

function tree(parent, x, z, scale = 1, autumn = false) {
  const node = group(parent, '庭院乔木', x, datum + 0.11, z);
  node.scale.setScalar(scale);
  post(node, mats.oak, 0, 0.72, 0, 0.075, 1.44);
  const colors = autumn ? ['#a35d43', '#bf7544', '#aa4f33', '#b47a4b'] : ['#677b4f', '#879664', '#6a8554', '#93a36d'];
  const leaves = colors.map(color => new THREE.MeshStandardMaterial({ color, roughness: 1, flatShading: true }));
  for (let i = 0; i < 13; i++) {
    const angle = i * 2.39996;
    const spread = i > 9 ? 0.27 : 0.75;
    const height = i > 9 ? 2.38 : 1.53 + 0.53 * (i % 3) / 2;
    const leaf = round(node, leaves[i % leaves.length], Math.cos(angle) * spread, height, Math.sin(angle) * spread, 0.35 + (i % 3) * 0.09, 0.41, 0.43);
    leaf.rotation.y = angle;
  }
}

function cookingShelter(parent) {
  const node = group(parent, '西北户外厨房', -2.36, datum, -4.61);
  box(node, mats.stone, 0, 0.04, 0, 3, 0.08, 3.5);
  for (const [x, z] of [[-1.4, -1.64], [1.4, -1.64], [-1.4, 1.64], [1.4, 1.64]]) {
    box(node, mats.oak, x, 1.26, z, 0.16, 2.52, 0.16);
  }
  box(node, mats.roofEdge, 0, 2.52, 0, 3.22, 0.14, 3.69).rotation.x = 0.06;
  for (let x = -1.49; x < 1.55; x += 0.17) {
    box(node, mats.frame, x, 2.604, 0, 0.075, 0.034, 3.68).rotation.x = 0.06;
  }
  box(node, mats.rock, 0, 0.53, -1.58, 3, 1.06, 0.26);
  for (let x = -0.99; x <= 1.04; x += 0.202) {
    box(node, mats.sill, x, 1.29, -1.58, 0.06, 0.43, 0.19);
  }
  for (const y of [1.07, 1.28, 1.5]) box(node, mats.sill, 0, y, -1.58, 2.02, 0.046, 0.19);
  box(node, mats.rock, 0, 0.48, -1.16, 2.83, 0.88, 0.56);
  box(node, mats.stone, 0, 0.955, -1.16, 2.89, 0.075, 0.62);
  box(node, mats.steel, 0.77, 1.0, -1.16, 0.6, 0.03, 0.38);
  box(node, mats.frame, -0.85, 1.0, -1.16, 0.54, 0.05, 0.39);
  post(node, mats.oak, -0.38, 0.712, 0.6, 0.47, 0.068);
  post(node, mats.oak, -0.38, 0.36, 0.6, 0.06, 0.72);
  chair(node, -1.05, 0.6, Math.PI / 2);
  chair(node, 0.28, 0.6, -Math.PI / 2);
}

function terrace(parent) {
  const node = group(parent, '东北塑木平台', 10.54, datum + 0.15, -4.52);
  box(node, mats.oak, 0, -0.074, 0, 3.115, 0.148, 3.62);
  for (let x = -1.49; x < 1.52; x += 0.132) {
    box(node, mats.wood, x, -0.006, 0, 0.127, 0.025, 3.62);
  }
  post(node, mats.oak, 0, 0.7, 0.025, 0.52, 0.059);
  post(node, mats.frame, 0, 0.343, 0.025, 0.07, 0.686);
  chair(node, -0.66, -0.59, 0.7);
  chair(node, 0.68, -0.58, -0.7);
  chair(node, -0.64, 0.64, 2.35);
  chair(node, 0.66, 0.67, -2.35);
  plant(node, -1.29, 1.6, 0, 1.3);
}

function paving(parent) {
  const pavingSurface = group(parent, '石板园路');
  const stoneColors = ['#a7a089', '#c3b18e', '#bfb19a', '#c8ba9f', '#b5ad9b'];
  const slabs = stoneColors.map(color => new THREE.MeshStandardMaterial({ color, roughness: 0.9 }));
  const paths = [
    [rect(-3.73, -0.1, -0.11, 11.65), 0.12],
    [rect(11.91, -0.12, 13.51, 11.65), 0.12],
    [rect(-0.13, 9.13, 11.91, 11.68), 0.12],
    [rect(-0.76, -6.2, 0.64, -2.98), 0],
    [[[0.23, -3.6], [3.2, -3.6], [3.2, -2.98], [5.37, -2.98], [5.37, -3.83], [8.12, -3.83], [8.12, -5.17], [8.92, -5.17], [8.92, -1.4], [6.36, -1.4], [6.36, -1.9], [3.16, -1.9], [3.16, -2.38], [0.23, -2.38]], 0],
    [rect(6.7, -1.69, 8.14, 0), 0.12],
    [rect(8.45, -2.43, 13.54, -0.12), 0],
  ];
  for (const [poly, height] of paths) plate(pavingSurface, mats.paving, poly, datum + height, 0.075);
  for (const [x1, z1, x2, z2, y] of [[-3.73, 0, -0.13, 11.61, 0.122], [11.93, 0, 13.52, 11.61, 0.122], [-0.13, 9.12, 11.93, 11.65, 0.122], [8.58, -2.4, 13.5, -0.13, 0.002]]) {
    const spacing = 0.61;
    let row = 0;
    for (let z = z1; z < z2 - 0.02; z += spacing) {
      const depth = Math.min(spacing, z2 - z);
      let col = 0;
      for (let x = x1; x < x2 - 0.02;) {
        const width = Math.min(col === 0 && row % 2 ? spacing / 2 : spacing, x2 - x);
        box(pavingSurface, slabs[(col * 5 + row * 7 + (col ^ row)) % slabs.length], x + width / 2, datum + y, z + depth / 2, width - 0.011, 0.016, depth - 0.011);
        x += width;
        col++;
      }
      row++;
    }
  }
}

export function buildGarden(root) {
  const points = border();
  const site = group(root, '庭院');
  const proposal = group(site, '庭院施工方案');
  const present = group(site, '庭院施工阶段示意');
  plate(site, mats.soil, points, datum - 0.035, 0.33);
  plate(proposal, mats.darkStone, points, datum - 0.02, 0.052);
  enclosure(proposal, points, false);
  paving(proposal);
  cookingShelter(proposal);
  terrace(proposal);
  const beds = [
    [[0.68, -6.16], [8.58, -6.16], [8.22, -5.22], [7.38, -4.08], [5.45, -3.94], [4.06, -3.23], [2.3, -3.6], [0.68, -3.6]],
    [[-3.68, -2.72], [-2, -2.82], [-1.43, -1.88], [-2.13, -0.2], [-3.68, -0.2]],
    [[-0.05, -1.42], [3.13, -2.16], [6.32, -1.86], [6.52, -0.29], [0.02, -0.22]],
    [[12.15, -6.17], [13.48, -6.17], [13.48, -2.6], [12.18, -2.6]],
    rect(-2.92, 10.43, -1.92, 11.43), rect(10.89, 10.43, 11.89, 11.43),
  ];
  beds.forEach((poly, i) => plate(proposal, mats.lawn, poly, datum + (i > 3 ? 0.22 : 0.10), 0.16));
  for (const [x, z, s, autumn] of [[3.27, -5.04, 1.22, true], [12.54, -5.35, 1.21], [-2.78, -1.59, 0.94], [-2.42, 10.93, 0.83], [11.39, 10.93, 0.83]]) {
    tree(proposal, x, z, s, autumn);
  }
  for (const [x, z, s] of [[0.99, -5.8, 1.7], [6.7, -5.75, 1.8], [7.84, -5.6, 1.9], [12.85, -3.23, 1.6], [2.47, -0.9, 1.4], [4.85, -1.24, 1.5]]) {
    plant(proposal, x, z, datum + 0.1, s);
  }
  for (const [x, z, s] of [[1.6, -4.7, 0.34], [5.59, -5.6, 0.44], [4.81, -0.63, 0.38], [-2.63, -0.91, 0.28]]) {
    round(proposal, mats.rock, x, datum + 0.11, z, s, s * 0.43, s * 0.71);
  }
  plate(present, mats.cement, [[west, -0.13], [east, -0.13], ...points.slice(2)], datum + 0.12, 0.11);
  enclosure(present, points, true);
  present.visible = false;
  return { site, proposal, present };
}
