// image_loader.cpp - 完整修改版本

#include <algorithm>
#include <cstring>
#include <deque>
#include <map>
#include <memory>
#include <mutex>
#include <stack>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif

#include <SDL.h>
#include <SDL_image.h>
#include <SDL_ttf.h>
#include <cJSON.h>

// Debug print
//#define _DEBUG
#ifdef _DEBUG
#define DEBUG_PRINT(fmt, ...) printf("[DEBUG] " fmt "\n", ##__VA_ARGS__)
#else
#define DEBUG_PRINT(fmt, ...)
#endif

// 创建UTF-8字符串版本的括号对映射
const std::unordered_map<std::string, std::string> lt_bracket_pairs = {{"\"", "\""}, {"[", "]"}, {"<", ">"}, {"【", "】"}, {"〔", "〕"}, {"「", "」"}, {"『", "』"}, {"〖", "〗"}, {"《", "》"}, {"〈", "〉"}, {"“", "”"}};

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
  void SetGlobalConfig(const char *assets_path, bool preload_character, bool preload_background, int pre_resize, float min_image_ratio) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (assets_path) {
      strncpy(assets_path_, assets_path, sizeof(assets_path_) - 1);
      assets_path_[sizeof(assets_path_) - 1] = '\0';
    }
    preload_character_ = preload_character;
    preload_background_ = preload_background;
    pre_resize_ = pre_resize;
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

    cJSON *preloading = cJSON_GetObjectItem(json_root, "preloading");
    if (preloading) {
      cJSON *preload_char = cJSON_GetObjectItem(preloading, "preload_character");
      if (preload_char) {
        preload_character_ = cJSON_IsTrue(preload_char);
      }

      cJSON *preload_bg = cJSON_GetObjectItem(preloading, "preload_background");
      if (preload_bg) {
        preload_background_ = cJSON_IsTrue(preload_bg);
      }
    }

    cJSON *pre_resize = cJSON_GetObjectItem(json_root, "pre_resize");
    if (pre_resize && cJSON_IsNumber(pre_resize)) {
      pre_resize_ = pre_resize->valueint;
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

    if (strcmp(cache_type, "all") == 0) {
      ClearStaticLayerCache();
      ClearPreviewCache();
      ClearFontCache();
      DEBUG_PRINT("All caches cleared");
    } else if (strcmp(cache_type, "layers") == 0) {
      ClearStaticLayerCache();
      DEBUG_PRINT("Static layer cache cleared");
    } else if (strcmp(cache_type, "preview") == 0) {
      ClearPreviewCache();
      DEBUG_PRINT("Preview cache cleared");
    } else if (strcmp(cache_type, "fonts") == 0) {
      ClearFontCache();
      DEBUG_PRINT("Font cache cleared");
    }
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

    return true;
  }

  // Generate complete image
  LoadResult GenerateCompleteImage(const char *assets_path, int canvas_width, int canvas_height, const char *components_json, const char *character_name, int emotion_index, int background_index, unsigned char **out_data, int *out_width, int *out_height) {

    DEBUG_PRINT("Starting to generate complete image");

    if (!InitSDL()) {
      return LoadResult::SDL_INIT_FAILED;
    }

    // Parse JSON
    cJSON *json_root = cJSON_Parse(components_json);
    if (!json_root) {
      DEBUG_PRINT("JSON parse error");
      return LoadResult::JSON_PARSE_ERROR;
    }

    if (!cJSON_IsArray(json_root)) {
      DEBUG_PRINT("JSON root is not an array");
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
    SDL_FillRect(canvas, nullptr, SDL_MapRGBA(canvas->format, 0, 0, 0, 0));

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

      const char *type = GetJsonString(comp_obj, "type", "");

      // 需要缓存图层
      if (!has_cache_mark) {
        // Determine component type
        bool use_fixed_character = GetJsonBool(comp_obj, "use_fixed_character", false);
        bool use_fixed_background = GetJsonBool(comp_obj, "use_fixed_background", false);

        // Determine if component is static
        bool is_static = false;
        if (strcmp(type, "textbox") == 0 || strcmp(type, "extra") == 0 || strcmp(type, "namebox") == 0) {
          is_static = true;
        } else if (strcmp(type, "character") == 0 && use_fixed_character) {
          is_static = true;
        } else if (strcmp(type, "background") == 0 && use_fixed_background) {
          is_static = true;
        }

        if (is_static) {
          // If it's a static component and no current static segment, create one
          if (!current_static_segment) {
            current_static_segment = SDL_CreateRGBSurfaceWithFormat(0, canvas_width, canvas_height, 32, SDL_PIXELFORMAT_ABGR8888);
            if (current_static_segment) {
              SDL_FillRect(current_static_segment, nullptr, SDL_MapRGBA(current_static_segment->format, 0, 0, 0, 0));
              DEBUG_PRINT("Starting new static layer segment");
            }
          }
        } else if (current_static_segment) {
          // Encounter dynamic component, save current static segment
          AddStaticLayerToCache(current_static_segment);
          current_static_segment = nullptr;
          DEBUG_PRINT("Saving static layer segment");
        }
      }

      // Get draw targets
      SDL_Surface *draw_target1 = canvas; // Always draw to canvas
      SDL_Surface *draw_target2 = (!has_cache_mark && current_static_segment) ? current_static_segment : nullptr;

      // Draw component based on type
      bool draw_success = false;
      if (strcmp(type, "background") == 0) {
        draw_success = DrawBackgroundComponent(draw_target1, draw_target2, comp_obj, background_index);
      } else if (strcmp(type, "character") == 0) {
        draw_success = DrawCharacterComponent(draw_target1, draw_target2, comp_obj, character_name, emotion_index);
      } else if (strcmp(type, "namebox") == 0) {
        draw_success = DrawNameboxComponent(draw_target1, draw_target2, comp_obj);
      } else {
        draw_success = DrawGenericComponent(draw_target1, draw_target2, comp_obj);
      }

      if (!draw_success) {
        DEBUG_PRINT("Failed to draw component: %s", type);
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
    DEBUG_PRINT("Starting DrawContentWithTextAndImage");

    if (!text || !out_data || !out_width || !out_height) {
      DEBUG_PRINT("Invalid parameters");
      return LoadResult::FAILED;
    }

    DEBUG_PRINT("Input text length: %d", strlen(text));

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

    // 获取画布尺寸
    SDL_LockMutex(cache_mutex_);
    int canvas_width = preview_cache_->width;
    int canvas_height = preview_cache_->height;
    SDL_UnlockMutex(cache_mutex_);

    DEBUG_PRINT("Canvas size: %dx%d", canvas_width, canvas_height);

    // 创建新的画布
    SDL_Surface *canvas = SDL_CreateRGBSurfaceWithFormat(0, canvas_width, canvas_height, 32, SDL_PIXELFORMAT_ABGR8888);
    if (!canvas) {
      DEBUG_PRINT("Failed to create canvas: %s", SDL_GetError());
      return LoadResult::FAILED;
    }

    // 先绘制缓存预览作为背景
    SDL_LockMutex(cache_mutex_);
    SDL_Surface *preview_surface = SDL_CreateRGBSurfaceWithFormatFrom(preview_cache_->data, preview_cache_->width, preview_cache_->height, 32, preview_cache_->pitch, SDL_PIXELFORMAT_ABGR8888);
    SDL_UnlockMutex(cache_mutex_);

    if (preview_surface) {
      SDL_BlitSurface(preview_surface, nullptr, canvas, nullptr);
      SDL_FreeSurface(preview_surface);
      DEBUG_PRINT("Background preview drawn");
    }

    // 解析emoji数据（现在包含位置信息）
    std::vector<std::string> emoji_list;
    std::vector<std::pair<int, int>> emoji_positions;

    if (emoji_json && emoji_json[0] != '\0') {
      DEBUG_PRINT("Parsing emoji JSON: %s", emoji_json);
      cJSON *json_root = cJSON_Parse(emoji_json);
      if (json_root) {
        // 解析emoji列表
        cJSON *emojis_array = cJSON_GetObjectItem(json_root, "emojis");
        if (emojis_array && cJSON_IsArray(emojis_array)) {
          int array_size = cJSON_GetArraySize(emojis_array);
          DEBUG_PRINT("Found %d emojis in list", array_size);
          for (int i = 0; i < array_size; i++) {
            cJSON *item = cJSON_GetArrayItem(emojis_array, i);
            if (item && cJSON_IsString(item)) {
              emoji_list.push_back(item->valuestring);
              DEBUG_PRINT("Emoji %d: %s", i, item->valuestring);
            }
          }
        } else {
          DEBUG_PRINT("No emojis array found in JSON");
        }

        // 解析位置列表
        cJSON *positions_array = cJSON_GetObjectItem(json_root, "positions");
        if (positions_array && cJSON_IsArray(positions_array)) {
          int array_size = cJSON_GetArraySize(positions_array);
          DEBUG_PRINT("Found %d emoji positions", array_size);
          for (int i = 0; i < array_size; i++) {
            cJSON *item = cJSON_GetArrayItem(positions_array, i);
            if (item && cJSON_IsArray(item)) {
              cJSON *start_item = cJSON_GetArrayItem(item, 0);
              cJSON *end_item = cJSON_GetArrayItem(item, 1);
              if (start_item && end_item && cJSON_IsNumber(start_item) && cJSON_IsNumber(end_item)) {
                emoji_positions.push_back(std::make_pair(start_item->valueint, end_item->valueint));
                DEBUG_PRINT("Emoji position %d: start=%d, end=%d", i, start_item->valueint, end_item->valueint);
              }
            }
          }
        } else {
          DEBUG_PRINT("No positions array found in JSON");
        }
        cJSON_Delete(json_root);
      } else {
        DEBUG_PRINT("Failed to parse emoji JSON");
      }
    } else {
      DEBUG_PRINT("No emoji JSON provided");
    }

    DEBUG_PRINT("Emoji list size: %zu, positions size: %zu", emoji_list.size(), emoji_positions.size());

    // 绘制图片（如果有）
    if (image_data && image_width > 0 && image_height > 0) {
      DEBUG_PRINT("Drawing image: %dx%d", image_width, image_height);
      DrawImageToCanvasSimple(canvas, image_data, image_width, image_height, image_pitch);
    } else {
      DEBUG_PRINT("No image data provided");
    }

    // 绘制文本（如果有）- 使用新的函数，传入emoji位置信息
    if (strlen(text) > 0) {
      DEBUG_PRINT("Drawing text: '%s'", text);
      DrawTextToCanvasWithEmojiAndPositions(canvas, std::string(text), emoji_list, emoji_positions);
    } else {
      DEBUG_PRINT("No text to draw");
    }

    // 返回图像数据
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

  // 文本片段数据结构
  struct TextFragmentData {
    std::string text;
    SDL_Color color;
    bool is_emoji;

    TextFragmentData(const std::string &t, const SDL_Color &c, bool emoji = false) : text(t), color(c), is_emoji(emoji) {}
  };
  // 新增：使用emoji位置信息的文本绘制函数
  void DrawTextToCanvasWithEmojiAndPositions(SDL_Surface *canvas, const std::string &text, const std::vector<std::string> &emoji_list, const std::vector<std::pair<int, int>> &emoji_positions);

  // 新增：使用emoji位置信息解析文本
  void ParseTextWithBracketsAndEmojiPositions(const std::string &text, const std::vector<std::string> &emoji_list, const std::vector<std::pair<int, int>> &emoji_positions, const SDL_Color &text_color, const SDL_Color &bracket_color,
                                              std::vector<TextFragmentData> &fragments);

  // 新增：辅助函数：解析文本中的括号
  void ParseBracketsInText(const std::string &text, const SDL_Color &text_color, const SDL_Color &bracket_color, std::vector<TextFragmentData> &fragments);

  // 解析RGB颜色
  SDL_Color ParseColor(cJSON *color_array) {
    SDL_Color color = {255, 255, 255, 255};
    if (color_array && cJSON_IsArray(color_array)) {
      cJSON *r = cJSON_GetArrayItem(color_array, 0);
      cJSON *g = cJSON_GetArrayItem(color_array, 1);
      cJSON *b = cJSON_GetArrayItem(color_array, 2);

      if (r && cJSON_IsNumber(r))
        color.r = static_cast<Uint8>(r->valueint);
      if (g && cJSON_IsNumber(g))
        color.g = static_cast<Uint8>(g->valueint);
      if (b && cJSON_IsNumber(b))
        color.b = static_cast<Uint8>(b->valueint);
    }
    return color;
  }

  // 查找带扩展名的文件
  bool FindFileWithExtensions(const char *base_path, const char *extensions[], char *found_path, size_t found_path_size) {
    for (int i = 0; extensions[i]; i++) {
      snprintf(found_path, sizeof(found_path), "%s%s", base_path, extensions[i]);
      printf("Trying path: %s\n", found_path);
      SDL_RWops *file = SDL_RWFromFile(found_path, "rb");
      if (file) {
        SDL_RWclose(file);
        return true;
      }
    }
    return false;
  }

  // Load and free character image (no caching)
  SDL_Surface *LoadCharacterImage(const char *character_name, int emotion_index) {
    if (!character_name)
      return nullptr;

    // Build file path
    char file_path[1024];
    snprintf(file_path, sizeof(file_path), "%s/chara/%s/%s (%d)", assets_path_, character_name, character_name, emotion_index);

    // Try multiple extensions
    const char *extensions[] = {".webp", ".png", ".jpg", ".jpeg", ".bmp", nullptr};
    char found_path[1024] = {0};

    for (int i = 0; extensions[i]; i++) {
      snprintf(found_path, sizeof(found_path), "%s%s", file_path, extensions[i]);
      SDL_RWops *file = SDL_RWFromFile(found_path, "rb");
      if (file) {
        SDL_RWclose(file);
        break;
      }
      found_path[0] = '\0';
    }

    if (found_path[0] == '\0') {
      DEBUG_PRINT("Character image not found: %s", file_path);
      return nullptr;
    }

    // Load image
    SDL_Surface *surface = IMG_Load(found_path);
    if (!surface) {
      DEBUG_PRINT("Failed to load character: %s", found_path);
      return nullptr;
    }

    // Convert to RGBA format
    SDL_Surface *rgba_surface = SDL_ConvertSurfaceFormat(surface, SDL_PIXELFORMAT_ABGR8888, 0);
    SDL_FreeSurface(surface);

    return rgba_surface;
  }

  // Load and free background image (no caching)
  SDL_Surface *LoadBackgroundImage(const char *background_name) {
    if (!background_name)
      return nullptr;

    // Build file path
    char file_path[1024];
    snprintf(file_path, sizeof(file_path), "%s/background/%s", assets_path_, background_name);

    // Try multiple extensions
    const char *extensions[] = {".webp", ".png", ".jpg", ".jpeg", ".bmp", nullptr};
    char found_path[1024] = {0};

    for (int i = 0; extensions[i]; i++) {
      snprintf(found_path, sizeof(found_path), "%s%s", file_path, extensions[i]);
      SDL_RWops *file = SDL_RWFromFile(found_path, "rb");
      if (file) {
        SDL_RWclose(file);
        break;
      }
      found_path[0] = '\0';
    }

    // If not found in background folder, try shader folder
    if (found_path[0] == '\0') {
      snprintf(file_path, sizeof(file_path), "%s/shader/%s", assets_path_, background_name);

      for (int i = 0; extensions[i]; i++) {
        snprintf(found_path, sizeof(found_path), "%s%s", file_path, extensions[i]);
        SDL_RWops *file = SDL_RWFromFile(found_path, "rb");
        if (file) {
          SDL_RWclose(file);
          break;
        }
        found_path[0] = '\0';
      }
    }

    if (found_path[0] == '\0') {
      DEBUG_PRINT("Background image not found: %s", background_name);
      return nullptr;
    }

    // Load image
    SDL_Surface *surface = IMG_Load(found_path);
    if (!surface) {
      DEBUG_PRINT("Failed to load background: %s", found_path);
      return nullptr;
    }

    // Convert to RGBA format
    SDL_Surface *rgba_surface = SDL_ConvertSurfaceFormat(surface, SDL_PIXELFORMAT_ABGR8888, 0);
    SDL_FreeSurface(surface);

    return rgba_surface;
  }

  // Load and free component image (no caching)
  SDL_Surface *LoadComponentImage(const char *overlay) {
    if (!overlay || strlen(overlay) == 0)
      return nullptr;

    // Build component path
    char comp_path[1024];
    char base_name[256];
    strncpy(base_name, overlay, sizeof(base_name) - 1);
    base_name[sizeof(base_name) - 1] = '\0';
    char *dot = strrchr(base_name, '.');
    if (dot)
      *dot = '\0';

    char base_path[1024];
    snprintf(base_path, sizeof(base_path), "%s/shader/%s", assets_path_, base_name);

    // Try multiple extensions
    const char *extensions[] = {".webp", ".png", ".jpg", ".jpeg", ".bmp", nullptr};
    SDL_Surface *comp_surface = nullptr;

    for (int i = 0; extensions[i]; i++) {
      snprintf(comp_path, sizeof(comp_path), "%s%s", base_path, extensions[i]);
      comp_surface = IMG_Load(comp_path);
      if (comp_surface)
        break;
    }

    if (!comp_surface) {
      return nullptr;
    }

    SDL_Surface *rgba_surface = SDL_ConvertSurfaceFormat(comp_surface, SDL_PIXELFORMAT_ABGR8888, 0);
    SDL_FreeSurface(comp_surface);

    return rgba_surface;
  }

  // Draw background component
  bool DrawBackgroundComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj, int background_index) {
    const char *overlay = GetJsonString(comp_obj, "overlay", "");
    char bg_name[32];

    if (strlen(overlay) > 0) {
      char base_name[256];
      strncpy(base_name, overlay, sizeof(base_name) - 1);
      char *dot = strrchr(base_name, '.');
      if (dot)
        *dot = '\0';
      strncpy(bg_name, base_name, sizeof(bg_name));
      bg_name[sizeof(bg_name) - 1] = '\0';
    } else {
      snprintf(bg_name, sizeof(bg_name), "c%d", background_index);
    }

    SDL_Surface *bg_surface = LoadBackgroundImage(bg_name);
    if (!bg_surface)
      return false;

    // Apply scaling
    float scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    SDL_Surface *final_surface = bg_surface;

    if (scale != 1.0f) {
      SDL_Surface *scaled = SDL_CreateRGBSurfaceWithFormat(0, static_cast<int>(bg_surface->w * scale), static_cast<int>(bg_surface->h * scale), 32, SDL_PIXELFORMAT_ABGR8888);
      if (scaled) {
        SDL_BlitScaled(bg_surface, nullptr, scaled, nullptr);
        SDL_FreeSurface(bg_surface);
        final_surface = scaled;
      }
    }

    // Calculate position
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));

    SDL_Rect pos = {0, 0, final_surface->w, final_surface->h};

    if (strstr(align, "right")) {
      pos.x = target1->w - final_surface->w;
    } else if (strstr(align, "center")) {
      pos.x = (target1->w - final_surface->w) / 2;
    }

    if (strstr(align, "bottom")) {
      pos.y = target1->h - final_surface->h;
    } else if (strstr(align, "middle")) {
      pos.y = (target1->h - final_surface->h) / 2;
    }

    pos.x += offset_x;
    pos.y += offset_y;

    // Draw to target surfaces
    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, &pos);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, &pos);

    SDL_FreeSurface(final_surface);
    return true;
  }

  // Draw character component
  bool DrawCharacterComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj, const char *character_name, int emotion_index) {
    bool use_fixed_character = GetJsonBool(comp_obj, "use_fixed_character", false);

    const char *draw_char_name;
    int draw_emotion;

    if (use_fixed_character) {
      draw_char_name = GetJsonString(comp_obj, "character_name", "");
      draw_emotion = static_cast<int>(GetJsonNumber(comp_obj, "emotion_index", 1));
    } else {
      draw_char_name = character_name;
      draw_emotion = emotion_index;
    }

    if (!draw_char_name || strlen(draw_char_name) == 0 || draw_emotion <= 0) {
      return false;
    }

    SDL_Surface *char_surface = LoadCharacterImage(draw_char_name, draw_emotion);
    if (!char_surface)
      return false;

    // Apply scaling
    float comp_scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    float chara_scale = static_cast<float>(GetJsonNumber(comp_obj, "scale1", 1.0));
    float scale = comp_scale * chara_scale;
    SDL_Surface *final_surface = char_surface;

    if (scale != 1.0f) {
      SDL_Surface *scaled = SDL_CreateRGBSurfaceWithFormat(0, static_cast<int>(char_surface->w * scale), static_cast<int>(char_surface->h * scale), 32, SDL_PIXELFORMAT_ABGR8888);
      if (scaled) {
        SDL_BlitScaled(char_surface, nullptr, scaled, nullptr);
        SDL_FreeSurface(char_surface);
        final_surface = scaled;
      }
    }

    // Calculate position
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int comp_offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int comp_offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));
    int chara_offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x1", 0));
    int chara_offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y1", 0));
    int offset_x = comp_offset_x + chara_offset_x;
    int offset_y = comp_offset_y + chara_offset_y;

    SDL_Rect pos = {0, 0, final_surface->w, final_surface->h};

    if (strstr(align, "right")) {
      pos.x = target1->w - final_surface->w;
    } else if (strstr(align, "center")) {
      pos.x = (target1->w - final_surface->w) / 2;
    }

    if (strstr(align, "bottom")) {
      pos.y = target1->h - final_surface->h;
    } else if (strstr(align, "middle")) {
      pos.y = (target1->h - final_surface->h) / 2;
    }

    pos.x += offset_x;
    pos.y += offset_y;

    SDL_Surface *temp_layer = SDL_CreateRGBSurfaceWithFormat(0, target1->w, target1->h, 32, SDL_PIXELFORMAT_ABGR8888);

    SDL_BlitSurface(final_surface, nullptr, temp_layer, &pos);
    SDL_FreeSurface(final_surface);
    final_surface = temp_layer;

    // Draw to target surfaces
    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, nullptr);
    printf("target1: %d, %d, %d, %d\n", target1->w, target1->h, pos.x, pos.y);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, nullptr);

    SDL_FreeSurface(final_surface);
    return true;
  }

  SDL_Surface *DrawNameboxWithText(cJSON *comp_obj) {
    const char *overlay = GetJsonString(comp_obj, "overlay", "");
    // DEBUG_PRINT("draw_namebox_with_text: overlay = %s", overlay);

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

    // DEBUG_PRINT("draw_namebox_with_text: Namebox loaded, size: %dx%d", namebox_surface->w, namebox_surface->h);

    // 获取文本配置
    cJSON *textcfg_obj = cJSON_GetObjectItem(comp_obj, "textcfg");
    if (!textcfg_obj || !cJSON_IsArray(textcfg_obj)) {
      DEBUG_PRINT("draw_namebox_with_text: No text configurations found for namebox");
      return namebox_surface; // 返回没有文字的namebox
    }

    int text_config_count = cJSON_GetArraySize(textcfg_obj);
    // DEBUG_PRINT("draw_namebox_with_text: Found %d text configurations", text_config_count);

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
        // DEBUG_PRINT("draw_namebox_with_text: Config %d, font_size = %d", i, font_size);
        if (font_size > max_font_size) {
          max_font_size = font_size;
        }
      }
    }

    if (max_font_size == 0) {
      max_font_size = 92; // 默认值
    }
    // DEBUG_PRINT("draw_namebox_with_text: Max font size = %d", max_font_size);

    // 计算基线位置（基于最大字体大小）- 高度的65%
    int baseline_y = static_cast<int>(namebox_surface->h * 0.65);
    // DEBUG_PRINT("draw_namebox_with_text: baseline_y = %d (namebox height = %d)", baseline_y, namebox_surface->h);

    // 起始X位置 - 以270为中心，根据最大字体大小调整
    int current_x = 270 - max_font_size / 2;
    // DEBUG_PRINT("draw_namebox_with_text: Starting current_x = %d", current_x);

    // 获取字体名称
    const char *font_name = GetJsonString(comp_obj, "font_name", "font3");
    // DEBUG_PRINT("draw_namebox_with_text: font_name = %s", font_name);

    // 绘制每个文本
    for (int i = 0; i < text_config_count; i++) {
      cJSON *config_obj = cJSON_GetArrayItem(textcfg_obj, i);
      if (!config_obj) {
        continue;
      }

      const char *text = GetJsonString(config_obj, "text", "");
      if (strlen(text) == 0) {
        // DEBUG_PRINT("draw_namebox_with_text: Config %d has empty text", i);
        continue;
      }

      int font_size = static_cast<int>(GetJsonNumber(config_obj, "font_size", 92.0));
      //   DEBUG_PRINT("draw_namebox_with_text: Drawing text: '%s', font_size = %d", text, font_size);

      // 获取字体颜色
      SDL_Color text_color;
      cJSON *color_obj = cJSON_GetObjectItem(config_obj, "font_color");
      if (color_obj) {
        text_color = ParseColor(color_obj);
        // DEBUG_PRINT("draw_namebox_with_text: Color RGB(%d, %d, %d)", text_color.r, text_color.g, text_color.b);
      } else {
        text_color = {255, 255, 255, 255}; // 默认白色
        // DEBUG_PRINT("draw_namebox_with_text: Using default color");
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

      // 获取字体的ascent（基线以上的高度）
      int ascent = TTF_FontAscent(font);
      //   DEBUG_PRINT("draw_namebox_with_text: Text size: %dx%d, ascent: %d", text_width, text_height, ascent);

      // 基线对齐：baseline_y - ascent 得到文本顶部的y坐标
      int text_top_y = baseline_y - ascent;

      // 绘制阴影文字 (2像素偏移)
      SDL_Surface *shadow_surface = TTF_RenderUTF8_Blended(font, text, shadow_color);
      if (shadow_surface) {
        int shadow_x = current_x + 2;
        int shadow_y = text_top_y + 2;

        // DEBUG_PRINT("draw_namebox_with_text: Drawing shadow at (%d, %d)", shadow_x, shadow_y);

        SDL_Rect shadow_rect = {shadow_x, shadow_y, shadow_surface->w, shadow_surface->h};
        SDL_BlitSurface(shadow_surface, nullptr, namebox_surface, &shadow_rect);
        SDL_FreeSurface(shadow_surface);
      }

      // 绘制主文字
      SDL_Surface *text_surface = TTF_RenderUTF8_Blended(font, text, text_color);
      if (!text_surface) {
        DEBUG_PRINT("draw_namebox_with_text: Failed to render text: %s", text);
        continue;
      }

      int main_x = current_x;
      int main_y = text_top_y;

      //   DEBUG_PRINT("draw_namebox_with_text: Drawing main text at (%d, %d)", main_x, main_y);

      SDL_Rect main_rect = {main_x, main_y, text_surface->w, text_surface->h};
      SDL_BlitSurface(text_surface, nullptr, namebox_surface, &main_rect);

      // 更新当前X位置为下一个文本
      current_x += text_width;
      DEBUG_PRINT("draw_namebox_with_text: Updated current_x = %d", current_x);

      SDL_FreeSurface(text_surface);
    }

    DEBUG_PRINT("draw_namebox_with_text: Completed successfully");
    return namebox_surface;
  }

  // Draw Namebox component (without text, just the image)
  bool DrawNameboxComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj) {
    // DEBUG_PRINT("DrawNameboxComponent: Starting...");

    // 使用新的函数绘制带文字的namebox
    SDL_Surface *namebox_surface = DrawNameboxWithText(comp_obj);
    // 加载图像
    if (!namebox_surface) {
    //   DEBUG_PRINT("DrawNameboxComponent: Failed to draw namebox with text");
      return false;
    }

    // 缩放
    float scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    SDL_Surface *final_surface = namebox_surface;

    if (scale != 1.0f) {
      SDL_Surface *scaled = SDL_CreateRGBSurfaceWithFormat(0, static_cast<int>(namebox_surface->w * scale), static_cast<int>(namebox_surface->h * scale), 32, SDL_PIXELFORMAT_ABGR8888);
      if (scaled) {
        SDL_BlitScaled(namebox_surface, nullptr, scaled, nullptr);
        SDL_FreeSurface(namebox_surface);
        final_surface = scaled;
      }
    }

    // 计算位置
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));

    SDL_Rect pos = {0, 0, final_surface->w, final_surface->h};

    if (strstr(align, "right")) {
      pos.x = target1->w - final_surface->w;
    } else if (strstr(align, "center")) {
      pos.x = (target1->w - final_surface->w) / 2;
    }

    if (strstr(align, "bottom")) {
      pos.y = target1->h - final_surface->h;
    } else if (strstr(align, "middle")) {
      pos.y = (target1->h - final_surface->h) / 2;
    }

    pos.x += offset_x;
    pos.y += offset_y;

    SDL_Surface *temp_layer = SDL_CreateRGBSurfaceWithFormat(0, target1->w, target1->h, 32, SDL_PIXELFORMAT_ABGR8888);

    SDL_BlitSurface(final_surface, nullptr, temp_layer, &pos);
    SDL_FreeSurface(final_surface);
    final_surface = temp_layer;

    // 绘制到目标表面
    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, nullptr);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, nullptr);

    SDL_FreeSurface(final_surface);

    // DEBUG_PRINT("DrawNameboxComponent: Completed successfully");
    return true;
  }

  // Draw generic component
  bool DrawGenericComponent(SDL_Surface *target1, SDL_Surface *target2, cJSON *comp_obj) {
    const char *overlay = GetJsonString(comp_obj, "overlay", "");
    if (strlen(overlay) == 0)
      return true;

    SDL_Surface *comp_surface = LoadComponentImage(overlay);
    if (!comp_surface)
      return false;

    // Scaling
    float scale = static_cast<float>(GetJsonNumber(comp_obj, "scale", 1.0));
    SDL_Surface *final_surface = comp_surface;

    if (scale != 1.0f) {
      SDL_Surface *scaled = SDL_CreateRGBSurfaceWithFormat(0, static_cast<int>(comp_surface->w * scale), static_cast<int>(comp_surface->h * scale), 32, SDL_PIXELFORMAT_ABGR8888);
      if (scaled) {
        SDL_BlitScaled(comp_surface, nullptr, scaled, nullptr);
        SDL_FreeSurface(comp_surface);
        final_surface = scaled;
      }
    }

    // Calculate position
    const char *align = GetJsonString(comp_obj, "align", "top-left");
    int offset_x = static_cast<int>(GetJsonNumber(comp_obj, "offset_x", 0));
    int offset_y = static_cast<int>(GetJsonNumber(comp_obj, "offset_y", 0));

    SDL_Rect pos = {0, 0, final_surface->w, final_surface->h};

    if (strstr(align, "right")) {
      pos.x = target1->w - final_surface->w;
    } else if (strstr(align, "center")) {
      pos.x = (target1->w - final_surface->w) / 2;
    }

    if (strstr(align, "bottom")) {
      pos.y = target1->h - final_surface->h;
    } else if (strstr(align, "middle")) {
      pos.y = (target1->h - final_surface->h) / 2;
    }

    pos.x += offset_x;
    pos.y += offset_y;

    // Draw to target surfaces
    if (target1)
      SDL_BlitSurface(final_surface, nullptr, target1, &pos);
    if (target2)
      SDL_BlitSurface(final_surface, nullptr, target2, &pos);

    SDL_FreeSurface(final_surface);
    return true;
  }

  // Get font (with caching)
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
  void DrawImageToCanvasSimple(SDL_Surface *canvas, unsigned char *image_data, int image_width, int image_height, int image_pitch) {
    StyleConfig *config = &style_config_;

    const char *enabled = config->paste_enabled;
    if (strcmp(enabled, "off") == 0) {
      return; // 不粘贴图片
    }

    int paste_x = config->paste_x;
    int paste_y = config->paste_y;
    int paste_width = config->paste_width;
    int paste_height = config->paste_height;

    SDL_Surface *img_surface = SDL_CreateRGBSurfaceWithFormatFrom(image_data, image_width, image_height, 32, image_pitch, SDL_PIXELFORMAT_ABGR8888);

    if (!img_surface) {
      return;
    }

    // 计算缩放
    int region_w = paste_width;
    int region_h = paste_height;
    int img_w = img_surface->w;
    int img_h = img_surface->h;

    int new_width = img_w;
    int new_height = img_h;

    float scale_w = static_cast<float>(region_w) / img_w;
    float scale_h = static_cast<float>(region_h) / img_h;

    // 根据填充模式调整
    if (strcmp(config->paste_fill_mode, "width") == 0) {
      new_width = region_w;
      new_height = static_cast<int>(img_h * scale_w);
    } else if (strcmp(config->paste_fill_mode, "height") == 0) {
      new_height = region_h;
      new_width = static_cast<int>(img_w * scale_h);
    } else { // fit模式
      float scale = (scale_w < scale_h) ? scale_w : scale_h;
      new_width = static_cast<int>(img_w * scale);
      new_height = static_cast<int>(img_h * scale);
    }

    // 调整图片大小
    SDL_Surface *resized_surface = SDL_CreateRGBSurfaceWithFormat(0, new_width, new_height, 32, SDL_PIXELFORMAT_ABGR8888);

    if (resized_surface) {
      SDL_BlitScaled(img_surface, nullptr, resized_surface, nullptr);

      // 根据对齐方式调整位置
      int final_x = paste_x;
      int final_y = paste_y;

      // 水平对齐
      if (strcmp(config->paste_align, "center") == 0) {
        final_x += (region_w - new_width) / 2;
      } else if (strcmp(config->paste_align, "right") == 0) {
        final_x += region_w - new_width;
      }

      // 垂直对齐
      if (strcmp(config->paste_valign, "middle") == 0) {
        final_y += (region_h - new_height) / 2;
      } else if (strcmp(config->paste_valign, "bottom") == 0) {
        final_y += region_h - new_height;
      }

      SDL_Rect dest_rect = {final_x, final_y, new_width, new_height};
      SDL_BlitSurface(resized_surface, nullptr, canvas, &dest_rect);
      SDL_FreeSurface(resized_surface);
    }

    SDL_FreeSurface(img_surface);
  }

  // Cache management functions
  void ClearPreviewCache() {
    SDL_LockMutex(cache_mutex_);
    preview_cache_.reset();
    SDL_UnlockMutex(cache_mutex_);
  }

  void ClearFontCache() {
    SDL_LockMutex(cache_mutex_);
    if (font_cache_) {
      delete font_cache_;
      font_cache_ = nullptr;
    }
    // 清理emoji字体缓存
    static TTF_Font *emoji_font = nullptr;
    if (emoji_font) {
      TTF_CloseFont(emoji_font);
      emoji_font = nullptr;
    }
    static int cached_emoji_size = 0;
    cached_emoji_size = 0;
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
  bool preload_character_ = false;
  bool preload_background_ = false;
  int pre_resize_ = 1080;
  float min_image_ratio_ = 0.2f;

  // SDL state
  bool sdl_initialized_ = false;
  bool img_initialized_ = false;
  bool ttf_initialized_ = false;

  // Caches (only fonts, static layers, and preview)
  FontCacheEntry *font_cache_ = nullptr;
  std::unique_ptr<ImageData> preview_cache_;

  StaticLayerNode *static_layer_cache_first_ = nullptr;
  StaticLayerNode *static_layer_cache_current_ = nullptr;
  int static_layer_cache_count_ = 0;

  SDL_mutex *cache_mutex_ = nullptr;

  std::mutex mutex_;

  // 新增：加载emoji图片
  SDL_Surface *LoadEmojiImage(const std::string &emoji_text, int target_size);

  // 新增：将emoji字符串转换为文件名
  std::string EmojiToFileName(const std::string &emoji_text);
};

