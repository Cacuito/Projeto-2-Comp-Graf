from __future__ import annotations

from typing import Any

import graphics_math as gm
import wgpu
from rendercanvas.glfw import RenderCanvas, loop

from camera3d import Camera3D
from spotlight import SpotLight
from shader import Shader
from pipeline import Pipeline
from phongmaterial import PhongMaterial
from transform import Transform
from node import Node
from scene import Scene
from renderer import Renderer
from cube import Cube
from sphere import Sphere

canvas: RenderCanvas
device: wgpu.GPUDevice
context: Any
renderer: Renderer
camera: Camera3D
scene: Scene

# Posição inicial da câmara em perspectiva (visão inclinada e superior)
viewer_pos: gm.Vec3 = gm.vec3(4.0, 5.0, 6.0)

def initialize(device: wgpu.GPUDevice, target_format: str) -> None:
    global camera, scene

    # 1. Configuração da câmara e do manipulador Arcball
    camera = Camera3D(viewer_pos[0], viewer_pos[1], viewer_pos[2])
    arcball = camera.create_arcball()
    arcball.attach(canvas)

    # 2. Fonte de luz de Spot
    # Posicionada acima da mesa em (0.0, 5.0, 0.0), apontando diretamente para baixo (0.0, -1.0, 0.0)
    # Ângulo de corte (cutoff_angle) de 30 graus e expoente de concentração (exponent) de 8.0
    light = SpotLight(
        pos_x=0.0, pos_y=5.0, pos_z=0.0,
        dir_x=0.0, dir_y=-1.0, dir_z=0.0,
        cutoff_angle=30.0,
        exponent=8.0,
        space="world"
    )

    # 3. Materiais Phong (Cores inspiradas na ilustração)
    mat_table = PhongMaterial(0.92, 0.92, 0.94)    # Branco / Cinzento claro (Mesa)
    mat_box   = PhongMaterial(0.95, 0.70, 0.15)    # Amarelo / Dourado (Caixa)
    mat_green = PhongMaterial(0.40, 0.85, 0.40)    # Verde (Esfera menor)
    mat_red   = PhongMaterial(0.95, 0.35, 0.35)    # Vermelho (Esfera maior)

    # 4. Geometrias 3D
    cube = Cube(device)
    sphere = Sphere(device)

    # ==========================
    # MODELAGEM DA MESA (exata da tarefa 2.1)
    # ==========================
    trf_top = Transform()
    trf_top.translate(0.0, 0.0, 0.0)
    trf_top.scale(4.0, 0.2, 4.0)
    node_top = Node(None, trf_top, [mat_table], [cube])

    # 4 Pernas da mesa
    leg_x = 1.75
    leg_z = 1.75
    leg_y = -2.3  # Abaixo do tampo

    legs_nodes = []
    for dx in [-leg_x, leg_x]:
        for dz in [-leg_z, leg_z]:
            trf_leg = Transform()
            trf_leg.translate(dx, leg_y, dz)
            trf_leg.scale(0.25, 2.4, 0.25)
            legs_nodes.append(Node(None, trf_leg, [mat_table], [cube]))

    # ==========================
    # OBJETOS SOBRE A MESA (exatos da tarefa 2.1)
    # ==========================
    # Caixa amarela sobre a mesa (lado esquerdo)
    trf_box = Transform()
    trf_box.translate(-0.8, 0.2, 0.4)
    trf_box.scale(1.2, 0.6, 1.2)
    node_box = Node(None, trf_box, [mat_box], [cube])

    # Esfera pequena verde (em cima da caixa amarela)
    trf_green_sphere = Transform()
    trf_green_sphere.translate(-0.8, 1.15, 0.4)
    trf_green_sphere.scale(0.35, 0.35, 0.35)
    node_green_sphere = Node(None, trf_green_sphere, [mat_green], [sphere])

    # Esfera maior vermelha (apoiada sobre o tampo da mesa, lado direito)
    trf_red_sphere = Transform()
    trf_red_sphere.translate(1.0, 0.8, -0.8)
    trf_red_sphere.scale(0.6, 0.6, 0.6)
    node_red_sphere = Node(None, trf_red_sphere, [mat_red], [sphere])

    # 5. Configuração do Shader 3D e Pipeline (iluminação por fragmento com spot)
    shader = Shader(device, "../shaders/ilum_frag/spot.wgsl", light=light, space="world")
    shader.set_vertex_buffers([
        {"array_stride": 3 * 4, "step_mode": "vertex",
         "attributes": [{"format": "float32x3", "offset": 0, "var_name": "coord"}]},
        {"array_stride": 3 * 4, "step_mode": "vertex",
         "attributes": [{"format": "float32x3", "offset": 0, "var_name": "normal"}]},
    ])
    pipeline = Pipeline(shader, target_format, primitive={"cull_mode": "back"})

    # Registo dos materiais
    shader.add_material(mat_table)
    shader.add_material(mat_box)
    shader.add_material(mat_green)
    shader.add_material(mat_red)

    # 6. Grafo de Cena
    all_objects = [node_top, *legs_nodes, node_box, node_green_sphere, node_red_sphere]
    root = Node(pipeline, nodes=all_objects)
    scene = Scene(root)

def draw() -> None:
    target_texture = context.get_current_texture()
    renderer.render(target_texture, scene, camera)

def on_key(event: Any) -> None:
    if event["key"] == "q":
        canvas.close()

def main() -> None:
    global canvas, device, context, renderer

    canvas = RenderCanvas(size=(800, 600), title="Tarefa 2.2 - Luz de Spot", update_mode="continuous", max_fps=60)
    adapter = wgpu.gpu.request_adapter_sync()
    device = adapter.request_device_sync()
    context = canvas.get_context("wgpu")

    target_format = context.get_preferred_format(device.adapter)
    context.configure(device=device, format=target_format)

    # Fundo escuro para contrastar e tornar o feixe cónico do spot visível
    renderer = Renderer(device, depth_test=True, clear_value=(0.08, 0.08, 0.10, 1.0))

    initialize(device, target_format)

    canvas.add_event_handler(on_key, "key_down")
    canvas.request_draw(draw)
    loop.run()

if __name__ == "__main__":
    main()