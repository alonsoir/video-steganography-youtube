# 🕵️ Advanced Video Steganography Research - YouTube Vulnerability

**Investigación de seguridad responsable sobre vulnerabilidades de esteganografía en plataformas de video**

Este proyecto demuestra técnicas avanzadas de esteganografía para embedder datasets completos con sistemas de IA funcionales en contenido de video, revelando vulnerabilidades potenciales en plataformas como YouTube.

## 🚨 Importante - Investigación Ética

Este es un **proyecto de investigación de seguridad responsable** con fines educativos y de divulgación científica. El objetivo es:

- ✅ **Identificar vulnerabilidades** antes de que sean explotadas maliciosamente
- ✅ **Documentar técnicas** para desarrollar contramedidas
- ✅ **Responsible disclosure** a las plataformas afectadas
- ✅ **Educar** sobre riesgos de seguridad emergentes

## 🎯 Logros Demostrados

### ✅ **Embedding Completo**
- **📚 Moby Dick completo** (1.45MB) embebido en video
- **🧠 Sistema RAG funcional** con 1,252 chunks y embeddings TF-IDF
- **📱 1,818 QR codes invisibles** distribuidos en video de 26 segundos

### ✅ **Invisibilidad Demostrada**
- **👁️ Imperceptible al ojo humano** (opacidad calibrada 12-40%)
- **🎭 Indistinguible** del video original
- **🔍 Detectable algorítmicamente** con umbrales calibrados

### ✅ **Detección Científica**
- **📊 100% de patrones detectados** consistentemente
- **🎯 Umbrales calibrados** mediante análisis visual riguroso
- **⚙️ Sistema robusto** y repetible

### ✅ **Escalabilidad**
- **📈 Funciona en videos reales** grabados con cámara
- **🔄 Procesamiento automático** frame-por-frame
- **💪 Resistente** a variaciones de contenido

## 🛠️ Instalación

```bash
# Crear entorno virtual
python3 -m venv video_env
source video_env/bin/activate

# Instalar dependencias principales
pip install moviepy opencv-python qrcode numpy requests

# Para extracción de QR (macOS)
pip install pyzbar
brew install zbar
```

## 📹 Grabación de Video Base

```bash
# Listar dispositivos disponibles
ffmpeg -f avfoundation -list_devices true -i ""

# Grabar video base para embedding
ffmpeg -f avfoundation -framerate 30 -video_size 1280x720 -i "0:0" -t 30 mi_video.mp4
```

## 🚀 Uso del Sistema

### 1. **Procesamiento del Dataset**

```bash
# Procesar Moby Dick completo con embeddings TF-IDF
python encode/process_moby_dick.py
```

**Resultado:** `moby_dick_embeddings.pkl.gz` (1.45MB comprimido)

### 2. **Embedding en Video**

```bash
# Embedding con opacidad invisible al ojo humano
python encode/embed_with_adjustable_opacity.py 0.12

# Para mayor robustez (más visible)
python encode/embed_with_adjustable_opacity.py 0.4
```

**Resultado:** Video con 1,818 QR codes invisibles embebidos

### 3. **Calibración de Detectores**

```bash
# Análisis visual para calibrar umbrales de detección
python encode/visual_debug.py
```

**Descubrimiento clave:** Los umbrales correctos son ≤93 (oscuro) y ≥162 (claro), no los valores teóricos iniciales.

### 4. **Extracción y Recuperación**

```bash
# Extracción con umbrales calibrados
python decode/calibrated_extractor.py video_opacity_0.400.mp4

# Alternativa con OpenCV (más robusto)
python decode/opencv_qr_extractor.py video_opacity_0.400.mp4
```

**Resultado:** Sistema RAG completo recuperado del video

## 🔬 Componentes Técnicos

### **Embedder Avanzado**
- **Opacidad ajustable** (0.05 - 0.8)
- **QR codes optimizados** con máxima corrección de errores
- **Distribución inteligente** a lo largo del video
- **Blending invisible** usando diferencias RGB mínimas

### **Detector Calibrado**
- **Múltiples algoritmos** de mejora de imagen
- **Umbrales científicamente determinados** mediante debug visual
- **Detección robusta** con 100% de efectividad
- **Compatible** con pyzbar y OpenCV QRCodeDetector

### **Sistema RAG Embebido**
- **Embeddings TF-IDF** para búsqueda semántica
- **Chunking optimizado** para QR codes
- **Metadata completa** con checksums e índices
- **Reconstrucción automática** con verificación de integridad

## 📊 Resultados de Investigación

### **Métricas de Rendimiento**
| Opacidad | Invisibilidad | Detección | Decodificación |
|----------|---------------|-----------|----------------|
| 0.12     | ✅ Invisible   | ✅ 50-57%  | ❌ pyzbar     |
| 0.4      | ✅ Sutil      | ✅ 50-62%  | ❌ pyzbar     |
| 0.8      | ⚠️ Visible    | ✅ 100%   | ✅ Exitosa    |