// ==================== 新增函数实现 ====================

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

  // 加载图片
  SDL_Surface *emoji_surface = IMG_Load(file_path);
  if (!emoji_surface) {
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
    SDL_Surface *scaled_surface = SDL_CreateRGBSurfaceWithFormat(0, target_size, target_size, 32, SDL_PIXELFORMAT_ABGR8888);
    if (scaled_surface) {
      // 保持宽高比缩放
      float scale = (static_cast<float>(target_size) / rgba_surface->w < static_cast<float>(target_size) / rgba_surface->h) ? (static_cast<float>(target_size) / rgba_surface->w) : (static_cast<float>(target_size) / rgba_surface->h);
      int new_w = static_cast<int>(rgba_surface->w * scale);
      int new_h = static_cast<int>(rgba_surface->h * scale);
      int offset_x = (target_size - new_w) / 2;
      int offset_y = (target_size - new_h) / 2;

      SDL_Rect dest_rect = {offset_x, offset_y, new_w, new_h};
      SDL_FillRect(scaled_surface, nullptr, SDL_MapRGBA(scaled_surface->format, 0, 0, 0, 0));
      SDL_BlitScaled(rgba_surface, nullptr, scaled_surface, &dest_rect);

      SDL_FreeSurface(rgba_surface);
      rgba_surface = scaled_surface;
      DEBUG_PRINT("Emoji scaled to: %dx%d", rgba_surface->w, rgba_surface->h);
    }
  }

  return rgba_surface;
}

