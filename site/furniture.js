import { baths, furnishings } from './plan.js';
import { box, cushion, group, mats, plant, post, round } from './geometry.js';

function bed(node, { w, d }) {
  box(node, mats.oak, 0, 0.17, 0, w, 0.26, d);
  cushion(node, mats.linen, 0, 0.37, 0.024, w - 0.06, 0.19, d - 0.09);
  cushion(node, mats.wood, 0, 0.53, -d / 2 + 0.044, w, 0.61, 0.09);
  cushion(node, mats.cloth, 0, 0.49, 0.18, w - 0.04, 0.105, d - 0.42);
  cushion(node, mats.accent, 0, 0.55, d * 0.29, w - 0.02, 0.063, d * 0.35);
  for (const x of w < 1.35 ? [0] : [-w / 4, w / 4]) {
    cushion(node, mats.ceramic, x, 0.51, -d / 2 + 0.31, w * 0.4, 0.145, 0.39, 0.07).rotation.y = Math.sign(x) * 0.035;
  }
}

function wardrobe(node, { w, d }) {
  box(node, mats.oak, 0, 1.08, 0, w, 2.16, d);
  for (let i = 0; i < 4; i++) {
    const x = (i - 1.5) * w / 4;
    box(node, mats.wood, x, 1.12, d / 2 + 0.012, w / 4 - 0.009, 2.05, 0.025);
    box(node, mats.frame, x + w / 13, 1.13, d / 2 + 0.032, 0.018, 0.17, 0.022);
  }
}

function sofa(node, { w, d }) {
  cushion(node, mats.sofa, 0, 0.24, 0, w, 0.31, d, 0.065);
  cushion(node, mats.sofa, 0, 0.62, -d / 2 + 0.11, w, 0.41, 0.21, 0.058);
  for (const side of [-1, 1]) {
    cushion(node, mats.sofa, side * (w / 2 - 0.072), 0.51, 0.03, 0.145, 0.29, d - 0.05);
    for (const z of [-d * 0.35, d * 0.35]) box(node, mats.oak, side * w * 0.39, 0.075, z, 0.065, 0.15, 0.065);
  }
  const seats = Math.max(1, Math.round(w / 0.76));
  const span = (w - 0.30) / seats;
  for (let i = 0; i < seats; i++) {
    const x = span * (i - (seats - 1) / 2);
    cushion(node, mats.linen, x, 0.411, 0.058, span - 0.014, 0.126, d - 0.24);
    cushion(node, i % 2 ? mats.pillow : mats.accent, x, 0.624, -d / 2 + 0.245, span * 0.73, 0.32, 0.13).rotation.x = -0.17;
  }
}

function massageChair(node, { w, d, h }) {
  cushion(node, mats.frame, 0, 0.095, -0.07, w * 0.89, 0.19, d * 0.65, 0.07);
  cushion(node, mats.frame, 0, 0.31, -0.084, w * 0.9, 0.34, d * 0.68, 0.12);
  cushion(node, mats.frame, 0, h - 0.398, -0.33, w * 0.79, 0.77, 0.24, 0.112).rotation.x = -0.39;
  cushion(node, mats.stairRail, 0, 0.484, -0.07, w * 0.66, 0.112, 0.56, 0.052);
  cushion(node, mats.stairRail, 0, 0.789, -0.222, 0.43, 0.50, 0.123, 0.06).rotation.x = -0.39;
  cushion(node, mats.stairRail, 0, 1.004, -0.37, 0.31, 0.165, 0.105, 0.047).rotation.x = -0.39;
  for (const side of [-1, 1]) {
    cushion(node, mats.frame, side * (w / 2 - 0.075), 0.475, -0.046, 0.15, 0.36, 0.84, 0.069);
    cushion(node, mats.frame, side * 0.148, 0.25, 0.53, 0.276, 0.42, 0.258, 0.07).rotation.x = -0.38;
    cushion(node, mats.stairRail, side * 0.148, 0.112, 0.648, 0.263, 0.166, 0.21, 0.061);
  }
  cushion(node, mats.steel, 0.30, 0.656, 0.242, 0.078, 0.023, 0.106, 0.011);
}

export function chair(parent, x, z, angle = 0, upholstered = false) {
  const node = group(parent, '座椅', x, 0, z);
  node.rotation.y = angle;
  for (const x of [-0.17, 0.17]) {
    for (const z of [-0.15, 0.15]) box(node, mats.oak, x, 0.216, z, 0.044, 0.432, 0.044);
    box(node, mats.oak, x, 0.66, -0.175, 0.04, 0.45, 0.04);
  }
  cushion(node, upholstered ? mats.accent : mats.sofa, 0, 0.445, 0, 0.425, 0.075, 0.425);
  cushion(node, upholstered ? mats.accent : mats.oak, 0, 0.777, -0.178, 0.41, 0.205, 0.046);
  return node;
}

