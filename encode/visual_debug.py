#!/usr/bin/env python3
"""
Debug visual para entender exactamente qué valores RGB estamos generando
y ajustar el detector en consecuencia
"""

import cv2
import qrcode
import numpy as np
import pickle
import base64
import matplotlib.pyplot as plt
from typing import List, Tuple
import os


class VisualDebugger:
    def __init__(self, data_file: str = "moby_dick_embeddings.pkl.gz"):
        """Debug visual completo"""
        print("🔍 Cargando datos de Moby Dick...")
        with open(data_file, 'rb') as f:
            self.compressed_data = f.read()

        self.qr_size = 120

    def create_debug_qr(self) -> bytes:
        """Crear fragmento simple para debug"""
        test_data = self.compressed_data[:400]

        metadata = {
            'idx': 0,
            'total': 1,
            'size': len(test_data),
            'checksum': hash(test_data)
        }

        return pickle.dumps(metadata) + b'|SEPARATOR|' + test_data

    def create_standard_qr(self, data: bytes) -> np.ndarray:
        """Crear QR code estándar (blanco y negro puro)"""

        b64_data = base64.b64encode(data).decode('ascii')

        qr = qrcode.QRCode(
            version=10,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )

        qr.add_data(b64_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((self.qr_size, self.qr_size))

        return np.array(qr_img.convert("RGB"))

    def apply_steganography_transform(self, qr_array: np.ndarray, opacity_factor: float) -> np.ndarray:
        """Aplicar transformación de esteganografía y mostrar valores exactos"""

        print(f"\n🔬 Analizando transformación con factor {opacity_factor:.3f}:")

        # Copiar array original
        invisible_qr = qr_array.copy().astype(np.float32)

        # Crear máscaras
        mask_black = (qr_array == 0).all(axis=2)
        mask_white = (qr_array == 255).all(axis=2)

        print(f"  📊 Píxeles negros originales: {np.sum(mask_black)}")
        print(f"  📊 Píxeles blancos originales: {np.sum(mask_white)}")

        # Calcular valores como en el embedder original
        dark_value = max(0, 10 - int(opacity_factor * 30))
        light_value = min(255, 245 + int(opacity_factor * 30))

        print(f"  🎯 Valor oscuro calculado: {dark_value}")
        print(f"  🎯 Valor claro calculado: {light_value}")

        # Aplicar transformación
        invisible_qr[mask_black] = [dark_value, dark_value, dark_value]
        invisible_qr[mask_white] = [light_value, light_value, light_value]

        # Verificar valores reales después de la transformación
        result = invisible_qr.astype(np.uint8)

        # Analizar valores únicos en la imagen resultante
        unique_values = np.unique(result.reshape(-1, 3), axis=0)
        print(f"  📈 Valores RGB únicos en imagen resultante:")
        for i, rgb in enumerate(unique_values[:10]):  # Mostrar solo primeros 10
            count = np.sum(np.all(result == rgb, axis=2))
            print(f"    RGB{tuple(rgb)}: {count} píxeles")

        return result

    def embed_and_analyze_blending(self, opacity: float):
        """Crear frame con blending y analizar valores finales"""

        print(f"\n🎨 ANÁLISIS DE BLENDING CON OPACIDAD {opacity:.3f}")
        print("=" * 50)

        # Crear frame base gris
        frame = np.full((400, 600, 3), 128, dtype=np.uint8)
        print(f"🖼️ Frame base: RGB(128, 128, 128) - gris medio")

        # Crear QR transformado
        test_fragment = self.create_debug_qr()
        qr_standard = self.create_standard_qr(test_fragment)
        qr_transformed = self.apply_steganography_transform(qr_standard, opacity)

        # Embedder con blending
        x, y = 50, 50
        h, w = qr_transformed.shape[:2]

        print(f"\n🔀 Aplicando blending con opacidad {opacity:.3f}:")

        # Región original
        region = frame[y:y + h, x:x + w].astype(np.float32)
        qr_float = qr_transformed.astype(np.float32)

        print(f"  📊 Muestra región original: RGB{tuple(region[10, 10].astype(int))}")
        print(f"  📊 Muestra QR transformado: RGB{tuple(qr_float[10, 10].astype(int))}")

        # Aplicar blending
        blended = (1 - opacity) * region + opacity * qr_float
        final_result = blended.astype(np.uint8)

        print(f"  📊 Muestra resultado final: RGB{tuple(final_result[10, 10])}")

        # Insertar en frame
        frame[y:y + h, x:x + w] = final_result

        # Analizar la región embebida
        embedded_region = frame[y:y + h, x:x + w]

        print(f"\n📈 ANÁLISIS DE REGIÓN EMBEBIDA:")
        unique_values = np.unique(embedded_region.reshape(-1, 3), axis=0)
        print(f"  📊 Valores RGB únicos en región embebida:")

        value_counts = []
        for rgb in unique_values:
            count = np.sum(np.all(embedded_region == rgb, axis=2))
            value_counts.append((tuple(rgb), count))

        # Ordenar por frecuencia
        value_counts.sort(key=lambda x: x[1], reverse=True)

        for i, (rgb, count) in enumerate(value_counts[:10]):
            print(f"    RGB{rgb}: {count} píxeles ({count / embedded_region.size * 100:.1f}%)")

        # Guardar imagen para inspección
        filename = f"debug_blended_{opacity:.3f}.png"
        cv2.imwrite(filename, frame)
        print(f"💾 Imagen guardada: {filename}")

        return frame, embedded_region

    def test_detection_with_real_values(self, embedded_region: np.ndarray, opacity: float):
        """Probar detección usando los valores reales generados"""

        print(f"\n🔍 PROBANDO DETECCIÓN CON VALORES REALES:")

        # Convertir a escala de grises
        gray = cv2.cvtColor(embedded_region, cv2.COLOR_BGR2GRAY)

        # Analizar distribución de valores de gris
        hist, bins = np.histogram(gray.flatten(), bins=256, range=[0, 256])

        print(f"  📊 Rango de valores de gris: {gray.min()} - {gray.max()}")
        print(f"  📊 Valor más común: {np.argmax(hist)}")
        print(f"  📊 Valores únicos: {len(np.unique(gray))}")

        # Encontrar picos en el histograma (valores más frecuentes)
        peak_indices = np.where(hist > np.percentile(hist, 95))[0]
        print(f"  📈 Picos principales en histograma: {peak_indices}")

        # Probar diferentes umbrales basados en valores reales
        thresholds = [
            (gray.min(), gray.min() + 5),  # Valores más oscuros
            (gray.max() - 5, gray.max()),  # Valores más claros
            (120, 136),  # Alrededor del gris base
        ]

        for i, (low, high) in enumerate(thresholds):
            count = np.sum((gray >= low) & (gray <= high))
            percentage = count / gray.size * 100
            print(f"  🎯 Umbral {i + 1} [{low}-{high}]: {count} píxeles ({percentage:.1f}%)")

        # Proponer umbrales optimizados
        q25, q75 = np.percentile(gray, [25, 75])
        suggested_dark_threshold = q25
        suggested_light_threshold = q75

        print(f"\n💡 UMBRALES SUGERIDOS BASADOS EN DATOS REALES:")
        print(f"  🌑 Umbral oscuro: <= {suggested_dark_threshold:.0f}")
        print(f"  🌕 Umbral claro: >= {suggested_light_threshold:.0f}")

        return suggested_dark_threshold, suggested_light_threshold

    def run_complete_debug(self):
        """Ejecutar debug completo"""

        print("🔬 DEBUG VISUAL COMPLETO")
        print("🎯 Analizando valores RGB reales generados")
        print("=" * 60)

        opacities_to_test = [0.1, 0.2, 0.3, 0.5]
        suggested_thresholds = []

        for opacity in opacities_to_test:
            frame, embedded_region = self.embed_and_analyze_blending(opacity)
            dark_thresh, light_thresh = self.test_detection_with_real_values(embedded_region, opacity)
            suggested_thresholds.append((opacity, dark_thresh, light_thresh))

        print(f"\n📊 RESUMEN DE UMBRALES SUGERIDOS:")
        print("=" * 40)
        for opacity, dark, light in suggested_thresholds:
            print(f"Opacidad {opacity:.1f}: oscuro <= {dark:.0f}, claro >= {light:.0f}")

        # Sugerir umbral promedio
        avg_dark = np.mean([dark for _, dark, _ in suggested_thresholds])
        avg_light = np.mean([light for _, _, light in suggested_thresholds])

        print(f"\n🎯 UMBRALES PROMEDIO RECOMENDADOS:")
        print(f"  🌑 Oscuro: <= {avg_dark:.0f}")
        print(f"  🌕 Claro: >= {avg_light:.0f}")

        return avg_dark, avg_light


def main():
    """
    Ejecutar debug visual completo
    """
    debugger = VisualDebugger()

    # Ejecutar análisis completo
    dark_threshold, light_threshold = debugger.run_complete_debug()

    print(f"\n🛠️ SIGUIENTE PASO:")
    print(f"Actualizar algoritmo de detección con umbrales:")
    print(f"  very_dark = (region <= {dark_threshold:.0f})")
    print(f"  very_light = (region >= {light_threshold:.0f})")


if __name__ == "__main__":
    main()