void ImageLoaderManager::DrawTextToCanvasWithEmojiAndPositions(SDL_Surface *canvas, const std::string &text, const std::vector<std::string> &emoji_list, const std::vector<std::pair<int, int>> &emoji_positions) {
  DEBUG_PRINT("=== Starting DrawTextToCanvasWithEmojiAndPositions ===");

  StyleConfig *config = &style_config_;
  DEBUG_PRINT("Style config loaded: font=%s, size=%d", config->font_family, config->font_size);

  // 获取普通字体（用于文本渲染）
  TTF_Font *normal_font = GetFontCached(config->font_family, config->font_size);
  if (!normal_font) {
    DEBUG_PRINT("ERROR: Failed to get normal font: %s (size %d)", config->font_family, config->font_size);
    return;
  }
  DEBUG_PRINT("Normal font loaded successfully");

  // 文本区域
  int text_x = config->textbox_x;
  int text_y = config->textbox_y;
  int text_width = config->textbox_width;
  int text_height = config->textbox_height;

  DEBUG_PRINT("Text area: x=%d, y=%d, width=%d, height=%d", text_x, text_y, text_width, text_height);

  // 颜色
  SDL_Color text_color = {config->text_color[0], config->text_color[1], config->text_color[2], 255};
  SDL_Color bracket_color = {config->bracket_color[0], config->bracket_color[1], config->bracket_color[2], 255};
  SDL_Color shadow_color = {config->shadow_color[0], config->shadow_color[1], config->shadow_color[2], 255};

  DEBUG_PRINT("Text color: R=%d, G=%d, B=%d", text_color.r, text_color.g, text_color.b);
  DEBUG_PRINT("Bracket color: R=%d, G=%d, B=%d", bracket_color.r, bracket_color.g, bracket_color.b);

  // 解析文本，使用emoji位置信息
  std::vector<TextFragmentData> fragments;
  ParseTextWithBracketsAndEmojiPositions(text, emoji_list, emoji_positions, text_color, bracket_color, fragments);

  DEBUG_PRINT("Parsed text into %zu fragments", fragments.size());
  for (size_t i = 0; i < fragments.size(); i++) {
    const TextFragmentData &frag = fragments[i];
    DEBUG_PRINT("Fragment %zu: text='%s', is_emoji=%d", i, frag.text.c_str(), frag.is_emoji);
  }

  // 换行处理（使用普通字体测量）
  std::vector<std::vector<TextFragmentData>> lines;
  std::vector<TextFragmentData> current_line;
  int current_width = 0;
  int emoji_size = int(config->font_size * 1.2); // emoji图片大小等于字体大小

  for (size_t i = 0; i < fragments.size(); i++) {
    const TextFragmentData &frag = fragments[i];
    int frag_width;

    if (frag.is_emoji) {
      // emoji使用固定大小
      frag_width = emoji_size;
      DEBUG_PRINT("Fragment %zu (emoji): width=%d", i, frag_width);
    } else {
      TTF_SizeUTF8(normal_font, frag.text.c_str(), &frag_width, nullptr);
      DEBUG_PRINT("Fragment %zu (text): text='%s', width=%d", i, frag.text.c_str(), frag_width);
    }

    if (current_width + frag_width > text_width && !current_line.empty()) {
      // 换行
      lines.push_back(current_line);
      current_line.clear();
      current_width = 0;
    }

    current_line.push_back(frag);
    current_width += frag_width;
  }

  // 添加最后一行
  if (!current_line.empty()) {
    lines.push_back(current_line);
  }

  DEBUG_PRINT("Wrapped text into %zu lines", lines.size());

  // 计算总高度（每行高度为字体高度）
  int line_height = config->font_size;
  int total_height = lines.size() * line_height;
  DEBUG_PRINT("Line height: %d, total text height: %d", line_height, total_height);

  // 计算垂直起始位置
  int current_y = text_y;
  if (strcmp(config->text_valign, "middle") == 0) {
    current_y += (text_height - total_height) / 2;
    DEBUG_PRINT("Vertical alignment: middle, y=%d", current_y);
  } else if (strcmp(config->text_valign, "bottom") == 0) {
    current_y = text_y + text_height - total_height;
    DEBUG_PRINT("Vertical alignment: bottom, y=%d", current_y);
  } else {
    DEBUG_PRINT("Vertical alignment: top, y=%d", current_y);
  }

  // 绘制每一行
  for (size_t line_idx = 0; line_idx < lines.size(); line_idx++) {
    const std::vector<TextFragmentData> &line = lines[line_idx];

    DEBUG_PRINT("--- Drawing line %zu with %zu fragments ---", line_idx, line.size());

    int line_width = 0;
    for (size_t frag_idx = 0; frag_idx < line.size(); frag_idx++) {
      const TextFragmentData &frag = line[frag_idx];
      int w;

      if (frag.is_emoji) {
        w = emoji_size;
      } else {
        TTF_SizeUTF8(normal_font, frag.text.c_str(), &w, nullptr);
      }
      line_width += w;
    }

    DEBUG_PRINT("Line %zu total width: %d", line_idx, line_width);

    // 计算水平起始位置
    int current_x = text_x;
    if (strcmp(config->text_align, "center") == 0) {
      current_x += (text_width - line_width) / 2;
      DEBUG_PRINT("Horizontal alignment: center, x=%d", current_x);
    } else if (strcmp(config->text_align, "right") == 0) {
      current_x += text_width - line_width;
      DEBUG_PRINT("Horizontal alignment: right, x=%d", current_x);
    } else {
      DEBUG_PRINT("Horizontal alignment: left, x=%d", current_x);
    }

    // 绘制这一行的每个片段
    for (size_t frag_idx = 0; frag_idx < line.size(); frag_idx++) {
      const TextFragmentData &frag = line[frag_idx];

      DEBUG_PRINT("Drawing fragment %zu: text='%s', is_emoji=%d", frag_idx, frag.text.c_str(), frag.is_emoji);

      if (frag.is_emoji) {
        // 加载并绘制emoji图片
        SDL_Surface *emoji_surface = LoadEmojiImage(frag.text, emoji_size);
        if (emoji_surface) {
          SDL_Rect emoji_rect = {current_x, current_y + int(emoji_size / 6), emoji_surface->w, emoji_surface->h};
          SDL_BlitSurface(emoji_surface, nullptr, canvas, &emoji_rect);
          current_x += emoji_surface->w;
          SDL_FreeSurface(emoji_surface);
          DEBUG_PRINT("Emoji drawn at (%d, %d), size=%dx%d", emoji_rect.x, emoji_rect.y, emoji_rect.w, emoji_rect.h);
        } else {
          // emoji图片加载失败，绘制一个灰色方块作为fallback
          DEBUG_PRINT("Failed to load emoji image, drawing fallback square");
          SDL_Rect fallback_rect = {current_x, current_y, emoji_size, emoji_size};
          SDL_FillRect(canvas, &fallback_rect, SDL_MapRGBA(canvas->format, 200, 200, 200, 255));
          current_x += emoji_size;
        }
      } else {
        // 普通文本渲染
        DEBUG_PRINT("Drawing text fragment: '%s'", frag.text.c_str());

        // 绘制阴影
        if (config->shadow_offset_x != 0 || config->shadow_offset_y != 0) {
          SDL_Surface *shadow_surface = TTF_RenderUTF8_Blended(normal_font, frag.text.c_str(), shadow_color);
          if (shadow_surface) {
            SDL_Rect shadow_rect = {current_x + config->shadow_offset_x, current_y + config->shadow_offset_y, shadow_surface->w, shadow_surface->h};
            SDL_BlitSurface(shadow_surface, nullptr, canvas, &shadow_rect);
            SDL_FreeSurface(shadow_surface);
          }
        }

        // 绘制文本
        SDL_Surface *text_surface = TTF_RenderUTF8_Blended(normal_font, frag.text.c_str(), frag.color);
        if (text_surface) {
          DEBUG_PRINT("Text surface created: %dx%d", text_surface->w, text_surface->h);
          SDL_Rect text_rect = {current_x, current_y, text_surface->w, text_surface->h};
          SDL_BlitSurface(text_surface, nullptr, canvas, &text_rect);
          current_x += text_surface->w;
          SDL_FreeSurface(text_surface);
          DEBUG_PRINT("Text drawn at (%d, %d)", text_rect.x, text_rect.y);
        } else {
          DEBUG_PRINT("ERROR: Failed to create text surface: %s", TTF_GetError());
        }
      }
    }

    // 移动到下一行
    current_y += line_height;
    DEBUG_PRINT("Moving to next line, y=%d", current_y);
  }

  DEBUG_PRINT("=== Finished DrawTextToCanvasWithEmojiAndPositions ===");
}

