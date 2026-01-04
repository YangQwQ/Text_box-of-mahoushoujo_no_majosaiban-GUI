// image_loader.cpp

#include <algorithm>
#include <cstring>
#include <memory>
#include <mutex>
#include <stack>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

// 计时用
#define _DEBUG
#ifdef _DEBUG
#include <chrono>
#define DEBUG_PRINT(fmt, ...) printf("[DEBUG] " fmt "\n", ##__VA_ARGS__)
#define TIME_SCOPE_VAR(line, name) image_loader::utils::Timer timer_##line(name)
#define TIME_SCOPE(name) TIME_SCOPE_VAR(__LINE__, name)

#else
#define DEBUG_PRINT(fmt, ...)
#define TIME_SCOPE(name) ((void)0)
#endif

#include <SDL.h>
#include <SDL_image.h>
#include <SDL_ttf.h>
#include <cJSON.h>

// 创建UTF-8字符串版本的括号对映射
const std::unordered_map<std::string, std::string> lt_bracket_pairs = {{"\"", "\""}, {"[", "]"}, {"<", ">"}, {"【", "】"}, {"〔", "〕"}, {"「", "」"}, {"『", "』"}, {"〖", "〗"}, {"《", "》"}, {"〈", "〉"}, {"“", "”"}};

// 简单的计时宏定义

#define TIME_START_VAR(line, name) auto time_start_##line = std::chrono::high_resolution_clock::now()
#define TIME_START(name) TIME_START_VAR(__LINE__, name)

