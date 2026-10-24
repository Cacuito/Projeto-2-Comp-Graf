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
from texture import Texture
from sampler import Sampler
from textureset import TextureSet
from transform import Transform
from node import Node
from scene import Scene
from renderer import Renderer
from cube import Cube
from sphere import Sphere
from quad import Quad

canvas: RenderCanvas
device: wgpu.GPUDevice
context: Any
renderer: Renderer
camera: Camera3D
scene: Scene
spot_light: SpotLight

viewer_pos: gm.Vec3 = gm.vec3(4.0, 5.0, 6.0)

# Estados das teclas de atalho (0.0 = desligado, 1.0 = ligado)
enable_light2: float = 1.0   # Tecla 1: 2ª fonte de luz
enable_fog: float = 0.0      # Tecla 2: Neblina (Fog)
enable_clip: float = 0.0     # Tecla 3: Plano de corte (Clipping Plane)

def initialize(device: wgpu.GPUDevice, target_format: str) -> None:
    global camera, scene, spot_light

    # Câmara e Arcball
    camera = Camera3D(viewer_pos[0], viewer_pos[1], viewer_pos[2])
    arcball = camera.create_arcball()
    arcball.attach(canvas)

    # Fonte de Luz Spot principal
    spot_light = SpotLight(
        pos_x=0.0, pos_y=5.0, pos_z=0.0,
        dir_x=0.0, dir_y=-1.0, dir_z=0.0,
        cutoff_angle=32.0,
        exponent=7.0,
        space="world"
    )
    spot_light.set_effects(enable_light2, enable_fog, enable_clip)

    # Materiais Phong
    mat_table = PhongMaterial(0.45, 0.25, 0.12)    # Marrom / Madeira para a mesa
    mat_box   = PhongMaterial(0.95, 0.70, 0.15)    # Amarelo / Dourado para a caixa
    mat_green = PhongMaterial(0.40, 0.85, 0.40)    # Verde para a esfera menor
    mat_red   = PhongMaterial(0.95, 0.35, 0.35)    # Vermelho para a esfera maior
    mat_white = PhongMaterial(1.0, 1.0, 1.0)       # Branco neutro para a folha de papel

    # Geometrias
    cube = Cube(device)
    sphere = Sphere(device)
    quad = Quad(device)

    # Pipeline: Geometrias 3D Sólidas (Mesa, Caixa e Esferas)
    shader_3d = Shader(device, "../shaders/ilum_frag/proj2.wgsl", light=spot_light, space="world")
    shader_3d.set_vertex_buffers([
        {"array_stride": 3 * 4, "step_mode": "vertex", "attributes": [{"format": "float32x3", "offset": 0, "var_name": "coord"}]},
        {"array_stride": 3 * 4, "step_mode": "vertex", "attributes": [{"format": "float32x3", "offset": 0, "var_name": "normal"}]},
    ])
    pipeline_3d = Pipeline(shader_3d, target_format, primitive={"cull_mode": "back"})

    for m in [mat_table, mat_box, mat_green, mat_red]:
        shader_3d.add_material(m)

    # Pipeline: Papéis Decal
    paper_tex = Texture(device, "decal_texture", "../images/paper.jpg")
    paper_sampler = Sampler(device, "decal_sampler")
    paper_textures = TextureSet([paper_tex, paper_sampler])

    shader_paper = Shader(device, "../shaders/ilum_frag/proj2_paper.wgsl", light=spot_light, space="world")
    shader_paper.set_vertex_buffers([
        {"array_stride": 2 * 4, "step_mode": "vertex", "attributes": [{"format": "float32x2", "offset": 0, "var_name": "coord"}]},
        {"array_stride": 2 * 4, "step_mode": "vertex", "attributes": [{"format": "float32x2", "offset": 0, "var_name": "texcoord"}]},
    ])
    
    pipeline_paper = Pipeline(
        shader_paper,
        target_format,
        primitive={"cull_mode": "none"},
        depth_stencil={"depth_bias": -1, "depth_bias_slope_scale": -1}
    )
    shader_paper.add_material(mat_white)
    shader_paper.add_texture_set(paper_textures)

    # MODELAGEM DA MESA E PERNAS
    trf_top = Transform()
    trf_top.translate(0.0, 0.0, 0.0)
    trf_top.scale(4.0, 0.2, 4.0)
    node_top = Node(None, trf_top, [mat_table], [cube])

    leg_x = 1.75
    leg_z = 1.75
    leg_y = -2.3
    legs_nodes = []
    for dx in [-leg_x, leg_x]:
        for dz in [-leg_z, leg_z]:
            trf_leg = Transform()
            trf_leg.translate(dx, leg_y, dz)
            trf_leg.scale(0.25, 2.4, 0.25)
            legs_nodes.append(Node(None, trf_leg, [mat_table], [cube]))

    # OBJETOS SOBRE A MESA
    trf_box = Transform()
    trf_box.translate(-0.8, 0.2, 0.4)
    trf_box.scale(1.2, 0.6, 1.2)
    node_box = Node(None, trf_box, [mat_box], [cube])

    # Esfera verde
    trf_green = Transform()
    trf_green.translate(-0.8, 1.15, 0.4)
    trf_green.scale(0.35, 0.35, 0.35)
    node_green = Node(None, trf_green, [mat_green], [sphere])

    # Esfera vermelha
    trf_red = Transform()
    trf_red.translate(1.0, 0.8, -0.8)
    trf_red.scale(0.6, 0.6, 0.6)
    node_red = Node(None, trf_red, [mat_red], [sphere])


    # FOLHAS DE PAPEL (Decals na face superior da mesa)

    # Folha 1
    trf_paper1 = Transform()
    trf_paper1.translate(-0.5, 0.204, 0.6)
    trf_paper1.rotate(20.0, 0.0, 1.0, 0.0)
    trf_paper1.rotate(-90.0, 1.0, 0.0, 0.0)
    trf_paper1.scale(0.8, 1.1, 1.0)
    node_paper1 = Node(pipeline_paper, trf_paper1, [mat_white, paper_textures], [quad])

    # Folha 2
    trf_paper2 = Transform()
    trf_paper2.translate(0.6, 0.204, 0.3)
    trf_paper2.rotate(-25.0, 0.0, 1.0, 0.0)
    trf_paper2.rotate(-90.0, 1.0, 0.0, 0.0)
    trf_paper2.scale(0.7, 0.95, 1.0)
    node_paper2 = Node(pipeline_paper, trf_paper2, [mat_white, paper_textures], [quad])

    # Nó raiz contendo todos os objetos 3D e os papéis
    all_nodes = [node_top, *legs_nodes, node_box, node_green, node_red, node_paper1, node_paper2]
    scene = Scene(Node(pipeline_3d, nodes=all_nodes))

