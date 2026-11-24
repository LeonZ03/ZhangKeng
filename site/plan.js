// x goes east, z goes south. Every length is in metres. Ground floor finish is ±0.000.
export const axes = { x: [0, 3.5, 8.3, 11.8], z: [0, 2.1, 3.6, 5.2, 7.8, 9, 9.9] };
export const footprint = { west: -0.1, east: 11.9, north: -0.1, south: 9.1 };
export const upperElevation = 3.3;
export const yard = { west: -3.86, east: 13.66, north: -6.36, south: 11.86, radius: 1 };
export const roof = { mainEave: 4.65, mainRidge: 7.02, crossEave: 5.72, crossRidge: 7.72 };

const windowAt = (start, width, sill, height) => ({ start, width, sill, height, type: 'window' });
const doorAt = (start, width, height, type = 'door') => ({ start, width, sill: 0, height, type });
const wall = (axis, position, start, end, openings = [], exterior = false, height, thickness = exterior ? 0.2 : 0.15) =>
  ({ axis, position, start, end, openings, exterior, height, thickness });

export const floors = {
  ground: {
    tag: '1F', label: '一层', elevation: 0, height: 3.12, size: [11.8, 9.9],
    summary: '客餐厅、厨房、三间卧室、两间卫浴',
    rooms: [
      { name: '西北卧室', bounds: [0.1, 0.1, 3.4, 3.51], finish: 'wood' },
      { name: '西南卧室', bounds: [0.1, 5.28, 3.4, 8.9], finish: 'wood' },
      { name: '东南卧室', bounds: [8.4, 5.28, 11.7, 8.9], finish: 'wood' },
      { name: '餐厅', bounds: [3.6, 0.1, 8.2, 3.6], finish: 'tile' },
      { name: '客厅', bounds: [3.6, 3.6, 8.2, 7.7], finish: 'tile' },
      { name: '厨房', bounds: [8.4, 0.1, 11.7, 2.02], finish: 'stone' },
      { name: '储藏间', bounds: [9.49, 2.18, 11.7, 3.52], finish: 'stone' },
      { name: '西侧卫生间', bounds: [0.1, 3.68, 2.35, 5.12], finish: 'bath' },
      { name: '东侧卫生间', bounds: [9.58, 3.68, 11.7, 5.12], finish: 'bath' },
    ],
    walls: [
      wall('x', 0, -0.1, 11.9, [windowAt(0.75, 2, 0.55, 2), windowAt(4.1, 2, 0.55, 2), doorAt(7.05, 1.05, 2.3), windowAt(9.05, 2, 0.55, 2)], true),
      wall('z', 0, 0.1, 8.9, [windowAt(4.05, 0.7, 0.55, 2)], true),
      wall('z', 11.8, 0.1, 8.9, [windowAt(4.05, 0.7, 0.55, 2)], true),
      wall('x', 9, -0.1, 3.6, [windowAt(0.75, 2, 0.35, 2.2)], true),
      wall('x', 9, 8.2, 11.9, [windowAt(9.05, 2, 0.35, 2.2)], true),
      wall('x', 7.8, 3.6, 8.2, [doorAt(4.1, 1.5, 2.4, 'entry'), windowAt(5.9, 1.8, 0.35, 2.2)], true),
      wall('z', 3.5, 0.1, 3.6, [], false, 3.12, 0.2),
      wall('z', 3.5, 5.2, 7.8, [], false, 3.12, 0.2),
      wall('z', 3.5, 7.8, 8.9, [], true),
      wall('z', 8.3, 0.1, 2.1, [doorAt(1.1, 0.9, 2.3)], false, 3.12, 0.2),
      wall('z', 8.3, 3.6, 7.8, [], false, 3.12, 0.2),
      wall('z', 8.3, 7.8, 8.9, [], true),
      wall('x', 3.6, 0.1, 3.4, [doorAt(2.45, 0.9, 2.3)]),
      wall('x', 5.2, 0.1, 3.4, [doorAt(2.45, 0.9, 2.3)]),
      wall('z', 2.4, 3.68, 5.12, [doorAt(4.4, 0.7, 2.3)]),
      wall('x', 2.1, 8.4, 11.7),
      wall('z', 9.45, 2.18, 3.52, [doorAt(2.3, 0.8, 2.3)]),
      wall('x', 3.6, 8.4, 11.7, [doorAt(8.45, 0.9, 2.3)]),
      wall('z', 9.5, 3.68, 5.12, [doorAt(4.4, 0.7, 2.3)]),
      wall('x', 5.2, 9.5, 11.7),
    ],
  },
  upper: {
    tag: '2F', label: '二层', elevation: upperElevation, height: 2.64, size: [11.8, 10],
    summary: '茶室、卧室、儿童娱乐区、书房兼卧室、卫浴、南阳台和北晾台',
    rooms: [
      { name: '茶室', bounds: [3.6, 2.2, 8.2, 7.7], finish: 'wood' },
      { name: '卧室', bounds: [0.1, 5.28, 3.4, 8.9], finish: 'wood' },
      { name: '卫生间', bounds: [0.1, 3.68, 2.35, 5.12], finish: 'bath' },
      { name: '北晾台', bounds: [3.6, 0.1, 8.2, 2.0], finish: 'stone' },
      { name: '南阳台', bounds: [3.6, 7.9, 8.2, 9.89], finish: 'stone' },
      { name: '儿童娱乐区', bounds: [0.1, 0.1, 3.4, 3.52], finish: 'tile', planned: true },
      { name: '书房兼卧室', bounds: [8.4, 0.1, 11.7, 8.9], finish: 'tile', planned: true },
    ],
    walls: [
      wall('x', 0, -0.1, 3.5, [], true, 1.35),
      wall('x', 0, 3.5, 8.3, [windowAt(4.9, 2, 0.52, 2)], true, 'cross'),
      wall('x', 0, 8.3, 11.9, [], true, 1.35),
      wall('z', 0, 0.1, 8.9, [doorAt(2.55, 0.9, 2.3, 'entry'), windowAt(4.05, 0.7, 0.76, 1.4), windowAt(5.65, 0.7, 0.76, 1.2)], true, 'gable'),
      wall('z', 11.8, 0.1, 8.9, [windowAt(3.7, 2, 0.8, 2)], true, 'gable'),
      wall('x', 9, -0.1, 3.5, [], true, 1.35),
      wall('x', 9, 8.3, 11.9, [], true, 1.35),
      wall('x', 7.8, 3.5, 8.3, [doorAt(4.65, 2.5, 2.7, 'slide')], true, 'cross'),
      wall('z', 3.5, 0.1, 2.1, [], false, 2.45, 0.2),
      wall('x', 2.1, 3.6, 8.2, [doorAt(7.1, 1, 2.1)], false, 2.45, 0.2),
      wall('z', 3.5, 3.6, 7.8, [], false, 2.45, 0.2),
      wall('z', 8.3, 0.1, 7.8, [doorAt(2.3, 0.9, 2.3)], false, 2.45, 0.2),
      wall('x', 3.6, 0.1, 2.4, [], false, 2.45),
      wall('z', 2.4, 3.68, 5.12, [doorAt(4.4, 0.7, 2.1)], false, 2.45),
      wall('x', 5.2, 0.1, 3.4, [doorAt(2.45, 0.9, 2.3)], false, 2.45),
    ],
  },
};

