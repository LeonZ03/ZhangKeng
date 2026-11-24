import * as THREE from 'three';
import { floors, roof, upperElevation } from './plan.js';
import { addMesh, beam, box, group, mats, outline, plate } from './geometry.js';
import { buildFurniture } from './furniture.js';
import { buildGarden } from './garden.js';

const mainMid = 4.5;
const crossMid = 5.9;
const mainSlope = (roof.mainRidge - roof.mainEave) / mainMid;
const crossSlope = (roof.crossRidge - roof.crossEave) / 2.4;
const mainHeight = (z) => roof.mainRidge - Math.abs(z - mainMid) * mainSlope;
const crossHeight = (x) => roof.crossRidge - Math.abs(x - crossMid) * crossSlope;

function axisBox(parent, material, wall, begin, end, low, high, depth, offset = 0) {
  if (end - begin < 0.002 || high - low < 0.002) return;
  const m = (begin + end) / 2, y = (low + high) / 2, w = end - begin, h = high - low;
  if (wall.axis === 'x') return box(parent, material, m, y, wall.position + offset, w, h, depth);
  return box(parent, material, wall.position + offset, y, m, depth, h, w);
}

function wallPanel(parent, wall, material, begin, end, low, highA, highB) {
  if (end - begin < 0.002 || Math.max(highA, highB) - low < 0.002) return;
  if (Math.abs(highA - highB) < 0.0001) {
    axisBox(parent, material, wall, begin, end, low, highA, wall.thickness);
    return;
  }
  const shape = outline([[begin, low], [end, low], [end, Math.max(low, highB)], [begin, Math.max(low, highA)]]);
  const mesh = addMesh(parent, new THREE.ExtrudeGeometry(shape, { depth: wall.thickness, bevelEnabled: false }), material);
  if (wall.axis === 'x') mesh.position.z = wall.position - wall.thickness / 2;
  else {
    mesh.rotation.y = -Math.PI / 2;
    mesh.position.x = wall.position + wall.thickness / 2;
  }
}

function frameOpening(parent, wall, opening, clip) {
  const { start, width, height, sill, type } = opening;
  const end = start + width;
  const top = Math.min(sill + height, clip);
  if (top <= sill) return;
  const clear = type === 'window' || type === 'slide' || type === 'entry';
  const frame = clear || wall.exterior ? mats.frame : mats.wood;
  const fw = type === 'slide' ? 0.059 : 0.047;
  const thickness = type === 'window' ? 0.082 : 0.104;
  if (wall.exterior) {
    const edge = wall.thickness + 0.029;
    axisBox(parent, mats.trim, wall, start - 0.065, start, sill, top, edge);
    axisBox(parent, mats.trim, wall, end, end + 0.065, sill, top, edge);
    if (top === sill + height) axisBox(parent, mats.trim, wall, start - 0.065, end + 0.065, top, top + 0.058, edge);
    if (sill > 0) axisBox(parent, mats.sill, wall, start - 0.064, end + 0.064, sill - 0.049, sill + 0.002, edge + 0.09);
  }
  axisBox(parent, frame, wall, start, start + fw, sill, top, thickness);
  axisBox(parent, frame, wall, end - fw, end, sill, top, thickness);
  if (top === sill + height) axisBox(parent, frame, wall, start, end, top - fw, top, thickness);
  if (clear) {
    axisBox(parent, frame, wall, start, end, sill, sill + fw, thickness);
    if (width > 1.2) {
      const middle = start + width / 2;
      axisBox(parent, frame, wall, middle - fw / 3, middle + fw / 3, sill, top, thickness);
    }
    if (type === 'window' && width > 1.2 && top - sill > 1.1) {
      axisBox(parent, frame, wall, start, end, sill + 1.03, sill + 1.066, thickness);
    }
    const glass = axisBox(parent, mats.window, wall, start + fw, end - fw, sill + fw, top - 0.014, 0.021);
    if (glass) glass.castShadow = false;
  } else if (type === 'door' && sill === 0 && clip < 2) {
    // The cut view keeps the door swing and the passage readable.
    const alongX = wall.axis === 'x';
    const length = width - 0.08;
    const panel = box(parent, mats.wood, alongX ? start + 0.045 : wall.position + length / 2,
      Math.min(top, 0.78) / 2, alongX ? wall.position + length / 2 : start + 0.045,
      alongX ? 0.042 : length, Math.min(top, 0.78), alongX ? length : 0.042);
    panel.castShadow = false;
  }
}

