from __future__ import annotations

import math
from typing import Any

import graphics_math as gm
from light import Light


class SpotLight(Light):
    """Fonte de luz do tipo Spot com suporte a luz adicional e efeitos"""

    def __init__(
        self,
        pos_x: float,
        pos_y: float,
        pos_z: float,
        dir_x: float,
        dir_y: float,
        dir_z: float,
        cutoff_angle: float = 30.0,
        exponent: float = 10.0,
        space: str = "world",
        **values: Any,
    ) -> None:
        super().__init__(space, **values)
        self.set_position(pos_x, pos_y, pos_z)
        self.set_direction(dir_x, dir_y, dir_z)
        self.set_spot_params(cutoff_angle, exponent)

        # Valores padrão para os efeitos adicionais do Projeto 2
        self.set("light2_position", gm.vec4(4.0, 3.0, 4.0, 1.0))
        self.set("light2_diffuse", gm.vec4(0.4, 0.4, 0.45, 1.0))
        self.set("camera_position", gm.vec4(4.0, 5.0, 6.0, 1.0))
        self.set("clip_plane", gm.vec4(0.0, -1.0, 0.0, 0.6))
        self.set("fog_color", gm.vec4(0.12, 0.12, 0.14, 1.0))
        # x: light2 (1=on), y: fog (0=off), z: clip (0=off), w: reserva
        self.set("effects_toggle", gm.vec4(1.0, 0.0, 0.0, 0.0))

    def set_position(self, x: float, y: float, z: float) -> None:
        self.set("light_position", gm.vec4(x, y, z, 1.0))

    def set_direction(self, x: float, y: float, z: float) -> None:
        length = math.sqrt(x * x + y * y + z * z)
        if length > 0.0:
            x, y, z = x / length, y / length, z / length
        self.set("spot_direction", gm.vec4(x, y, z, 0.0))

    def set_spot_params(self, cutoff_angle_degrees: float, exponent: float) -> None:
        rad = math.radians(cutoff_angle_degrees)
        cos_cutoff = math.cos(rad)
        self.set("spot_params", gm.vec4(cos_cutoff, exponent, 0.0, 0.0))

    def set_effects(self, enable_light2: float, enable_fog: float, enable_clip: float) -> None:
        self.set("effects_toggle", gm.vec4(enable_light2, enable_fog, enable_clip, 0.0))

    def map(self, matrix: gm.Mat4) -> dict[str, Any]:
        position = self.get("light_position")
        direction = self.get("spot_direction")
        light2_pos = self.get("light2_position")

        # Retorna o dicionário completo que o Shader mapeia na struct Global
        return {
            "light_position": matrix @ position,
            "spot_direction": matrix @ direction,
            "spot_params": self.get("spot_params"),
            "light2_position": matrix @ light2_pos,
            "light2_diffuse": self.get("light2_diffuse"),
            "camera_position": self.get("camera_position"),
            "clip_plane": self.get("clip_plane"),
            "fog_color": self.get("fog_color"),
            "effects_toggle": self.get("effects_toggle"),
        }