#define TIME_END_VAR(line, name)                                                                                                                                                                                                                              \
  do {                                                                                                                                                                                                                                                        \
    auto time_end_##line = std::chrono::high_resolution_clock::now();                                                                                                                                                                                         \
    auto duration_##line = std::chrono::duration_cast<std::chrono::microseconds>(time_end_##line - time_start_##line);                                                                                                                                        \
    double ms_##line = duration_##line.count() / 1000.0;                                                                                                                                                                                                      \
    image_loader::DEBUG_PRINT("Time [%s]: %.3f ms", name, ms_##line);                                                                                                                                                                                         \
  } while (0)

#define TIME_END(name) TIME_END_VAR(__LINE__, name)

namespace image_loader {

// Return codes
enum class LoadResult { SUCCESS = 1, FAILED = 0, FILE_NOT_FOUND = -1, SDL_INIT_FAILED = -2, IMAGE_INIT_FAILED = -3, TTF_INIT_FAILED = -4, UNSUPPORTED_FORMAT = -5, JSON_PARSE_ERROR = -6, TEXT_CONFIG_ERROR = -7 };

// Fill modes
enum class FillMode { FIT = 0, WIDTH = 1, HEIGHT = 2 };
enum class AlignMode { LEFT = 0, CENTER = 1, RIGHT = 2 };
enum class VAlignMode { TOP = 0, MIDDLE = 1, BOTTOM = 2 };

// Simple ImageData structure (compatible with original C structure)
struct ImageData {
  unsigned char *data = nullptr;
  int width = 0;
  int height = 0;
  int pitch = 0;

  ImageData() = default;

  ~ImageData() {
    if (data) {
      free(data);
      data = nullptr;
    }
  }

  // Create from SDL surface
  static std::unique_ptr<ImageData> FromSurface(SDL_Surface *surface) {
    if (!surface)
      return nullptr;

    auto image_data = std::make_unique<ImageData>();
    image_data->width = surface->w;
    image_data->height = surface->h;
    image_data->pitch = surface->pitch;

    size_t data_size = static_cast<size_t>(surface->h) * surface->pitch;
    image_data->data = static_cast<unsigned char *>(malloc(data_size));
    if (image_data->data && surface->pixels) {
      memcpy(image_data->data, surface->pixels, data_size);
    }

    return image_data;
  }

private:
  // Disable copy
  ImageData(const ImageData &) = delete;
  ImageData &operator=(const ImageData &) = delete;
};

// Font cache entry
struct FontCacheEntry {
  char font_name[256] = {0};
  int size = 0;
  TTF_Font *font = nullptr;
  std::unordered_map<uint32_t, int> char_width_cache; // 字符宽度缓存
  FontCacheEntry *next = nullptr;

  ~FontCacheEntry() {
    if (font) {
      TTF_CloseFont(font);
      font = nullptr;
    }
    if (next) {
      delete next;
      next = nullptr;
    }
  }
};

// 文件路径缓存结构
struct FilePathCache {
  std::unordered_map<std::string, std::string> path_map; // 文件名(不含扩展名) -> 完整路径
  std::mutex mutex;
  bool initialized = false;

  void Clear() {
    std::lock_guard<std::mutex> lock(mutex);
    path_map.clear();
    initialized = false;
  }

  bool FindFile(const std::string &base_name, const std::vector<std::string> &extensions, std::string &found_path) {
    std::lock_guard<std::mutex> lock(mutex);

    // 先尝试直接查找缓存
    auto it = path_map.find(base_name);
    if (it != path_map.end()) {
      found_path = it->second;
      return true;
    }

    // 如果没有找到，尝试所有扩展名
    for (const auto &ext : extensions) {
      std::string test_path = base_name + ext;
      SDL_RWops *file = SDL_RWFromFile(test_path.c_str(), "rb");
      if (file) {
        SDL_RWclose(file);
        path_map[base_name] = test_path;
        found_path = test_path;
        return true;
      }
    }

    return false;
  }

  void AddPath(const std::string &base_name, const std::string &full_path) {
    std::lock_guard<std::mutex> lock(mutex);
    path_map[base_name] = full_path;
  }
};

// Static layer node
struct StaticLayerNode {
  SDL_Surface *layer_surface = nullptr;
  StaticLayerNode *next = nullptr;

  ~StaticLayerNode() {
    if (layer_surface) {
      SDL_FreeSurface(layer_surface);
      layer_surface = nullptr;
    }
    if (next) {
      delete next;
      next = nullptr;
    }
  }
};

struct StyleConfig {
  char aspect_ratio[32] = "16:9";
  unsigned char bracket_color[4] = {239, 79, 84, 255}; // #ef4f54
  char font_family[256] = "font3";
  int font_size = 55;

  // 粘贴图片设置
  char paste_align[32] = "center";
  char paste_enabled[32] = "mixed";
  char paste_fill_mode[32] = "width";
  int paste_height = 800;
  char paste_valign[32] = "middle";
  int paste_width = 800;
  int paste_x = 1500;
  int paste_y = 200;

  unsigned char shadow_color[4] = {0, 0, 0, 255}; // #000000
  int shadow_offset_x = 0;
  int shadow_offset_y = 0;
  char text_align[32] = "left";
  unsigned char text_color[4] = {255, 255, 255, 255}; // #FFFFFF
  char text_valign[32] = "top";
  int textbox_height = 245;
  int textbox_width = 1579;
  int textbox_x = 470;
  int textbox_y = 1080;
  bool use_character_color = true;
};

// ==================== 通用工具函数 ====================
namespace utils {
#ifdef _DEBUG
// 时间测量辅助类
class Timer {
private:
  std::chrono::time_point<std::chrono::high_resolution_clock> start_time;
  std::string name;
  bool active;

public:
  Timer(const std::string &timer_name) : name(timer_name), active(true) { start_time = std::chrono::high_resolution_clock::now(); }

  ~Timer() {
    if (active) {
      stop();
    }
  }

  // 手动停止计时并返回结果
  double stop() {
    if (!active)
      return 0.0;

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    double ms = duration.count() / 1000.0;
    DEBUG_PRINT("Timer [%s]: %.3f ms", name.c_str(), ms);
    active = false;
    return ms;
  }

  // 获取当前耗时（毫秒）
  double elapsed() const {
    auto current_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(current_time - start_time);
    return duration.count() / 1000.0;
  }

  // 获取当前耗时（微秒）
  double elapsed_us() const {
    auto current_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(current_time - start_time);
    return static_cast<double>(duration.count());
  }
};
#endif
// 计算缩放后的尺寸
SDL_Rect CalculateScaledRect(int src_width, int src_height, int dst_width, int dst_height, const std::string &fill_mode) {
  SDL_Rect result = {0, 0, src_width, src_height};

  if (fill_mode == "width") {
    float scale = static_cast<float>(dst_width) / src_width;
    result.w = dst_width;
    result.h = static_cast<int>(src_height * scale);
  } else if (fill_mode == "height") {
    float scale = static_cast<float>(dst_height) / src_height;
    result.h = dst_height;
    result.w = static_cast<int>(src_width * scale);
  } else { // fit模式
    float scale_w = static_cast<float>(dst_width) / src_width;
    float scale_h = static_cast<float>(dst_height) / src_height;
    float scale = (scale_w < scale_h) ? scale_w : scale_h;
    result.w = static_cast<int>(src_width * scale);
    result.h = static_cast<int>(src_height * scale);
  }

  return result;
}

// 计算对齐位置
void CalculateAlignment(int region_x, int region_y, int region_width, int region_height, int item_width, int item_height, const std::string &align, const std::string &valign, int &out_x, int &out_y) {
  // 水平对齐
  if (align == "center") {
    out_x = region_x + (region_width - item_width) / 2;
  } else if (align == "right") {
    out_x = region_x + region_width - item_width;
  } else { // left
    out_x = region_x;
  }

  // 垂直对齐
  if (valign == "middle") {
    out_y = region_y + (region_height - item_height) / 2;
  } else if (valign == "bottom") {
    out_y = region_y + region_height - item_height;
  } else { // top
    out_y = region_y;
  }
}

// 根据对齐字符串计算位置
SDL_Rect CalculatePosition(const char *align_str, int offset_x, int offset_y, int target_width, int target_height, int source_width, int source_height) {
  SDL_Rect pos = {0, 0, source_width, source_height};

  if (!align_str)
    align_str = "top-left";
  std::string align(align_str);

  // 水平对齐
  if (align.find("right") != std::string::npos) {
    pos.x = target_width - source_width;
  } else if (align.find("center") != std::string::npos) {
    pos.x = (target_width - source_width) / 2;
  }

  // 垂直对齐
  if (align.find("bottom") != std::string::npos) {
    pos.y = target_height - source_height;
  } else if (align.find("middle") != std::string::npos) {
    pos.y = (target_height - source_height) / 2;
  }

  // 应用偏移
  pos.x += offset_x;
  pos.y += offset_y;

  return pos;
}

// 智能计算文本和图片区域分配
void CalculateTextImageRegions(bool has_text, bool has_image, const std::string &enabled_mode, const StyleConfig &style_config, int text_length, int emoji_count, int &text_x, int &text_y, int &text_width, int &text_height, int &image_x, int &image_y,
                               int &image_width, int &image_height) {
  // 默认使用原始区域
  text_x = style_config.textbox_x;
  text_y = style_config.textbox_y;
  text_width = style_config.textbox_width;
  text_height = style_config.textbox_height;

  image_x = style_config.paste_x;
  image_y = style_config.paste_y;
  image_width = style_config.paste_width;
  image_height = style_config.paste_height;

  // 智能区域分配逻辑
  if (has_image && has_text) {
    if (enabled_mode == "off") {
      // 估算文本长度
      int total_char_count = text_length / 3 + emoji_count;

      // 根据文本长度决定分配比例
      float image_ratio = (total_char_count < 20) ? 0.7f : 0.5f;

      // 计算分割后的区域（文本在左，图片在右）
      int total_width = style_config.textbox_width;
      int text_region_width = static_cast<int>(total_width * (1.0f - image_ratio));
      int image_region_width = total_width - text_region_width;

      // 文本区域（左侧）
      text_width = text_region_width;
      text_height = style_config.textbox_height;

      // 图片区域（右侧）
      image_x = style_config.textbox_x + text_region_width;
      image_y = style_config.textbox_y;
      image_width = image_region_width;
      image_height = style_config.textbox_height;
    }
  } else if (has_image && enabled_mode != "always") {
    // 只有图片时，使用文本框区域
    image_x = style_config.textbox_x;
    image_y = style_config.textbox_y;
    image_width = style_config.textbox_width;
    image_height = style_config.textbox_height;
  }
}

} // namespace utils

// ==================== Global Manager Class ====================
class ImageLoaderManager {
public:
  static ImageLoaderManager &GetInstance() {
    static ImageLoaderManager instance;
    return instance;
  }

  ~ImageLoaderManager() { Cleanup(); }

  // Disable copy
  ImageLoaderManager(const ImageLoaderManager &) = delete;
  ImageLoaderManager &operator=(const ImageLoaderManager &) = delete;

  // Set global configuration
  void SetGlobalConfig(const char *assets_path, float min_image_ratio) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (assets_path) {
      strncpy(assets_path_, assets_path, sizeof(assets_path_) - 1);
      assets_path_[sizeof(assets_path_) - 1] = '\0';
    }
    min_image_ratio_ = min_image_ratio;

    DEBUG_PRINT("Global configuration set: assets_path=%s", assets_path_);
  }

  // Update GUI settings
  void UpdateGuiSettings(const char *settings_json) {
    DEBUG_PRINT("Updating GUI settings");

    if (!settings_json)
      return;

    cJSON *json_root = cJSON_Parse(settings_json);
    if (!json_root) {
      DEBUG_PRINT("Failed to parse JSON");
      return;
    }

    // 解析压缩设置
    cJSON *compression = cJSON_GetObjectItem(json_root, "image_compression");
    if (compression) {
      cJSON *enabled = cJSON_GetObjectItem(compression, "pixel_reduction_enabled");
      if (enabled) {
        compression_enabled_ = cJSON_IsTrue(enabled);
      }

      cJSON *ratio = cJSON_GetObjectItem(compression, "pixel_reduction_ratio");
      if (ratio && cJSON_IsNumber(ratio)) {
        compression_ratio_ = ratio->valueint;
      }
    }

    cJSON_Delete(json_root);
  }

  void UpdateStyleConfig(const char *style_json) {
    DEBUG_PRINT("Updating style configuration");

    if (!style_json)
      return;

    cJSON *json_root = cJSON_Parse(style_json);
    if (!json_root) {
      DEBUG_PRINT("Failed to parse style JSON");
      return;
    }

    // 解析样式配置
    cJSON *aspect_ratio_item = cJSON_GetObjectItem(json_root, "aspect_ratio");
    if (aspect_ratio_item && cJSON_IsString(aspect_ratio_item)) {
      const char *aspect_ratio = aspect_ratio_item->valuestring;
      if (aspect_ratio) {
        strncpy(style_config_.aspect_ratio, aspect_ratio, sizeof(style_config_.aspect_ratio) - 1);
      }
    }

    // 解析括号颜色
    cJSON *bracket_color_item = cJSON_GetObjectItem(json_root, "bracket_color");
    if (bracket_color_item && cJSON_IsString(bracket_color_item)) {
      const char *bracket_color_str = bracket_color_item->valuestring;
      if (bracket_color_str && bracket_color_str[0] == '#') {
        int r, g, b;
        sscanf(bracket_color_str + 1, "%02x%02x%02x", &r, &g, &b);
        style_config_.bracket_color[0] = r;
        style_config_.bracket_color[1] = g;
        style_config_.bracket_color[2] = b;
        style_config_.bracket_color[3] = 255;
      }
    }

    // 解析字体
    cJSON *font_family_item = cJSON_GetObjectItem(json_root, "font_family");
    if (font_family_item && cJSON_IsString(font_family_item)) {
      const char *font_family = font_family_item->valuestring;
      if (font_family) {
        strncpy(style_config_.font_family, font_family, sizeof(style_config_.font_family) - 1);
      }
    }

    cJSON *font_size = cJSON_GetObjectItem(json_root, "font_size");
    if (font_size && cJSON_IsNumber(font_size)) {
      style_config_.font_size = font_size->valueint;
    }

    // 解析粘贴图片设置
    cJSON *paste_settings = cJSON_GetObjectItem(json_root, "paste_image_settings");
    if (paste_settings) {
      cJSON *align_item = cJSON_GetObjectItem(paste_settings, "align");
      if (align_item && cJSON_IsString(align_item)) {
        const char *align = align_item->valuestring;
        if (align)
          strncpy(style_config_.paste_align, align, sizeof(style_config_.paste_align) - 1);
      }

      cJSON *enabled_item = cJSON_GetObjectItem(paste_settings, "enabled");
      if (enabled_item && cJSON_IsString(enabled_item)) {
        const char *enabled = enabled_item->valuestring;
        if (enabled)
          strncpy(style_config_.paste_enabled, enabled, sizeof(style_config_.paste_enabled) - 1);
      }

      cJSON *fill_mode_item = cJSON_GetObjectItem(paste_settings, "fill_mode");
      if (fill_mode_item && cJSON_IsString(fill_mode_item)) {
        const char *fill_mode = fill_mode_item->valuestring;
        if (fill_mode)
          strncpy(style_config_.paste_fill_mode, fill_mode, sizeof(style_config_.paste_fill_mode) - 1);
      }

      cJSON *height = cJSON_GetObjectItem(paste_settings, "height");
      if (height && cJSON_IsNumber(height))
        style_config_.paste_height = height->valueint;

      cJSON *valign_item = cJSON_GetObjectItem(paste_settings, "valign");
      if (valign_item && cJSON_IsString(valign_item)) {
        const char *valign = valign_item->valuestring;
        if (valign)
          strncpy(style_config_.paste_valign, valign, sizeof(style_config_.paste_valign) - 1);
      }

      cJSON *width = cJSON_GetObjectItem(paste_settings, "width");
      if (width && cJSON_IsNumber(width))
        style_config_.paste_width = width->valueint;

      cJSON *x = cJSON_GetObjectItem(paste_settings, "x");
      if (x && cJSON_IsNumber(x))
        style_config_.paste_x = x->valueint;

      cJSON *y = cJSON_GetObjectItem(paste_settings, "y");
      if (y && cJSON_IsNumber(y))
        style_config_.paste_y = y->valueint;
    }

    // 解析阴影颜色
    cJSON *shadow_color_item = cJSON_GetObjectItem(json_root, "shadow_color");
    if (shadow_color_item && cJSON_IsString(shadow_color_item)) {
      const char *shadow_color_str = shadow_color_item->valuestring;
      if (shadow_color_str && shadow_color_str[0] == '#') {
        int r, g, b;
        sscanf(shadow_color_str + 1, "%02x%02x%02x", &r, &g, &b);
        style_config_.shadow_color[0] = r;
        style_config_.shadow_color[1] = g;
        style_config_.shadow_color[2] = b;
        style_config_.shadow_color[3] = 255;
      }
    }

    cJSON *shadow_offset_x = cJSON_GetObjectItem(json_root, "shadow_offset_x");
    if (shadow_offset_x && cJSON_IsNumber(shadow_offset_x)) {
      style_config_.shadow_offset_x = shadow_offset_x->valueint;
    }

    cJSON *shadow_offset_y = cJSON_GetObjectItem(json_root, "shadow_offset_y");
    if (shadow_offset_y && cJSON_IsNumber(shadow_offset_y)) {
      style_config_.shadow_offset_y = shadow_offset_y->valueint;
    }

    // 解析文本对齐
    cJSON *text_align_item = cJSON_GetObjectItem(json_root, "text_align");
    if (text_align_item && cJSON_IsString(text_align_item)) {
      const char *text_align = text_align_item->valuestring;
      if (text_align) {
        strncpy(style_config_.text_align, text_align, sizeof(style_config_.text_align) - 1);
      }
    }

    // 解析文本颜色
    cJSON *text_color_item = cJSON_GetObjectItem(json_root, "text_color");
    if (text_color_item && cJSON_IsString(text_color_item)) {
      const char *text_color_str = text_color_item->valuestring;
      if (text_color_str && text_color_str[0] == '#') {
        int r, g, b;
        sscanf(text_color_str + 1, "%02x%02x%02x", &r, &g, &b);
        style_config_.text_color[0] = r;
        style_config_.text_color[1] = g;
        style_config_.text_color[2] = b;
        style_config_.text_color[3] = 255;
      }
    }

    cJSON *text_valign_item = cJSON_GetObjectItem(json_root, "text_valign");
    if (text_valign_item && cJSON_IsString(text_valign_item)) {
      const char *text_valign = text_valign_item->valuestring;
      if (text_valign) {
        strncpy(style_config_.text_valign, text_valign, sizeof(style_config_.text_valign) - 1);
      }
    }

    // 解析文本框尺寸
    cJSON *textbox_height = cJSON_GetObjectItem(json_root, "textbox_height");
    if (textbox_height && cJSON_IsNumber(textbox_height)) {
      style_config_.textbox_height = textbox_height->valueint;
    }

    cJSON *textbox_width = cJSON_GetObjectItem(json_root, "textbox_width");
    if (textbox_width && cJSON_IsNumber(textbox_width)) {
      style_config_.textbox_width = textbox_width->valueint;
    }

    cJSON *textbox_x = cJSON_GetObjectItem(json_root, "textbox_x");
    if (textbox_x && cJSON_IsNumber(textbox_x)) {
      style_config_.textbox_x = textbox_x->valueint;
    }

    cJSON *textbox_y = cJSON_GetObjectItem(json_root, "textbox_y");
    if (textbox_y && cJSON_IsNumber(textbox_y)) {
      style_config_.textbox_y = textbox_y->valueint;
    }

    cJSON *use_character_color = cJSON_GetObjectItem(json_root, "use_character_color");
    if (use_character_color) {
      style_config_.use_character_color = cJSON_IsTrue(use_character_color);
    }

    cJSON_Delete(json_root);

    DEBUG_PRINT("Style configuration updated: font=%s, size=%d", style_config_.font_family, style_config_.font_size);
  }

  // Clear cache
  void ClearCache(const char *cache_type) {
    DEBUG_PRINT("Clearing cache: %s", cache_type ? cache_type : "null");

    std::lock_guard<std::mutex> lock(mutex_);

    if (!cache_type)
      return;

    ClearStaticLayerCache();
  }

  // Initialize SDL
  bool InitSDL() {
    if (!sdl_initialized_) {
      if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        DEBUG_PRINT("SDL initialization failed: %s", SDL_GetError());
        return false;
      }
      sdl_initialized_ = true;
    }

    if (!img_initialized_) {
      int imgFlags = IMG_INIT_PNG | IMG_INIT_JPG | IMG_INIT_WEBP;
      int initted = IMG_Init(imgFlags);
      if ((initted & imgFlags) != imgFlags) {
        DEBUG_PRINT("IMG_Init warning: %s", IMG_GetError());
      }
      img_initialized_ = true;
    }

    if (!ttf_initialized_) {
      if (TTF_Init() == -1) {
        DEBUG_PRINT("TTF initialization failed: %s", TTF_GetError());
        return false;
      }
      ttf_initialized_ = true;
    }

    if (!cache_mutex_) {
      cache_mutex_ = SDL_CreateMutex();
      if (!cache_mutex_) {
        DEBUG_PRINT("Failed to create cache mutex");
        return false;
      }
    }
    if (!renderer_initialized_) {
      if (!InitRenderer()) {
        DEBUG_PRINT("Failed to initialize renderer for scaling");
        return false;
      }
    }

    return true;
  }

  // Initialize SDL Renderer (for high-quality scaling)
  bool InitRenderer() {
    if (!sdl_initialized_) {
      if (!InitSDL()) {
        return false;
      }
    }

    // 创建离屏窗口用于渲染器
    if (!renderer_window_) {
      // 创建隐藏窗口
      renderer_window_ = SDL_CreateWindow("ImageLoader Renderer", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 1, 1, // 最小尺寸
                                          SDL_WINDOW_HIDDEN);
      if (!renderer_window_) {
        DEBUG_PRINT("Failed to create renderer window: %s", SDL_GetError());
        return false;
      }
    }

    // 创建渲染器
    if (!renderer_) {
      // 使用硬件加速渲染器，支持高质量缩放
      renderer_ = SDL_CreateRenderer(renderer_window_, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_TARGETTEXTURE);
      if (!renderer_) {
        DEBUG_PRINT("Failed to create renderer: %s", SDL_GetError());
        // 尝试软件渲染器作为备选
        renderer_ = SDL_CreateRenderer(renderer_window_, -1, SDL_RENDERER_SOFTWARE | SDL_RENDERER_TARGETTEXTURE);
        if (!renderer_) {
          DEBUG_PRINT("Failed to create software renderer: %s", SDL_GetError());
          return false;
        }
      }

      // 设置渲染器缩放质量为线性插值（更平滑）
      SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "linear");
      SDL_RenderSetLogicalSize(renderer_, 1, 1);

      DEBUG_PRINT("Renderer initialized successfully");
    }

    renderer_initialized_ = true;
    return true;
  }

  // Cleanup renderer resources
  void CleanupRenderer() {
    if (renderer_) {
      SDL_DestroyRenderer(renderer_);
      renderer_ = nullptr;
      renderer_initialized_ = false;
      DEBUG_PRINT("Renderer destroyed");
    }

    if (renderer_window_) {
      SDL_DestroyWindow(renderer_window_);
      renderer_window_ = nullptr;
      DEBUG_PRINT("Renderer window destroyed");
    }
  }

  LoadResult GeneratePreviewImage(const char *assets_path, int canvas_width, int canvas_height, const char *components_json, const char *character_name, int emotion_index, int background_index, unsigned char **out_data, int *out_width, int *out_height) {
    TIME_SCOPE("Starting to generate preview image");

    if (!InitSDL()) {
      return LoadResult::SDL_INIT_FAILED;
    }

    // Parse JSON
    cJSON *json_root = cJSON_Parse(components_json);
    if (!json_root || !cJSON_IsArray(json_root)) {
      DEBUG_PRINT("JSON parse error");
      cJSON_Delete(json_root);
      return LoadResult::JSON_PARSE_ERROR;
    }

    // Create canvas
    SDL_Surface *canvas = SDL_CreateRGBSurfaceWithFormat(0, canvas_width, canvas_height, 32, SDL_PIXELFORMAT_ABGR8888);
    if (!canvas) {
      DEBUG_PRINT("Failed to create canvas: %s", SDL_GetError());
      cJSON_Delete(json_root);
      return LoadResult::FAILED;
    }

    // Fill with transparent
    // SDL_FillRect(canvas, nullptr, SDL_MapRGBA(canvas->format, 0, 0, 0, 0));

    // Check for cache mark
    bool has_cache_mark = static_layer_cache_first_ != nullptr;
    int component_count = cJSON_GetArraySize(json_root);

    // Reset static layer cache pointer
    ResetStaticLayerCachePointer();

    // If no cache mark, clear and reinitialize static layer cache
    if (!has_cache_mark) {
      ClearStaticLayerCache();
      DEBUG_PRINT("Reinitializing static layer cache");
    }

    // Current static layer segment (for caching consecutive static components)
    SDL_Surface *current_static_segment = nullptr;

    // Draw each component
    for (int i = 0; i < component_count; i++) {
      cJSON *comp_obj = cJSON_GetArrayItem(json_root, i);

      // Check if it's a cache mark
      cJSON *use_cache = cJSON_GetObjectItem(comp_obj, "use_cache");
      if (use_cache && cJSON_IsTrue(use_cache)) {
        // If it's a cache mark, get next cached static layer
        SDL_Surface *cached_layer = GetNextCachedLayer();
        if (cached_layer) {
          DEBUG_PRINT("Drawing cached layer");
          SDL_BlitSurface(cached_layer, nullptr, canvas, nullptr);
        }
        continue;
      }

      bool enabled = GetJsonBool(comp_obj, "enabled", true);
      if (!enabled)
        continue;

      std::string type(GetJsonString(comp_obj, "type", ""));
      // 需要缓存图层
      if (!has_cache_mark) {

        // Determine if component is static
        bool is_static = false;
        if (type == "textbox" || type == "extra" || type == "namebox" || type == "text")
          is_static = true;
        else if (type == "character" && GetJsonBool(comp_obj, "use_fixed_character", false))
          is_static = true;
        else if (type == "background" && GetJsonBool(comp_obj, "use_fixed_background", false))
          is_static = true;

        if (is_static) {
          // If it's a static component and no current static segment, create one
          if (!current_static_segment)
            current_static_segment = SDL_CreateRGBSurfaceWithFormat(0, canvas_width, canvas_height, 32, SDL_PIXELFORMAT_ABGR8888);
        } else {
          // Encounter dynamic component, save current static segment
          AddStaticLayerToCache(current_static_segment);
          current_static_segment = nullptr;
          DEBUG_PRINT("Saving static layer segment");
        }
      }

      // Draw component based on type
      bool draw_success = false;
      if (type == "background") {
        draw_success = DrawBackgroundComponent(canvas, current_static_segment, comp_obj, background_index);
      } else if (type == "character") {
        draw_success = DrawCharacterComponent(canvas, current_static_segment, comp_obj, character_name, emotion_index);
      } else if (type == "namebox") {
        draw_success = DrawNameboxComponent(canvas, current_static_segment, comp_obj);
      } else if (type == "text") {
        draw_success = DrawTextComponent(canvas, current_static_segment, comp_obj);
      } else {
        draw_success = DrawGenericComponent(canvas, current_static_segment, comp_obj);
      }

      if (!draw_success) {
        DEBUG_PRINT("Failed to draw component: %s", type.c_str());
      }
    }

    // Handle last static segment (only when no cache mark)
    if (!has_cache_mark && current_static_segment) {
      AddStaticLayerToCache(current_static_segment);
      DEBUG_PRINT("Saving final static layer segment");
    }

    cJSON_Delete(json_root);

    // Cache the generated image as preview (replace old preview)
    ClearPreviewCache();
    preview_cache_ = ImageData::FromSurface(canvas);

    DEBUG_PRINT("Preview cache updated: %dx%d", preview_cache_->width, preview_cache_->height);

    // Return image data
    *out_width = canvas->w;
    *out_height = canvas->h;
    size_t data_size = static_cast<size_t>(canvas->h) * canvas->pitch;
    *out_data = static_cast<unsigned char *>(malloc(data_size));

    if (*out_data) {
      memcpy(*out_data, canvas->pixels, data_size);
      SDL_FreeSurface(canvas);
      DEBUG_PRINT("Image generation successful: %dx%d", *out_width, *out_height);
      return LoadResult::SUCCESS;
    } else {
      SDL_FreeSurface(canvas);
      DEBUG_PRINT("Failed to allocate output buffer");
      return LoadResult::FAILED;
    }
  }

  LoadResult DrawContentWithTextAndImage(const char *text, const char *emoji_json, unsigned char *image_data, int image_width, int image_height, int image_pitch, unsigned char **out_data, int *out_width, int *out_height) {
    TIME_SCOPE("Starting DrawContentWithTextAndImage");
    // 1. 参数检查
    if (!text || !out_data || !out_width || !out_height) {
      DEBUG_PRINT("Invalid parameters");
      return LoadResult::FAILED;
    }
    DEBUG_PRINT("Input text length: %zd", strlen(text));

    if (!InitSDL()) {
      DEBUG_PRINT("SDL initialization failed");
      return LoadResult::SDL_INIT_FAILED;
    }

    // 检查预览缓存
    SDL_LockMutex(cache_mutex_);
    bool has_preview = (preview_cache_ != nullptr);
    SDL_UnlockMutex(cache_mutex_);

    if (!has_preview) {
      DEBUG_PRINT("No preview in cache, cannot draw content");
      return LoadResult::FAILED;
    }

    // 2. 获取画布
    SDL_LockMutex(cache_mutex_);
    SDL_Surface *canvas = SDL_CreateRGBSurfaceWithFormatFrom(preview_cache_->data, preview_cache_->width, preview_cache_->height, 32, preview_cache_->pitch, SDL_PIXELFORMAT_ABGR8888);
    SDL_UnlockMutex(cache_mutex_);

    if (!canvas) {
      DEBUG_PRINT("Failed to create canvas: %s", SDL_GetError());
      return LoadResult::FAILED;
    }

    // 2. 解析emoji数据
    std::vector<std::string> emoji_list;
    std::vector<std::pair<int, int>> emoji_positions;

    if (emoji_json && emoji_json[0] != '\0') {
      DEBUG_PRINT("Parsing emoji JSON: %s", emoji_json);
      cJSON *json_root = cJSON_Parse(emoji_json);
      if (json_root) {
        cJSON *emojis_array = cJSON_GetObjectItem(json_root, "emojis");
        cJSON *positions_array = cJSON_GetObjectItem(json_root, "positions");
        if (emojis_array && cJSON_IsArray(emojis_array)) {
          int array_size = cJSON_GetArraySize(emojis_array);
          for (int i = 0; i < array_size; i++) {
            cJSON *item = cJSON_GetArrayItem(emojis_array, i);
            if (item && cJSON_IsString(item)) {
              emoji_list.push_back(item->valuestring);
              item = cJSON_GetArrayItem(positions_array, i);
              cJSON *start_item = cJSON_GetArrayItem(item, 0);
              cJSON *end_item = cJSON_GetArrayItem(item, 1);
              emoji_positions.push_back(std::make_pair(start_item->valueint, end_item->valueint));
            }
          }
        }
        cJSON_Delete(json_root);
      }
    }

    // 3. 确定文本和图片绘制区域
    bool has_text = (text && strlen(text) > 0);
    bool has_image = (image_data && image_width > 0 && image_height > 0);

    // 使用工具函数计算区域分配
    int text_x, text_y, text_width, text_height;
    int image_x, image_y, image_width_region, image_height_region;

    utils::CalculateTextImageRegions(has_text, has_image, style_config_.paste_enabled, style_config_, strlen(text), emoji_list.size(), text_x, text_y, text_width, text_height, image_x, image_y, image_width_region, image_height_region);

    // 4. 绘制图片和文本
    if (has_image) {
      DEBUG_PRINT("Drawing image: %dx%d", image_width, image_height);
      DrawImageToCanvas(canvas, image_data, image_width, image_height, image_pitch, image_x, image_y, image_width_region, image_height_region);
    }
    if (has_text) {
      DEBUG_PRINT("Drawing text: '%s'", text);
      DrawTextAndEmojiToCanvas(canvas, std::string(text), emoji_list, emoji_positions, text_x, text_y, text_width, text_height);
    }

    // 5. 压缩图像 - 使用渲染器进行高质量缩放
    if (compression_enabled_ && compression_ratio_ > 0) {
      DEBUG_PRINT("Applying compression with renderer: ratio=%d%%", compression_ratio_);

      // 计算新尺寸
      int new_width = static_cast<int>(canvas->w * (1.0f - compression_ratio_ / 100.0f));
      int new_height = static_cast<int>(canvas->h * (1.0f - compression_ratio_ / 100.0f));

      DEBUG_PRINT("Compressing from %dx%d to %dx%d", canvas->w, canvas->h, new_width, new_height);

      // 尝试使用渲染器进行高质量缩放
      SDL_Surface *compressed_surface = ScaleSurfaceWithRenderer(canvas, new_width, new_height);

      if (compressed_surface) {
        // 替换原画布
        SDL_FreeSurface(canvas);
        canvas = compressed_surface;
        DEBUG_PRINT("Renderer compression successful, new size: %dx%d", canvas->w, canvas->h);
      }
    }

    // 6. 返回图像数据
    *out_width = canvas->w;
    *out_height = canvas->h;
    size_t data_size = static_cast<size_t>(canvas->h) * canvas->pitch;
    *out_data = static_cast<unsigned char *>(malloc(data_size));

    if (*out_data) {
      memcpy(*out_data, canvas->pixels, data_size);
      SDL_FreeSurface(canvas);
      DEBUG_PRINT("Content drawing successful: %dx%d", *out_width, *out_height);
      return LoadResult::SUCCESS;
    } else {
      SDL_FreeSurface(canvas);
      DEBUG_PRINT("Failed to allocate output buffer");
      return LoadResult::FAILED;
    }
  }

  // Cleanup all resources
  void Cleanup() {
    ClearCache("all");

    // 清理渲染器资源
    CleanupRenderer();

    if (cache_mutex_) {
      SDL_DestroyMutex(cache_mutex_);
      cache_mutex_ = nullptr;
    }

    if (ttf_initialized_) {
      TTF_Quit();
      ttf_initialized_ = false;
    }

    if (img_initialized_) {
      IMG_Quit();
      img_initialized_ = false;
    }

    if (sdl_initialized_) {
      SDL_Quit();
      sdl_initialized_ = false;
    }

    DEBUG_PRINT("All resources cleaned up");
  }

