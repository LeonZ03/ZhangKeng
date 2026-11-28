import * as THREE from 'three';
import { furnishings, roof, yard } from './plan.js';

const clearance = 0.012;
const reach = 4;
const axes = ['x', 'y', 'z'];
const limits = {
  x: [yard.west - 2, yard.east + 2],
  y: [-0.55, roof.crossRidge + 3],
  z: [yard.north - 2, yard.south + 2],
};
const reports = {
  swing: ['已关上', '已打开'], slide: ['已关上', '已推开'],
  light: ['已关灯', '已开灯'], water: ['已关水', '正在出水'],
  burner: ['已熄火', '已点火'],
};
const vertical = new THREE.Vector3(0, 1, 0);

function makeWater(length) {
  const water = new THREE.Mesh(
    new THREE.CylinderGeometry(0.006, 0.004, length, 9),
    new THREE.MeshStandardMaterial({ color: 0xaad8df, roughness: 0.2, transparent: true, opacity: 0.68, depthWrite: false }),
  );
  water.name = '出水';
  water.position.y = -length / 2;
  return water;
}

function makeBurnerFlame(radius) {
  const flame = new THREE.Group();
  flame.name = '灶眼火焰';
  const jets = 18;
  const profile = [[0.5, -0.5], [1, -0.32], [0.8, -0.12], [0.42, 0.13], [0.12, 0.36], [0, 0.5]];
  const shape = new THREE.LatheGeometry(profile.map(([radius, y]) => new THREE.Vector2(radius, y)), 7);
  const points = shape.getAttribute('position');
  const colors = new Float32Array(points.count * 4);
  for (let i = 0; i < points.count; i++) {
    const alpha = Math.min(1, (0.5 - points.getY(i)) * 3.2);
    colors.set([1, 1, 1, alpha], i * 4);
  }
  shape.setAttribute('color', new THREE.BufferAttribute(colors, 4));
  const outer = new THREE.InstancedMesh(shape, new THREE.MeshBasicMaterial({
    color: 0x2c7bff, vertexColors: true, transparent: true, opacity: 0.70, depthWrite: false, toneMapped: false,
  }), jets);
  const core = new THREE.InstancedMesh(shape, new THREE.MeshBasicMaterial({
    color: 0xa2dfff, vertexColors: true, transparent: true, opacity: 0.91, depthWrite: false, toneMapped: false,
  }), jets);
  core.renderOrder = 1;
  const jet = new THREE.Object3D();
  const tilt = new THREE.Vector3();
  for (let i = 0; i < jets; i++) {
    const angle = i * 2 * Math.PI / jets;
    const x = Math.cos(angle), z = Math.sin(angle);
    const height = 0.047 + 0.011 * Math.sin(5 * angle + 0.6);
    jet.quaternion.setFromUnitVectors(vertical, tilt.set(0.26 * x, 1, 0.26 * z).normalize());
    jet.position.set((radius + 0.006) * x, height / 2, (radius + 0.006) * z);
    jet.scale.set(0.012, height, 0.012);
    jet.updateMatrix();
    outer.setMatrixAt(i, jet.matrix);
    jet.position.set((radius + 0.004) * x, height * 0.29, (radius + 0.004) * z);
    jet.scale.set(0.006, height * 0.58, 0.006);
    jet.updateMatrix();
    core.setMatrixAt(i, jet.matrix);
  }
  flame.add(outer, core);
  return flame;
}

