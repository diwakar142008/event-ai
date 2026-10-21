"use client";

import { useEffect, useRef } from "react";

type ThreeModule = typeof import("three");

function ridgeGeometry(THREE: ThreeModule, depth: number, peak: number, seed: number) {
  const columns = 88;
  const rows = 10;
  const vertices: number[] = [];
  const indices: number[] = [];
  const peaks = [
    [-0.72, 0.42 + seed * 0.03, 0.085],
    [-0.33, 0.72 - seed * 0.02, 0.07],
    [0.08, 0.48 + seed * 0.025, 0.1],
    [0.55, 0.82 - seed * 0.025, 0.075],
    [0.88, 0.34 + seed * 0.02, 0.09],
  ];

  for (let row = 0; row <= rows; row++) {
    const z = depth + row * 2.2;
    const depthFade = 1 - row / (rows + 1) * 0.45;
    for (let column = 0; column <= columns; column++) {
      const xNorm = column / columns * 2 - 1;
      let height = -22;
      for (const [center, amplitude, width] of peaks) {
        height += peak * amplitude * Math.exp(-((xNorm - center) ** 2) / width);
      }
      height += Math.sin(xNorm * 19 + seed) * 1.4 + Math.sin(xNorm * 43 + seed * 4) * 0.55;
      const x = xNorm * 210;
      const y = -12 + height * depthFade - (row * 0.6);
      vertices.push(x, y, z);
    }
  }

  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      const a = row * (columns + 1) + column;
      const b = a + columns + 1;
      indices.push(a, b, a + 1, b, b + 1, a + 1);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function makeCloudLayer(THREE: ThreeModule, count: number, z: number, opacity: number) {
  const geometry = new THREE.SphereGeometry(1, 10, 7);
  const material = new THREE.MeshBasicMaterial({
    color: 0xffe5d2,
    transparent: true,
    opacity,
    depthWrite: false,
    fog: false,
  });
  const cloud = new THREE.InstancedMesh(geometry, material, count * 4);
  const matrix = new THREE.Matrix4();
  const position = new THREE.Vector3();
  const rotation = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  const dummy = new THREE.Object3D();

  for (let cloudIndex = 0; cloudIndex < count; cloudIndex++) {
    const centerX = (cloudIndex / count - 0.5) * 430 + (Math.sin(cloudIndex * 7.1) * 12);
    const centerY = -4 + Math.sin(cloudIndex * 5.3) * 7;
    const cloudWidth = 10 + ((cloudIndex * 17) % 22);
    for (let lobe = 0; lobe < 4; lobe++) {
      const index = cloudIndex * 4 + lobe;
      position.set(
        centerX + (lobe - 1.5) * cloudWidth * 0.24,
        centerY + Math.sin(lobe * 2.8 + cloudIndex) * 2.4,
        z + Math.sin(lobe + cloudIndex * 0.4) * 1.8,
      );
      rotation.setFromEuler(new THREE.Euler(0, 0, Math.sin(lobe * 3 + cloudIndex) * 0.12));
      scale.set(cloudWidth * (0.65 + (lobe % 2) * 0.16), 2.2 + (lobe % 3) * 0.7, 2.5);
      dummy.position.copy(position);
      dummy.quaternion.copy(rotation);
      dummy.scale.copy(scale);
      dummy.updateMatrix();
      matrix.copy(dummy.matrix);
      cloud.setMatrixAt(index, matrix);
    }
  }
  cloud.instanceMatrix.needsUpdate = true;
  return cloud;
}

export default function CinematicScene() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    let renderer: import("three").WebGLRenderer | null = null;
    let animationFrame = 0;
    let observer: ResizeObserver | null = null;
    let cleanup: (() => void) | null = null;

    void import("three").then((THREE) => {
      if (!mount.isConnected) return;
      try {
        const width = mount.clientWidth;
        const height = mount.clientHeight;
        const smallDevice = window.matchMedia("(max-width: 700px)").matches || (navigator.hardwareConcurrency || 8) < 4;
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0xcab6a0, 0.0017);

        const camera = new THREE.PerspectiveCamera(42, width / Math.max(height, 1), 0.1, 1000);
        camera.position.set(0, 18, 112);
        camera.lookAt(0, 18, 0);

        renderer = new THREE.WebGLRenderer({ alpha: false, antialias: false, powerPreference: "low-power" });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, smallDevice ? 1.2 : 1.6));
        renderer.setSize(width, height);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.14;
        renderer.domElement.className = "cinematic-canvas";
        renderer.domElement.setAttribute("aria-hidden", "true");
        mount.appendChild(renderer.domElement);

        const skyGeometry = new THREE.SphereGeometry(480, 32, 20);
        const skyMaterial = new THREE.ShaderMaterial({
          side: THREE.BackSide,
          depthWrite: false,
          vertexShader: `varying vec3 vWorldPosition; void main(){ vec4 world=modelMatrix*vec4(position,1.0); vWorldPosition=world.xyz; gl_Position=projectionMatrix*viewMatrix*world; }`,
          fragmentShader: `
            varying vec3 vWorldPosition;
            void main(){
              float h=normalize(vWorldPosition).y;
              vec3 teal=vec3(0.42,0.68,0.67);
              vec3 pale=vec3(0.84,0.79,0.68);
              vec3 peach=vec3(0.91,0.59,0.45);
              vec3 rose=vec3(0.42,0.31,0.34);
              vec3 color=mix(rose,peach,smoothstep(-0.5,-0.03,h));
              color=mix(color,pale,smoothstep(-0.02,0.2,h));
              color=mix(color,teal,smoothstep(0.23,0.74,h));
              float glow=exp(-pow((h+0.04)*8.0,2.0))*0.18;
              color+=vec3(1.0,0.68,0.43)*glow;
              gl_FragColor=vec4(color,1.0);
            }`,
        });
        scene.add(new THREE.Mesh(skyGeometry, skyMaterial));

        scene.add(new THREE.HemisphereLight(0xffe8d3, 0x493a48, 2.0));
        const sun = new THREE.DirectionalLight(0xffd7ad, 2.8);
        sun.position.set(-90, 80, 45);
        scene.add(sun);

        const ranges = [
          { z: -64, peak: 47, color: 0x876e72, opacity: 0.72 },
          { z: -35, peak: 35, color: 0x8f7475, opacity: 0.85 },
          { z: -10, peak: 25, color: 0x66545b, opacity: 0.98 },
        ];
        ranges.forEach((range, index) => {
          const geometry = ridgeGeometry(THREE, range.z, range.peak, index + 1);
          const material = new THREE.MeshStandardMaterial({
            color: range.color,
            roughness: 1,
            metalness: 0,
            transparent: range.opacity < 1,
            opacity: range.opacity,
            flatShading: true,
          });
          scene.add(new THREE.Mesh(geometry, material));
        });

        const cloudLayers = [
          makeCloudLayer(THREE, smallDevice ? 12 : 19, 24, 0.13),
          makeCloudLayer(THREE, smallDevice ? 10 : 17, 45, 0.1),
          makeCloudLayer(THREE, smallDevice ? 8 : 13, 68, 0.075),
        ];
        cloudLayers.forEach((layer) => scene.add(layer));

        const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
        const finePointer = window.matchMedia("(pointer: fine)");
        let pointerX = 0;
        let pointerY = 0;
        let targetX = 0;
        let targetY = 0;
        const onPointer = (event: PointerEvent) => {
          if (!finePointer.matches || reducedMotion.matches) return;
          targetX = (event.clientX / window.innerWidth - 0.5) * 5;
          targetY = (event.clientY / window.innerHeight - 0.5) * -2.5;
        };
        const onContextLost = (event: Event) => {
          event.preventDefault();
          if (renderer) renderer.domElement.style.visibility = "hidden";
          cancelAnimationFrame(animationFrame);
        };
        const onContextRestored = () => {
          if (renderer) renderer.domElement.style.visibility = "visible";
          renderFrame();
        };
        renderer.domElement.addEventListener("webglcontextlost", onContextLost);
        renderer.domElement.addEventListener("webglcontextrestored", onContextRestored);
        window.addEventListener("pointermove", onPointer, { passive: true });

        observer = new ResizeObserver(() => {
          if (!renderer || !mount) return;
          const nextWidth = mount.clientWidth;
          const nextHeight = mount.clientHeight;
          camera.aspect = nextWidth / Math.max(nextHeight, 1);
          camera.updateProjectionMatrix();
          renderer.setSize(nextWidth, nextHeight);
        });
        observer.observe(mount);

        const clock = new THREE.Clock();
        const renderFrame = () => {
          if (!renderer) return;
          const time = clock.getElapsedTime();
          const motion = reducedMotion.matches ? 0 : 1;
          pointerX += (targetX - pointerX) * 0.018;
          pointerY += (targetY - pointerY) * 0.018;
          camera.position.x = Math.sin(time * 0.08) * 1.1 * motion + pointerX;
          camera.position.y = 18 + Math.sin(time * 0.11) * 0.5 * motion + pointerY;
          camera.lookAt(pointerX * 0.25, 18 + pointerY * 0.2, 0);
          cloudLayers.forEach((layer, index) => {
            layer.position.x = Math.sin(time * (0.012 + index * 0.003) + index) * (2.5 + index);
          });
          renderer.render(scene, camera);
          if (!reducedMotion.matches) animationFrame = requestAnimationFrame(renderFrame);
        };
        cleanup = () => {
          cancelAnimationFrame(animationFrame);
          observer?.disconnect();
          window.removeEventListener("pointermove", onPointer);
          renderer?.domElement.removeEventListener("webglcontextlost", onContextLost);
          renderer?.domElement.removeEventListener("webglcontextrestored", onContextRestored);
          scene.traverse((object) => {
            if (object instanceof THREE.Mesh || object instanceof THREE.InstancedMesh) {
              object.geometry.dispose();
              const materials = Array.isArray(object.material) ? object.material : [object.material];
              materials.forEach((material) => material.dispose());
            }
          });
          renderer?.dispose();
          renderer?.domElement.remove();
          renderer = null;
        };
        renderFrame();
      } catch {
        // The CSS sky remains visible if WebGL is unavailable or initialization fails.
        renderer?.dispose();
        renderer?.domElement.remove();
        renderer = null;
      }
    });

    return () => {
      cleanup?.();
      observer?.disconnect();
      cancelAnimationFrame(animationFrame);
      renderer?.dispose();
      renderer?.domElement.remove();
    };
  }, []);

  return <div ref={mountRef} className="cinematic-scene" aria-hidden="true" />;
}
