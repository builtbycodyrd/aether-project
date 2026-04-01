#pragma once

// Maintainer note:
// This header is the controlled place for build-time defaults. The long-term
// product direction is per-device provisioning during pairing, not shipping
// customer Wi-Fi credentials inside release binaries. For now this exists so
// maintainers can compile a test binary while the final provisioning pipeline
// is still being designed.

#ifndef AETHER_WIFI_SSID
#define AETHER_WIFI_SSID "CHANGE_ME_WIFI"
#endif

#ifndef AETHER_WIFI_PASSWORD
#define AETHER_WIFI_PASSWORD "CHANGE_ME_PASSWORD"
#endif

#ifndef AETHER_HOSTNAME
#define AETHER_HOSTNAME "aether-camera"
#endif

#ifndef AETHER_CAMERA_NAME
#define AETHER_CAMERA_NAME "Aether Camera"
#endif