void ImageLoaderManager::ParseTextWithBracketsAndEmojiPositions(const std::string &text, const std::vector<std::string> &emoji_list, const std::vector<std::pair<int, int>> &emoji_positions, const SDL_Color &text_color, const SDL_Color &bracket_color,
                                                                std::vector<TextFragmentData> &fragments) {
  DEBUG_PRINT("=== Parsing text with emoji positions ===");
  DEBUG_PRINT("Input text: '%s' (length: %zu, UTF-8 bytes: %zu)", text.c_str(), text.length(), text.size());
  DEBUG_PRINT("Emoji count: %zu, positions count: %zu", emoji_list.size(), emoji_positions.size());

  if (emoji_positions.empty()) {
    DEBUG_PRINT("WARNING: Emoji positions not provided or mismatch.");
    ParseBracketsInText(text, text_color, bracket_color, fragments);
    return;
  }

  // 使用emoji位置信息解析文本
  size_t current_pos = 0; // 当前字节位置

  // 按照emoji位置分割文本
  for (size_t i = 0; i < emoji_positions.size(); i++) {
    int emoji_start = emoji_positions[i].first;
    int emoji_end = emoji_positions[i].second;

    DEBUG_PRINT("Emoji %zu: position start=%d, end=%d", i, emoji_start, emoji_end);

    // 验证位置是否在范围内
    if (emoji_positions.empty()) {
      DEBUG_PRINT("No emoji positions provided. Parsing entire text for brackets.");
      // 直接解析整个文本中的括号
      ParseBracketsInText(text, text_color, bracket_color, fragments);
      return;
    }

    // 添加emoji之前的文本
    if (emoji_start > static_cast<int>(current_pos)) {
      // 提取emoji之前的文本
      size_t before_len = emoji_start - current_pos;
      if (before_len > 0) {
        // 注意：这里使用字节位置，直接截取字节
        std::string before_emoji = text.substr(current_pos, before_len);
        DEBUG_PRINT("Text before emoji %zu: '%s' (UTF-8 length: %zu)", i, before_emoji.c_str(), before_emoji.size());
        // 解析括号
        ParseBracketsInText(before_emoji, text_color, bracket_color, fragments);
      }
    }

    // 添加emoji
    if (i < emoji_list.size()) {
      DEBUG_PRINT("Adding emoji %zu: '%s' (UTF-8 bytes: %zu)", i, emoji_list[i].c_str(), emoji_list[i].size());
      fragments.push_back(TextFragmentData(emoji_list[i], text_color, true));
    } else {
      DEBUG_PRINT("ERROR: Emoji index %zu out of range (total: %zu)", i, emoji_list.size());
    }

    current_pos = emoji_end;
  }

  // 添加最后的文本
  if (current_pos < text.size()) {
    std::string remaining_text = text.substr(current_pos);
    if (!remaining_text.empty()) {
      DEBUG_PRINT("Remaining text after all emojis: '%s' (UTF-8 bytes: %zu)", remaining_text.c_str(), remaining_text.size());
      ParseBracketsInText(remaining_text, text_color, bracket_color, fragments);
    }
  }

  DEBUG_PRINT("Parsing complete. Created %zu fragments.", fragments.size());
}

