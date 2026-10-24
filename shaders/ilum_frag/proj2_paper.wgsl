struct Matrix {
  vertex: mat4x4<f32>,
  normal: mat4x4<f32>,
}
@group(1) @binding(0) var<storage, read> matrix: array<Matrix>;

struct Global {
  projection: mat4x4<f32>,
  light_ambient: vec3<f32>,
  light_diffuse: vec3<f32>,
  light_specular: vec3<f32>,
  light_position: vec4<f32>,
  spot_direction: vec4<f32>,
  spot_params: vec4<f32>,
  light2_position: vec4<f32>,
  light2_diffuse: vec4<f32>,
  camera_position: vec4<f32>,
  clip_plane: vec4<f32>,
  fog_color: vec4<f32>,
  effects_toggle: vec4<f32>,
}
@group(0) @binding(0) var<uniform> global: Global;

struct Material {
  base_color: vec3<f32>,
  opacity: f32,
  specular_color: vec3<f32>,
  shininess: f32,
}
@group(2) @binding(0) var<uniform> material: Material;

@group(3) @binding(0) var decal_texture: texture_2d<f32>;
@group(3) @binding(1) var decal_sampler: sampler;

struct VertexOutput {
  @builtin(position) clip_position: vec4<f32>,
  @location(0) frag_pos: vec3<f32>,
  @location(1) uv: vec2<f32>,
}

@vertex
fn vs_main(
  @builtin(instance_index) instance_index: u32,
  @location(0) coord: vec2<f32>,
  @location(1) texcoord: vec2<f32>
) -> VertexOutput {
  let m = matrix[instance_index];
  var out: VertexOutput;

  // Quad 2D no plano XY transformado pela matriz do nó
  let pos_world = (m.vertex * vec4<f32>(coord, 0.0, 1.0)).xyz;
  out.frag_pos = pos_world;
  out.uv = texcoord;
  out.clip_position = global.projection * vec4<f32>(pos_world, 1.0);
  return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
  // Efeito de Plano de Corte
  if (global.effects_toggle.z > 0.5) {
    let dist = dot(vec4<f32>(in.frag_pos, 1.0), global.clip_plane);
    if (dist < 0.0) {
      discard;
    }
  }

  // Amostragem da folha de papel
  let tex_val = textureSample(decal_texture, decal_sampler, in.uv);
  var color = tex_val.rgb * material.base_color;

  // Efeito de Fog no papel
  if (global.effects_toggle.y > 0.5) {
    let dist_cam = length(global.camera_position.xyz - in.frag_pos);
    let fog_factor = clamp((dist_cam - 5.0) / (14.0 - 5.0), 0.0, 1.0);
    color = mix(color, global.fog_color.rgb, fog_factor);
  }

  return vec4<f32>(color, 1.0);
}