def on_key(event: Any) -> None:
    global enable_light2, enable_fog, enable_clip

    if event["key"] == "1":
        enable_light2 = 1.0 - enable_light2
        print(f"[TECLADO] Segunda Luz (PointLight): {'LIGADA' if enable_light2 else 'DESLIGADA'}")
        spot_light.set_effects(enable_light2, enable_fog, enable_clip)
    elif event["key"] == "2":
        enable_fog = 1.0 - enable_fog
        print(f"[TECLADO] Fog (Neblina): {'LIGADO' if enable_fog else 'DESLIGADO'}")
        spot_light.set_effects(enable_light2, enable_fog, enable_clip)
    elif event["key"] == "3":
        enable_clip = 1.0 - enable_clip
        print(f"[TECLADO] Plano de Corte (Clipping Plane): {'LIGADO' if enable_clip else 'DESLIGADO'}")
        spot_light.set_effects(enable_light2, enable_fog, enable_clip)
    elif event["key"] == "q":
        canvas.close()

def draw() -> None:
    target_texture = context.get_current_texture()
    renderer.render(target_texture, scene, camera)

def main() -> None:
    global canvas, device, context, renderer

    canvas = RenderCanvas(size=(900, 650), title="Projeto 2: Mesa 3D com Spot, 2ª Luz, Fog e Corte", update_mode="continuous", max_fps=60)
    adapter = wgpu.gpu.request_adapter_sync()
    device = adapter.request_device_sync()
    context = canvas.get_context("wgpu")

    target_format = context.get_preferred_format(device.adapter)
    context.configure(device=device, format=target_format)

    renderer = Renderer(device, depth_test=True, clear_value=(0.12, 0.12, 0.14, 1.0))

    initialize(device, target_format)

    canvas.add_event_handler(on_key, "key_down")
    canvas.request_draw(draw)
    print("\n================ CONTROLES DO PROJETO 2 ================")
    print(" [1] Alternar Segunda Fonte de Luz (PointLight)")
    print(" [2] Alternar Efeito de Fog (Neblina)")
    print(" [3] Alternar Plano de Corte (Clipping Plane)")
    print(" [Arcball] Clique e arraste para orbitar a cena com o mouse")
    print(" [Q] Fechar aplicação\n=======================================================\n")
    loop.run()

if __name__ == "__main__":
    main()