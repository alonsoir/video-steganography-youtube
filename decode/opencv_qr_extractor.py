#!/usr/bin/env python3
"""
Extractor usando OpenCV QR detector (más robusto que pyzbar)
Para QR codes sutiles que pyzbar no puede decodificar
"""

import cv2
import numpy as np
import pickle
import gzip
import base64
from typing import List, Dict, Any, Optional, Tuple
import os
import sys


class OpenCVQRExtractor:
    def __init__(self):
        """Extractor usando OpenCV QR detector"""
        self.extracted_fragments = {}
        self.total_fragments = None

        # UMBRALES CALIBRADOS
        self.dark_threshold = 93
        self.light_threshold = 162
        self.min_qr_pixels = 500

        # Crear detector OpenCV QR
        self.qr_detector = cv2.QRCodeDetector()

        print(f"🎯 Extractor OpenCV QR:")
        print(f"  🌑 Umbral oscuro: <= {self.dark_threshold}")
        print(f"  🌕 Umbral claro: >= {self.light_threshold}")
        print(f"  🔍 Detector: OpenCV QRCodeDetector")

    def enhance_qr_multiple_methods(self, frame: np.ndarray, region: Tuple[int, int, int, int]) -> List[np.ndarray]:
        """
        Crear múltiples versiones mejoradas del QR para maximizar decodificación
        """
        x, y, w, h = region
        qr_region = frame[y:y + h, x:x + w].copy()
        gray = cv2.cvtColor(qr_region, cv2.COLOR_BGR2GRAY)

        enhanced_versions = []

        # Método 1: Umbrales calibrados estrictos
        mask_dark = gray <= self.dark_threshold
        mask_light = gray >= self.light_threshold

        if np.sum(mask_dark) > self.min_qr_pixels and np.sum(mask_light) > self.min_qr_pixels:
            enhanced1 = gray.copy()
            enhanced1[mask_dark] = 0
            enhanced1[mask_light] = 255
            # Mantener valores intermedios como están
            enhanced_versions.append(enhanced1)

        # Método 2: Thresholding adaptativo
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        enhanced_versions.append(adaptive_thresh)

        # Método 3: Otsu thresholding
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        enhanced_versions.append(otsu_thresh)

        # Método 4: Contraste mejorado + umbralizado
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_contrast = clahe.apply(gray)
        _, contrast_thresh = cv2.threshold(enhanced_contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        enhanced_versions.append(contrast_thresh)

        return enhanced_versions

    def decode_qr_opencv(self, qr_image: np.ndarray) -> Optional[str]:
        """
        Decodificar QR usando OpenCV detector
        """
        try:
            # OpenCV QR detector
            retval, decoded_info, points, _ = self.qr_detector.detectAndDecodeMulti(qr_image)

            if retval and decoded_info:
                for info in decoded_info:
                    if info:  # No vacío
                        return info
        except Exception as e:
            pass

        return None

    def scan_frame_opencv(self, frame: np.ndarray, qr_size: int = 120) -> List[bytes]:
        """
        Escanear frame con múltiples métodos de mejora
        """
        found_qrs = []
        height, width = frame.shape[:2]
        step_size = qr_size // 3

        scan_count = 0
        detection_count = 0
        decode_count = 0

        for y in range(0, height - qr_size, step_size):
            for x in range(0, width - qr_size, step_size):
                scan_count += 1

                # Generar múltiples versiones mejoradas
                enhanced_versions = self.enhance_qr_multiple_methods(frame, (x, y, qr_size, qr_size))

                if enhanced_versions:
                    detection_count += 1

                    # Probar decodificación con cada versión
                    for i, enhanced in enumerate(enhanced_versions):
                        decoded_text = self.decode_qr_opencv(enhanced)

                        if decoded_text:
                            decode_count += 1
                            print(f"    ✅ QR decodificado en ({x},{y}) método {i + 1}")

                            try:
                                # Convertir de base64 a bytes
                                decoded_data = base64.b64decode(decoded_text)
                                found_qrs.append(decoded_data)
                                break  # No necesitamos probar más métodos para esta región
                            except Exception as e:
                                print(f"    ⚠️ Error decodificando base64: {e}")

        detection_rate = detection_count / scan_count * 100 if scan_count > 0 else 0
        decode_rate = decode_count / detection_count * 100 if detection_count > 0 else 0

        print(
            f"    📊 Escaneadas: {scan_count}, detecciones: {detection_count} ({detection_rate:.1f}%), decodificadas: {decode_count} ({decode_rate:.1f}%)")

        return found_qrs

    def parse_fragment(self, fragment_data: bytes) -> Optional[Dict[str, Any]]:
        """Parsear fragmento extraído"""
        try:
            separator = b'|SEPARATOR|'
            if separator not in fragment_data:
                return None

            metadata_bytes, data_bytes = fragment_data.split(separator, 1)
            metadata = pickle.loads(metadata_bytes)

            if hash(data_bytes) != metadata['checksum']:
                print(f"⚠️ Checksum mismatch en fragmento {metadata['idx']}")
                return None

            return {
                'index': metadata['idx'],
                'total': metadata['total'],
                'size': metadata['size'],
                'data': data_bytes
            }
        except Exception as e:
            print(f"⚠️ Error parseando fragmento: {e}")
            return None

    def extract_from_video_opencv(self, video_path: str) -> bool:
        """Extraer usando OpenCV QR detector"""

        print(f"🎬 Analizando con OpenCV QR detector: {video_path}")

        if not os.path.exists(video_path):
            print(f"❌ Video no encontrado: {video_path}")
            return False

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print(f"📊 Video: {total_frames} frames a {fps:.1f} FPS")
        print("🔍 Extrayendo con OpenCV QR detector...")

        frame_count = 0
        total_qrs_decoded = 0
        frame_skip = max(1, total_frames // 100)  # Procesar 100 frames

        while frame_count < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % (frame_skip * 10) == 0:
                print(
                    f"  🔍 Frame {frame_count + 1}/{total_frames} - Fragmentos únicos: {len(self.extracted_fragments)}")

            # Escanear frame
            qr_data_list = self.scan_frame_opencv(frame)
            total_qrs_decoded += len(qr_data_list)

            # Procesar fragmentos
            for qr_data in qr_data_list:
                fragment = self.parse_fragment(qr_data)
                if fragment:
                    idx = fragment['index']
                    if idx not in self.extracted_fragments:
                        self.extracted_fragments[idx] = fragment

                        if self.total_fragments is None:
                            self.total_fragments = fragment['total']
                            print(f"📱 Total fragmentos esperados: {self.total_fragments}")

            frame_count += frame_skip

        cap.release()

        print(f"\n✅ Extracción OpenCV completada")
        print(f"📱 QR codes decodificados: {total_qrs_decoded}")
        print(f"📱 Fragmentos únicos: {len(self.extracted_fragments)}")
        print(f"📱 Fragmentos esperados: {self.total_fragments}")

        if self.total_fragments:
            completion_rate = len(self.extracted_fragments) / self.total_fragments * 100
            print(f"📊 Tasa de completitud: {completion_rate:.1f}%")

        return len(self.extracted_fragments) > 0


def main():
    """Demo OpenCV QR extraction"""

    print("🎯 EXTRACTOR OPENCV QR - VULNERABILIDAD YOUTUBE")
    print("🔍 Usando OpenCV QRCodeDetector con múltiples métodos")
    print("=" * 60)

    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = "video_opacity_0.120.mp4"

    print(f"📹 Video a analizar: {video_path}")

    extractor = OpenCVQRExtractor()

    if extractor.extract_from_video_opencv(video_path):
        print("\n🎉 ¡EXTRACCIÓN OPENCV EXITOSA!")
        print("🚨 QR codes detectados y decodificados con OpenCV")
        print("🎯 Vulnerabilidad demostrada con detector robusto")
    else:
        print("\n❌ OpenCV tampoco pudo decodificar los QR codes")
        print("💡 Necesitamos mayor opacidad para decodificación exitosa")


if __name__ == "__main__":
    main()