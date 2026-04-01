#pragma once

// Camera pin definitions derived from the board-selection style used by the
// official Espressif CameraWebServer example. This initial source workspace is
// intentionally conservative: AI Thinker is the first concrete board target.
// Additional boards should only be promoted after real compile and hardware
// validation.

#if defined(CAMERA_MODEL_AI_THINKER)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22
#else
#error "No validated pin map selected for this Aether firmware build. Start with CAMERA_MODEL_AI_THINKER."
#endif
