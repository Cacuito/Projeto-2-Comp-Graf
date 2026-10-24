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

  // Luz 1: SpotLight
  light_position: vec4<f32>,
  spot_direction: vec4<f32>,
  spot_params: vec4<f32>,      // x: cos_cutoff, y: exponent

  // Luz 2: PointLight Adicional
  light2_position: vec4<f32>,
  light2_diffuse: vec4<f32>,

  // Configurações e Efeitos
  camera_position: vec4<f32>,
  clip_plane: vec4<f32>,
  fog_color: vec4<f32>,
  effects_toggle: vec4<f32>,   // x: use_light2, y: use_fog, z: use_clip
}
@group(0) @binding(0) var<uniform> global: Global;

struct Material {
  base_color: vec3<f32>,
  opacity: f32,
  specular_color: vec3<f32>,
  shininess: f32,
}
@group(2) @binding(0) var<uniform> material: Material;

struct VertexOutput {
  @builtin(position) clip_position: vec4<f32>,
  @location(0) normal: vec3<f32>,
  @location(1) frag_pos: vec3<f32>,
  @location(2) view: vec3<f32>,
}

@vertex
fn vs_main(
  @builtin(instance_index) instance_index: u32,
  @location(0) coord: vec3<f32>,
  @location(1) normal: vec3<f32>
) -> VertexOutput {
  let m = matrix[instance_index];
  var out: VertexOutput;

  let pos_world = (m.vertex * vec4<f32>(coord, 1.0)).xyz;
  out.frag_pos = pos_world;
  out.normal = (m.normal * vec4<f32>(normal, 0.0)).xyz;
  out.view = normalize(-pos_world);
  out.clip_position = global.projection * vec4<f32>(pos_world, 1.0);
  return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
  // PLANO DE CORTE
  if (global.effects_toggle.z > 0.5) {
    let dist = dot(vec4<f32>(in.frag_pos, 1.0), global.clip_plane);
    if (dist < 0.0) {
      discard;
    }
  }

  let normal = normalize(in.normal);
  let view = normalize(in.view);
  let base_col = material.base_color;

  // Iluminação Ambiente
  var total_color = base_col * global.light_ambient.rgb;


  // SPOTLIGHT

  let light_vec1 = global.light_position.xyz - in.frag_pos;
  let l1 = normalize(light_vec1);
  let s_dir = normalize(global.spot_direction.xyz);
  let c = -dot(l1, s_dir);

  var k_spot: f32 = 0.0;
  if (c >= global.spot_params.x) {
    k_spot = pow(max(c, 0.0), global.spot_params.y);
  }

  let ndotl1 = max(dot(normal, l1), 0.0);
  if (ndotl1 > 0.0 && k_spot > 0.0) {
    let diff1 = base_col * global.light_diffuse.rgb * ndotl1;
    let refl1 = normalize(reflect(-l1, normal));
    let spec1 = material.specular_color * global.light_specular.rgb * pow(max(0.0, dot(refl1, view)), material.shininess);
    total_color += (diff1 + spec1) * k_spot;
  }


  // POINT LIGHT ADICIONAL (Tecla 1)
  if (global.effects_toggle.x > 0.5) {
    let light_vec2 = global.light2_position.xyz - in.frag_pos;
    let l2 = normalize(light_vec2);
    let ndotl2 = max(dot(normal, l2), 0.0);
    if (ndotl2 > 0.0) {
      let diff2 = base_col * global.light2_diffuse.rgb * ndotl2;
      let refl2 = normalize(reflect(-l2, normal));
      let spec2 = material.specular_color * global.light2_diffuse.rgb * pow(max(0.0, dot(refl2, view)), material.shininess);
      total_color += diff2 + spec2;
    }
  }


  // FOG / NEBLINA (Tecla 2)

  if (global.effects_toggle.y > 0.5) {
    let dist_cam = length(global.camera_position.xyz - in.frag_pos);
    let fog_factor = clamp((dist_cam - 5.0) / (14.0 - 5.0), 0.0, 1.0);
    total_color = mix(total_color, global.fog_color.rgb, fog_factor);
  }

  return vec4<f32>(total_color, 1.0);
}