private:
  ImageLoaderManager() = default;
  StyleConfig style_config_;

  // 新增：使用emoji位置信息的文本绘制函数
  void DrawTextAndEmojiToCanvas(SDL_Surface *canvas, const std::string &text, const std::vector<std::string> &emoji_list, const std::vector<std::pair<int, int>> &emoji_positions, int text_x, int text_y, int text_width, int text_height);

  std::vector<std::pair<int, int>> FastBreakTextIntoLines(TTF_Font *font, const std::string &text, int max_width) {
    std::vector<std::pair<int, int>> lines;
    int text_len = static_cast<int>(text.length());
    int start_byte = 0;

    while (start_byte < text_len) {
      int extent = 0;
      int char_count = 0;

      // 使用TTF_MeasureUTF8测量能容纳的字符数
      const char *remaining_text = text.c_str() + start_byte;
      if (TTF_MeasureUTF8(font, remaining_text, max_width, &extent, &char_count) == 0 && char_count > 0) {
        // 将字符数转换为字节数
        int byte_count = 0;
        int chars_processed = 0;
        int i = start_byte;

        while (i < text_len && chars_processed < char_count) {
          unsigned char c = static_cast<unsigned char>(text[i]);
          int char_len = 1;

          if (c < 0x80)
            char_len = 1;
          else if ((c & 0xE0) == 0xC0)
            char_len = 2;
          else if ((c & 0xF0) == 0xE0)
            char_len = 3;
          else if ((c & 0xF8) == 0xF0)
            char_len = 4;

          i += char_len;
          byte_count += char_len;
          chars_processed++;
        }

        int end_byte = start_byte + byte_count;
        lines.push_back({start_byte, end_byte});
        start_byte = end_byte;
      } else {
        // 无法测量，跳出循环
        break;
      }
    }

    if (lines.empty() && text_len > 0) {
      // 至少添加一行
      lines.push_back({0, text_len});
    }

    return lines;
  }

  bool FindBracketPairsInText(const std::string &text, std::vector<std::tuple<int, int, SDL_Color>> &bracket_segments, const SDL_Color &bracket_color_config) {
    TIME_SCOPE("2. FindBracketPairsInText");
    DEBUG_PRINT("Looking for bracket pairs in text of length %zu", text.length());

    bool found_any = false;

    // 使用栈来匹配括号，处理嵌套情况
    struct BracketInfo {
      int position;
      std::string bracket;
      bool is_left;
    };

    std::vector<BracketInfo> all_brackets;

    // 第一步：收集所有括号的位置
    for (size_t i = 0; i < text.length();) {
      unsigned char c = static_cast<unsigned char>(text[i]);
      int char_len = 1;

      // 计算UTF-8字符长度
      if (c < 0x80) {
        char_len = 1;
      } else if ((c & 0xE0) == 0xC0) {
        char_len = 2;
      } else if ((c & 0xF0) == 0xE0) {
        char_len = 3;
      } else if ((c & 0xF8) == 0xF0) {
        char_len = 4;
      }

      if (i + char_len > text.length()) {
        break;
      }

      std::string current_char = text.substr(i, char_len);

      // 检查是否是括号
      bool is_left = false;
      bool is_bracket = false;
      bool find_same_bracket = false;

      // 先检查是否是左括号
      auto left_it = lt_bracket_pairs.find(current_char);
      if (left_it != lt_bracket_pairs.end()) {
        is_bracket = true;
        // 检查是否是左右相同的括号
        is_left = true;
        if (current_char == left_it->second) {
          if (find_same_bracket) {
            is_left = false;
            find_same_bracket = false;
          } else
            find_same_bracket = true;
        }
      } else {
        for (const auto &pair : lt_bracket_pairs)
          if (!is_bracket && current_char == pair.second)
            is_bracket = true;
      }

      if (is_bracket) {
        all_brackets.push_back({static_cast<int>(i), current_char, is_left});
        // DEBUG_PRINT("Found bracket '%s' at position %zu (is_left: %d)", current_char.c_str(), i, is_left);
      }

      i += char_len;
    }

    // 第二步：使用栈匹配括号
    std::stack<BracketInfo> bracket_stack;

    for (const auto &bracket : all_brackets) {
      auto left_it = lt_bracket_pairs.find(bracket.bracket);

      if (bracket.is_left) {
        bracket_stack.push(bracket);
      } else {
        // 这是一个右括号，尝试在栈中找到匹配的左括号
        std::stack<BracketInfo> temp_stack;
        bool matched = false;

        while (!bracket_stack.empty()) {
          auto top = bracket_stack.top();
          bracket_stack.pop();

          // 检查是否匹配
          if (top.is_left) {
            auto it = lt_bracket_pairs.find(top.bracket);
            if (it != lt_bracket_pairs.end() && it->second == bracket.bracket) {
              // 找到匹配的括号对
              bracket_segments.emplace_back(top.position, bracket.position + static_cast<int>(bracket.bracket.length()), bracket_color_config);
              found_any = true;
              DEBUG_PRINT("Found matching bracket pair: [%d, %d) - '%s%s'", top.position, bracket.position + static_cast<int>(bracket.bracket.length()), top.bracket.c_str(), bracket.bracket.c_str());
              matched = true;

              // 将临时栈中的括号放回
              while (!temp_stack.empty()) {
                bracket_stack.push(temp_stack.top());
                temp_stack.pop();
              }
              break;
            }
          }

          temp_stack.push(top);
        }

        if (!matched) {
          // 没有找到匹配的左括号，将临时栈中的括号放回
          while (!temp_stack.empty()) {
            bracket_stack.push(temp_stack.top());
            temp_stack.pop();
          }
        }
      }
    }

    // 第三步：按起始位置排序并合并重叠的括号段
    if (!bracket_segments.empty()) {
      std::sort(bracket_segments.begin(), bracket_segments.end(), [](const auto &a, const auto &b) { return std::get<0>(a) < std::get<0>(b); });

      // 合并重叠的括号段
      std::vector<std::tuple<int, int, SDL_Color>> merged_segments;
      auto current = bracket_segments[0];

      for (size_t i = 1; i < bracket_segments.size(); i++) {
        auto &next = bracket_segments[i];
        int current_start = std::get<0>(current);
        int current_end = std::get<1>(current);
        int next_start = std::get<0>(next);
        int next_end = std::get<1>(next);

        if (next_start <= current_end) {
          // 重叠或相邻，合并
          if (next_end > current_end) {
            std::get<1>(current) = next_end;
          }
        } else {
          merged_segments.push_back(current);
          current = next;
        }
      }
      merged_segments.push_back(current);

      bracket_segments = merged_segments;
    }

    DEBUG_PRINT("Found %zu bracket segments after merging", bracket_segments.size());
    return found_any;
  }

  // 使用渲染器进行高质量缩放
  SDL_Surface *ScaleSurfaceWithRenderer(SDL_Surface *surface, int new_width, int new_height) {
    if (!surface || new_width <= 0 || new_height <= 0) {
      DEBUG_PRINT("Invalid parameters for renderer scaling");
      return nullptr;
    }

    // 初始化渲染器（如果尚未初始化）
    if (!renderer_initialized_) {
      if (!InitRenderer()) {
        DEBUG_PRINT("Failed to initialize renderer for scaling");
        return nullptr;
      }
    }

    // 创建源纹理
    SDL_Texture *source_texture = SDL_CreateTextureFromSurface(renderer_, surface);
    if (!source_texture) {
      DEBUG_PRINT("Failed to create source texture: %s", SDL_GetError());
      return nullptr;
    }

    // 设置纹理的缩放模式为线性插值（更平滑）
    SDL_SetTextureScaleMode(source_texture, SDL_ScaleModeLinear);

    // 创建目标纹理（可渲染目标）
    SDL_Texture *target_texture = SDL_CreateTexture(renderer_, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_TARGET, new_width, new_height);
    if (!target_texture) {
      DEBUG_PRINT("Failed to create target texture: %s", SDL_GetError());
      SDL_DestroyTexture(source_texture);
      return nullptr;
    }

    // 设置目标纹理为当前渲染目标
    SDL_Texture *previous_target = SDL_GetRenderTarget(renderer_);
    if (SDL_SetRenderTarget(renderer_, target_texture) != 0) {
      DEBUG_PRINT("Failed to set render target: %s", SDL_GetError());
      SDL_DestroyTexture(source_texture);
      SDL_DestroyTexture(target_texture);
      return nullptr;
    }

    // 清除渲染目标（透明）
    SDL_SetRenderDrawColor(renderer_, 0, 0, 0, 0);
    SDL_RenderClear(renderer_);

    // 将源纹理渲染到目标纹理，使用高质量缩放
    SDL_Rect dest_rect = {0, 0, new_width, new_height};
    if (SDL_RenderCopy(renderer_, source_texture, nullptr, &dest_rect) != 0) {
      DEBUG_PRINT("Failed to render copy: %s", SDL_GetError());
      SDL_SetRenderTarget(renderer_, previous_target);
      SDL_DestroyTexture(source_texture);
      SDL_DestroyTexture(target_texture);
      return nullptr;
    }

    // 恢复之前的渲染目标
    SDL_SetRenderTarget(renderer_, previous_target);

    // 创建表面来存储结果
    SDL_Surface *result_surface = SDL_CreateRGBSurfaceWithFormat(0, new_width, new_height, 32, SDL_PIXELFORMAT_ABGR8888);
    if (!result_surface) {
      DEBUG_PRINT("Failed to create result surface: %s", SDL_GetError());
      SDL_DestroyTexture(source_texture);
      SDL_DestroyTexture(target_texture);
      return nullptr;
    }

    // 从纹理读取像素到表面
    if (SDL_SetRenderTarget(renderer_, target_texture) == 0) {
      if (SDL_RenderReadPixels(renderer_, nullptr, SDL_PIXELFORMAT_ABGR8888, result_surface->pixels, result_surface->pitch) != 0) {
        DEBUG_PRINT("Failed to read pixels from texture: %s", SDL_GetError());
        SDL_FreeSurface(result_surface);
        result_surface = nullptr;
      }
      SDL_SetRenderTarget(renderer_, previous_target);
    } else {
      DEBUG_PRINT("Failed to set render target for reading pixels");
      SDL_FreeSurface(result_surface);
      result_surface = nullptr;
    }

    // 清理纹理
    SDL_DestroyTexture(source_texture);
    SDL_DestroyTexture(target_texture);

    return result_surface;
  }

  // 解析RGB颜色
  SDL_Color ParseColor(cJSON *color_item) {
    SDL_Color color = {255, 255, 255, 255};
    if (!color_item) {
      return color;
    }

    if (cJSON_IsArray(color_item)) {
      // RGB数组格式
      cJSON *r = cJSON_GetArrayItem(color_item, 0);
      cJSON *g = cJSON_GetArrayItem(color_item, 1);
      cJSON *b = cJSON_GetArrayItem(color_item, 2);
      cJSON *a = cJSON_GetArrayItem(color_item, 3);

      if (r && cJSON_IsNumber(r))
        color.r = static_cast<Uint8>(r->valueint);
      if (g && cJSON_IsNumber(g))
        color.g = static_cast<Uint8>(g->valueint);
      if (b && cJSON_IsNumber(b))
        color.b = static_cast<Uint8>(b->valueint);
      if (a && cJSON_IsNumber(a))
        color.a = static_cast<Uint8>(a->valueint);
    } else if (cJSON_IsString(color_item)) {
      // 十六进制字符串格式，如"#FFFFFF"
      const char *color_str = color_item->valuestring;
      if (color_str && color_str[0] == '#') {
        unsigned int hex_color = 0;
        if (strlen(color_str) >= 7) {
          // 解析 #RRGGBB 格式
          sscanf(color_str + 1, "%06x", &hex_color);
          color.r = (hex_color >> 16) & 0xFF;
          color.g = (hex_color >> 8) & 0xFF;
          color.b = hex_color & 0xFF;
          color.a = 255;
        } else if (strlen(color_str) >= 9) {
          // 解析 #RRGGBBAA 格式
          sscanf(color_str + 1, "%08x", &hex_color);
          color.r = (hex_color >> 24) & 0xFF;
          color.g = (hex_color >> 16) & 0xFF;
          color.b = (hex_color >> 8) & 0xFF;
          color.a = hex_color & 0xFF;
        }
      }
    }

    return color;
  }

  // 查找带扩展名的文件 (使用缓存优化版本)
  bool FindFileWithExtensions(const char *base_path, const std::vector<std::string> &extensions, std::string &found_path) { return file_path_cache_.FindFile(base_path, extensions, found_path); }

  // 加载角色图片
  SDL_Surface *LoadCharacterImage(const char *character_name, int emotion_index) {
    if (!character_name)
      return nullptr;

    // Build file path
    char file_path[1024];
    snprintf(file_path, sizeof(file_path), "%s/chara/%s/%s (%d)", assets_path_, character_name, character_name, emotion_index);

    // 使用文件路径缓存
    std::string found_path;
    static const std::vector<std::string> extensions = {".webp", ".png", ".jpg", ".jpeg", ".bmp"};

    if (!FindFileWithExtensions(file_path, extensions, found_path)) {
      DEBUG_PRINT("Character image not found: %s", file_path);
      return nullptr;
    }

    // Load image
    SDL_Surface *surface = IMG_Load(found_path.c_str());
    if (!surface) {
      DEBUG_PRINT("Failed to load character: %s", found_path.c_str());
      return nullptr;
    }
    return surface;
  }

  // 加载背景图片
  SDL_Surface *LoadBackgroundImage(const char *background_name) {
    if (!background_name)
      return nullptr;

    // Build file path
    char file_path[1024];
    snprintf(file_path, sizeof(file_path), "%s/background/%s", assets_path_, background_name);

    // 使用文件路径缓存
    std::string found_path;
    static const std::vector<std::string> extensions = {".webp", ".png", ".jpg", ".jpeg", ".bmp"};

    if (!FindFileWithExtensions(file_path, extensions, found_path)) {
      // If not found in background folder, try shader folder
      snprintf(file_path, sizeof(file_path), "%s/shader/%s", assets_path_, background_name);

      if (!FindFileWithExtensions(file_path, extensions, found_path)) {
        DEBUG_PRINT("Background image not found: %s", background_name);
        return nullptr;
      }
    }

    // Load image
    SDL_Surface *surface = IMG_Load(found_path.c_str());
    if (!surface) {
      DEBUG_PRINT("Failed to load background: %s", found_path.c_str());
      return nullptr;
    }
    return surface;
  }

  // 加载组件图片
  SDL_Surface *LoadComponentImage(const char *overlay) {
    if (!overlay || strlen(overlay) == 0)
      return nullptr;

    // Build component path
    char base_name[256];
    strncpy(base_name, overlay, sizeof(base_name) - 1);
    base_name[sizeof(base_name) - 1] = '\0';
    char *dot = strrchr(base_name, '.');
    if (dot)
      *dot = '\0';

    char base_path[1024];
    snprintf(base_path, sizeof(base_path), "%s/shader/%s", assets_path_, base_name);

    // 使用文件路径缓存
    std::string found_path;
    static const std::vector<std::string> extensions = {".webp", ".png", ".jpg", ".jpeg", ".bmp"};

    if (!FindFileWithExtensions(base_path, extensions, found_path)) {
      return nullptr;
    }

    SDL_Surface *comp_surface = IMG_Load(found_path.c_str());
    if (!comp_surface) {
      return nullptr;
    }
    return comp_surface;
  }

  // 背景组件绘制
  bool DrawBackgroundComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj, int background_index) {
    const char *overlay = GetJsonString(comp_obj, "overlay", "");

    DEBUG_PRINT("draw background, overlay: %s", overlay ? overlay : "null");

    SDL_Surface *bg_surface = nullptr;

    if (overlay && strlen(overlay) > 0) {
      // 检查是否是颜色值（以#开头的十六进制颜色）
      if (overlay[0] == '#') {
        // 解析颜色值，支持 #RRGGBB 格式
        unsigned int hex_color = 0;
        if (strlen(overlay) >= 7) {
          sscanf(overlay + 1, "%06x", &hex_color);
          Uint8 r = (hex_color >> 16) & 0xFF;
          Uint8 g = (hex_color >> 8) & 0xFF;
          Uint8 b = hex_color & 0xFF;

          // 创建一个纯色表面（使用画布尺寸）
          int canvas_width = target1 ? target1->w : 2560;
          int canvas_height = target1 ? target1->h : 1440;

          bg_surface = SDL_CreateRGBSurfaceWithFormat(0, canvas_width, canvas_height, 32, SDL_PIXELFORMAT_ABGR8888);
          if (bg_surface) {
            SDL_FillRect(bg_surface, nullptr, SDL_MapRGBA(bg_surface->format, r, g, b, 255));
          }
        }
      } else {
        // 加载图片背景
        char bg_name[32];
        strncpy(bg_name, overlay, sizeof(bg_name) - 1);
        char *dot = strrchr(bg_name, '.');
        if (dot)
          *dot = '\0';

        bg_surface = LoadBackgroundImage(bg_name);
      }
    } else {
      // 随机背景
      char bg_name[32];
      snprintf(bg_name, sizeof(bg_name), "c%d", background_index);
      bg_surface = LoadBackgroundImage(bg_name);
    }

    if (!bg_surface)
      return false;

    // 使用渲染器进行高质量缩放
    float scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    SDL_Surface *final_surface = bg_surface;

    if (scale != 1.0f) {
      SDL_Surface *scaled_surface = ScaleSurfaceWithRenderer(bg_surface, static_cast<int>(bg_surface->h * scale), static_cast<int>(bg_surface->w * scale));
      if (scaled_surface) {
        SDL_FreeSurface(bg_surface);
        final_surface = scaled_surface;
      }
    }

    // 使用工具函数计算位置
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));

    // Draw to target surfaces
    SDL_Rect pos = utils::CalculatePosition(align, offset_x, offset_y, target1->w, target1->h, final_surface->w, final_surface->h);
    SDL_Rect pos1 = pos;
    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, &pos);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, &pos1);

    SDL_FreeSurface(final_surface);
    return true;
  }

  // 角色组件绘制
  bool DrawCharacterComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj, const char *character_name, int emotion_index) {
    const char *draw_char_name = character_name;
    int draw_emotion = emotion_index;

    draw_char_name = GetJsonString(comp_obj, "character_name", "");
    draw_emotion = static_cast<int>(GetJsonNumber(comp_obj, "emotion_index", 1));

    if (!draw_char_name || strlen(draw_char_name) == 0 || draw_emotion <= 0) {
      return false;
    }

    SDL_Surface *char_surface = LoadCharacterImage(draw_char_name, draw_emotion);
    if (!char_surface)
      return false;

    // 使用渲染器进行高质量缩放
    float comp_scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    float chara_scale = static_cast<float>(GetJsonNumber(comp_obj, "scale1", 1.0));
    float scale = comp_scale * chara_scale;

    SDL_Surface *final_surface = char_surface;

    if (scale != 1.0f) {
      int new_width = static_cast<int>(char_surface->w * scale);
      int new_height = static_cast<int>(char_surface->h * scale);

      SDL_Surface *scaled_surface = ScaleSurfaceWithRenderer(char_surface, new_width, new_height);
      if (scaled_surface) {
        SDL_FreeSurface(char_surface);
        final_surface = scaled_surface;
      }
    }

    // 使用工具函数计算位置
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int comp_offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int comp_offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));
    int chara_offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x1", 0));
    int chara_offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y1", 0));
    int offset_x = comp_offset_x + chara_offset_x;
    int offset_y = comp_offset_y + chara_offset_y;

    SDL_Rect pos = utils::CalculatePosition(align, offset_x, offset_y, target1->w, target1->h, final_surface->w, final_surface->h);
    SDL_Rect pos1 = pos;

    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, &pos);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, &pos1);

    SDL_FreeSurface(final_surface);
    return true;
  }

  SDL_Surface *DrawNameboxWithText(cJSON *comp_obj) {
    const char *overlay = GetJsonString(comp_obj, "overlay", "");

    if (strlen(overlay) == 0) {
      DEBUG_PRINT("draw_namebox_with_text: Empty overlay");
      return nullptr;
    }

    // 加载图像
    SDL_Surface *namebox_surface = LoadComponentImage(overlay);
    if (!namebox_surface) {
      DEBUG_PRINT("draw_namebox_with_text: Failed to load namebox image: %s", overlay);
      return nullptr;
    }

    // 获取文本配置
    cJSON *textcfg_obj = cJSON_GetObjectItem(comp_obj, "textcfg");
    if (!textcfg_obj || !cJSON_IsArray(textcfg_obj)) {
      DEBUG_PRINT("draw_namebox_with_text: No text configurations found for namebox");
      return namebox_surface; // 返回没有文字的namebox
    }

    int text_config_count = cJSON_GetArraySize(textcfg_obj);

    if (text_config_count == 0) {
      DEBUG_PRINT("draw_namebox_with_text: Empty text configurations for namebox");
      return namebox_surface;
    }

    // 查找最大字体大小用于基线计算
    int max_font_size = 0;
    for (int i = 0; i < text_config_count; i++) {
      cJSON *config_obj = cJSON_GetArrayItem(textcfg_obj, i);
      if (config_obj) {
        int font_size = static_cast<int>(GetJsonNumber(config_obj, "font_size", 92.0));
        if (font_size > max_font_size) {
          max_font_size = font_size;
        }
      }
    }

    // 计算基线位置（基于最大字体大小）- 高度的65%
    int baseline_y = static_cast<int>(namebox_surface->h * 0.65);

    // 起始X位置 - 以270为中心，根据最大字体大小调整
    int current_x = 270 - max_font_size / 2;

    // 获取字体名称
    const char *font_name = GetJsonString(comp_obj, "font_name", "font3");

    // 绘制每个文本
    for (int i = 0; i < text_config_count; i++) {
      cJSON *config_obj = cJSON_GetArrayItem(textcfg_obj, i);
      if (!config_obj) {
        continue;
      }

      const char *text = GetJsonString(config_obj, "text", "");
      if (strlen(text) == 0) {
        continue;
      }

      int font_size = static_cast<int>(GetJsonNumber(config_obj, "font_size", 92.0));

      // 获取颜色配置
      SDL_Color text_color;
      cJSON *color_obj = cJSON_GetObjectItem(config_obj, "font_color");
      if (color_obj) {
        text_color = ParseColor(color_obj);
      }

      // 获取字体
      TTF_Font *font = GetFontCached(font_name, font_size);
      if (!font) {
        DEBUG_PRINT("draw_namebox_with_text: Failed to get font: %s (size %d)", font_name, font_size);
        continue;
      }

      // 阴影颜色（黑色）
      SDL_Color shadow_color = {0, 0, 0, 255};

      // 计算文本的度量信息，用于基线对齐
      int text_width, text_height;
      TTF_SizeUTF8(font, text, &text_width, &text_height);

      // 基线对齐：baseline_y - ascent 得到文本顶部的y坐标
      int text_top_y = baseline_y - TTF_FontAscent(font);

      // 绘制阴影文字 (2像素偏移)
      SDL_Surface *shadow_surface = TTF_RenderUTF8_Blended(font, text, shadow_color);
      if (shadow_surface) {
        SDL_Rect shadow_rect = {current_x + 2, text_top_y + 2, shadow_surface->w, shadow_surface->h};
        SDL_BlitSurface(shadow_surface, nullptr, namebox_surface, &shadow_rect);
        SDL_FreeSurface(shadow_surface);
      }

      // 绘制主文字
      SDL_Surface *text_surface = TTF_RenderUTF8_Blended(font, text, text_color);
      if (!text_surface) {
        DEBUG_PRINT("draw_namebox_with_text: Failed to render text: %s", text);
        continue;
      }

      SDL_Rect main_rect = {current_x, text_top_y, text_surface->w, text_surface->h};
      SDL_BlitSurface(text_surface, nullptr, namebox_surface, &main_rect);

      // 更新当前X位置为下一个文本
      current_x += text_width;
      DEBUG_PRINT("draw_namebox_with_text: Updated current_x = %d", current_x);

      SDL_FreeSurface(text_surface);
    }

    DEBUG_PRINT("draw_namebox_with_text: Completed successfully");
    return namebox_surface;
  }

  // 名字框组件绘制
  bool DrawNameboxComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj) {

    // 使用新的函数绘制带文字的namebox
    SDL_Surface *namebox_surface = DrawNameboxWithText(comp_obj);
    // 加载图像
    if (!namebox_surface) {
      DEBUG_PRINT("DrawNameboxComponent: Failed to draw namebox with text");
      return false;
    }

    // 使用渲染器进行高质量缩放
    float scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    SDL_Surface *final_surface = namebox_surface;

    if (scale != 1.0f) {
      int new_width = static_cast<int>(namebox_surface->w * scale);
      int new_height = static_cast<int>(namebox_surface->h * scale);

      SDL_Surface *scaled_surface = ScaleSurfaceWithRenderer(namebox_surface, new_width, new_height);
      if (scaled_surface) {
        SDL_FreeSurface(namebox_surface);
        final_surface = scaled_surface;
      }
    }

    // 使用工具函数计算位置
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));

    SDL_Rect pos = utils::CalculatePosition(align, offset_x, offset_y, target1->w, target1->h, final_surface->w, final_surface->h);
    SDL_Rect pos1 = pos;

    // 绘制到目标表面
    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, &pos);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, &pos1);

    SDL_FreeSurface(final_surface);

    return true;
  }

  // 图层组件绘制
  bool DrawGenericComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj) {
    const char *overlay = GetJsonString(comp_obj, "overlay", "");

    if (strlen(overlay) == 0)
      return true;

    SDL_Surface *comp_surface = LoadComponentImage(overlay);
    if (!comp_surface)
      return false;

    // 使用渲染器进行高质量缩放
    float scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    SDL_Surface *final_surface = comp_surface;

    if (scale != 1.0f) {
      int new_width = static_cast<int>(comp_surface->w * scale);
      int new_height = static_cast<int>(comp_surface->h * scale);

      SDL_Surface *scaled_surface = ScaleSurfaceWithRenderer(comp_surface, new_width, new_height);
      if (scaled_surface) {
        SDL_FreeSurface(comp_surface);
        final_surface = scaled_surface;
      }
    }

    // 使用工具函数计算位置
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));

    // Draw to target surfaces
    SDL_Rect pos = utils::CalculatePosition(align, offset_x, offset_y, target1->w, target1->h, final_surface->w, final_surface->h);
    SDL_Rect pos1 = pos;

    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, &pos);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, &pos1);

    SDL_FreeSurface(final_surface);
    return true;
  }
  bool DrawTextComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj) {
    const char *text = GetJsonString(comp_obj, "text", "");
    if (strlen(text) == 0) {
      DEBUG_PRINT("DrawTextComponent: Empty text");
      return true;
    }

    // 获取字体配置
    const char *font_name = GetJsonString(comp_obj, "font_family", style_config_.font_family);
    int font_size = static_cast<int>(GetJsonNumber(comp_obj, "font_size", style_config_.font_size));

    DEBUG_PRINT("DrawTextComponent: text='%s', font=%s, size=%d", text, font_name, font_size);

    // 获取颜色配置 - 支持多种格式
    SDL_Color text_color = {255, 255, 255, 255};
    cJSON *text_color_obj = cJSON_GetObjectItem(comp_obj, "text_color");
    if (text_color_obj) {
      text_color = ParseColor(text_color_obj);
    }

    SDL_Color shadow_color = {0, 0, 0, 255};
    cJSON *shadow_color_obj = cJSON_GetObjectItem(comp_obj, "shadow_color");
    if (shadow_color_obj) {
      shadow_color = ParseColor(shadow_color_obj);
    }

    int shadow_offset_x = static_cast<int>(GetJsonNumber(comp_obj, "shadow_offset_x", style_config_.shadow_offset_x));
    int shadow_offset_y = static_cast<int>(GetJsonNumber(comp_obj, "shadow_offset_y", style_config_.shadow_offset_y));

    // 获取对齐方式
    const char *align_str = GetJsonString(comp_obj, "align", "top-left");
    int offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));

    // 获取最大宽度（用于换行）
    int max_width = static_cast<int>(GetJsonNumber(comp_obj, "max_width", 0));

    // 获取字体
    TTF_Font *font = GetFontCached(font_name, font_size);
    if (!font) {
      DEBUG_PRINT("DrawTextComponent: Failed to get font: %s (size %d)", font_name, font_size);
      return false;
    }

    // 计算文本尺寸
    int text_width, text_height;
    SDL_Surface *final_text_surface = nullptr;

    // 使用TTF_MeasureUTF8来简化换行计算
    std::vector<std::pair<int, int>> lines_ranges = FastBreakTextIntoLines(font, text, max_width);

    // 计算总高度
    int line_height = TTF_FontHeight(font);
    int line_spacing = static_cast<int>(line_height * 0.15); // 15%行间距
    text_height = static_cast<int>(lines_ranges.size()) * line_height + static_cast<int>(lines_ranges.size() - 1) * line_spacing;
    text_width = max_width;

    // 创建文本表面
    final_text_surface = SDL_CreateRGBSurfaceWithFormat(0, text_width, text_height, 32, SDL_PIXELFORMAT_ABGR8888);
    if (!final_text_surface) {
      DEBUG_PRINT("DrawTextComponent: Failed to create text surface");
      return false;
    }

    // 绘制每一行
    int current_y = 0;
    for (const auto &line_range : lines_ranges) {
      int start_byte = line_range.first;
      int end_byte = line_range.second;

      if (start_byte >= end_byte) {
        current_y += line_height + line_spacing;
        continue;
      }

      // 提取行文本
      std::string line_str = std::string(text).substr(start_byte, end_byte - start_byte);

      if (line_str.empty()) {
        current_y += line_height + line_spacing;
        continue;
      }

      int line_width, single_line_height;
      TTF_SizeUTF8(font, line_str.c_str(), &line_width, &single_line_height);

      // 在最大宽度内水平对齐（默认左对齐）
      int line_x = 0;

      // 绘制阴影
      if (shadow_offset_x != 0 || shadow_offset_y != 0) {
        SDL_Surface *shadow_surface = TTF_RenderUTF8_Blended(font, line_str.c_str(), shadow_color);
        if (shadow_surface) {
          SDL_Rect shadow_rect = {line_x + shadow_offset_x, current_y + shadow_offset_y, shadow_surface->w, shadow_surface->h};
          SDL_BlitSurface(shadow_surface, nullptr, final_text_surface, &shadow_rect);
          SDL_FreeSurface(shadow_surface);
        }
      }

      // 绘制文本
      SDL_Surface *line_surface = TTF_RenderUTF8_Blended(font, line_str.c_str(), text_color);
      if (line_surface) {
        SDL_Rect line_rect = {line_x, current_y, line_surface->w, line_surface->h};
        SDL_BlitSurface(line_surface, nullptr, final_text_surface, &line_rect);
        SDL_FreeSurface(line_surface);
      }

      current_y += line_height + line_spacing;
    }

    if (!final_text_surface) {
      DEBUG_PRINT("DrawTextComponent: No text surface created");
      return false;
    }

    // 使用工具函数计算位置
    SDL_Rect pos = utils::CalculatePosition(align_str, offset_x, offset_y, target1->w, target1->h, final_text_surface->w, final_text_surface->h);
    SDL_Rect pos1 = pos;
    DEBUG_PRINT("DrawTextComponent: Drawing at position (%d, %d), size: %dx%d", pos.x, pos.y, pos.w, pos.h);

    // 绘制到目标表面
    if (target1) {
      SDL_BlitSurface(final_text_surface, nullptr, target1, &pos);
      DEBUG_PRINT("DrawTextComponent: Drawn to target1");
    }
    if (target2) {
      SDL_BlitSurface(final_text_surface, nullptr, target2, &pos1);
      DEBUG_PRINT("DrawTextComponent: Drawn to target2");
    }

    SDL_FreeSurface(final_text_surface);
    return true;
  }

  // Get font (with caching and character width caching)
  TTF_Font *GetFontCached(const char *font_name, int size) {
    if (!ttf_initialized_)
      return nullptr;

    SDL_LockMutex(cache_mutex_);

    // Search in cache
    FontCacheEntry *current = font_cache_;
    while (current) {
      if (strcmp(current->font_name, font_name) == 0 && current->size == size) {
        SDL_UnlockMutex(cache_mutex_);
        return current->font;
      }
      current = current->next;
    }

    // Build font path
    char font_path[1024];
    const char *extensions[] = {".ttf", ".otf", ".ttc", nullptr};
    TTF_Font *font = nullptr;

    for (int i = 0; extensions[i]; i++) {
      snprintf(font_path, sizeof(font_path), "%s/fonts/%s%s", assets_path_, font_name, extensions[i]);

      SDL_RWops *file = SDL_RWFromFile(font_path, "rb");
      if (file) {
        SDL_RWclose(file);
        font = TTF_OpenFont(font_path, size);
        if (font) {
          // Add to cache
          FontCacheEntry *new_entry = new FontCacheEntry();
          strncpy(new_entry->font_name, font_name, sizeof(new_entry->font_name));
          new_entry->size = size;
          new_entry->font = font;
          new_entry->next = font_cache_;
          font_cache_ = new_entry;

          SDL_UnlockMutex(cache_mutex_);
          return font;
        }
      }
    }

    SDL_UnlockMutex(cache_mutex_);
    DEBUG_PRINT("Font not found: %s", font_name);
    return nullptr;
  }

  // 绘制图片到画布
  void DrawImageToCanvas(SDL_Surface *canvas, unsigned char *image_data, int image_width, int image_height, int image_pitch, int paste_x, int paste_y, int paste_width, int paste_height) {
    StyleConfig *config = &style_config_;
    TIME_SCOPE("DrawImageToCanvas");

    SDL_Surface *img_surface = SDL_CreateRGBSurfaceWithFormatFrom(image_data, image_width, image_height, 32, image_pitch, SDL_PIXELFORMAT_ABGR8888);

    if (!img_surface) {
      DEBUG_PRINT("Failed to create image surface");
      return;
    }

    // 使用工具函数计算缩放后的尺寸
    SDL_Rect scaled_rect = utils::CalculateScaledRect(img_surface->w, img_surface->h, paste_width, paste_height, config->paste_fill_mode);

    DEBUG_PRINT("Fill mode: %s, new size: %dx%d", config->paste_fill_mode, scaled_rect.w, scaled_rect.h);

    // 调整图片大小 - 使用渲染器进行高质量缩放
    SDL_Surface *resized_surface = ScaleSurfaceWithRenderer(img_surface, scaled_rect.w, scaled_rect.h);

    if (resized_surface) {
      // 使用工具函数计算对齐位置
      int final_x, final_y;
      utils::CalculateAlignment(paste_x, paste_y, paste_width, paste_height, scaled_rect.w, scaled_rect.h, config->paste_align, config->paste_valign, final_x, final_y);

      SDL_Rect dest_rect = {final_x, final_y, scaled_rect.w, scaled_rect.h};
      DEBUG_PRINT("Drawing image to canvas at (%d, %d) with size %dx%d", dest_rect.x, dest_rect.y, dest_rect.w, dest_rect.h);

      SDL_BlitSurface(resized_surface, nullptr, canvas, &dest_rect);
      SDL_FreeSurface(resized_surface);
    } else {
      DEBUG_PRINT("Failed to create resized surface");
    }

    SDL_FreeSurface(img_surface);
    DEBUG_PRINT("Image drawing completed");
  }

  // Cache management functions
  void ClearPreviewCache() {
    SDL_LockMutex(cache_mutex_);
    preview_cache_.reset();
    SDL_UnlockMutex(cache_mutex_);
  }

  void ClearStaticLayerCache() {
    SDL_LockMutex(cache_mutex_);
    if (static_layer_cache_first_) {
      delete static_layer_cache_first_;
      static_layer_cache_first_ = nullptr;
      static_layer_cache_current_ = nullptr;
      static_layer_cache_count_ = 0;
    }
    SDL_UnlockMutex(cache_mutex_);
  }

  void AddStaticLayerToCache(SDL_Surface *layer_surface) {
    if (!layer_surface)
      return;

    SDL_LockMutex(cache_mutex_);

    StaticLayerNode *new_node = new StaticLayerNode();
    new_node->layer_surface = layer_surface;
    new_node->next = nullptr;

    if (!static_layer_cache_first_) {
      static_layer_cache_first_ = new_node;
      static_layer_cache_current_ = new_node;
    } else {
      // Find the last node
      StaticLayerNode *last = static_layer_cache_first_;
      while (last->next) {
        last = last->next;
      }
      last->next = new_node;
    }

    static_layer_cache_count_++;

    SDL_UnlockMutex(cache_mutex_);

    DEBUG_PRINT("Added layer to cache, current count: %d", static_layer_cache_count_);
  }

  SDL_Surface *GetNextCachedLayer() {
    SDL_LockMutex(cache_mutex_);

    if (!static_layer_cache_current_) {
      SDL_UnlockMutex(cache_mutex_);
      return nullptr;
    }

    SDL_Surface *layer = static_layer_cache_current_->layer_surface;
    static_layer_cache_current_ = static_layer_cache_current_->next;

    SDL_UnlockMutex(cache_mutex_);

    DEBUG_PRINT("Retrieved cached layer");
    return layer;
  }

  void ResetStaticLayerCachePointer() {
    SDL_LockMutex(cache_mutex_);
    static_layer_cache_current_ = static_layer_cache_first_;
    SDL_UnlockMutex(cache_mutex_);
  }

  // JSON helper functions
  static const char *GetJsonString(cJSON *obj, const char *key, const char *default_val) {
    cJSON *item = cJSON_GetObjectItem(obj, key);
    if (item && cJSON_IsString(item)) {
      return item->valuestring;
    }
    return default_val;
  }

  static double GetJsonNumber(cJSON *obj, const char *key, double default_val) {
    cJSON *item = cJSON_GetObjectItem(obj, key);
    if (item && cJSON_IsNumber(item)) {
      return item->valuedouble;
    }
    return default_val;
  }

  static bool GetJsonBool(cJSON *obj, const char *key, bool default_val) {
    cJSON *item = cJSON_GetObjectItem(obj, key);
    if (item) {
      if (cJSON_IsBool(item)) {
        return cJSON_IsTrue(item);
      } else if (cJSON_IsNumber(item)) {
        return item->valueint != 0;
      }
    }
    return default_val;
  }

