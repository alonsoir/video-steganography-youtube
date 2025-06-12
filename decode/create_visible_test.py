#!/usr/bin/env python3
"""
Crear versión de prueba con QR codes VISIBLES
Para verificar que el pipeline completo funciona
Luego graduarlo a invisible
"""

import cv2
import qrcode
import numpy as np
import pickle
import gzip
import base64
from typing import List, Tuple, Dict, Any


class VisibleTestEmbedder:
    def __init__(self, data_file: str = "moby_dick_embeddings.pkl.gz"):
        """Embedder de prueba con QR codes visibles"""
        print("🔍 Cargando datos de Moby Dick...")
        with open(data_file, 'rb') as f:
            self.compressed_data = f.read()
        print(f"📦 Datos cargados: {len(self.compressed_data):,} bytes")

        # Configuración QR para prueba
        self.qr_size = 150  # Más grande para mejor detección
        self.max_qr_data = 800
        self.opacity = 0.3  # MUY visible para testing

    def fragment_data(self) -> List[bytes]:
        """Fragmentar datos (mismo que versión invisible)"""
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

    def create_visible_qr(self, data: bytes) -> np.ndarray:
        """Crear QR code MUY VISIBLE para testing"""

        b64_data = base64.b64encode(data).decode('ascii')

        # Verificar tamaño
        error_correction = qrcode.constants.ERROR_CORRECT_H
        if len(b64_data) > 2953:
            error_correction = qrcode.constants.ERROR_CORRECT_L

        qr = qrcode.QRCode(
            version=None,
            error_correction=error_correction,
            box_size=10,  # Más grande
            border=4,  # Borde más visible
        )

        try:
            qr.add_data(b64_data)
            qr.make(fit=True)
        except ValueError:
            # Fallback para datos grandes
            truncated_data = data[:400]
            b64_data = base64.b64encode(truncated_data).decode('ascii')
            qr.clear()
            qr.add_data(b64_data)
            qr.make(fit=True)

        # Crear imagen QR VISIBLE
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((self.qr_size, self.qr_size))

        # Convertir a array numpy
        qr_array = np.array(qr_img.convert("RGB"))

        return qr_array

    def embed_qr_in_frame(self, frame: np.ndarray, qr_visible: np.ndarray,
                          position: Tuple[int, int] = None) -> np.ndarray:
        """Embedder QR VISIBLE en frame"""

        frame_modified = frame.copy().astype(np.float32)
        h, w = qr_visible.shape[:2]

        if position is None:
            # Posición fija para testing
            x, y = 50, 50
        else:
            x, y = position

        # Verificar límites
        if y + h > frame.shape[0] or x + w > frame.shape[1]:
            return frame.astype(np.uint8)

        # Blending VISIBLE para testing
        region = frame_modified[y:y + h, x:x + w]
        qr_float = qr_visible.astype(np.float32)

        # Mezcla visible (opacidad alta)
        blended = (1 - self.opacity) * region + self.opacity * qr_float
        frame_modified[y:y + h, x:x + w] = blended

        return frame_modified.astype(np.uint8)

    def create_test_video(self, input_video: str, output_video: str, max_qrs: int = 10):
        """Crear video de prueba con QR codes visibles"""

        print("🎬 Creando video de prueba con QR codes VISIBLES...")

        cap = cv2.VideoCapture(input_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📊 Video: {width}x{height}, {fps} FPS, {total_frames} frames")

        # Configurar writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

        # Fragmentar datos (solo primeros fragmentos para testing)
        fragments = self.fragment_data()[:max_qrs]

        frames_per_qr = max(1, total_frames // len(fragments))
        print(f"📊 Embeddiendo {len(fragments)} QR codes de prueba")
        print(f"📊 Un QR cada {frames_per_qr} frames")

        # Generar QR codes visibles
        print("🔍 Generando QR codes VISIBLES...")
        visible_qrs = []
        for i, fragment in enumerate(fragments):
            qr_array = self.create_visible_qr(fragment)
            visible_qrs.append(qr_array)
            print(f"  QR {i + 1}/{len(fragments)} generado")

        # Procesar frames
        print("🎥 Procesando frames...")
        frame_count = 0
        qr_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Embedder QR si corresponde
            if (frame_count % frames_per_qr == 0 and
                    qr_index < len(visible_qrs)):
                # Posición visible y diferente para cada QR
                x = 50 + (qr_index % 3) * 200
                y = 50 + (qr_index // 3) * 200

                frame = self.embed_qr_in_frame(frame, visible_qrs[qr_index], (x, y))
                print(f"  QR {qr_index + 1} embebido en frame {frame_count} en posición ({x},{y})")
                qr_index += 1

            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        print(f"✅ Video de prueba creado: {output_video}")
        print(f"📱 QR codes embebidos: {qr_index}")
        print("👁️ QR codes son VISIBLES para testing")

        return output_video


def main():
    """
    Crear video de prueba con QR codes visibles
    """
    print("🧪 CREADOR DE VIDEO DE PRUEBA")
    print("🎯 QR codes VISIBLES para verificar pipeline")
    print("=" * 50)

    embedder = VisibleTestEmbedder()

    input_video = "mi_video.mp4"
    test_video = "test_visible_qr.mp4"

    # Crear video de prueba
    embedder.create_test_video(input_video, test_video, max_qrs=5)

    print("\n✅ ¡Video de prueba creado!")
    print(f"📹 Archivo: {test_video}")
    print("👁️ Los QR codes son claramente visibles")
    print("\n🔍 Siguiente paso:")
    print(f"python debug_extraction.py  # Cambiar video_path a '{test_video}'")


if __name__ == "__main__":
    main()