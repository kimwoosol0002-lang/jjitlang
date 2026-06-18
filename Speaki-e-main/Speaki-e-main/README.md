# Speaki-e
그저 스피키를 잡아당길 수 있는 웹 페이지입니다.

## 🚀 Key Features (주요 기능)

* **WebGL & GLSL 기반 실시간 이미지 왜곡**: CPU 연산 부담을 줄이고 GPU를 활용하여 60fps의 부드러운 이미지 변형 연산을 수행합니다.
* **스프링-댐핑 물리 엔진 (Spring-Damping Physics)**: 마우스를 놓았을 때 이미지가 원래 상태로 복원되면서 탄성 있는 흔들림(Elastic Shiver)을 표현합니다.
* **스마트 투명도 정제 알고리즘 (Hole-Filling & Dilution)**: 웹 프론트엔드 환경에서 이미지 변형 시 발생하는 투명 픽셀 경계선 노이즈를 제어하기 위해 **Nearest-Neighbor Search** 및 **Box Blur(Averaging)** 혼합 알고리즘을 구현했습니다.
* **인터랙티브 사운드 시스템**: 드래그 상태와 릴리즈(마우스를 뗌) 분기 조건(확률적 오디오 재생 및 연쇄 재생)에 따라 다른 사운드 이펙트를 매끄럽게 제어합니다.
* **하이브리드 폴백 가드 (Fallback Guard)**: 사용자의 브라우저 환경이 WebGL을 지원하지 않거나 CORS 제한 환경(`file://` 프로토콜 등)일 경우, 깨짐 없이 부드럽게 원본 이미지를 시각화하는 오버레이 및 대체 렌더링 시스템을 탑재했습니다.

---

## 🛠️ Tech Stack (기술 스택)

* **Frontend**: HTML5, CSS3 (Minimalistic Design), JavaScript (Vanilla JS ES6+)
* **Graphics API**: WebGL 1.0, GLSL (OpenGL Shading Language)
* **Audio**: HTML5 Audio API

---

## 📐 Deep Dive & Core Architecture (주요 핵심 구현)

### 1. GLSL Fragment Shader Distortion
마우스 드래그의 시작점(`uDragStart`)과 현재 위치(`uMouse`) 사이의 벡터 및 거리를 기반으로 텍스처 좌표(UV)를 끌어당깁니다. 화면 가장자리로 갈수록 왜곡 강도가 자연스럽게 감소하도록 감쇄 함수(`edgeAnchor`)를 설계했습니다.

```glsl
// 왜곡 연산 및 테두리 감쇄 필터 스니펫
vec2 delta = (uv - uDragStart);
delta.x *= uAspect;
float dist = length(delta);

// 가장자리 변형 방지를 위한 앵커 계산
float edgeAnchor = pow(vUv.x * (1.0 - vUv.x) * vUv.y * (1.0 - vUv.y) * 16.0, 0.8);
float influence = exp(-dist * 6.5) * edgeAnchor;
vec2 pull = (uMouse - uDragStart) * influence * uStrength;
uv -= pull;