private:
  // Global configuration
  char assets_path_[1024] = {0};
  float min_image_ratio_ = 0.2f;

  // SDL state
  bool sdl_initialized_ = false;
  bool img_initialized_ = false;
  bool ttf_initialized_ = false;

  // Renderer state
  SDL_Window *renderer_window_ = nullptr;
  SDL_Renderer *renderer_ = nullptr;
  bool renderer_initialized_ = false;

  // 压缩设置
  bool compression_enabled_ = false;
  int compression_ratio_ = 40; // 默认40%

  // Caches (only fonts, static layers, and preview)
  FontCacheEntry *font_cache_ = nullptr;
  std::unique_ptr<ImageData> preview_cache_;

  StaticLayerNode *static_layer_cache_first_ = nullptr;
  StaticLayerNode *static_layer_cache_current_ = nullptr;
  int static_layer_cache_count_ = 0;

  SDL_mutex *cache_mutex_ = nullptr;

  std::mutex mutex_;

  // 文件路径缓存
  FilePathCache file_path_cache_;

  // 加载emoji图片
  SDL_Surface *LoadEmojiImage(const std::string &emoji_text, int target_size);
  //   void DrawImageToCanvasWithRegion(SDL_Surface *canvas, unsigned char *image_data, int image_width, int image_height, int image_pitch, int region_x, int region_y, int region_width, int region_height);
  // 将emoji字符串转换为文件名
  std::string EmojiToFileName(const std::string &emoji_text);
};

