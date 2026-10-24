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
  spot_params: vec4<f32>,      // x: cos_theta, y: s_exp
  camera_position: vec4<f32>,
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

  let pos_space = (m.vertex * vec4<f32>(coord, 1.0)).xyz;
  out.frag_pos = pos_space;
  out.normal = (m.normal * vec4<f32>(normal, 0.0)).xyz;
  out.view = normalize(-pos_space);
  out.clip_position = global.projection * vec4<f32>(pos_space, 1.0);
  return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
  let normal = normalize(in.normal);
  let view = normalize(in.view);

  // Vetor l: aponta do ponto iluminado para a fonte de luz
  let light_vec = global.light_position.xyz - in.frag_pos;
  let l = normalize(light_vec);

  // Direcao central do spot
  let s_dir = normalize(global.spot_direction.xyz);

  // c = -l . s_dir (cosseno do angulo entre s_dir e a direcao do feixe para o ponto)
  let c = -dot(l, s_dir);

  let cos_theta = global.spot_params.x;
  let s_exp = global.spot_params.y;

  // Calculo do coeficiente de spot
  var k_spot: f32 = 0.0;
  if (c >= cos_theta) {
    k_spot = pow(max(c, 0.0), s_exp);
  }

  // Componente ambiente nao e atenuada pelo cone do spot
  var color = material.base_color * global.light_ambient.rgb;

  let ndotl = dot(normal, l);
  if (ndotl > 0.0 && k_spot > 0.0) {
    let diffuse = material.base_color * global.light_diffuse.rgb * ndotl;
    let refl = normalize(reflect(-l, normal));
    let specular = material.specular_color * global.light_specular.rgb * pow(max(0.0, dot(refl, view)), material.shininess);

    color += (diffuse + specular) * k_spot;
  }

  return vec4<f32>(color, 1.0);
}