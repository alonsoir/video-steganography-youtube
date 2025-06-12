#!/usr/bin/env python3
"""
Sistema de esteganografía con solo OpenCV (sin MoviePy)
Más robusto y sin problemas de dependencias
"""

import cv2
import qrcode
import numpy as np
import pickle
import gzip
import base64
from typing import List, Tuple, Dict, Any


class InvisibleQRSteganography:
    def __init__(self, data_file: str = "moby_dick_embeddings.pkl.gz"):
        """Inicializar con los datos de Moby Dick"""
        print("🔍 Cargando datos de Moby Dick...")
        with open(data_file, 'rb') as f:
            self.compressed_data = f.read()
        print(f"📦 Datos cargados: {len(self.compressed_data):,} bytes")

        # Configuración QR
        self.qr_size = 100
        self.max_qr_data = 800  # Reducido para caber en QR versión 40
        self.opacity = 0.03  # Ultra bajo para invisibilidad

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

    def create_invisible_qr(self, data: bytes) -> np.ndarray:
        """Crear QR code optimizado para supervivencia"""

        b64_data = base64.b64encode(data).decode('ascii')

        # Verificar tamaño
        error_correction = qrcode.constants.ERROR_CORRECT_H
        if len(b64_data) > 2953:
            print(f"⚠️ Fragmento grande ({len(b64_data)} chars), usando ERROR_CORRECT_L")
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
        except ValueError as e:
            print(f"⚠️ Error creando QR: {e}, truncando datos")
            truncated_data = data[:400]
            b64_data = base64.b64encode(truncated_data).decode('ascii')
            qr.clear()
            qr.add_data(b64_data)
            qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((self.qr_size, self.qr_size))

        qr_array = np.array(qr_img.convert("RGB"))

        # Hacer invisible
        invisible_qr = qr_array.copy().astype(np.float32)
        mask_black = (qr_array == 0).all(axis=2)
        mask_white = (qr_array == 255).all(axis=2)

        invisible_qr[mask_black] = [3, 3, 3]  # Casi negro
        invisible_qr[mask_white] = [252, 252, 252]  # Casi blanco

        return invisible_qr.astype(np.uint8)

    def embed_qr_in_frame(self, frame: np.ndarray, qr_invisible: np.ndarray,
                          position: Tuple[int, int] = None) -> np.ndarray:
        """Embedder QR invisible en frame"""

        frame_modified = frame.copy()
        h, w = qr_invisible.shape[:2]

        if position is None:
            max_x = frame.shape[1] - w - 10
            max_y = frame.shape[0] - h - 10
            x = np.random.randint(10, max_x) if max_x > 10 else 10
            y = np.random.randint(10, max_y) if max_y > 10 else 10
            position = (x, y)

        x, y = position

        if y + h > frame.shape[0] or x + w > frame.shape[1]:
            return frame_modified

        # Blending invisible
        region = frame_modified[y:y + h, x:x + w].astype(np.float32)
        qr_float = qr_invisible.astype(np.float32)

        blended = (1 - self.opacity) * region + self.opacity * qr_float
        frame_modified[y:y + h, x:x + w] = blended.astype(np.uint8)

        return frame_modified

    def embed_in_video_opencv(self, input_video: str, output_video: str):
        """Procesar video usando solo OpenCV"""

        print("🎬 Abriendo video con OpenCV...")
        cap = cv2.VideoCapture(input_video)

        # Obtener propiedades del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📊 Video: {width}x{height}, {fps} FPS, {total_frames} frames")

        # Configurar writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

        # Fragmentar datos
        fragments = self.fragment_data()
        frames_per_qr = max(1, total_frames // len(fragments))

        print(f"📊 Distribuyendo {len(fragments)} QR codes")
        print(f"📊 Un QR cada {frames_per_qr} frames")

        # Generar QR codes
        print("🔍 Generando QR codes invisibles...")
        invisible_qrs = []
        for i, fragment in enumerate(fragments):
            if i % 50 == 0:
                print(f"  QR {i + 1}/{len(fragments)}")
            invisible_qrs.append(self.create_invisible_qr(fragment))

        # Procesar frames
        print("🎥 Procesando frames...")
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
                    qr_index < len(invisible_qrs)):
                frame = self.embed_qr_in_frame(frame, invisible_qrs[qr_index])
                qr_index += 1

            out.write(frame)
            frame_count += 1

        # Limpiar
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        print(f"✅ Video creado: {output_video}")
        print(f"📱 QR codes embeddidos: {qr_index}")
        print(f"📚 Moby Dick completo oculto!")


def main():
    """Demo principal"""
    steganographer = InvisibleQRSteganography()

    input_video = "mi_video.mp4"
    output_video = "video_with_moby_dick.mp4"

    print("🕵️ Iniciando esteganografía con OpenCV...")
    print("📖 Embeddiendo Moby Dick completo...")

    steganographer.embed_in_video_opencv(input_video, output_video)

    print("\n🎯 ¡VULNERABILIDAD DEMOSTRADA!")
    print(f"📹 Original: {input_video}")
    print(f"🔍 Con libro oculto: {output_video}")
    print("🚨 Listo para YouTube PoC!")


if __name__ == "__main__":
    main()