// 实现EmojiToFileName函数
std::string ImageLoaderManager::EmojiToFileName(const std::string &emoji_text) {
  std::string filename = "emoji_u";

  // 将emoji字符串中的每个码点转换为十六进制
  const char *str = emoji_text.c_str();
  int i = 0;
  while (str[i]) {
    unsigned char c = static_cast<unsigned char>(str[i]);

    // 计算UTF-8字符的码点
    Uint32 codepoint = 0;
    int char_len = 0;

    if (c < 0x80) {
      codepoint = c;
      char_len = 1;
    } else if ((c & 0xE0) == 0xC0) {
      if (str[i + 1]) {
        codepoint = ((c & 0x1F) << 6) | (str[i + 1] & 0x3F);
        char_len = 2;
      }
    } else if ((c & 0xF0) == 0xE0) {
      if (str[i + 1] && str[i + 2]) {
        codepoint = ((c & 0x0F) << 12) | ((str[i + 1] & 0x3F) << 6) | (str[i + 2] & 0x3F);
        char_len = 3;
      }
    } else if ((c & 0xF8) == 0xF0) {
      if (str[i + 1] && str[i + 2] && str[i + 3]) {
        codepoint = ((c & 0x07) << 18) | ((str[i + 1] & 0x3F) << 12) | ((str[i + 2] & 0x3F) << 6) | (str[i + 3] & 0x3F);
        char_len = 4;
      }
    }

    if (codepoint > 0) {
      // 将码点转换为小写十六进制
      char hex[16];
      snprintf(hex, sizeof(hex), "%04x", codepoint);
      if (i > 0)
        filename += "_";
      filename += hex;
    }

    if (char_len > 0) {
      i += char_len;
    } else {
      i++;
    }
  }

  filename += ".png";
  return filename;
}