// Footprints of drawn furniture were scaled from the 1:50 sheets where dimensions are absent.
// x and z are centres before rotation. Footprints include seating where supplied as a set.
export const furnishings = [
  { id: 'bed-nw', floor: 'ground', room: '西北卧室', name: '双人床', type: 'bed', x: 1.12, z: 1.44, w: 1.52, d: 2, angle: 90 },
  { id: 'bed-sw', floor: 'ground', room: '西南卧室', name: '双人床', type: 'bed', x: 1.14, z: 7.5, w: 1.8, d: 2.04, angle: 90 },
  { id: 'bed-se', floor: 'ground', room: '东南卧室', name: '双人床', type: 'bed', x: 10.68, z: 7.5, w: 1.8, d: 2.04, angle: -90 },
  { id: 'wardrobe-nw', floor: 'ground', room: '西北卧室', name: '衣柜', type: 'wardrobe', x: 1.15, z: 3.22, w: 2.1, d: 0.56, angle: 180 },
  { id: 'wardrobe-sw', floor: 'ground', room: '西南卧室', name: '衣柜', type: 'wardrobe', x: 1.15, z: 5.53, w: 2.1, d: 0.53, angle: 0 },
  { id: 'wardrobe-se', floor: 'ground', room: '东南卧室', name: '衣柜', type: 'wardrobe', x: 10.65, z: 5.53, w: 2.1, d: 0.53, angle: 0 },
  { id: 'dining', floor: 'ground', room: '餐厅', name: '八人餐桌组', type: 'dining', x: 5.24, z: 1.75, w: 1.85, d: 2.8, angle: 0, tabletop: [1, 2] },
  { id: 'sofa-long', floor: 'ground', room: '客厅', name: '三人沙发', type: 'sofa', x: 7.72, z: 5.63, w: 2.23, d: 0.78, angle: -90 },
  { id: 'sofa-short', floor: 'ground', room: '客厅', name: '双人沙发', type: 'sofa', x: 6.47, z: 7.2, w: 1.58, d: 0.78, angle: 180 },
  { id: 'sofa-chair', floor: 'ground', room: '客厅', name: '单人沙发', type: 'sofa', x: 6.65, z: 3.99, w: 0.86, d: 1.22, angle: 0 },
  { id: 'coffee', floor: 'ground', room: '客厅', name: '茶几', type: 'coffee', x: 6.65, z: 5.63, w: 0.63, d: 1.28, angle: 0 },
  { id: 'tea', floor: 'upper', room: '茶室', name: '茶桌与五把座椅', type: 'tea', x: 6.76, z: 5.63, w: 2.43, d: 3.64, angle: 0, tabletop: [1.1, 2.92] },
  { id: 'bed-up', floor: 'upper', room: '卧室', name: '双人床', type: 'bed', x: 1.16, z: 7.1, w: 1.8, d: 2, angle: 90 },
  // Proposed placements for the two spaces left blank in the drawings.
  { id: 'play-mat', floor: 'upper', room: '儿童娱乐区', name: '软垫与玩具', type: 'play-mat', x: 1.77, z: 1.38, w: 1.85, d: 1.48, angle: 0 },
  { id: 'play-storage', floor: 'upper', room: '儿童娱乐区', name: '玩具收纳柜', type: 'shelf', x: 1.79, z: 0.35, w: 1.56, d: 0.4, h: 0.64, shelves: 2, bins: true, angle: 0 },
  { id: 'study-desk', floor: 'upper', room: '书房兼卧室', name: '书桌与座椅', type: 'desk', x: 11.0, z: 4.69, w: 1.5, d: 1.27, deskDepth: 0.62, angle: -90 },
  { id: 'study-shelf', floor: 'upper', room: '书房兼卧室', name: '书柜', type: 'shelf', x: 8.63, z: 4.78, w: 1.36, d: 0.37, h: 1.4, shelves: 3, angle: 90 },
  { id: 'study-bed', floor: 'upper', room: '书房兼卧室', name: '单人床', type: 'bed', x: 10.58, z: 7.74, w: 1.2, d: 2.04, angle: 180 },
];

export const baths = [
  { floor: 'ground', x: 0.5, z: 3.72, direction: 1 },
  { floor: 'ground', x: 11.34, z: 3.72, direction: -1 },
  { floor: 'upper', x: 0.5, z: 3.72, direction: 1 },
];