void ImageLoaderManager::ParseBracketsInText(const std::string &text, const SDL_Color &text_color, const SDL_Color &bracket_color, std::vector<TextFragmentData> &fragments) {
//   DEBUG_PRINT("=== ParseBracketsInText Start ===");
//   DEBUG_PRINT("Input text: '%s' (UTF-8 bytes: %zu)", text.c_str(), text.size());

  size_t i = 0;
  while (i < text.size()) {
    // 获取当前字符的字节数
    unsigned char c = static_cast<unsigned char>(text[i]);
    int char_len = 1;

    if (c < 0x80) {
      char_len = 1;
    } else if ((c & 0xE0) == 0xC0) {
      char_len = 2;
    } else if ((c & 0xF0) == 0xE0) {
      char_len = 3;
    } else if ((c & 0xF8) == 0xF0) {
      char_len = 4;
    }

    // 提取当前字符
    std::string current_char;
    if (i + char_len <= text.size()) {
      current_char = text.substr(i, char_len);
    } else {
      current_char = text.substr(i, 1);
      char_len = 1;
    }

    // DEBUG_PRINT("Processing char at pos %zu: '%s'", i, current_char.c_str());

    // 检查是否是左括号
    auto it_left = lt_bracket_pairs.find(current_char);
    if (it_left != lt_bracket_pairs.end()) {
      std::string left_bracket = current_char;
      std::string right_bracket = it_left->second;

    //   DEBUG_PRINT("Found left bracket: '%s', looking for matching right bracket: '%s'", left_bracket.c_str(), right_bracket.c_str());

      // 寻找匹配的右括号
      size_t j = i + char_len;
      int bracket_depth = 1; // 我们已经有一个左括号
      size_t match_pos = std::string::npos;

      while (j < text.size()) {
        // 获取下一个字符
        unsigned char c2 = static_cast<unsigned char>(text[j]);
        int next_len = 1;

        if (c2 < 0x80) {
          next_len = 1;
        } else if ((c2 & 0xE0) == 0xC0) {
          next_len = 2;
        } else if ((c2 & 0xF0) == 0xE0) {
          next_len = 3;
        } else if ((c2 & 0xF8) == 0xF0) {
          next_len = 4;
        }

        std::string next_char;
        if (j + next_len <= text.size()) {
          next_char = text.substr(j, next_len);
        } else {
          next_char = text.substr(j, 1);
          next_len = 1;
        }

        // DEBUG_PRINT("  At pos %zu, char: '%s'", j, next_char.c_str());

        // 检查是否是同类型的左括号（支持嵌套）
        auto it_left2 = lt_bracket_pairs.find(next_char);
        if (left_bracket != right_bracket && it_left2 != lt_bracket_pairs.end() && it_left2->second == right_bracket) {
          bracket_depth++;
        //   DEBUG_PRINT("    Found nested left bracket, depth now: %d", bracket_depth);
        }
        // 检查是否是匹配的右括号
        else if (next_char == right_bracket) {
          bracket_depth--;
        //   DEBUG_PRINT("    Found matching right bracket, depth now: %d", bracket_depth);

          if (bracket_depth == 0) {
            match_pos = j;
            // DEBUG_PRINT("    Found matching bracket at position %zu", match_pos);
            break;
          }
        }

        j += next_len;
      }

      if (match_pos != std::string::npos) {
        // 找到匹配的右括号
        // 1. 添加左括号
        fragments.push_back(TextFragmentData(left_bracket, bracket_color, false));

        // 2. 添加括号内的内容
        size_t content_start = i + char_len;
        size_t content_len = match_pos - content_start;
        if (content_len > 0) {
          std::string content = text.substr(content_start, content_len);
          fragments.push_back(TextFragmentData(content, bracket_color, false));
        }

        // 3. 添加右括号
        fragments.push_back(TextFragmentData(right_bracket, bracket_color, false));

        // 跳过已处理的部分
        i = match_pos + (right_bracket.size());
        continue;
      }
    }

      // 普通文本
      static std::string current_text;
      if (current_text.empty()) {
        current_text = current_char;
      } else {
        // 检查前一个字符是否是普通文本
        size_t last_fragment_end = 0;
        if (!fragments.empty()) {
          const TextFragmentData &last_frag = fragments.back();
          if (last_frag.color.r == text_color.r && last_frag.color.g == text_color.g && last_frag.color.b == text_color.b) {
            // 合并到上一个片段
            fragments.back().text += current_char;
          } else {
            // 创建新片段
            fragments.push_back(TextFragmentData(current_char, text_color, false));
          }
        } else {
          // 第一个片段
          fragments.push_back(TextFragmentData(current_char, text_color, false));
        }
      }

    i += char_len;
  }
}

} // namespace image_loader