function table(node, w, d, height, material = mats.wood) {
  cushion(node, material, 0, height - 0.03, 0, w, 0.06, d, 0.02);
  for (const x of [-w / 2 + 0.12, w / 2 - 0.12]) {
    for (const z of [-d / 2 + 0.12, d / 2 - 0.12]) box(node, mats.oak, x, height / 2 - 0.02, z, 0.075, height - 0.04, 0.075);
  }
}

function dining(node, item, tea = false) {
  const [w, d] = item.tabletop;
  table(node, w, d, 0.755, tea ? mats.oak : mats.wood);
  chair(node, 0, -d / 2 - 0.18, 0, tea);
  for (const z of [-d * 0.32, 0, d * 0.32]) chair(node, -w / 2 - 0.2, z, Math.PI / 2, tea);
  if (tea) {
    chair(node, w / 2 + 0.28, 0, -Math.PI / 2, true);
    box(node, mats.wood, 0, 0.77, -0.2, 0.34, 0.035, 0.69);
    round(node, mats.ceramic, 0, 0.845, -0.3, 0.095, 0.07, 0.095);
    for (const x of [-0.107, 0.107]) post(node, mats.ceramic, x, 0.811, 0.01, 0.043, 0.035);
  } else {
    chair(node, 0, d / 2 + 0.18, Math.PI);
    for (const z of [-d * 0.32, 0, d * 0.32]) chair(node, w / 2 + 0.2, z, -Math.PI / 2);
    for (const x of [-0.3, 0.3]) {
      for (const z of [-0.65, 0, 0.65]) post(node, mats.ceramic, x, 0.768, z, 0.111, 0.016);
    }
  }
}

function playMat(node, { w, d }) {
  cushion(node, mats.linen, 0, 0.012, 0, w, 0.024, d, 0.008);
  const colors = [mats.accent, mats.linen, mats.sofa];
  for (let row = 0; row < 2; row++) {
    for (let col = 0; col < 3; col++) {
      cushion(node, colors[(row + col) % colors.length], (col - 1) * w / 3, 0.029, (row - 0.5) * d / 2,
        w / 3 - 0.008, 0.02, d / 2 - 0.008, 0.007);
    }
  }
  cushion(node, mats.pillow, -0.57, 0.099, -0.41, 0.4, 0.12, 0.35, 0.05);
  for (const [x, z, color] of [[0.39, -0.25, mats.wood], [0.58, -0.21, mats.pillow], [0.43, 0.03, mats.accent]]) {
    cushion(node, color, x, 0.097, z, 0.14, 0.12, 0.14, 0.009);
  }
}

function shelf(node, { w, d, h, shelves, bins }) {
  const board = 0.024;
  const level = (h - board) / shelves;
  box(node, mats.wood, 0, h / 2, -d / 2 + board / 2, w, h, board);
  for (const x of [-w / 2 + board / 2, 0, w / 2 - board / 2]) {
    box(node, mats.oak, x, h / 2, board / 2, board, h, d - board);
  }
  for (let row = 0; row <= shelves; row++) {
    box(node, mats.wood, 0, board / 2 + row * level, board / 2, w - board * 2, board, d - board);
    if (row === shelves) break;
    for (const x of [-w / 4, w / 4]) {
      if (bins) {
        cushion(node, x < 0 ? mats.sofa : mats.accent, x, board + row * level + 0.083, 0.01,
          w / 2 - 0.11, 0.16, d - 0.10, 0.016);
      } else if ((row + Number(x > 0)) % 3 === 1) {
        for (const [i, color] of [mats.linen, mats.pillow, mats.frame].entries()) {
          box(node, color, x + (i - 1) * 0.018, board + row * level + 0.028 * (i + 0.5), 0.027,
            0.26 - 0.019 * i, 0.028, 0.19 - 0.013 * i).rotation.y = (i - 1) * 0.069;
        }
      } else {
        const colors = x < 0 ? [mats.frame, mats.accent, mats.linen] : [mats.pillow, mats.linen, mats.oak, mats.accent];
        let offset = x - w * (row % 2 ? 0.05 : 0.15);
        for (const [i, color] of colors.entries()) {
          const height = 0.172 + ((i * 3 + row * 2) % 5) * 0.027;
          const thick = 0.024 + (i % 3) * 0.011;
          box(node, color, offset + thick / 2, board + row * level + height / 2, 0.009 + 0.016 * (i % 2),
            thick, height, 0.13 + 0.025 * (i % 3));
          offset += thick + 0.006;
        }
      }
    }
  }
}

function desk(node, { w, d, deskDepth }) {
  const desktop = group(node, '书桌', 0, 0, (deskDepth - d) / 2);
  table(desktop, w, deskDepth, 0.75);
  box(desktop, mats.frame, -0.11, 0.761, -0.02, 0.34, 0.021, 0.24);
  box(desktop, mats.linen, 0.47, 0.764, 0.045, 0.21, 0.028, 0.26);
  chair(node, 0, d / 2 - 0.29, Math.PI);
}

