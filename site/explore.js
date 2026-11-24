import * as THREE from 'three';
import { createExploreScene } from './explore-scene.js';

const movementKeys = new Map([
  ['KeyW', 'forward'], ['KeyS', 'back'], ['KeyA', 'left'], ['KeyD', 'right'],
  ['ArrowLeft', 'left'], ['ArrowRight', 'right'], ['ArrowUp', 'up'], ['ArrowDown', 'down'],
  ['ShiftLeft', 'faster'], ['ShiftRight', 'faster'],
]);

export function createExplorer({ canvas, stage, requestFrame, exit }) {
  const camera = new THREE.PerspectiveCamera(69, 1, 0.008, 90);
  camera.rotation.order = 'YXZ';
  const hud = document.getElementById('explore-hud');
  const reticle = document.getElementById('explore-reticle');
  const target = document.getElementById('explore-target');
  const notice = document.getElementById('explore-feedback');
  const moveButtons = [...hud.querySelectorAll('[data-fly]')];
  const inputs = new Map();
  const pointer = new THREE.Vector2();
  const center = new THREE.Vector2();
  const delta = new THREE.Vector3();
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let world, currentModel, drag, aim, feedbackTimer, lastFrame = 0, lastPick = -Infinity;
  let active = false, locked = false, wasDragged = false, cameraChanged = false, aimChanged = false;

  function ready() {
    return active && !document.hidden && !document.querySelector('dialog[open]');
  }

  function feedback(message) {
    clearTimeout(feedbackTimer);
    notice.textContent = message;
    notice.hidden = !message;
    if (message) feedbackTimer = setTimeout(() => { notice.hidden = true; }, 3200);
  }

  function showTarget(item) {
    const label = world.hint(item);
    if (target.textContent !== label) target.textContent = label;
    target.hidden = !label;
    canvas.classList.toggle('explore-pickable', Boolean(item));
    reticle.classList.toggle('aimed', Boolean(item));
  }

  function pointAt(x, y) {
    const rect = canvas.getBoundingClientRect();
    pointer.set((x - rect.left) / rect.width * 2 - 1, 1 - (y - rect.top) / rect.height * 2);
    return pointer;
  }

  function invalidateAim() {
    aimChanged = true;
    requestFrame();
  }

  function look(dx, dy, speed) {
    camera.rotation.y -= dx * speed;
    camera.rotation.x = THREE.MathUtils.clamp(camera.rotation.x - dy * speed, -1.52, 1.52);
    cameraChanged = true;
    invalidateAim();
  }

  function move(held, dt) {
    const forward = Number(held.has('forward')) - Number(held.has('back'));
    const side = Number(held.has('right')) - Number(held.has('left'));
    const rise = Number(held.has('up')) - Number(held.has('down'));
    const speed = held.has('faster') ? 2 : 1;
    const yaw = camera.rotation.y;
    const stride = dt * 1.65 * speed / Math.max(1, Math.hypot(forward, side));
    delta.set(
      (Math.cos(yaw) * side - Math.sin(yaw) * forward) * stride,
      rise * dt * 1.3 * speed,
      (-Math.sin(yaw) * side - Math.cos(yaw) * forward) * stride,
    );
    if (forward || side || rise) {
      const moved = world.move(camera.position, delta);
      cameraChanged ||= moved;
      return true;
    }
    return false;
  }

  function update(now) {
    if (!ready()) {
      lastFrame = 0;
      return { changed: false, moving: false, shadows: false };
    }
    const dt = lastFrame ? Math.min((now - lastFrame) / 1000, 0.09) : 1 / 60;
    const travelling = move(new Set(inputs.values()), dt);
    const motion = world.step(dt, camera.position, reducedMotion.matches);
    aimChanged ||= cameraChanged || motion.changed;
    if (aimChanged && now - lastPick > 65) {
      const rayPoint = locked ? center : aim ? pointAt(...aim) : null;
      showTarget(rayPoint ? world.pick(camera, rayPoint) : null);
      aimChanged = false;
      lastPick = now;
    }
    const changed = cameraChanged || motion.changed;
    const moving = travelling || motion.moving || aimChanged;
    cameraChanged = false;
    lastFrame = moving ? now : 0;
    return { changed, moving, shadows: motion.changed };
  }

  function act(at) {
    const item = world.pick(camera, at);
    if (!item) return;
    world.interact(item);
    cameraChanged = true;
    invalidateAim();
  }

  function clearDrag() {
    const id = drag?.id;
    drag = undefined;
    if (id !== undefined && canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
    stage.classList.remove('explore-looking');
  }

  function clearInput() {
    inputs.clear();
    lastFrame = 0;
    clearDrag();
    for (const button of moveButtons) button.classList.remove('held');
  }

  function pause() {
    if (!active) return;
    clearInput();
    if (document.pointerLockElement === canvas) document.exitPointerLock();
    showTarget(null);
  }

  function reset() {
    pause();
    camera.position.set(4.47, 1.57, 10.55);
    camera.rotation.set(0, 0, 0);
    aim = undefined;
    feedback('');
    cameraChanged = true;
    canvas.focus({ preventScroll: true });
    invalidateAim();
  }

  function enter(model) {
    if (currentModel !== model) {
      currentModel = model;
      world = createExploreScene(model, feedback);
    }
    world.refresh();
    active = true;
    hud.hidden = false;
    canvas.tabIndex = 0;
    canvas.setAttribute('aria-label', '自由探索别墅，操作见视口下方');
    reset();
  }

  function leave() {
    pause();
    active = false;
    locked = false;
    world.finish();
    hud.hidden = true;
    reticle.hidden = true;
    canvas.removeAttribute('tabindex');
    canvas.setAttribute('aria-label', '可旋转、缩放和切换楼层的三维别墅');
    feedback('');
  }

  canvas.addEventListener('pointerdown', event => {
    if (!ready() || locked || event.button !== 0 || drag) return;
    canvas.focus({ preventScroll: true });
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY };
    wasDragged = false;
    canvas.setPointerCapture(drag.id);
  });
  canvas.addEventListener('pointermove', event => {
    if (!ready() || locked) return;
    if (drag?.id === event.pointerId) {
      wasDragged ||= Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 4;
      if (wasDragged) {
        aim = undefined;
        stage.classList.add('explore-looking');
        look(event.clientX - drag.x, event.clientY - drag.y, 0.004);
      }
      drag.x = event.clientX;
      drag.y = event.clientY;
    } else if (!drag && event.pointerType === 'mouse') {
      aim = [event.clientX, event.clientY];
      invalidateAim();
    }
  });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(type, event => {
    if (drag?.id !== event.pointerId) return;
    if (type === 'pointercancel') wasDragged = true;
    clearDrag();
  });
  canvas.addEventListener('pointerleave', () => {
    if (!active || locked || drag) return;
    aim = undefined;
    showTarget(null);
  });
  canvas.addEventListener('mousemove', event => {
    if (locked && ready() && (event.movementX || event.movementY)) look(event.movementX, event.movementY, 0.002);
  });
  canvas.addEventListener('click', event => {
    if (!ready() || event.detail > 1 || (!locked && wasDragged)) return;
    act(locked ? center : pointAt(event.clientX, event.clientY));
  });
  canvas.addEventListener('dblclick', async event => {
    if (!ready() || locked || wasDragged || event.pointerType === 'touch') return;
    try {
      await canvas.requestPointerLock?.();
    } catch {
      feedback('可以拖动画面环顾');
    }
  });
  document.addEventListener('pointerlockchange', () => {
    const ownsLock = document.pointerLockElement === canvas;
    if (ownsLock && !ready()) { document.exitPointerLock(); return; }
    if (!active) return;
    locked = ownsLock;
    reticle.hidden = !locked;
    clearInput();
    aim = undefined;
    invalidateAim();
  });
  canvas.addEventListener('wheel', event => {
    if (!ready() || event.ctrlKey || !event.deltaY) return;
    event.preventDefault();
    const pixels = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? canvas.clientHeight : 1);
    delta.set(0, -THREE.MathUtils.clamp(pixels, -140, 140) * 0.0015, 0);
    if (world.move(camera.position, delta)) {
      cameraChanged = true;
      invalidateAim();
    }
  }, { passive: false });

  window.addEventListener('keydown', event => {
    if (!ready() || event.defaultPrevented) return;
    if (event.code === 'Escape' && !event.repeat) {
      event.preventDefault();
      if (locked) pause();
      else exit();
      return;
    }
    if ((!locked && document.activeElement !== canvas) || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.code === 'Enter' || event.code === 'Space') {
      event.preventDefault();
      if (!event.repeat) act(center);
      return;
    }
    const direction = movementKeys.get(event.code);
    if (!direction) return;
    event.preventDefault();
    inputs.set(event.code, direction);
    requestFrame();
  });
  window.addEventListener('keyup', event => inputs.delete(event.code));
  window.addEventListener('blur', pause);
  document.addEventListener('visibilitychange', () => {
    if (!active) return;
    if (document.hidden) pause();
    else requestFrame();
  });

  for (const button of moveButtons) {
    button.addEventListener('pointerdown', event => {
      if (!ready() || event.button !== 0) return;
      event.preventDefault();
      button.setPointerCapture(event.pointerId);
      inputs.set(event.pointerId, button.dataset.fly);
      button.classList.add('held');
      requestFrame();
    });
    for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(type, event => {
      inputs.delete(event.pointerId);
      button.classList.remove('held');
    });
    button.addEventListener('click', event => {
      if (!ready() || event.detail !== 0) return;
      move(new Set([button.dataset.fly]), 0.16);
      invalidateAim();
    });
  }
  document.getElementById('explore-reset').addEventListener('click', reset);
  document.getElementById('explore-exit').addEventListener('click', exit);

  function resize(aspect) {
    camera.aspect = aspect;
    camera.updateProjectionMatrix();
  }

  return { camera, enter, leave, pause, update, resize };
}