// C interface export functions
extern "C" {

__declspec(dllexport) void set_global_config(const char *assets_path, bool preload_character, bool preload_background, int pre_resize, float min_image_ratio) {
  image_loader::ImageLoaderManager::GetInstance().SetGlobalConfig(assets_path, preload_character, preload_background, pre_resize, min_image_ratio);
}

__declspec(dllexport) void update_gui_settings(const char *settings_json) { image_loader::ImageLoaderManager::GetInstance().UpdateGuiSettings(settings_json); }

__declspec(dllexport) void update_style_config(const char *style_json) { image_loader::ImageLoaderManager::GetInstance().UpdateStyleConfig(style_json); }

__declspec(dllexport) void clear_cache(const char *cache_type) { image_loader::ImageLoaderManager::GetInstance().ClearCache(cache_type); }

__declspec(dllexport) int generate_complete_image(const char *assets_path, int canvas_width, int canvas_height, const char *components_json, const char *character_name, int emotion_index, int background_index, unsigned char **out_data, int *out_width,
                                                  int *out_height) {

  return static_cast<int>(image_loader::ImageLoaderManager::GetInstance().GenerateCompleteImage(assets_path, canvas_width, canvas_height, components_json, character_name, emotion_index, background_index, out_data, out_width, out_height));
}

// 简化的绘制函数
__declspec(dllexport) int draw_content_simple(const char *text, const char *emoji_json, unsigned char *image_data, int image_width, int image_height, int image_pitch, unsigned char **out_data, int *out_width, int *out_height) {
  return static_cast<int>(image_loader::ImageLoaderManager::GetInstance().DrawContentWithTextAndImage(text, emoji_json, image_data, image_width, image_height, image_pitch, out_data, out_width, out_height));
}

__declspec(dllexport) void free_image_data(unsigned char *data) {
  if (data) {
    free(data);
  }
}

__declspec(dllexport) void cleanup_all() { image_loader::ImageLoaderManager::GetInstance().Cleanup(); }

} // extern "C"