function walls(parent, floor, cut) {
  const slice = cut ? 0.95 : Infinity;
  for (const wall of floor.walls) {
    const { start, end, height, openings, thickness, exterior } = wall;
    const ridge = height === 'gable' ? mainMid : height === 'cross' ? crossMid : null;
    const roofShape = height === 'gable' ? mainHeight : crossHeight;
    const shapeTop = u => ridge === null ? (height ?? floor.height) : roofShape(u) - upperElevation;
    const top = u => Math.min(slice, shapeTop(u));
    const material = cut ? mats.wallCut : exterior ? mats.plaster : mats.wall;
    const ends = [start, end, ...openings.flatMap(({ start, width }) => [start, start + width])];
    if (ridge !== null && start < ridge && ridge < end) ends.push(ridge);
    ends.sort((a, b) => a - b);
    for (let i = 1; i < ends.length; i++) {
      const a = ends[i - 1], b = ends[i];
      const opening = openings.find(o => (a + b) / 2 > o.start && (a + b) / 2 < o.start + o.width);
      const strips = opening ? [[0, opening.sill], [opening.sill + opening.height, Infinity]] : [[0, Infinity]];
      for (const [lo, hi] of strips) wallPanel(parent, wall, material, a, b, lo, Math.min(top(a), hi), Math.min(top(b), hi));
      if (exterior && !cut) {
        const accents = floor.elevation === 0 ? [0.38, 0.434, 1.17, 1.225, 2, 2.05, 2.82] : [0.34, 0.39, 1.18, 1.24, 2.1];
        for (const y of accents) {
          if (y >= Math.min(top(a), top(b)) || (opening && y >= opening.sill && y <= opening.sill + opening.height)) continue;
          axisBox(parent, mats.trim, wall, a, b, y, y + 0.014, thickness + 0.004);
        }
        if (!floor.elevation && (!opening || opening.sill > 0.2)) {
          axisBox(parent, mats.footer, wall, a, b, 0.002, 0.18, thickness + 0.008);
        }
      }
    }
    openings.forEach(opening => frameOpening(parent, wall, opening, slice));
  }
}

function balcony(parent, cut) {
  const y = cut ? 0.52 : 1.04;
  for (const [axis, pos, a, b] of [['x', 9.9, 3.5, 8.3], ['z', 3.5, 7.9, 9.9], ['z', 8.3, 7.9, 9.9]]) {
    const rail = { axis, position: pos };
    axisBox(parent, mats.frame, rail, a, b, y, y + 0.042, 0.052);
    axisBox(parent, mats.sill, rail, a, b, 0.01, 0.085, 0.095);
    const count = Math.ceil((b - a) / 0.96);
    for (let i = 0; i <= count; i++) {
      const m = a + (b - a) * i / count;
      axisBox(parent, mats.steel, rail, m - 0.018, m + 0.018, 0.075, y, 0.035);
    }
    const glazing = axisBox(parent, mats.window, rail, a, b, 0.085, y, 0.021);
    glazing.castShadow = false;
  }
}