function lowCabinet(node, { w, d, h, doors }) {
  const plinth = 0.062, top = 0.028, panel = 0.021;
  const doorHeight = h - plinth - top - 0.012;
  box(node, mats.frame, 0, plinth / 2, -0.027, w - 0.06, plinth, d - 0.075);
  box(node, mats.oak, 0, (h + plinth - top) / 2, -panel / 2, w - 0.014, h - plinth - top, d - panel);
  box(node, mats.wood, 0, h - top / 2, 0, w, top, d);
  for (let i = 0; i < doors; i++) {
    const width = w / doors;
    const x = width * (i + 0.5) - w / 2;
    box(node, mats.wood, x, plinth + doorHeight / 2 + 0.006, (d - panel) / 2, width - 0.009, doorHeight, panel);
    box(node, mats.frame, x, h - 0.105, d / 2 + 0.005, 0.112, 0.014, 0.012);
  }
}

const models = {
  bed, wardrobe, sofa, dining, shelf, desk, 'play-mat': playMat, 'low-cabinet': lowCabinet, 'massage-chair': massageChair,
  tea: (node, item) => dining(node, item, true),
  coffee: (node, { w, d }) => {
    table(node, w, d, 0.35, mats.oak);
    box(node, mats.linen, 0.09, 0.368, -0.27, 0.2, 0.032, 0.26);
    post(node, mats.ceramic, 0, 0.39, 0.26, 0.103, 0.06);
  },
};

function bath(parent, { x, z, direction }) {
  const node = group(parent, '卫浴洁具', x, 0, z);
  node.scale.x = direction;
  box(node, mats.bath, 0.03, 0.022, 0.35, 0.72, 0.044, 0.69);
  post(node, mats.steel, 0.04, 0.98, 0.075, 0.017, 1.92);
  post(node, mats.steel, 0.04, 1.96, 0.18, 0.114, 0.033);
  box(node, mats.ceramic, 0.67, 0.46, 0.18, 0.39, 0.65, 0.2);
  round(node, mats.ceramic, 0.67, 0.32, 0.43, 0.208, 0.27, 0.288);
  round(node, mats.bath, 0.67, 0.567, 0.464, 0.141, 0.025, 0.192);
  box(node, mats.oak, 1.43, 0.43, 0.28, 0.69, 0.77, 0.54);
  box(node, mats.stone, 1.43, 0.826, 0.28, 0.74, 0.065, 0.59);
  round(node, mats.ceramic, 1.43, 0.861, 0.31, 0.25, 0.073, 0.177);
  post(node, mats.steel, 1.43, 0.927, 0.102, 0.018, 0.141);
}

function kitchen(parent) {
  const node = group(parent, '厨房和储藏');
  box(node, mats.wood, 10.08, 0.449, 0.405, 3.33, 0.897, 0.61);
  box(node, mats.stone, 10.08, 0.916, 0.405, 3.33, 0.061, 0.634);
  box(node, mats.wood, 11.41, 0.449, 1.35, 0.57, 0.897, 1.28);
  box(node, mats.stone, 11.41, 0.916, 1.35, 0.61, 0.061, 1.28);
  for (let x = 8.69; x < 11.3; x += 0.52) box(node, mats.oak, x, 0.46, 0.719, 0.5, 0.72, 0.026);
  for (const x of [9.79, 10.17]) {
    cushion(node, mats.steel, x, 0.951, 0.422, 0.335, 0.03, 0.37, 0.012);
    post(node, mats.frame, x, 0.971, 0.423, 0.028, 0.006);
  }
  post(node, mats.steel, 9.98, 1.055, 0.225, 0.017, 0.226);
  box(node, mats.frame, 11.405, 0.966, 1.34, 0.47, 0.035, 0.72);
  for (const z of [1.18, 1.51]) post(node, mats.steel, 11.405, 0.993, z, 0.126, 0.025);
  box(node, mats.ceramic, 8.75, 0.94, 0.436, 0.59, 1.88, 0.61);
}

function bedside(parent, x, z) {
  table(group(parent, '床头柜', x, 0, z), 0.46, 0.42, 0.45);
  post(parent, mats.timber, x, 0.548, z, 0.022, 0.21);
  round(parent, mats.cloth, x, 0.648, z, 0.106, 0.082, 0.106);
}

export function buildFurniture(layer, floor) {
  const movable = new Map();
  const fixtures = group(layer, '固定设施');
  for (const item of furnishings.filter(item => item.floor === floor)) {
    const node = group(layer, item.name, item.x, 0.018, item.z);
    node.rotation.y = item.angle * Math.PI / 180;
    node.userData.itemId = item.id;
    models[item.type](node, item);
    movable.set(item.id, node);
  }
  for (const fixture of baths.filter(fixture => fixture.floor === floor)) bath(fixtures, fixture);
  if (floor === 'ground') {
    kitchen(fixtures);
    for (const z of [0.39, 2.44, 6.35, 8.68]) bedside(fixtures, 0.4, z);
    for (const z of [6.35, 8.68]) bedside(fixtures, 11.39, z);
    bedside(fixtures, 7.72, 7.2);
    plant(fixtures, 7.68, 3.95, 0, 1.5);
  } else {
    bedside(fixtures, 0.41, 5.93);
    bedside(fixtures, 0.41, 8.29);
  }
  return movable;
}
