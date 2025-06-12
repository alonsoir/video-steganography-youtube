#!/usr/bin/env python3
"""
Test progresivo para encontrar la opacidad mínima detectable
Crear videos con diferentes opacidades y probar detección
"""

import cv2
import qrcode
import numpy as np
import pickle
import base64
from typing import List, Tuple
import os


class ProgressiveOpacityTester:
    def __init__(self, data_file: str = "moby_dick_embeddings.pkl.gz"):
        """Tester progresivo de opacidades"""
        print("🔍 Cargando datos de Moby Dick...")
        with open(data_file, 'rb') as f:
            self.compressed_data = f.read()

        self.qr_size = 120
        self.max_qr_data = 800

    def create_single_test_qr(self) -> bytes:
        """Crear un solo fragmento de prueba"""
        # Usar solo los primeros 400 bytes para test rápido
        test_data = self.compressed_data[:400]

        metadata = {
            'idx': 0,
            'total': 1,
            'size': len(test_data),
            'checksum': hash(test_data)
        }

        fragment_package = pickle.dumps(metadata) + b'|SEPARATOR|' + test_data
        return fragment_package

    def create_test_qr_image(self, data: bytes, opacity_factor: float = 1.0) -> np.ndarray:
        """Crear QR de prueba con opacidad específica"""

        b64_data = base64.b64encode(data).decode('ascii')

        qr = qrcode.QRCode(
            version=10,  # Versión fija para consistencia
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )

        qr.add_data(b64_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((self.qr_size, self.qr_size))
        qr_array = np.array(qr_img.convert("RGB"))

        # Aplicar factor de opacidad para hacer más o menos sutil
        invisible_qr = qr_array.copy().astype(np.float32)
        mask_black = (qr_array == 0).all(axis=2)
        mask_white = (qr_array == 255).all(axis=2)

        # Calcular valores basados en factor de opacidad
        dark_value = max(0, 10 - int(opacity_factor * 30))
        light_value = min(255, 245 + int(opacity_factor * 30))

        invisible_qr[mask_black] = [dark_value, dark_value, dark_value]
        invisible_qr[mask_white] = [light_value, light_value, light_value]

        return invisible_qr.astype(np.uint8)

    def create_test_frame(self, opacity: float) -> np.ndarray:
        """Crear frame de prueba con QR embebido"""

        # Crear frame base (gris uniforme para mejor contraste)
        frame = np.full((400, 600, 3), 128, dtype=np.uint8)  # Gris medio

        # Crear QR de prueba
        test_fragment = self.create_single_test_qr()
        qr_image = self.create_test_qr_image(test_fragment, opacity_factor=opacity)

        # Embedder QR en posición fija
        x, y = 50, 50
        h, w = qr_image.shape[:2]

        # Blending con opacidad especificada
        region = frame[y:y + h, x:x + w].astype(np.float32)
        qr_float = qr_image.astype(np.float32)

        blended = (1 - opacity) * region + opacity * qr_float
        frame[y:y + h, x:x + w] = blended.astype(np.uint8)

        # Añadir texto informativo
        cv2.putText(frame, f"Opacity: {opacity:.3f}", (200, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def test_detection_sensitivity(self, frame: np.ndarray, opacity: float) -> bool:
        """Probar si nuestro detector puede encontrar el QR en este frame"""

        # Usar el mismo algoritmo que en el extractor
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Analizar región donde sabemos que está el QR
        x, y = 50, 50
        size = self.qr_size
        region = gray[y:y + size, x:x + size]

        # Buscar valores característicos de QR invisible
        very_dark = np.sum((region >= 0) & (region <= 15))  # Casi negro
        very_light = np.sum((region >= 240) & (region <= 255))  # Casi blanco

        print(f"    Opacidad {opacity:.3f}: dark_pixels={very_dark}, light_pixels={very_light}")

        # Criterio de detección
        threshold = 200  # Ajustable
        detected = very_dark > threshold and very_light > threshold

        return detected

    def run_progressive_test(self):
        """Ejecutar test progresivo de opacidades"""

        print("🧪 TEST PROGRESIVO DE OPACIDADES")
        print("🎯 Encontrando opacidad mínima detectable")
        print("=" * 60)

        # Rango de opacidades a probar
        opacities = [0.05, 0.08, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

        detected_opacities = []

        for opacity in opacities:
            print(f"\n🔍 Probando opacidad {opacity:.3f}...")

            # Crear frame de prueba
            test_frame = self.create_test_frame(opacity)

            # Guardar frame para inspección visual
            filename = f"test_opacity_{opacity:.3f}.png"
            cv2.imwrite(filename, test_frame)

            # Probar detección
            detected = self.test_detection_sensitivity(test_frame, opacity)

            if detected:
                print(f"    ✅ DETECTADO con opacidad {opacity:.3f}")
                detected_opacities.append(opacity)
            else:
                print(f"    ❌ NO detectado con opacidad {opacity:.3f}")

        print(f"\n📊 RESULTADOS:")
        print(f"🔍 Opacidades probadas: {len(opacities)}")
        print(f"✅ Opacidades detectables: {len(detected_opacities)}")

        if detected_opacities:
            min_detectable = min(detected_opacities)
            print(f"🎯 Opacidad mínima detectable: {min_detectable:.3f}")
            print(f"💡 Recomendación: Usar opacidad {min_detectable + 0.02:.3f} para margen de seguridad")

            return min_detectable
        else:
            print("❌ NINGUNA opacidad fue detectable")
            print("💡 Necesitas:")
            print("  1. Mejorar algoritmo de detección")
            print("  2. Usar opacidades más altas (>0.5)")
            print("  3. Verificar que el embedding funciona")

            return None

    def create_optimized_video(self, input_video: str, optimal_opacity: float):
        """Crear video con opacidad optimizada"""

        print(f"\n🎬 Creando video con opacidad optimizada: {optimal_opacity:.3f}")

        from embed_with_adjustable_opacity import AdjustableOpacityEmbedder

        embedder = AdjustableOpacityEmbedder(opacity=optimal_opacity)
        output_video = f"video_optimized_{optimal_opacity:.3f}.mp4"

        embedder.embed_in_video_opencv(input_video, output_video)

        print(f"✅ Video optimizado: {output_video}")
        return output_video


def main():
    """
    Ejecutar test progresivo completo
    """
    tester = ProgressiveOpacityTester()

    # Ejecutar test de opacidades
    optimal_opacity = tester.run_progressive_test()

    if optimal_opacity:
        print(f"\n🚀 CREANDO VIDEO CON OPACIDAD OPTIMIZADA")

        # Crear video con opacidad óptima
        input_video = "mi_video.mp4"
        optimized_video = tester.create_optimized_video(input_video, optimal_opacity + 0.02)

        print(f"\n🎯 SIGUIENTE PASO:")
        print(f"python decode/extract_hidden_data.py {optimized_video}")
    else:
        print(f"\n⚠️ NO SE ENCONTRÓ OPACIDAD DETECTABLE")
        print(f"💡 Opciones:")
        print(f"  1. Crear video con QR codes muy visibles para testing")
        print(f"  2. Mejorar algoritmo de detección")
        print(f"  3. Usar opacidades más altas (0.6-0.8)")


if __name__ == "__main__":
    main()