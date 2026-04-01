#include "esp_camera.h"
#include <ESPmDNS.h>
#include <WebServer.h>
#include <WiFi.h>

#include "aether_build_config.h"

// This firmware workspace is derived from the product contract established by
// Espressif's CameraWebServer example, but narrowed to the behavior Aether
// Console actually needs: Wi-Fi onboarding defaults, MJPEG preview, and a
// stable /control surface for tuning. It is not yet shipped as a validated
// release binary package.
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins_aether.h"

WebServer controlServer(80);
WebServer streamServer(81);

constexpr char kBoundary[] = "frame";

bool setSensorValue(sensor_t* sensor, const String& name, int value) {
  if (name == "framesize") return sensor->set_framesize(sensor, static_cast<framesize_t>(value)) == 0;
  if (name == "quality") return sensor->set_quality(sensor, value) == 0;
  if (name == "brightness") return sensor->set_brightness(sensor, value) == 0;
  if (name == "contrast") return sensor->set_contrast(sensor, value) == 0;
  if (name == "saturation") return sensor->set_saturation(sensor, value) == 0;
  if (name == "sharpness") return sensor->set_sharpness(sensor, value) == 0;
  if (name == "special_effect") return sensor->set_special_effect(sensor, value) == 0;
  if (name == "awb") return sensor->set_whitebal(sensor, value) == 0;
  if (name == "awb_gain") return sensor->set_awb_gain(sensor, value) == 0;
  if (name == "wb_mode") return sensor->set_wb_mode(sensor, value) == 0;
  if (name == "aec") return sensor->set_exposure_ctrl(sensor, value) == 0;
  if (name == "aec2") return sensor->set_aec2(sensor, value) == 0;
  if (name == "ae_level") return sensor->set_ae_level(sensor, value) == 0;
  if (name == "agc") return sensor->set_gain_ctrl(sensor, value) == 0;
  if (name == "agc_gain") return sensor->set_agc_gain(sensor, value) == 0;
  if (name == "gainceiling") return sensor->set_gainceiling(sensor, static_cast<gainceiling_t>(value)) == 0;
  if (name == "bpc") return sensor->set_bpc(sensor, value) == 0;
  if (name == "wpc") return sensor->set_wpc(sensor, value) == 0;
  if (name == "raw_gma") return sensor->set_raw_gma(sensor, value) == 0;
  if (name == "lenc") return sensor->set_lenc(sensor, value) == 0;
  if (name == "dcw") return sensor->set_dcw(sensor, value) == 0;
  if (name == "colorbar") return sensor->set_colorbar(sensor, value) == 0;
  if (name == "hmirror") return sensor->set_hmirror(sensor, value) == 0;
  if (name == "vflip") return sensor->set_vflip(sensor, value) == 0;
  return false;
}

String jsonStatus() {
  sensor_t* sensor = esp_camera_sensor_get();
  if (!sensor) {
    return "{\"ok\":false,\"error\":\"sensor unavailable\"}";
  }

  camera_status_t status = sensor->status;
  String json = "{";
  json += "\"ok\":true,";
  json += "\"camera_name\":\"" + String(AETHER_CAMERA_NAME) + "\",";
  json += "\"hostname\":\"" + String(AETHER_HOSTNAME) + "\",";
  json += "\"framesize\":" + String(status.framesize) + ",";
  json += "\"quality\":" + String(status.quality) + ",";
  json += "\"brightness\":" + String(status.brightness) + ",";
  json += "\"contrast\":" + String(status.contrast) + ",";
  json += "\"saturation\":" + String(status.saturation) + ",";
  json += "\"sharpness\":" + String(status.sharpness) + ",";
  json += "\"special_effect\":" + String(status.special_effect) + ",";
  json += "\"awb\":" + String(status.awb) + ",";
  json += "\"awb_gain\":" + String(status.awb_gain) + ",";
  json += "\"wb_mode\":" + String(status.wb_mode) + ",";
  json += "\"aec\":" + String(status.aec) + ",";
  json += "\"aec2\":" + String(status.aec2) + ",";
  json += "\"ae_level\":" + String(status.ae_level) + ",";
  json += "\"agc\":" + String(status.agc) + ",";
  json += "\"agc_gain\":" + String(status.agc_gain) + ",";
  json += "\"gainceiling\":" + String(status.gainceiling) + ",";
  json += "\"bpc\":" + String(status.bpc) + ",";
  json += "\"wpc\":" + String(status.wpc) + ",";
  json += "\"raw_gma\":" + String(status.raw_gma) + ",";
  json += "\"lenc\":" + String(status.lenc) + ",";
  json += "\"dcw\":" + String(status.dcw) + ",";
  json += "\"colorbar\":" + String(status.colorbar) + ",";
  json += "\"hmirror\":" + String(status.hmirror) + ",";
  json += "\"vflip\":" + String(status.vflip);
  json += "}";
  return json;
}