// 实现LoadEmojiImage函数
SDL_Surface *ImageLoaderManager::LoadEmojiImage(const std::string &emoji_text, int target_size) {
  DEBUG_PRINT("Loading emoji image for: '%s'", emoji_text.c_str());

  std::string filename = EmojiToFileName(emoji_text);
  DEBUG_PRINT("Emoji filename: %s", filename.c_str());

  // 构建完整路径
  char file_path[1024];
  snprintf(file_path, sizeof(file_path), "%s/emoji/%s", assets_path_, filename.c_str());

  DEBUG_PRINT("Emoji file path: %s", file_path);

  // 使用文件路径缓存
  std::string found_path;
  static const std::vector<std::string> extensions = {".png", ".webp", ".jpg", ".jpeg"};

  // 先尝试直接路径
  SDL_Surface *emoji_surface = IMG_Load(file_path);

  if (!emoji_surface) {
    // 如果没有找到，尝试所有扩展名
    std::string base_name = file_path;
    size_t dot_pos = base_name.rfind('.');
    if (dot_pos != std::string::npos) {
      base_name = base_name.substr(0, dot_pos);
    }

    if (!FindFileWithExtensions(base_name.c_str(), extensions, found_path)) {
      DEBUG_PRINT("Failed to load emoji image: %s", IMG_GetError());

      // 尝试加载不带修饰符的基础版本（如果有修饰符）
      // 例如，emoji_u1f596_1f3fd.png -> emoji_u1f596.png
      size_t last_underscore = filename.rfind('_');
      if (last_underscore != std::string::npos) {
        std::string base_filename = filename.substr(0, last_underscore) + ".png";
        snprintf(file_path, sizeof(file_path), "%s/emoji/%s", assets_path_, base_filename.c_str());
        DEBUG_PRINT("Trying fallback emoji file: %s", file_path);
        emoji_surface = IMG_Load(file_path);
      }

      if (!emoji_surface) {
        DEBUG_PRINT("Fallback emoji image also failed to load");
        return nullptr;
      }
    } else {
      emoji_surface = IMG_Load(found_path.c_str());
    }
  }

  if (!emoji_surface) {
    return nullptr;
  }

  // 转换为RGBA格式
  SDL_Surface *rgba_surface = SDL_ConvertSurfaceFormat(emoji_surface, SDL_PIXELFORMAT_ABGR8888, 0);
  SDL_FreeSurface(emoji_surface);

  if (!rgba_surface) {
    DEBUG_PRINT("Failed to convert emoji surface to RGBA");
    return nullptr;
  }

  DEBUG_PRINT("Emoji image loaded: %dx%d", rgba_surface->w, rgba_surface->h);

  // 如果需要缩放，调整大小到目标尺寸
  if (target_size > 0 && (rgba_surface->w != target_size || rgba_surface->h != target_size)) {
    // 使用渲染器进行高质量缩放
    SDL_Surface *scaled_surface = ScaleSurfaceWithRenderer(rgba_surface, target_size, target_size);
    if (scaled_surface) {
      SDL_FreeSurface(rgba_surface);
      rgba_surface = scaled_surface;
      DEBUG_PRINT("Emoji scaled to: %dx%d", rgba_surface->w, rgba_surface->h);
    }
  }

  return rgba_surface;
}

