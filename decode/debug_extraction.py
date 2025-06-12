#!/usr/bin/env python3
"""
Detector mejorado para QR codes ultra-sutiles
Debug y análisis de diferencias mínimas en video
"""

import cv2
import numpy as np
import pickle
import gzip
import base64
from typing import List, Dict, Any, Optional, Tuple
import os


class SensitiveQRDetector:
    def __init__(self):
        """Detector ultra-sensible para QR invisibles"""
        self.extracted_fragments = {}
        self.total_fragments = None

    def analyze_frame_differences(self, frame: np.ndarray, show_stats: bool = False) -> List[Tuple[int, int]]:
        """
        Analizar frame buscando diferencias sutiles que indiquen QR codes
        """
        height, width = frame.shape[:2]
        suspicious_regions = []

        # Convertir a escala de grises para análisis más preciso
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Buscar regiones con patrones de valores específicos
        # Los QR invisibles tienen valores como 3 (casi negro) y 252 (casi blanco)

        qr_size = 100
        step_size = 50

        for y in range(0, height - qr_size, step_size):
            for x in range(0, width - qr_size, step_size):
                region = gray[y:y + qr_size, x:x + qr_size]

                # Buscar valores característicos de QR invisible
                very_dark = np.sum((region >= 0) & (region <= 10))  # Casi negro
                very_light = np.sum((region >= 245) & (region <= 255))  # Casi blanco

                # Si hay suficientes píxeles "sospechosos"
                if very_dark > 200 and very_light > 200:
                    suspicious_regions.append((x, y))

                    if show_stats:
                        print(f"🔍 Región sospechosa en ({x},{y}): dark={very_dark}, light={very_light}")

        return suspicious_regions

    def extract_and_enhance_region(self, frame: np.ndarray, x: int, y: int, size: int = 100) -> np.ndarray:
        """
        Extraer región y aplicar mejoras extremas para revelar QR invisible
        """
        # Extraer región
        region = frame[y:y + size, x:x + size].copy()

        # Convertir a escala de grises
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY).astype(np.float32)

        # Aplicar múltiples técnicas de mejora

        # 1. Amplificación extrema de contraste
        enhanced = gray.copy()

        # Mapear valores sospechosos a extremos
        enhanced[gray <= 10] = 0  # Negro puro para valores 0-10
        enhanced[gray >= 245] = 255  # Blanco puro para valores 245-255

        # 2. Mejora adicional: buscar transiciones sutiles
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Amplificar gradientes pequeños que podrían ser bordes de QR
        gradient_threshold = np.percentile(gradient_magnitude, 95)
        edge_mask = gradient_magnitude > gradient_threshold * 0.1

        enhanced[edge_mask] = 0 if np.mean(gray[edge_mask]) < 128 else 255

        # 3. Filtro morfológico para limpiar ruido
        kernel = np.ones((3, 3), np.uint8)
        enhanced = cv2.morphologyEx(enhanced.astype(np.uint8), cv2.MORPH_CLOSE, kernel)

        # Convertir de vuelta a RGB para visualización
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)

        return enhanced_rgb

    def simple_qr_decode(self, enhanced_image: np.ndarray) -> Optional[str]:
        """
        Decodificador QR simple usando OpenCV (sin pyzbar)
        """
        try:
            # Intentar con detector QR de OpenCV
            qr_detector = cv2.QRCodeDetector()

            # Convertir a escala de grises si es necesario
            if len(enhanced_image.shape) == 3:
                gray = cv2.cvtColor(enhanced_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = enhanced_image

            # Intentar detectar y decodificar
            retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(gray)

            if retval and decoded_info:
                return decoded_info[0] if decoded_info[0] else None

        except Exception as e:
            print(f"⚠️ Error en decodificación simple: {e}")

        return None

    def debug_analyze_video(self, video_path: str, max_frames: int = 100):
        """
        Análisis de debug del video para entender el problema
        """
        print(f"🔬 ANÁLISIS DEBUG DE VIDEO: {video_path}")

        if not os.path.exists(video_path):
            print(f"❌ Video no encontrado: {video_path}")
            return

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📊 Total frames: {total_frames}")
        print(f"🔍 Analizando primeros {min(max_frames, total_frames)} frames...")

        frame_count = 0
        total_suspicious = 0

        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            # Analizar diferencias en este frame
            suspicious_regions = self.analyze_frame_differences(frame, show_stats=(frame_count < 5))

            if suspicious_regions:
                total_suspicious += len(suspicious_regions)
                print(f"📍 Frame {frame_count}: {len(suspicious_regions)} regiones sospechosas")

                # Analizar primera región sospechosa en detalle
                if frame_count < 3:  # Solo para los primeros frames
                    x, y = suspicious_regions[0]
                    enhanced = self.extract_and_enhance_region(frame, x, y)

                    # Intentar decodificar
                    decoded = self.simple_qr_decode(enhanced)
                    if decoded:
                        print(f"🎉 QR decodificado en frame {frame_count}: {decoded[:50]}...")

                    # Guardar imagen para inspección manual
                    if frame_count == 0:
                        cv2.imwrite(f"debug_frame_{frame_count}_original.png", frame[y:y + 100, x:x + 100])
                        cv2.imwrite(f"debug_frame_{frame_count}_enhanced.png", enhanced)
                        print(f"💾 Guardadas imágenes debug para frame {frame_count}")

            frame_count += 1

        cap.release()

        print(f"\n📊 RESUMEN DEBUG:")
        print(f"🔍 Frames analizados: {frame_count}")
        print(f"📍 Total regiones sospechosas: {total_suspicious}")
        print(f"📊 Promedio por frame: {total_suspicious / frame_count:.1f}")

        if total_suspicious == 0:
            print("\n⚠️ PROBLEMA DETECTADO:")
            print("No se encontraron patrones de QR invisible")
            print("💡 Posibles soluciones:")
            print("1. Incrementar opacidad en el embedder")
            print("2. Usar QR codes más grandes")
            print("3. Verificar que el embedding funcionó correctamente")


def main():
    """
    Ejecutar análisis debug
    """
    detector = SensitiveQRDetector()

    video_path = "video_with_moby_dick.mp4"

    print("🔬 DETECTOR DEBUG PARA QR INVISIBLES")
    print("=" * 50)

    detector.debug_analyze_video(video_path, max_frames=50)

    print("\n💡 Si no se encuentran QR codes:")
    print("1. Ejecutar: python create_visible_test.py")
    print("2. Incrementar opacidad en el embedder")
    print("3. Verificar archivo video_with_moby_dick.mp4")


if __name__ == "__main__":
    main()