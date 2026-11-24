import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { createExplorer } from './explore.js';
import { buildModel } from './model.js';
import { floors, furnishings } from './plan.js';

const $ = (id) => document.getElementById(id);
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const floorButtons = [...document.querySelectorAll('[data-floor]')];
const inspector = $('inspector');
const phoneSettings = $('phone-settings');
const items = new Map(furnishings.map(item => [item.id, item]));
const storageKey = 'zhangkeng.furniture.v1';
const state = {
  mode: 'exterior', floor: 'ground', phase: 'proposal', spacing: 2.6,
  furniture: true, labels: true, item: '', measuring: false,
};

$('about-open').addEventListener('click', () => $('about').showModal());

function connectPhoneSettings() {
  const sidebarHost = inspector.parentElement;
  const phoneViewport = matchMedia('(max-width: 730px), (pointer: coarse) and (max-height: 600px)');
  function placeInspector() {
    if (phoneViewport.matches) {
      phoneSettings.append(inspector);
    } else {
      if (phoneSettings.open) phoneSettings.close();
      sidebarHost.append(inspector);
    }
  }
  phoneViewport.addEventListener('change', placeInspector);
  $('phone-settings-open').addEventListener('click', () => phoneSettings.showModal());
  phoneSettings.addEventListener('click', event => {
    if (event.target === phoneSettings && event.clientY < phoneSettings.getBoundingClientRect().top) phoneSettings.close();
  });
  placeInspector();
}

connectPhoneSettings();

function loadPlacements() {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    return new Map([...items.keys()].flatMap(id => {
      const item = saved?.[id];
      return item && [item.x, item.z, item.angle].every(Number.isFinite) ? [[id, item]] : [];
    }));
  } catch {
    return new Map();
  }
}

function clampPlacement(item, x, z, angle) {
  const room = floors[item.floor].rooms.find(room => room.name === item.room);
  const [left, back, right, front] = room.bounds;
  const turn = ((Math.round(angle / 90) * 90) % 360 + 360) % 360;
  const rotated = turn % 180 !== 0;
  const halfW = Math.min((rotated ? item.d : item.w) / 2, (right - left) / 2);
  const halfD = Math.min((rotated ? item.w : item.d) / 2, (front - back) / 2);
  return { x: THREE.MathUtils.clamp(x, left + halfW, right - halfW), z: THREE.MathUtils.clamp(z, back + halfD, front - halfD), angle: turn };
}