void ImageLoaderManager::DrawTextAndEmojiToCanvas(SDL_Surface *canvas, const std::string &text, const std::vector<std::string> &emoji_list, const std::vector<std::pair<int, int>> &emoji_positions, int text_x, int text_y, int text_width, int text_height) {
  TIME_SCOPE("=== Starting DrawTextAndEmojiToCanvas ===");

  StyleConfig *config = &style_config_;
  DEBUG_PRINT("Text area: %dx%d at (%d,%d)", text_width, text_height, text_x, text_y);
  DEBUG_PRINT("Original text length: %zu bytes", text.length());
  DEBUG_PRINT("Original text: '%s'", text.c_str());

  // 1. 准备颜色
  SDL_Color text_color = {config->text_color[0], config->text_color[1], config->text_color[2], 255};
  SDL_Color bracket_color = {config->bracket_color[0], config->bracket_color[1], config->bracket_color[2], 255};
  SDL_Color shadow_color = {config->shadow_color[0], config->shadow_color[1], config->shadow_color[2], 255};

  DEBUG_PRINT("Text color: RGB(%d,%d,%d)", text_color.r, text_color.g, text_color.b);
  DEBUG_PRINT("Bracket color: RGB(%d,%d,%d)", bracket_color.r, bracket_color.g, bracket_color.b);

  // 2. 首先查找所有括号段
  std::vector<std::tuple<int, int, SDL_Color>> bracket_segments;
  FindBracketPairsInText(text, bracket_segments, bracket_color);

  DEBUG_PRINT("Found %zu bracket segments", bracket_segments.size());
  for (size_t i = 0; i < bracket_segments.size(); i++) {
    int start = std::get<0>(bracket_segments[i]);
    int end = std::get<1>(bracket_segments[i]);
    DEBUG_PRINT("Bracket segment %zu: [%d, %d) - '%s'", i, start, end, text.substr(start, end - start).c_str());
  }

  // 3. 创建分段列表，emoji优先级高于括号
  std::vector<std::tuple<int, int, SDL_Color, bool>> all_segments; // start, end, color, is_emoji

  // 先添加括号段（标记为普通文本段，但使用括号颜色）
  for (const auto &seg : bracket_segments) {
    int start = std::get<0>(seg);
    int end = std::get<1>(seg);
    SDL_Color color = std::get<2>(seg);

    // 将括号段拆分为多个子段，排除emoji部分
    int current_pos = start;

    // 检查这个括号段内是否有emoji
    for (const auto &emoji_pos : emoji_positions) {
      int emoji_start = emoji_pos.first;
      int emoji_end = emoji_pos.second;

      // 如果emoji在这个括号段内
      if (emoji_start >= start && emoji_end <= end) {
        // 添加emoji之前的括号部分
        if (emoji_start > current_pos) {
          all_segments.emplace_back(current_pos, emoji_start, color, false);
          DEBUG_PRINT("Bracket subsegment before emoji: [%d, %d)", current_pos, emoji_start);
        }
        current_pos = emoji_end;
      }
    }

    // 添加剩余部分
    if (current_pos < end) {
      all_segments.emplace_back(current_pos, end, color, false);
      DEBUG_PRINT("Bracket subsegment after emoji: [%d, %d)", current_pos, end);
    }
  }

  // 4. 添加emoji段（使用文本颜色）
  for (size_t i = 0; i < emoji_positions.size(); i++) {
    int start = emoji_positions[i].first;
    int end = emoji_positions[i].second;

    if (start >= 0 && end <= static_cast<int>(text.length()) && start < end) {
      all_segments.emplace_back(start, end, text_color, true);
      DEBUG_PRINT("Emoji segment added: [%d, %d) - '%s'", start, end, text.substr(start, end - start).c_str());
    }
  }

  // 5. 按起始位置排序所有段
  std::sort(all_segments.begin(), all_segments.end(), [](const auto &a, const auto &b) { return std::get<0>(a) < std::get<0>(b); });

  // 6. 填充普通文本段
  std::vector<std::tuple<int, int, SDL_Color, bool>> final_segments;
  int current_pos = 0;

  for (const auto &seg : all_segments) {
    int seg_start = std::get<0>(seg);
    int seg_end = std::get<1>(seg);

    // 添加seg_start之前的普通文本段
    if (seg_start > current_pos) {
      final_segments.emplace_back(current_pos, seg_start, text_color, false);
      DEBUG_PRINT("Normal text segment added: [%d, %d)", current_pos, seg_start);
    }

    // 添加当前段
    final_segments.push_back(seg);

    current_pos = seg_end;
  }

  // 添加最后的普通文本段
  if (current_pos < static_cast<int>(text.length())) {
    final_segments.emplace_back(current_pos, static_cast<int>(text.length()), text_color, false);
    DEBUG_PRINT("Final normal text segment added: [%d, %d)", current_pos, static_cast<int>(text.length()));
  }

  all_segments = std::move(final_segments);

  DEBUG_PRINT("Total segments after processing: %zu", all_segments.size());

#ifdef _DEBUG
  // 调试：打印所有段
  for (size_t i = 0; i < all_segments.size(); i++) {
    const auto &seg = all_segments[i];
    int start = std::get<0>(seg);
    int end = std::get<1>(seg);
    SDL_Color color = std::get<2>(seg);
    bool is_emoji = std::get<3>(seg);

    if (start < end && start < static_cast<int>(text.length())) {
      std::string seg_text = text.substr(start, end - start);
      bool is_bracket_color = (color.r == bracket_color.r && color.g == bracket_color.g && color.b == bracket_color.b);
      DEBUG_PRINT("Segment %zu: [%d, %d) type=%s color=%s text='%s'", i, start, end, is_emoji ? "emoji" : "text", is_bracket_color ? "bracket" : "text", seg_text.c_str());
    }
  }
#endif

  // 7. 测量文本（使用特殊字符占位emoji）
  std::string measure_text = text;

  // 8. 查找最佳字体大小
  int best_font_size = config->font_size;
  TTF_Font *best_font = nullptr;
  std::vector<std::pair<int, int>> best_lines;

  int min_size = 12;
  int max_size = config->font_size;

  DEBUG_PRINT("Testing font sizes from %d to %d", min_size, max_size);

  {
    TIME_SCOPE("=== Finding Best Font Size ===");

    while (min_size <= max_size) {
      int mid_size = (min_size + max_size) / 2;
      TTF_Font *test_font = GetFontCached(config->font_family, mid_size);

      if (!test_font) {
        DEBUG_PRINT("Font size %d not available", mid_size);
        max_size = mid_size - 1;
        continue;
      }

      auto lines = FastBreakTextIntoLines(test_font, measure_text, text_width);

      int line_height = TTF_FontHeight(test_font);
      int estimated_height = static_cast<int>(lines.size() * line_height);

      DEBUG_PRINT("Font size %d: %zu lines, estimated height %d (max %d)", mid_size, lines.size(), estimated_height, text_height);

      if (estimated_height <= text_height) {
        best_font_size = mid_size;
        best_font = test_font;
        best_lines = lines;
        min_size = mid_size + 1;
        DEBUG_PRINT("Font size %d fits", mid_size);
      } else {
        max_size = mid_size - 1;
        DEBUG_PRINT("Font size %d too large", mid_size);
      }
    }

    if (!best_font) {
      DEBUG_PRINT("No fitting font found, using fallback size 12");
      best_font = GetFontCached(config->font_family, 12);
      if (!best_font) {
        DEBUG_PRINT("ERROR: Failed to get font");
        return;
      }
      best_lines = FastBreakTextIntoLines(best_font, measure_text, text_width);
    }
  }

  DEBUG_PRINT("Selected font size: %d", best_font_size);
  DEBUG_PRINT("Text wrapped into %zu lines", best_lines.size());

  // 9. 将分段分配到各行
  int line_height = TTF_FontHeight(best_font);
  int emoji_size = static_cast<int>(line_height * 0.9);

  // 为每一行分配分段
  std::vector<std::vector<std::tuple<int, int, SDL_Color, bool>>> lines_segments;
  size_t seg_index = 0;

  {
    TIME_SCOPE("9. Distributing Segments to Lines");

    for (const auto &line_range : best_lines) {
      std::vector<std::tuple<int, int, SDL_Color, bool>> line_segs;
      int line_start = line_range.first;
      int line_end = line_range.second;

      DEBUG_PRINT("Processing line %zu: range [%d, %d)", lines_segments.size(), line_start, line_end);

      // 查找属于这一行的分段
      while (seg_index < all_segments.size()) {
        int seg_start = std::get<0>(all_segments[seg_index]);
        int seg_end = std::get<1>(all_segments[seg_index]);

        // 如果段在当前行之前，跳过
        if (seg_end <= line_start) {
          seg_index++;
          continue;
        }

        // 如果段在当前行之后，结束当前行
        if (seg_start >= line_end) {
          break;
        }

        // 计算段与行的重叠部分
        int overlap_start = std::max(seg_start, line_start);
        int overlap_end = std::min(seg_end, line_end);

        if (overlap_start < overlap_end) {
          // 添加重叠部分到当前行
          SDL_Color seg_color = std::get<2>(all_segments[seg_index]);
          bool is_emoji = std::get<3>(all_segments[seg_index]);
          line_segs.emplace_back(overlap_start, overlap_end, seg_color, is_emoji);

          std::string seg_text = text.substr(overlap_start, overlap_end - overlap_start);
          DEBUG_PRINT("  Added segment [%d, %d) to line, type: %s, text: '%s'", overlap_start, overlap_end, is_emoji ? "emoji" : "text", seg_text.c_str());
        }

        // 如果段在当前行内结束，移动到下一个段
        if (seg_end <= line_end) {
          seg_index++;
        } else {
          // 段跨越到下一行，调整段的起始位置为当前行结束位置
          std::get<0>(all_segments[seg_index]) = line_end;
          break;
        }
      }

      if (!line_segs.empty()) {
        lines_segments.push_back(line_segs);
      }
    }

    DEBUG_PRINT("Distributed segments into %zu lines", lines_segments.size());
  }

  // 10. 绘制文本
  bool has_shadow = (config->shadow_offset_x != 0 || config->shadow_offset_y != 0);

  // 计算垂直起始位置
  int total_height = static_cast<int>(lines_segments.size() * line_height);
  int current_y = text_y;

  if (strcmp(config->text_valign, "middle") == 0) {
    current_y += (text_height - total_height) / 2;
  } else if (strcmp(config->text_valign, "bottom") == 0) {
    current_y += text_height - total_height;
  }

  DEBUG_PRINT("Vertical alignment: %s, start Y: %d, total height: %d", config->text_valign, current_y, total_height);

  // 绘制每一行
  for (size_t line_idx = 0; line_idx < lines_segments.size(); line_idx++) {
    const auto &line_segs = lines_segments[line_idx];
    if (line_segs.empty())
      continue;

    // 计算行宽
    int line_width = 0;
    for (const auto &seg : line_segs) {
      int seg_start = std::get<0>(seg);
      int seg_end = std::get<1>(seg);
      bool is_emoji = std::get<3>(seg);

      if (is_emoji) {
        line_width += emoji_size;
      } else {
        std::string seg_text = text.substr(seg_start, seg_end - seg_start);
        int seg_width = 0;
        TTF_SizeUTF8(best_font, seg_text.c_str(), &seg_width, nullptr);
        line_width += seg_width;
      }
    }

    // 计算水平起始位置
    int current_x = text_x;
    if (strcmp(config->text_align, "center") == 0) {
      current_x += (text_width - line_width) / 2;
    } else if (strcmp(config->text_align, "right") == 0) {
      current_x += text_width - line_width;
    }

    DEBUG_PRINT("Line %zu: width %d, start X: %d (alignment: %s)", line_idx, line_width, current_x, config->text_align);

    // 绘制当前行的所有分段
    for (const auto &seg : line_segs) {
      int seg_start = std::get<0>(seg);
      int seg_end = std::get<1>(seg);
      SDL_Color seg_color = std::get<2>(seg);
      bool is_emoji = std::get<3>(seg);

      if (is_emoji) {
        // 绘制emoji
        std::string emoji_text = text.substr(seg_start, seg_end - seg_start);
        DEBUG_PRINT("  Drawing emoji: '%s' at (%d, %d) with size %d", emoji_text.c_str(), current_x, current_y, emoji_size);

        SDL_Surface *emoji_surface = LoadEmojiImage(emoji_text, emoji_size);
        if (emoji_surface) {
          int emoji_y = current_y + (line_height - emoji_size) / 2;
          SDL_Rect emoji_rect = {current_x, emoji_y, emoji_surface->w, emoji_surface->h};
          SDL_BlitSurface(emoji_surface, nullptr, canvas, &emoji_rect);
          current_x += emoji_surface->w;
          SDL_FreeSurface(emoji_surface);
        } else {
          // emoji加载失败，绘制占位符
          DEBUG_PRINT("  Failed to load emoji, drawing placeholder");
          int emoji_y = current_y + (line_height - emoji_size) / 2;
          SDL_Rect placeholder_rect = {current_x, emoji_y, emoji_size, emoji_size};
          SDL_FillRect(canvas, &placeholder_rect, SDL_MapRGBA(canvas->format, 128, 128, 128, 255));
          current_x += emoji_size;
        }
      } else {
        // 绘制文本
        std::string seg_text = text.substr(seg_start, seg_end - seg_start);
        if (seg_text.empty())
          continue;

        DEBUG_PRINT("  Drawing text: '%s' (color: RGB(%d,%d,%d)) at (%d, %d)", seg_text.c_str(), seg_color.r, seg_color.g, seg_color.b, current_x, current_y);

        // 绘制阴影
        if (has_shadow) {
          SDL_Surface *shadow_surface = TTF_RenderUTF8_Blended(best_font, seg_text.c_str(), shadow_color);
          if (shadow_surface) {
            SDL_Rect shadow_rect = {current_x + config->shadow_offset_x, current_y + config->shadow_offset_y, shadow_surface->w, shadow_surface->h};
            SDL_BlitSurface(shadow_surface, nullptr, canvas, &shadow_rect);
            SDL_FreeSurface(shadow_surface);
          }
        }

        // 绘制文本
        SDL_Surface *text_surface = TTF_RenderUTF8_Blended(best_font, seg_text.c_str(), seg_color);
        if (text_surface) {
          SDL_Rect text_rect = {current_x, current_y, text_surface->w, text_surface->h};
          SDL_BlitSurface(text_surface, nullptr, canvas, &text_rect);
          current_x += text_surface->w;
          SDL_FreeSurface(text_surface);
        }
      }
    }

    current_y += line_height;
  }

  DEBUG_PRINT("Text drawing completed");
}

} // namespace image_loader