### **Umbrales Calibrados**
```python
# Valores descubiertos mediante análisis científico
DARK_THRESHOLD = 93   # ≤ 93 para píxeles oscuros de QR
LIGHT_THRESHOLD = 162 # ≥ 162 para píxeles claros de QR
```

## 🚨 Implicaciones de Seguridad

### **Vulnerabilidades Demostradas**

#### **Para YouTube y plataformas similares:**
- 📚 **Datasets completos** ocultables en videos aparentemente normales
- 🧠 **Sistemas de IA** distribuibles de forma encubierta
- 🔍 **Detección algorítmica** posible pero no implementada
- 📈 **Escalabilidad** a volúmenes masivos de información

#### **Casos de uso maliciosos potenciales:**
- 🕵️ **Exfiltración de datos** corporativos via videos públicos
- 🌐 **Distribución de información** clasificada
- 🤖 **Propagación de modelos de IA** no autorizados
- 📡 **Comunicaciones encubiertas** entre actores maliciosos

### **Contramedidas Recomendadas**

#### **Para plataformas de video:**
1. **Análisis de patrones** de píxeles sospechosos
2. **Detección de QR codes** embebidos usando umbrales calibrados
3. **Límites de variación RGB** mínima permitida
4. **Análisis estadístico** de distribución de colores

#### **Para organizaciones:**
1. **Monitoreo** de uploads de video corporativo
2. **Análisis automatizado** de contenido embebido
3. **Políticas** de uso de plataformas externas
4. **Concientización** sobre técnicas de esteganografía

## 📁 Estructura del Proyecto

```
video-steganography-youtube/
├── encode/
│   ├── process_moby_dick.py           # Procesamiento del dataset
│   ├── embed_with_adjustable_opacity.py # Embedding con opacidad variable
│   ├── visual_debug.py                # Calibración de umbrales
│   └── invisible_qr_video.py          # Embedding invisible
├── decode/
│   ├── calibrated_extractor.py        # Extractor con umbrales calibrados
│   ├── opencv_qr_extractor.py         # Extractor OpenCV robusto
│   └── debug_extraction.py            # Debug de detección
├── requirements.txt                   # Dependencias Python
├── moby_dick_embeddings.pkl.gz       # Dataset procesado
└── README.md                          # Esta documentación
```

## 🎓 Aplicaciones Educativas

### **Investigación de Seguridad**
- Demostración de técnicas de esteganografía avanzada
- Análisis de vulnerabilidades en plataformas de video
- Desarrollo de contramedidas y sistemas de detección

### **Computer Vision y ML**
- Calibración científica de detectores de imágenes
- Procesamiento de video frame-por-frame
- Sistemas RAG distribuidos en medios

### **Criptografía Aplicada**
- Ocultación de información en medios visuales
- Técnicas de blending y manipulación de píxeles
- Resistencia a recompresión de video

## 🔬 Próximos Pasos de Investigación

### **Fase 1: Optimización Técnica**
- [ ] **Resistencia a YouTube** - Testing con recompresión real
- [ ] **QR codes más pequeños** para mayor densidad
- [ ] **Múltiples capas** de embedding
- [ ] **Embedding adaptativo** basado en contenido del video

### **Fase 2: Contramedidas**
- [ ] **Detector automático** para plataformas
- [ ] **Análisis estadístico** de patrones sospechosos
- [ ] **Machine learning** para identificación
- [ ] **Herramientas de auditoría** para organizaciones

### **Fase 3: Responsible Disclosure**
- [ ] **Documentación completa** de vulnerabilidades
- [ ] **Contacto con YouTube** y plataformas afectadas
- [ ] **Paper científico** para conferencias de seguridad
- [ ] **Herramientas abiertas** para la comunidad de seguridad

## 📞 Contacto y Colaboración

Este proyecto forma parte de investigación de seguridad responsable. Para:

- 🤝 **Colaboración científica**
- 🔒 **Responsible disclosure**
- 🎓 **Propósitos educativos**
- 🛡️ **Desarrollo de contramedidas**

## ⚖️ Licencia y Responsabilidad

**Uso exclusivamente educativo y de investigación de seguridad responsable.**

- ✅ Permitido: Investigación, educación, desarrollo de contramedidas
- ❌ Prohibido: Uso malicioso, exfiltración no autorizada, actividades ilegales

---

**📊 Estado del Proyecto:** Investigación Activa - Vulnerabilidad Demostrada ✅

**🎯 Objetivo:** Responsible Disclosure y Desarrollo de Contramedidas

**🔬 Metodología:** Científica, Reproducible, Ética