function makeViewer() {
  const scene = new THREE.Scene();
  const stage = $('stage');
  const surface = $('viewer-surface');
  const viewport = $('viewport');
  const modelView = $('model-view');
  const loadingPanel = $('model-loading');
  const loadingStatus = $('loading-status');
  const loadingProgress = $('loading-progress');
  const loadingPercent = $('loading-percent');
  const modelNote = $('model-note');
  const modelRetry = $('model-retry');
  const modelControls = document.querySelectorAll('[data-model-controls]');
  const exploreButton = document.querySelector('[data-mode="explore"]');
  const mobile = matchMedia('(pointer: coarse)').matches;
  const elementary = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  elementary.shadowMap.enabled = true;
  elementary.shadowMap.type = THREE.PCFSoftShadowMap;
  elementary.shadowMap.autoUpdate = false;
  elementary.toneMapping = THREE.ACESFilmicToneMapping;
  elementary.toneMappingExposure = 1.16;
  const canvas = elementary.domElement;
  canvas.setAttribute('aria-label', '可旋转、缩放和切换楼层的郑家大院三维模型');
  viewport.prepend(canvas);

  const camera = new THREE.OrthographicCamera(-12, 12, 9, -9, 0.1, 180);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.14;
  controls.maxPolarAngle = Math.PI / 2.07;
  controls.minZoom = 0.53;
  controls.maxZoom = 4.8;

  let model = buildModel();
  scene.add(model.root);
  const lighting = new THREE.HemisphereLight(0xfaf3e5, 0x9c9b86, 1.95);
  const sun = new THREE.DirectionalLight(0xffe9cc, 2.32);
  sun.position.set(-10, 24, 16);
  sun.target.position.set(4.7, 2, 2.6);
  sun.castShadow = true;
  const shadowSize = mobile ? 1536 : 2048;
  sun.shadow.mapSize.set(shadowSize, shadowSize);
  Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 18, bottom: -18, near: 0.2, far: 66 });
  sun.shadow.camera.updateProjectionMatrix();
  sun.shadow.normalBias = 0.021;
  sun.shadow.bias = -0.00012;
  scene.add(lighting, sun, sun.target);
  const contact = new THREE.Mesh(new THREE.PlaneGeometry(180, 180), new THREE.ShadowMaterial({ opacity: 0.15 }));
  contact.rotation.x = -Math.PI / 2;
  contact.position.y = -0.68;
  contact.receiveShadow = true;
  scene.add(contact);
  const grid = new THREE.GridHelper(60, 60, '#a9aa94', '#b4b29f');
  grid.position.set(5, -0.689, 2.7);
  grid.material.transparent = true;
  grid.material.opacity = 0.13;
  scene.add(grid);

  const highlight = new THREE.LineLoop(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0x405536, depthTest: false }));
  highlight.renderOrder = 9;
  highlight.visible = false;
  scene.add(highlight);
  const measureLayer = new THREE.Group();
  scene.add(measureLayer);
  const measureDot = new THREE.SphereGeometry(0.063, 12, 8);
  const measureMaterial = new THREE.MeshBasicMaterial({ color: '#425b31', depthTest: false });
  const measureLineMaterial = new THREE.LineBasicMaterial({ color: '#496337', depthTest: false });

  const saved = loadPlacements();
  const ray = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0));
  const project = new THREE.Vector3();
  const north = new THREE.Vector3();
  const focus = new THREE.Vector3();
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let width = 1, height = 1, dirty = true, frameId = 0, gesture, labels = [], points = [], transition;
  let shelf = { ground: 0, upper: 3.3, roof: 0 };
  let showingStage = false;
  let pendingAsset;
  let surveyMode = 'exterior';
  const explorer = createExplorer({ canvas, requestFrame, exit: exitExploration });

  for (const item of furnishings) {
    const option = new Option(`${floors[item.floor].tag} · ${item.room} · ${item.name}`, item.id);
    $('item-select').append(option);
    const placement = saved.get(item.id);
    if (placement) saved.set(item.id, clampPlacement(item, placement.x, placement.z, placement.angle));
    place(item);
  }

  function place(item) {
    const value = saved.get(item.id) ?? item;
    const node = model.furniture.get(item.id);
    node.position.x = value.x;
    node.position.z = value.z;
    node.rotation.y = value.angle * Math.PI / 180;
    return value;
  }

  function save() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(Object.fromEntries(saved)));
    } catch {
      status('浏览器的本地存储不可用，刷新后会恢复图纸布置。');
    }
    $('reset-layout').disabled = saved.size === 0;
  }

  function requestFrame() {
    if (!frameId) frameId = requestAnimationFrame(draw);
  }

  function renderSoon(shadows = false) {
    dirty = true;
    if (shadows) elementary.shadowMap.needsUpdate = true;
    requestFrame();
  }

  function draw(now) {
    frameId = 0;
    if (pendingAsset && !gesture) applyAsset();
    if (stage.dataset.model === 'loading') return;
    if (transition) {
      const fraction = Math.min(1, (now - transition.start) / 410);
      const t = 1 - (1 - fraction) ** 3;
      model.building.ground.layer.position.y = THREE.MathUtils.lerp(transition.ground, shelf.ground, t);
      model.building.upper.layer.position.y = THREE.MathUtils.lerp(transition.upper, shelf.upper, t);
      model.roof.position.y = THREE.MathUtils.lerp(transition.roof, shelf.roof, t);
      elementary.shadowMap.needsUpdate = true;
      dirty = true;
      if (fraction === 1) transition = undefined;
    }
    const exploring = state.mode === 'explore';
    const movement = exploring ? explorer.update(now) : undefined;
    const nextFrame = exploring ? movement.moving : controls.update();
    if (movement?.shadows) elementary.shadowMap.needsUpdate = true;
    if (dirty || (exploring ? movement.changed : nextFrame)) {
      elementary.render(scene, exploring ? explorer.camera : camera);
      if (exploring) $('north-arrow').style.rotate = `${explorer.camera.rotation.y}rad`;
      else projectLabels();
      dirty = false;
      if (!showingStage) {
        showingStage = true;
        stage.dataset.ready = 'true';
      }
    }
    if (nextFrame || transition) requestFrame();
  }

  function projectLabels() {
    for (const label of labels) {
      project.set(label.x, label.y + (label.track?.position.y || 0), label.z).project(camera);
      label.el.hidden = Math.abs(project.x) > 1.04 || Math.abs(project.y) > 1.04 || Math.abs(project.z) > 1;
      label.el.style.transform = `translate(${(0.5 + project.x / 2) * width}px, ${(0.5 - project.y / 2) * height}px)`;
    }
    focus.copy(controls.target).project(camera);
    north.copy(controls.target).add(new THREE.Vector3(0, 0, -1)).project(camera);
    $('north-arrow').style.rotate = `${Math.atan2((north.x - focus.x) * width, (north.y - focus.y) * height)}rad`;
  }

  function label(point, text, className = '') {
    const el = document.createElement('span');
    el.className = `room-label ${className}`;
    el.textContent = text;
    $('labels').append(el);
    labels.push({ ...point, el });
  }

  function updateLabels() {
    labels = [];
    $('labels').replaceChildren();
    if (!state.labels || state.mode === 'exterior' || state.mode === 'explore') return;
    if (state.mode === 'exploded') {
      label({ x: -0.7, y: 0.3, z: 8.9, track: model.building.ground.layer }, '1F · 一层', 'level-tag');
      label({ x: -0.7, y: 0.3, z: 8.9, track: model.building.upper.layer }, '2F · 二层', 'level-tag');
      label({ x: 2.9, y: 6.3, z: 7.2, track: model.roof }, '屋顶', 'level-tag');
    } else if (floors[state.floor]) {
      for (const room of floors[state.floor].rooms) {
        const [x1, z1, x2, z2] = room.bounds;
        label({ x: (x1 + x2) / 2, y: 0.29, z: z1 * 0.47 + z2 * 0.53, track: model.building[state.floor].layer }, room.name, room.undecided ? 'unresolved' : '');
      }
    } else if (state.floor === 'yard' && state.phase === 'proposal') {
      label({ x: -2.36, y: 2.46, z: -4.5 }, '户外厨房');
      label({ x: 10.52, y: 0.74, z: -4.52 }, '塑木平台');
      label({ x: 4.2, y: 0.25, z: -3.65 }, '北花园');
    }
  }

  function resize() {
    width = Math.max(1, surface.clientWidth);
    height = Math.max(1, surface.clientHeight);
    const frame = stage.getBoundingClientRect();
    const exterior = state.mode === 'exterior';
    const explode = state.mode === 'exploded';
    const courtyard = state.floor === 'yard';
    const minWidth = exterior || explode || courtyard ? 26.2 : state.mode === 'plan' ? 14.8 : 16.2;
    const minHeight = explode ? 21.7 + (state.spacing - 2.6) * 1.45 : exterior || courtyard ? 18.4 : 12.3;
    const unitsPerPixel = Math.max(minWidth / Math.max(1, frame.width), minHeight / Math.max(1, frame.height));
    const halfWidth = width * unitsPerPixel / 2;
    const halfHeight = height * unitsPerPixel / 2;
    Object.assign(camera, { left: -halfWidth, right: halfWidth, top: halfHeight, bottom: -halfHeight });
    // Keep the default composition between the controls while projecting to the entire window.
    camera.setViewOffset(width, height, width / 2 - frame.left - frame.width / 2,
      height / 2 - frame.top - frame.height / 2, width, height);
    explorer.resize(width / height);
    const pixelLimit = mobile ? 2_000_000 : 5_000_000;
    const density = Math.min(window.devicePixelRatio, mobile ? 1.35 : 1.65, Math.sqrt(pixelLimit / (width * height)));
    if (elementary.getPixelRatio() !== density) elementary.setPixelRatio(density);
    elementary.setSize(width, height, false);
    renderSoon();
  }

  function resetCamera() {
    const solo = state.mode === 'cut' || state.mode === 'plan';
    const plan = state.mode === 'plan';
    const explode = state.mode === 'exploded';
    controls.enableRotate = !plan;
    controls.mouseButtons.LEFT = plan ? THREE.MOUSE.PAN : THREE.MOUSE.ROTATE;
    controls.touches.ONE = plan ? THREE.TOUCH.PAN : THREE.TOUCH.ROTATE;
    const center = solo && state.floor !== 'yard'
      ? [5.55, state.floor === 'roof' ? 5.95 : floors[state.floor].elevation + 0.16, 4.53]
      : [4.89, explode ? 4.34 + (state.spacing - 2.6) * 0.42 : solo ? -0.12 : 1.65, 2.69];
    controls.target.set(...center);
    camera.position.copy(controls.target).add(plan ? new THREE.Vector3(0, 34, 0.0034) : new THREE.Vector3(-22, solo ? 28 : explode ? 17 : 23, 27));
    camera.zoom = 1;
    resize();
    controls.update();
  }

  function status(message = '') {
    $('view-status').textContent = message;
    $('view-status').hidden = !message;
  }

  function clearMeasure() {
    points = [];
    for (const line of measureLayer.children) if (line.isLine) line.geometry.dispose();
    measureLayer.clear();
  }

  function stopMeasure() {
    state.measuring = false;
    clearMeasure();
    status();
  }

  function showModelStatus(mode, message = '') {
    const loading = mode === 'loading';
    stage.dataset.model = mode;
    loadingPanel.hidden = !loading;
    viewport.hidden = loading;
    modelView.hidden = loading;
    modelView.setAttribute('aria-busy', String(loading));
    modelNote.textContent = message;
    modelRetry.hidden = mode !== 'schematic';
    exploreButton.disabled = mode !== 'photo';
    for (const element of modelControls) element.inert = loading;
  }

  function applyAsset() {
    const fallback = model;
    model = pendingAsset.model;
    scene.environment = pendingAsset.environment;
    scene.environmentIntensity = 0.71;
    pendingAsset = undefined;

    elementary.toneMappingExposure = 1.13;
    elementary.shadowMap.type = THREE.PCFShadowMap;
    sun.color.set(0xfff5e8);
    sun.intensity = 3.05;
    sun.position.set(-7.4, 20, 23);
    sun.shadow.radius = mobile ? 2.3 : 3.25;
    sun.shadow.normalBias = 0.018;
    lighting.intensity = 0.32;
    contact.material.opacity = 0.24;

    for (const id of ['ground', 'upper']) {
      model.building[id].layer.position.y = fallback.building[id].layer.position.y;
    }
    model.roof.position.y = fallback.roof.position.y;
    fallback.root.removeFromParent();
    const geometries = new Set();
    const materials = new Set();
    fallback.root.traverse(object => {
      if (object.geometry?.isBufferGeometry) geometries.add(object.geometry);
      if (object.material) {
        for (const material of [object.material].flat()) {
          if (material?.isMaterial) materials.add(material);
        }
      }
    });
    geometries.forEach(geometry => geometry.dispose());
    materials.forEach(material => material.dispose());

    furnishings.forEach(place);
    scene.add(model.root);
    showModelStatus('photo', '写实模型已加载');
    updateModelVisibility();
    updateLabels();
    dirty = true;
    elementary.shadowMap.needsUpdate = true;
  }

  function setDownloadProgress(percent) {
    const text = `${percent}%`;
    if (loadingPercent.textContent === text) return;
    loadingProgress.value = percent;
    loadingPercent.textContent = text;
  }

  async function upgradeModel() {
    loadingStatus.textContent = '正在准备写实模型…';
    loadingProgress.removeAttribute('value');
    loadingPercent.textContent = '';
    showModelStatus('loading');
    try {
      const { loadAssetModel, makeDaylightEnvironment } = await import('./asset-model.js');
      loadingStatus.textContent = '正在下载写实模型…';
      const asset = await loadAssetModel((received, total) => {
        if (total > 0) setDownloadProgress(Math.min(100, Math.floor(received / total * 100)));
      }, () => {
        setDownloadProgress(100);
        loadingStatus.textContent = '正在生成三维画面…';
      });
      pendingAsset = { model: asset, environment: makeDaylightEnvironment() };
      renderSoon();
    } catch (error) {
      console.warn('Villa model could not load.', error);
      showModelStatus('schematic', '写实模型加载失败，当前为示意模型。');
      renderSoon(true);
    }
  }

  function updateModelVisibility() {
    const solo = state.mode === 'cut' || state.mode === 'plan';
    const exploded = state.mode === 'exploded';
    model.site.visible = !solo || state.floor === 'yard';
    model.roof.visible = !solo || state.floor === 'roof';
    model.roof.traverse(object => {
      if (object.isMesh) object.castShadow = !exploded && (object.userData.castShadow ?? true);
    });
    contact.visible = state.mode !== 'plan';
    const detailed = stage.dataset.model === 'photo';
    grid.visible = !detailed || state.mode === 'plan';
    if (detailed) sun.shadow.intensity = state.mode === 'plan' ? 0.36 : 0.89;
    model.proposal.visible = state.phase === 'proposal';
    model.present.visible = state.phase === 'present';
    for (const [id, layer] of Object.entries(model.building)) {
      layer.layer.visible = !solo || id === state.floor;
      layer.cut.visible = solo || exploded;
      layer.full.visible = !layer.cut.visible;
      layer.contents.visible = state.furniture || state.mode === 'explore';
    }
  }

  function show({ reset = false, animate = false } = {}) {
    const solo = state.mode === 'cut' || state.mode === 'plan';
    const exploded = state.mode === 'exploded';
    const exploring = state.mode === 'explore';
    shelf = {
      ground: exploded ? 0.68 : 0,
      upper: floors.upper.elevation + (exploded ? state.spacing : 0),
      roof: exploded ? state.spacing * 2 : 0,
    };
    if (animate && !reduced.matches) {
      transition = { start: performance.now(), ground: model.building.ground.layer.position.y, upper: model.building.upper.layer.position.y, roof: model.roof.position.y };
    } else {
      transition = undefined;
      model.building.ground.layer.position.y = shelf.ground;
      model.building.upper.layer.position.y = shelf.upper;
      model.roof.position.y = shelf.roof;
    }
    updateModelVisibility();
    modeButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mode === state.mode)));
    floorButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.floor === state.floor)));
    $('measure').setAttribute('aria-pressed', String(state.measuring));
    $('measure').disabled = exploring;
    canvas.classList.toggle('measuring', state.measuring);
    stage.classList.toggle('exploring', exploring);
    inspector.inert = exploring || stage.dataset.model === 'loading';
    $('furniture-visibility').checked = state.furniture;
    $('spacing-field').hidden = !exploded;
    $('spacing-value').value = `${state.spacing.toFixed(1)} m`;
    const orbitHint = mobile ? '单指拖动旋转 · 双指缩放或平移' : '拖动旋转 · 滚动缩放 · 右键拖动平移';
    const planHint = mobile ? '单指拖动平移 · 双指缩放' : '拖动平移 · 滚动或双指缩放';
    const gestureHint = state.mode === 'plan' ? planHint : orbitHint;
    $('view-hint').textContent = state.measuring ? '点选两个位置，测量水平距离' : gestureHint;
    $('view-hint').hidden = exploring;
    $('explore-hint').hidden = !exploring;
    const floor = floors[state.floor];
    $('floor-elevation').textContent = state.floor === 'ground' ? '±0.000' : state.floor === 'upper' ? '+3.300' : state.floor === 'roof' ? '照片估算' : '室外';
    $('scene-index').textContent = solo ? floor?.tag ?? (state.floor === 'roof' ? '屋面' : '室外') : exploded ? '逐层展开' : '整栋';
    $('scene-text').textContent = solo
      ? floor ? `${floor.label} · ${floor.size.map(n => n.toFixed(2)).join(' × ')} m` : state.floor === 'yard' ? '北花园与入户铺装' : '十字坡屋面'
      : exploded ? '一层、二层与屋顶' : '主屋与庭院';
    updateLabels();
    updateItem();
    if (reset) resetCamera();
    renderSoon(true);
  }

  function updateItem() {
    $('item-select').value = state.item;
    $('item-editor').hidden = !state.item;
    $('reset-layout').disabled = saved.size === 0;
    highlight.visible = false;
    const item = items.get(state.item);
    if (!item) return;
    const where = saved.get(item.id) ?? item;
    $('item-detail').textContent = `占地 ${item.w.toFixed(2)} × ${item.d.toFixed(2)} m · ${where.angle}°`;
    if (state.floor !== item.floor || !state.furniture || !['plan', 'cut'].includes(state.mode)) return;
    const dx = item.w / 2, dz = item.d / 2;
    highlight.geometry.dispose();
    highlight.geometry = new THREE.BufferGeometry().setFromPoints([[-dx, -dz], [dx, -dz], [dx, dz], [-dx, dz]].map(([x, z]) => new THREE.Vector3(x, 0, z)));
    highlight.position.set(where.x, floors[item.floor].elevation + 0.043, where.z);
    highlight.rotation.y = where.angle * Math.PI / 180;
    highlight.visible = true;
  }

  function select(id) {
    state.item = id;
    const item = items.get(id);
    if (!item) { updateItem(); renderSoon(); return; }
    const change = state.floor !== item.floor || !['cut', 'plan'].includes(state.mode);
    state.floor = item.floor;
    if (state.measuring) stopMeasure();
    if (state.mode !== 'plan') state.mode = 'cut';
    state.furniture = true;
    show({ reset: change });
  }

  function moveItem(id, x, z, angle) {
    const item = items.get(id);
    saved.set(id, clampPlacement(item, x, z, angle));
    place(item);
    updateItem();
    renderSoon(true);
  }

  function pointRay(event) {
    const bounds = canvas.getBoundingClientRect();
    pointer.set((event.clientX - bounds.left) / width * 2 - 1, 1 - (event.clientY - bounds.top) / height * 2);
    ray.setFromCamera(pointer, camera);
  }

  function floorPoint() {
    plane.constant = -(floors[state.floor].elevation + 0.041);
    return ray.ray.intersectPlane(plane, new THREE.Vector3());
  }

  function pick() {
    const visible = furnishings.filter(item => item.floor === state.floor).map(item => model.furniture.get(item.id));
    const hits = ray.intersectObjects(visible);
    let node = hits[0]?.object;
    while (node && !node.userData.itemId) node = node.parent;
    return node?.userData.itemId;
  }

  function takeMeasure() {
    if (points.length === 2) clearMeasure();
    const point = floorPoint();
    if (!point) return;
    points.push(point);
    const dot = new THREE.Mesh(measureDot, measureMaterial);
    dot.position.copy(point);
    dot.renderOrder = 10;
    measureLayer.add(dot);
    if (points.length === 2) {
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), measureLineMaterial);
      line.renderOrder = 10;
      measureLayer.add(line);
      const length = points[0].distanceTo(points[1]);
      status(`水平距离 ${length.toFixed(2)} m · 点一下重新测量`);
    } else status('已选择起点，点选终点。');
    renderSoon();
  }

  canvas.addEventListener('pointerdown', event => {
    if (state.mode === 'explore' || !event.isPrimary || event.button !== 0) return;
    pointRay(event);
    const editable = state.furniture && !state.measuring && ['plan', 'cut'].includes(state.mode) && floors[state.floor];
    const id = editable ? pick() : null;
    gesture = { pointerId: event.pointerId, x: event.clientX, z: event.clientY, id, moved: false };
    if (!id) return;
    const point = floorPoint();
    if (!point) return;
    select(id);
    const placement = saved.get(id) ?? items.get(id);
    Object.assign(gesture, { dx: placement.x - point.x, dz: placement.z - point.z, angle: placement.angle });
    controls.enabled = false;
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add('dragging');
  }, true);

  canvas.addEventListener('pointermove', event => {
    if (!gesture || gesture.pointerId !== event.pointerId) return;
    gesture.moved ||= Math.hypot(event.clientX - gesture.x, event.clientY - gesture.z) > 5;
    if (!gesture.moved || !gesture.id || gesture.dx === undefined) return;
    pointRay(event);
    const point = floorPoint();
    if (point) moveItem(gesture.id, point.x + gesture.dx, point.z + gesture.dz, gesture.angle);
  });

  function endGesture(event) {
    if (!gesture || gesture.pointerId !== event.pointerId) return;
    if (gesture.id && gesture.moved) save();
    if (state.measuring && !gesture.moved && event.type === 'pointerup') {
      pointRay(event);
      takeMeasure();
    }
    gesture = undefined;
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    controls.enabled = true;
    canvas.classList.remove('dragging');
    if (pendingAsset) renderSoon();
  }

  canvas.addEventListener('pointerup', endGesture);
  canvas.addEventListener('pointercancel', endGesture);
  controls.addEventListener('change', () => renderSoon());
  const sizing = new ResizeObserver(resize);
  sizing.observe(stage);
  sizing.observe(surface);

  function switchMode(mode, restoreSurvey = false) {
    const previous = state.mode;
    if (mode === previous || (mode === 'explore' && exploreButton.disabled)) return;
    const exploring = mode === 'explore';
    if (exploring) {
      surveyMode = previous;
      if (gesture) endGesture({ pointerId: gesture.pointerId, type: 'pointercancel' });
    }
    if (previous === 'explore') explorer.leave();
    controls.enabled = !exploring;
    const animate = !restoreSurvey && (mode === 'exploded' || (previous === 'exploded' && mode === 'exterior'));
    state.mode = mode;
    stopMeasure();
    if (!restoreSurvey && (mode === 'exterior' || mode === 'exploded')) state.item = '';
    show({ reset: !exploring && !restoreSurvey, animate });
    if (exploring) explorer.enter(model);
    if (restoreSurvey) resize();
  }

  function exitExploration() {
    if (state.mode !== 'explore') return;
    switchMode(surveyMode, true);
    exploreButton.focus({ preventScroll: true });
  }

  for (const button of modeButtons) button.addEventListener('click', () => switchMode(button.dataset.mode));
  for (const button of floorButtons) button.addEventListener('click', () => {
    if (phoneSettings.open) phoneSettings.close();
    state.floor = button.dataset.floor;
    state.mode = state.mode === 'plan' ? 'plan' : 'cut';
    state.item = '';
    stopMeasure();
    show({ reset: true });
  });
  $('yard-phase').addEventListener('change', event => { state.phase = event.target.value; show(); });
  $('spacing').addEventListener('input', event => { state.spacing = Number(event.target.value); show(); resize(); });
  $('furniture-visibility').addEventListener('change', event => { state.furniture = event.target.checked; show(); });
  $('room-visibility').addEventListener('change', event => { state.labels = event.target.checked; show(); });
  $('item-select').addEventListener('change', event => select(event.target.value));
  $('measure').addEventListener('click', () => {
    if (state.measuring) stopMeasure();
    else {
      state.measuring = true;
      state.mode = 'plan';
      state.item = '';
      if (!floors[state.floor]) state.floor = 'ground';
      status('点选测量起点。');
    }
    show({ reset: state.measuring });
  });
  $('reset-view').addEventListener('click', resetCamera);
  for (const [id, factor] of [['zoom-in', 1.18], ['zoom-out', 1 / 1.18]]) $(id).addEventListener('click', () => {
    camera.zoom = THREE.MathUtils.clamp(camera.zoom * factor, controls.minZoom, controls.maxZoom);
    camera.updateProjectionMatrix();
    renderSoon();
  });
  const offsets = { north: [0, -0.1], south: [0, 0.1], west: [-0.1, 0], east: [0.1, 0] };
  for (const button of document.querySelectorAll('[data-nudge]')) button.addEventListener('click', () => {
    const value = saved.get(state.item) ?? items.get(state.item);
    const [dx, dz] = offsets[button.dataset.nudge];
    moveItem(state.item, value.x + dx, value.z + dz, value.angle);
    save();
  });
  $('rotate-item').addEventListener('click', () => {
    const value = saved.get(state.item) ?? items.get(state.item);
    moveItem(state.item, value.x, value.z, value.angle + 90);
    save();
  });
  $('reset-layout').addEventListener('click', () => {
    saved.clear();
    furnishings.forEach(place);
    save();
    updateItem();
    renderSoon(true);
  });
  window.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || event.defaultPrevented || state.mode === 'explore' || document.querySelector('dialog[open]')) return;
    if (state.measuring) { stopMeasure(); show(); }
    else if (state.item) select('');
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    explorer.pause();
    status('图形上下文已断开，正在等待恢复。');
  });
  canvas.addEventListener('webglcontextrestored', () => { status(); renderSoon(true); });
  $('about-open').addEventListener('click', explorer.pause);
  $('about').addEventListener('close', () => {
    if (state.mode !== 'explore') return;
    canvas.focus({ preventScroll: true });
    requestFrame();
  });
  modelRetry.addEventListener('click', upgradeModel);
  show({ reset: true });
  upgradeModel();
}

try {
  makeViewer();
} catch (error) {
  console.error(error);
  $('stage').dataset.model = 'unavailable';
  $('model-loading').hidden = true;
  $('viewport').hidden = true;
  $('model-view').hidden = true;
  $('model-view').removeAttribute('aria-busy');
  $('view-error').textContent = '三维模型暂时无法打开。请启用浏览器的 WebGL 2 和硬件加速，再刷新页面。';
  $('view-error').hidden = false;
  document.querySelectorAll('.workbench button, .workbench input, .workbench select').forEach(control => { control.disabled = true; });
}