function stairs(parent) {
  const top = group(parent, '西侧室外木梯');
  const step = 0.25, rise = 3.45 / 18, bottom = -0.15;
  for (let i = 0; i < 17; i++) {
    const elevation = bottom + (i + 1) * rise;
    const depth = i < 2 ? elevation - bottom : 0.067;
    box(top, i < 2 ? mats.cement : mats.timber, -0.61, elevation - depth / 2, 7.85 - step * i, 1.02, depth, step + 0.012);
    if (i >= 2) box(top, mats.wood, -0.61, elevation + 0.003, 7.85 - step * i, 1.01, 0.011, step + 0.013);
  }
  for (const x of [-1.095, -0.13]) beam(top, mats.oak, [x, 0.22, 7.63], [x, 3.17, 3.54], 0.098, 0.19);
  box(top, mats.cement, -0.6, 3.21, 3.015, 1.17, 0.18, 1.2);
}

function floorSlabs(parent, id) {
  const shape = id === 'ground'
    ? [[-0.1, -0.1], [11.9, -0.1], [11.9, 9.1], [8.2, 9.1], [8.2, 7.9], [3.6, 7.9], [3.6, 9.1], [-0.1, 9.1]]
    : [[-0.1, -0.1], [11.9, -0.1], [11.9, 9.1], [8.4, 9.1], [8.4, 10], [3.4, 10], [3.4, 9.1], [-0.1, 9.1]];
  plate(parent, mats.tile, shape, 0, id === 'ground' ? 0.18 : 0.22);
  for (const room of floors[id].rooms) {
    const [x1, z1, x2, z2] = room.bounds;
    box(parent, mats[room.finish], (x1 + x2) / 2, 0.006, (z1 + z2) / 2, x2 - x1, 0.012, z2 - z1);
  }
  if (id === 'ground') {
    box(parent, mats.cement, 5.9, -0.105, 8.9, 5.0, 0.17, 2.2);
    box(parent, mats.stone, 5.9, -0.125, 10.085, 4.96, 0.114, 0.18);
    box(parent, mats.cement, 7.58, -0.084, -0.37, 1.55, 0.128, 0.62);
    box(parent, mats.stone, 7.58, -0.173, -0.78, 1.53, 0.126, 0.28);
  } else {
    box(parent, mats.trim, 5.9, -0.11, 9.885, 5.01, 0.24, 0.23);
  }
}