// C interface export functions
extern "C" {

__declspec(dllexport) void set_global_config(const char *assets_path, float min_image_ratio) { image_loader::ImageLoaderManager::GetInstance().SetGlobalConfig(assets_path, min_image_ratio); }

__declspec(dllexport) void update_gui_settings(const char *settings_json) { image_loader::ImageLoaderManager::GetInstance().UpdateGuiSettings(settings_json); }

__declspec(dllexport) void update_style_config(const char *style_json) { image_loader::ImageLoaderManager::GetInstance().UpdateStyleConfig(style_json); }

__declspec(dllexport) void clear_cache(const char *cache_type) { image_loader::ImageLoaderManager::GetInstance().ClearCache(cache_type); }

__declspec(dllexport) int generate_complete_image(const char *assets_path, int canvas_width, int canvas_height, const char *components_json, const char *character_name, int emotion_index, int background_index, unsigned char **out_data, int *out_width,
                                                  int *out_height) {

  return static_cast<int>(image_loader::ImageLoaderManager::GetInstance().GeneratePreviewImage(assets_path, canvas_width, canvas_height, components_json, character_name, emotion_index, background_index, out_data, out_width, out_height));
}

__declspec(dllexport) int draw_content_simple(const char *text, const char *emoji_json, unsigned char *image_data, int image_width, int image_height, int image_pitch, unsigned char **out_data, int *out_width, int *out_height) {
  return static_cast<int>(image_loader::ImageLoaderManager::GetInstance().DrawContentWithTextAndImage(text, emoji_json, image_data, image_width, image_height, image_pitch, out_data, out_width, out_height));
}

__declspec(dllexport) void free_image_data(unsigned char *data) {
  if (data) {
    free(data);
  }
}

__declspec(dllexport) void cleanup_all() { image_loader::ImageLoaderManager::GetInstance().Cleanup(); }

__declspec(dllexport) void cleanup_renderer() { image_loader::ImageLoaderManager::GetInstance().CleanupRenderer(); }

} // extern "C"