void handleRoot() {
  controlServer.send(200, "application/json", jsonStatus());
}

void handleStatus() {
  controlServer.send(200, "application/json", jsonStatus());
}

void handleControl() {
  if (!controlServer.hasArg("var") || !controlServer.hasArg("val")) {
    controlServer.send(400, "application/json", "{\"ok\":false,\"error\":\"missing var or val\"}");
    return;
  }

  sensor_t* sensor = esp_camera_sensor_get();
  if (!sensor) {
    controlServer.send(500, "application/json", "{\"ok\":false,\"error\":\"sensor unavailable\"}");
    return;
  }

  const String controlName = controlServer.arg("var");
  const int controlValue = controlServer.arg("val").toInt();
  if (!setSensorValue(sensor, controlName, controlValue)) {
    controlServer.send(400, "application/json", "{\"ok\":false,\"error\":\"unsupported control or failed write\"}");
    return;
  }

  controlServer.send(200, "application/json", jsonStatus());
}

void handleCapture() {
  camera_fb_t* frame = esp_camera_fb_get();
  if (!frame) {
    controlServer.send(500, "application/json", "{\"ok\":false,\"error\":\"capture failed\"}");
    return;
  }

  WiFiClient client = controlServer.client();
  client.print("HTTP/1.1 200 OK\r\n");
  client.print("Content-Type: image/jpeg\r\n");
  client.print("Content-Length: ");
  client.print(frame->len);
  client.print("\r\nAccess-Control-Allow-Origin: *\r\n\r\n");
  client.write(frame->buf, frame->len);
  esp_camera_fb_return(frame);
}

void handleStream() {
  WiFiClient client = streamServer.client();
  client.print("HTTP/1.1 200 OK\r\n");
  client.print("Access-Control-Allow-Origin: *\r\n");
  client.print("Cache-Control: no-cache\r\n");
  client.print("Connection: close\r\n");
  client.print("Content-Type: multipart/x-mixed-replace; boundary=");
  client.print(kBoundary);
  client.print("\r\n\r\n");

  while (client.connected()) {
    camera_fb_t* frame = esp_camera_fb_get();
    if (!frame) {
      delay(10);
      continue;
    }

    client.print("--");
    client.print(kBoundary);
    client.print("\r\nContent-Type: image/jpeg\r\nContent-Length: ");
    client.print(frame->len);
    client.print("\r\n\r\n");
    client.write(frame->buf, frame->len);
    client.print("\r\n");
    esp_camera_fb_return(frame);
    delay(1);
  }
}

bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = psramFound() ? 2 : 1;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;

  return esp_camera_init(&config) == ESP_OK;
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(AETHER_WIFI_SSID, AETHER_WIFI_PASSWORD);

  unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 30000) {
    delay(500);
  }
}

void setupServers() {
  controlServer.on("/", HTTP_GET, handleRoot);
  controlServer.on("/status", HTTP_GET, handleStatus);
  controlServer.on("/control", HTTP_GET, handleControl);
  controlServer.on("/capture", HTTP_GET, handleCapture);
  controlServer.begin();

  streamServer.on("/stream", HTTP_GET, handleStream);
  streamServer.begin();
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false);

  if (!initCamera()) {
    Serial.println("Camera init failed");
    return;
  }

  connectWifi();
  if (WiFi.status() == WL_CONNECTED) {
    MDNS.begin(AETHER_HOSTNAME);
  }

  setupServers();
}

void loop() {
  controlServer.handleClient();
  streamServer.handleClient();
  delay(1);
}