function roofSheet(parent, axis, start, end, low, high, height, trim = true) {
  const across = (at, u, y) => axis === 'x' ? [at, y, u] : [u, y, at];
  const rows = Math.ceil(Math.abs(high - low) / 0.31);
  const columns = Math.ceil((end - start) / 0.263);
  const subdivisions = 5;
  const data = [], colors = [], indices = [];
  const tones = ['#2b3034', '#31363a', '#393d41', '#303337', '#34383b'].map(color => new THREE.Color(color));
  for (let row = 0; row < rows; row++) {
    const bottom = THREE.MathUtils.lerp(low, high, row / rows);
    const top = THREE.MathUtils.lerp(low, high, (row + 1) / rows);
    const first = data.length / 3;
    const length = columns * subdivisions;
    for (let col = 0; col <= length; col++) {
      const at = THREE.MathUtils.lerp(start, end, col / length);
      const wave = (1 - Math.cos(2 * Math.PI * col / subdivisions)) * 0.020;
      const tone = tones[(Math.floor(col / subdivisions) * 7 + row * 3 + ((row ^ col) % 2)) % tones.length];
      for (const [u, raise] of [[bottom, 0.039], [top, 0.017]]) {
        data.push(...across(at, u, height(u) + wave + raise));
        colors.push(tone.r, tone.g, tone.b);
      }
      if (col > 0) {
        const i = first + col * 2;
        indices.push(i - 2, i, i - 1, i, i + 1, i - 1);
        if (row > 0) {
          const previous = i - 2 * (length + 1) + 1;
          indices.push(i - 2, previous - 2, i, i, previous - 2, previous);
        }
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(data, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  addMesh(parent, geometry, mats.roof);
  const width = Math.abs(high - low);
  const span = Math.hypot(width, height(high) - height(low));
  const slant = Math.atan2(height(high) - height(low), high - low);
  const middle = (low + high) / 2;
  const [x, y, z] = across((start + end) / 2, middle, height(middle) - 0.061);
  const boards = box(parent, mats.timber, x, y, z, axis === 'x' ? end - start : span, 0.095, axis === 'x' ? span : end - start);
  if (axis === 'x') boards.rotation.x = -slant;
  else boards.rotation.z = slant;
  if (!trim) return;
  for (const at of [start, end]) {
    beam(parent, mats.timber, across(at, low, height(low) - 0.11), across(at, high, height(high) - 0.11), 0.095, 0.14);
  }
  beam(parent, mats.roofEdge, across(start, low, height(low) + 0.015), across(end, low, height(low) + 0.015), 0.13, 0.08);
  for (let at = start + 0.25; at < end - 0.1; at += 0.59) {
    const inside = low + Math.sign(high - low) * 0.62;
    beam(parent, mats.oak, across(at, low + Math.sign(high - low) * 0.082, height(low) - 0.14), across(at, inside, height(inside) - 0.14), 0.074, 0.098);
  }
}

function makeRoof(parent) {
  // The wing eaves stop at the central bay. The valley sheets start behind the
  // central facade so the south balcony and the gable door remain exposed.
  for (const side of [-0.58, 9.58]) {
    roofSheet(parent, 'x', -0.57, 3.54, side, mainMid, mainHeight);
    roofSheet(parent, 'x', 8.26, 12.37, side, mainMid, mainHeight);
  }
  roofSheet(parent, 'x', 3.54, 8.26, 0.08, mainMid, mainHeight, false);
  roofSheet(parent, 'x', 3.54, 8.26, 7.72, mainMid, mainHeight, false);
  roofSheet(parent, 'z', -0.56, 8.39, 2.92, crossMid, crossHeight);
  roofSheet(parent, 'z', -0.56, 8.39, 8.88, crossMid, crossHeight);
  beam(parent, mats.roofEdge, [-0.61, roof.mainRidge + 0.047, mainMid], [12.41, roof.mainRidge + 0.047, mainMid], 0.157, 0.105);
  beam(parent, mats.roofEdge, [crossMid, roof.crossRidge + 0.047, -0.61], [crossMid, roof.crossRidge + 0.047, 8.43], 0.15, 0.105);

  // The upper faces of the central dormer meet the two lower roof slopes.
  const join = (roof.crossEave - roof.mainEave) / mainSlope;
  for (const x of [3.5, 8.3]) {
    const face = { axis: 'z', position: x, thickness: 0.18 };
    const fill = group(parent, '十字屋面侧封板');
    fill.position.y = roof.crossEave;
    fill.scale.y = -1;
    const a = 0.1, b = 7.8;
    wallPanel(fill, face, mats.plaster, a, join, 0, roof.crossEave - mainHeight(a) + 0.01, 0);
    wallPanel(fill, face, mats.plaster, 9 - join, b, 0, 0, roof.crossEave - mainHeight(b) + 0.01);
  }
}

export function buildModel() {
  const root = new THREE.Group();
  root.name = '樟坑别墅';
  const building = {};
  const furniture = new Map();
  for (const [id, floor] of Object.entries(floors)) {
    const layer = group(root, floor.label, 0, floor.elevation, 0);
    const full = group(layer, '完整墙体');
    const cut = group(layer, '剖切墙体');
    const contents = group(layer, '家具与固定设施');
    floorSlabs(layer, id);
    walls(full, floor, false);
    walls(cut, floor, true);
    if (id === 'upper') { balcony(full, false); balcony(cut, true); }
    if (id === 'ground') stairs(layer);
    for (const [itemId, object] of buildFurniture(contents, id)) furniture.set(itemId, object);
    cut.visible = false;
    building[id] = { layer, full, cut, contents };
  }
  const roofGroup = group(root, '深色十字坡屋顶');
  makeRoof(roofGroup);
  return { root, building, roof: roofGroup, furniture, ...buildGarden(root) };
}