export function createExploreScene(model, { announce, inspect }) {
  const ray = new THREE.Raycaster();
  const segment = new THREE.Box3();
  const endpoint = new THREE.Vector3();
  const direction = new THREE.Vector3();
  const localPoint = new THREE.Vector3();
  const localBounds = new THREE.Box3();
  const turn = new THREE.Quaternion();
  const hits = [];
  const targets = new Map();
  const motions = new Set();
  const litBurners = new Set();
  const surfaces = [];
  let flameTime = 0, flameFrame = -1;

  for (const info of furnishings) targets.set(model.furniture.get(info.id), { label: info.name, info });
  const nodes = [];
  model.root.traverse(node => {
    if (Object.hasOwn(reports, node.userData.exploreAction)) nodes.push(node);
  });
  for (const node of nodes) {
    const { exploreAction: action, exploreLabel: label, exploreAmount: amount } = node.userData;
    const item = { node, action, label, amount, value: 0, open: false, surfaces: [] };
    targets.set(node, item);
    if (action === 'swing' || action === 'burner') item.closed = node.quaternion.clone();
    if (action === 'slide') {
      item.closed = node.position.clone();
      item.travel = new THREE.Vector3(amount, 0, 0).applyQuaternion(node.quaternion);
    }
    if (action === 'light') {
      item.effect = new THREE.PointLight(0xffdfaa, 13, 2.6, 2);
      item.effect.name = '台灯光源';
      item.shades = [];
      node.traverse(mesh => {
        if (!mesh.isMesh || !mesh.material.emissive) return;
        mesh.material = mesh.material.clone();
        mesh.material.emissive.set(0xffc47e);
        mesh.material.emissiveIntensity = 0;
        item.shades.push(mesh.material);
      });
    }
    if (action === 'water') item.effect = makeWater(amount);
    if (action === 'burner') {
      item.effect = makeBurnerFlame(node.userData.exploreFlameRadius);
      const offset = new THREE.Vector3(...node.userData.exploreFlameOffset).applyQuaternion(item.closed);
      item.effect.position.addVectors(node.position, offset);
    }
    if (item.effect) {
      item.effect.visible = false;
      item.effect.userData.exploreEffect = true;
      // The flame sits over the burner while the knob turns on its own axis.
      const parent = action === 'burner' ? node.parent : node;
      parent.add(item.effect);
    }
  }

  function refresh() {
    surfaces.length = 0;
    for (const item of targets.values()) if (item.surfaces) item.surfaces.length = 0;
    model.root.updateWorldMatrix(true, true);
    function collect(node, inherited) {
      if (!node.visible || node.userData.exploreEffect) return;
      const item = targets.get(node) ?? inherited;
      if (node.isMesh) {
        const materials = Array.isArray(node.material) ? node.material : [node.material];
        if (materials.some(material => !material.transparent || material.opacity >= 0.25)) {
          if (!node.geometry.boundingBox) node.geometry.computeBoundingBox();
          const bounds = node.geometry.boundingBox.clone().applyMatrix4(node.matrixWorld);
          const surface = { mesh: node, bounds, item };
          surfaces.push(surface);
          item?.surfaces?.push(surface);
        }
      }
      for (const child of node.children) collect(child, item);
    }
    collect(model.root);
  }

  function firstHit(distance) {
    let closest;
    ray.near = 0.002;
    ray.far = distance;
    segment.setFromPoints([ray.ray.origin, ray.ray.at(distance, endpoint)]);
    for (const surface of surfaces) {
      if (!segment.intersectsBox(surface.bounds)) continue;
      hits.length = 0;
      surface.mesh.raycast(ray, hits);
      for (const hit of hits) {
        if (hit.distance >= ray.far) continue;
        ray.far = hit.distance;
        closest = { distance: hit.distance, item: surface.item };
      }
    }
    return closest;
  }

  function move(position, step) {
    let moved = false;
    for (const axis of axes) {
      const end = THREE.MathUtils.clamp(position[axis] + step[axis], ...limits[axis]);
      const distance = Math.abs(end - position[axis]);
      if (distance < 0.00001) continue;
      const sign = Math.sign(end - position[axis]);
      direction.set(0, 0, 0);
      direction[axis] = sign;
      ray.set(position, direction);
      const hit = firstHit(distance + clearance);
      const travel = hit ? Math.min(distance, Math.max(0, hit.distance - clearance)) : distance;
      position[axis] += sign * travel;
      moved ||= travel > 0;
    }
    return moved;
  }

  function pick(camera, pointer) {
    camera.updateMatrixWorld();
    ray.setFromCamera(pointer, camera);
    return firstHit(reach)?.item;
  }

  function interact(item) {
    if (!item.action) {
      const { room, name, w, d } = item.info;
      inspect(`${room} · ${name} · 占地 ${w.toFixed(2)} × ${d.toFixed(2)} m`);
      return;
    }
    item.open = !item.open;
    if (item.effect) {
      item.effect.visible = item.open;
      for (const shade of item.shades ?? []) shade.emissiveIntensity = item.open ? 0.8 : 0;
      if (item.action === 'burner') {
        apply(item, Number(item.open));
        if (item.open) litBurners.add(item);
        else litBurners.delete(item);
      }
    } else motions.add(item);
    announce(`${item.label} · ${reports[item.action][Number(item.open)]}`);
  }

  function apply(item, value) {
    const { node } = item;
    const amount = value * value * (3 - 2 * value);
    if (item.action === 'slide') node.position.copy(item.closed).addScaledVector(item.travel, amount);
    else node.quaternion.copy(item.closed).multiply(turn.setFromAxisAngle(vertical, item.amount * amount));
    node.updateWorldMatrix(true, true);
    for (const { mesh, bounds } of item.surfaces) bounds.copy(mesh.geometry.boundingBox).applyMatrix4(mesh.matrixWorld);
  }

  function step(dt, position, reducedMotion) {
    let changed = false;
    for (const item of motions) {
      const goal = Number(item.open);
      const next = reducedMotion || Math.abs(goal - item.value) <= dt * 2.5
        ? goal : item.value + Math.sign(goal - item.value) * dt * 2.5;
      apply(item, next);
      const blocked = item.surfaces.some(({ mesh, bounds }) => {
        if (!bounds.containsPoint(position)) return false;
        mesh.worldToLocal(localPoint.copy(position));
        return localBounds.copy(mesh.geometry.boundingBox).expandByScalar(clearance).containsPoint(localPoint);
      });
      if (blocked) {
        apply(item, item.value);
        item.open = !item.open;
        announce('请稍微离开门边');
      } else {
        item.value = next;
        changed = true;
        if (next === goal) motions.delete(item);
      }
    }
    const flickering = litBurners.size > 0 && !reducedMotion;
    let effectsChanged = false;
    if (flickering) {
      flameTime += dt;
      const frame = Math.floor(flameTime * 18);
      effectsChanged = frame !== flameFrame;
      if (effectsChanged) {
        flameFrame = frame;
        for (const item of litBurners) {
          item.effect.scale.y = 1 + 0.08 * Math.sin(flameTime * 21 + item.node.position.z * 11)
            + 0.035 * Math.sin(flameTime * 38);
        }
      }
    }
    return { changed, effectsChanged, moving: motions.size > 0 || flickering };
  }

  function finish() {
    for (const item of motions) {
      item.value = Number(item.open);
      apply(item, item.value);
    }
    motions.clear();
    for (const item of litBurners) {
      item.open = false;
      item.effect.visible = false;
      apply(item, 0);
    }
    litBurners.clear();
  }

  return { refresh, move, pick, interact, step, finish };
}
