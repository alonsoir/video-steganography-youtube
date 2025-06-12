#!/usr/bin/env python3
"""
Embedder con opacidad ajustable para encontrar el punto perfecto
Entre invisible al ojo humano pero detectable por algoritmo
"""
import sys

import cv2
import qrcode
import numpy as np
import pickle
import gzip
import base64
from typing import List, Tuple, Dict, Any


class AdjustableOpacityEmbedder:
    def __init__(self, data_file: str = "moby_dick_embeddings.pkl.gz", opacity: float = 0.15):
        """Embedder con opacidad configurable"""
        print("🔍 Cargando datos de Moby Dick...")
        with open(data_file, 'rb') as f:
            self.compressed_data = f.read()
        print(f"📦 Datos cargados: {len(self.compressed_data):,} bytes")

        # Configuración QR ajustable
        self.qr_size = 120  # Ligeramente más grande
        self.max_qr_data = 800
        self.opacity = opacity  # CONFIGURABLE

        print(f"⚙️ Configuración: opacidad={opacity:.3f}, tamaño QR={self.qr_size}px")

    def fragment_data(self) -> List[bytes]:
        """Fragmentar datos en chunks para QR codes"""
        print("✂️ Fragmentando datos para QR codes...")

        total_size = len(self.compressed_data)
        fragments = []

        for i in range(0, total_size, self.max_qr_data):
            chunk = self.compressed_data[i:i + self.max_qr_data]

            fragment_index = i // self.max_qr_data
            total_fragments = (total_size + self.max_qr_data - 1) // self.max_qr_data

            metadata = {
                'idx': fragment_index,
                'total': total_fragments,
                'size': len(chunk),
                'checksum': hash(chunk)
            }

            fragment_package = pickle.dumps(metadata) + b'|SEPARATOR|' + chunk
            fragments.append(fragment_package)

        print(f"📱 Creados {len(fragments)} fragmentos para QR codes")
        return fragments

    def create_optimized_qr(self, data: bytes) -> np.ndarray:
        """Crear QR code optimizado para detección sutil"""

        b64_data = base64.b64encode(data).decode('ascii')

        # Usar corrección de errores alta para resistencia
        error_correction = qrcode.constants.ERROR_CORRECT_H
        if len(b64_data) > 2953:
            error_correction = qrcode.constants.ERROR_CORRECT_L

        qr = qrcode.QRCode(
            version=None,
            error_correction=error_correction,
            box_size=8,
            border=2,
        )

        try:
            qr.add_data(b64_data)
            qr.make(fit=True)
        except ValueError:
            truncated_data = data[:400]
            b64_data = base64.b64encode(truncated_data).decode('ascii')
            qr.clear()
            qr.add_data(b64_data)
            qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((self.qr_size, self.qr_size))

        qr_array = np.array(qr_img.convert("RGB"))

        # Hacer sutil pero detectable
        invisible_qr = qr_array.copy().astype(np.float32)
        mask_black = (qr_array == 0).all(axis=2)
        mask_white = (qr_array == 255).all(axis=2)

        # Ajustar intensidad basada en opacidad
        # Opacidad mayor = diferencias más grandes
        dark_value = max(0, 5 - int(self.opacity * 20))  # 0-5
        light_value = min(255, 250 + int(self.opacity * 20))  # 250-255

        invisible_qr[mask_black] = [dark_value, dark_value, dark_value]
        invisible_qr[mask_white] = [light_value, light_value, light_value]

        return invisible_qr.astype(np.uint8)

    def embed_qr_in_frame(self, frame: np.ndarray, qr_invisible: np.ndarray,
                          position: Tuple[int, int] = None) -> np.ndarray:
        """Embedder QR con opacidad ajustable"""

        frame_modified = frame.copy().astype(np.float32)
        h, w = qr_invisible.shape[:2]

        if position is None:
            # Posición aleatoria pero consistente
            max_x = frame.shape[1] - w - 20
            max_y = frame.shape[0] - h - 20
            x = np.random.randint(20, max_x) if max_x > 20 else 20
            y = np.random.randint(20, max_y) if max_y > 20 else 20
            position = (x, y)

        x, y = position

        if y + h > frame.shape[0] or x + w > frame.shape[1]:
            return frame.astype(np.uint8)

        # Blending con opacidad configurable
        region = frame_modified[y:y + h, x:x + w]
        qr_float = qr_invisible.astype(np.float32)

        blended = (1 - self.opacity) * region + self.opacity * qr_float
        frame_modified[y:y + h, x:x + w] = blended

        return frame_modified.astype(np.uint8)

    def embed_in_video_opencv(self, input_video: str, output_video: str):
        """Procesar video con opacidad ajustable"""

        print(f"🎬 Embeddiendo con opacidad {self.opacity:.3f}...")

        cap = cv2.VideoCapture(input_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📊 Video: {width}x{height}, {fps} FPS, {total_frames} frames")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

        fragments = self.fragment_data()
        frames_per_qr = max(1, total_frames // len(fragments))

        print(f"📊 Distribuyendo {len(fragments)} QR codes")
        print(f"📊 Un QR cada {frames_per_qr} frames")

        # Generar QR codes
        print("🔍 Generando QR codes optimizados...")
        optimized_qrs = []
        for i, fragment in enumerate(fragments):
            if i % 100 == 0:
                print(f"  QR {i + 1}/{len(fragments)}")
            optimized_qrs.append(self.create_optimized_qr(fragment))

        # Procesar frames
        print("🎥 Embeddiendo en frames...")
        frame_count = 0
        qr_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 100 == 0:
                print(f"  Frame {frame_count + 1}/{total_frames}")

            # Embedder QR si corresponde
            if (frame_count % frames_per_qr == 0 and
                    qr_index < len(optimized_qrs)):
                frame = self.embed_qr_in_frame(frame, optimized_qrs[qr_index])
                qr_index += 1

            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        print(f"✅ Video creado: {output_video}")
        print(f"📱 QR codes embeddidos: {qr_index}")
        print(f"⚙️ Opacidad utilizada: {self.opacity:.3f}")


def create_multiple_versions():
    """Crear múltiples versiones con diferentes opacidades para testing"""

    print("🧪 CREANDO MÚLTIPLES VERSIONES PARA TESTING")
    print("=" * 60)

    input_video = "mi_video.mp4"
    opacities = [0.08, 0.12, 0.15]  # Progresivamente más visibles

    for opacity in opacities:
        print(f"\n🎯 Creando versión con opacidad {opacity:.3f}...")

        embedder = AdjustableOpacityEmbedder(opacity=opacity)
        output_video = f"video_opacity_{opacity:.3f}.mp4"

        embedder.embed_in_video_opencv(input_video, output_video)

        print(f"✅ Creado: {output_video}")

    print("\n🎯 ¡VERSIONES CREADAS!")
    print("🔍 Probar extracción con cada versión:")
    for opacity in opacities:
        print(f"  python test_extraction.py video_opacity_{opacity:.3f}.mp4")


def main():
    """
    Crear versión optimizada con opacidad ajustable
    """
    import sys

    if len(sys.argv) > 1:
        try:
            opacity = float(sys.argv[1])
        except ValueError:
            print("❌ Opacidad debe ser un número (ej: 0.12)")
            sys.exit(1)
    else:
        opacity = 0.12  # Valor por defecto más alto

    print(f"🎯 EMBEDDER CON OPACIDAD AJUSTABLE: {opacity:.3f}")
    print("=" * 50)

    embedder = AdjustableOpacityEmbedder(opacity=opacity)

    input_video = "mi_video.mp4"
    output_video = f"video_opacity_{opacity:.3f}.mp4"

    embedder.embed_in_video_opencv(input_video, output_video)

    print(f"\n✅ ¡Video optimizado creado!")
    print(f"📹 Archivo: {output_video}")
    print(f"⚙️ Opacidad: {opacity:.3f}")
    print("\n🔍 Probar extracción:")
    print(f"python decode/extract_hidden_data.py {output_video}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "multiple":
        create_multiple_versions()
    else:
        main()