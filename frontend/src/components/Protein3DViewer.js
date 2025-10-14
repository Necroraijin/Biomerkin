import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { motion } from 'framer-motion';

const Protein3DViewer = ({ proteinData, width = 800, height = 600 }) => {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const cameraRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // Initialize Three.js scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(50, 50, 50);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;
    controls.enablePan = true;
    controlsRef.current = controls;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 50, 50);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Add protein structure
    if (proteinData) {
      createProteinStructure(scene, proteinData);
    }

    // Mount renderer
    mountRef.current.appendChild(renderer.domElement);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    setIsLoading(false);

    // Cleanup
    return () => {
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [proteinData, width, height]);

  const createProteinStructure = (scene, data) => {
    try {
      // Clear existing protein structures
      const existingProtein = scene.getObjectByName('protein');
      if (existingProtein) {
        scene.remove(existingProtein);
      }

      // Create protein group
      const proteinGroup = new THREE.Group();
      proteinGroup.name = 'protein';

      // Create secondary structure elements
      if (data.secondary_structure) {
        createSecondaryStructure(proteinGroup, data.secondary_structure);
      }

      // Create domains if available
      if (data.domains) {
        createDomains(proteinGroup, data.domains);
      }

      // Create binding sites if available
      if (data.binding_sites) {
        createBindingSites(proteinGroup, data.binding_sites);
      }

      // Add protein to scene
      scene.add(proteinGroup);

      // Auto-fit camera to protein
      const box = new THREE.Box3().setFromObject(proteinGroup);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const fov = 75;
      const cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2 * Math.PI / 180));
      
      cameraRef.current.position.set(cameraZ, cameraZ, cameraZ);
      cameraRef.current.lookAt(center);
      controlsRef.current.target.copy(center);

    } catch (err) {
      console.error('Error creating protein structure:', err);
      setError('Failed to render protein structure');
    }
  };

  const createSecondaryStructure = (group, secondaryStructure) => {
    const { helices, sheets, loops } = secondaryStructure;

    // Create alpha helices (red)
    if (helices) {
      helices.forEach((helix, index) => {
        const geometry = new THREE.CylinderGeometry(1, 1, helix.length || 10, 8);
        const material = new THREE.MeshPhongMaterial({ 
          color: 0xff4444,
          transparent: true,
          opacity: 0.8
        });
        const helixMesh = new THREE.Mesh(geometry, material);
        helixMesh.position.set(helix.x || 0, helix.y || 0, helix.z || 0);
        helixMesh.rotation.set(helix.rx || 0, helix.ry || 0, helix.rz || 0);
        helixMesh.name = `helix_${index}`;
        group.add(helixMesh);
      });
    }

    // Create beta sheets (yellow)
    if (sheets) {
      sheets.forEach((sheet, index) => {
        const geometry = new THREE.PlaneGeometry(5, sheet.length || 10);
        const material = new THREE.MeshPhongMaterial({ 
          color: 0xffff44,
          transparent: true,
          opacity: 0.8,
          side: THREE.DoubleSide
        });
        const sheetMesh = new THREE.Mesh(geometry, material);
        sheetMesh.position.set(sheet.x || 0, sheet.y || 0, sheet.z || 0);
        sheetMesh.rotation.set(sheet.rx || 0, sheet.ry || 0, sheet.rz || 0);
        sheetMesh.name = `sheet_${index}`;
        group.add(sheetMesh);
      });
    }

    // Create loops (green)
    if (loops) {
      loops.forEach((loop, index) => {
        const geometry = new THREE.TubeGeometry(
          new THREE.CatmullRomCurve3(loop.points || [
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(5, 5, 5),
            new THREE.Vector3(10, 0, 10)
          ]),
          50,
          0.5,
          8,
          false
        );
        const material = new THREE.MeshPhongMaterial({ 
          color: 0x44ff44,
          transparent: true,
          opacity: 0.7
        });
        const loopMesh = new THREE.Mesh(geometry, material);
        loopMesh.name = `loop_${index}`;
        group.add(loopMesh);
      });
    }
  };

  const createDomains = (group, domains) => {
    domains.forEach((domain, index) => {
      const geometry = new THREE.SphereGeometry(domain.radius || 5, 16, 16);
      const material = new THREE.MeshPhongMaterial({ 
        color: new THREE.Color().setHSL(index / domains.length, 0.7, 0.5),
        transparent: true,
        opacity: 0.3,
        wireframe: true
      });
      const domainMesh = new THREE.Mesh(geometry, material);
      domainMesh.position.set(domain.x || 0, domain.y || 0, domain.z || 0);
      domainMesh.name = `domain_${domain.name || index}`;
      group.add(domainMesh);

      // Add domain label
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      canvas.width = 256;
      canvas.height = 64;
      context.fillStyle = 'white';
      context.font = '24px Arial';
      context.textAlign = 'center';
      context.fillText(domain.name || `Domain ${index + 1}`, 128, 40);

      const texture = new THREE.CanvasTexture(canvas);
      const labelMaterial = new THREE.SpriteMaterial({ map: texture });
      const label = new THREE.Sprite(labelMaterial);
      label.position.set(domain.x || 0, (domain.y || 0) + 8, domain.z || 0);
      label.scale.set(8, 2, 1);
      label.name = `label_${domain.name || index}`;
      group.add(label);
    });
  };

  const createBindingSites = (group, bindingSites) => {
    bindingSites.forEach((site, index) => {
      const geometry = new THREE.SphereGeometry(2, 16, 16);
      const material = new THREE.MeshPhongMaterial({ 
        color: 0xff00ff,
        transparent: true,
        opacity: 0.8,
        emissive: 0x220022
      });
      const siteMesh = new THREE.Mesh(geometry, material);
      siteMesh.position.set(site.x || 0, site.y || 0, site.z || 0);
      siteMesh.name = `binding_site_${index}`;
      group.add(siteMesh);
    });
  };

  const resetView = () => {
    if (controlsRef.current && sceneRef.current) {
      const protein = sceneRef.current.getObjectByName('protein');
      if (protein) {
        const box = new THREE.Box3().setFromObject(protein);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const cameraZ = Math.abs(maxDim / 2 / Math.tan(75 / 2 * Math.PI / 180));
        
        cameraRef.current.position.set(cameraZ, cameraZ, cameraZ);
        controlsRef.current.target.copy(center);
      }
    }
  };

  const toggleWireframe = () => {
    if (sceneRef.current) {
      const protein = sceneRef.current.getObjectByName('protein');
      if (protein) {
        protein.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.wireframe = !child.material.wireframe;
          }
        });
      }
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-2">⚠️</div>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="relative"
    >
      {/* 3D Viewer Container */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden shadow-lg">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-white">Loading 3D Structure...</p>
            </div>
          </div>
        )}
        
        <div 
          ref={mountRef} 
          className="w-full h-full"
          style={{ width, height }}
        />
        
        {/* Controls Overlay */}
        <div className="absolute top-4 right-4 flex flex-col space-y-2">
          <button
            onClick={resetView}
            className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
            title="Reset View"
          >
            🎯 Reset
          </button>
          <button
            onClick={toggleWireframe}
            className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
            title="Toggle Wireframe"
          >
            🔲 Wireframe
          </button>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-black bg-opacity-70 text-white p-3 rounded-md text-sm">
          <div className="font-semibold mb-2">Structure Legend:</div>
          <div className="flex items-center mb-1">
            <div className="w-4 h-4 bg-red-500 rounded mr-2"></div>
            <span>Alpha Helices</span>
          </div>
          <div className="flex items-center mb-1">
            <div className="w-4 h-4 bg-yellow-500 rounded mr-2"></div>
            <span>Beta Sheets</span>
          </div>
          <div className="flex items-center mb-1">
            <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
            <span>Loops</span>
          </div>
          <div className="flex items-center mb-1">
            <div className="w-4 h-4 bg-purple-500 rounded mr-2"></div>
            <span>Binding Sites</span>
          </div>
        </div>
      </div>

      {/* Protein Information */}
      {proteinData && (
        <div className="mt-4 p-4 bg-white rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Protein Structure Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Name:</span> {proteinData.name || 'Unknown'}
            </div>
            <div>
              <span className="font-medium">Length:</span> {proteinData.length || 'Unknown'} amino acids
            </div>
            <div>
              <span className="font-medium">Domains:</span> {proteinData.domains?.length || 0}
            </div>
            <div>
              <span className="font-medium">Binding Sites:</span> {proteinData.binding_sites?.length || 0}
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default Protein3DViewer;

