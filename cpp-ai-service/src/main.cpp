#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <net.h>
#include <sqlite3.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;

double elapsed_ms(const Clock::time_point &started) {
    return std::chrono::duration<double, std::milli>(Clock::now() - started).count();
}

struct Options {
    fs::path db_path = "/data/warehousekeeper/warehousekeeper.db";
    fs::path detector_model = "/opt/warehousekeeper/models/best_ncnn_model";
    fs::path freshness_model = "/opt/warehousekeeper/models/shufflenet_v2_freshness_ncnn_model";
    fs::path crop_dir = "/data/warehousekeeper/frames/crops";
    float confidence = 0.35F;
    float iou = 0.45F;
    int image_size = 640;
    int threads = 2;
    int poll_ms = 1000;
    bool once = false;
};

struct Detection {
    cv::Rect box;
    std::string species;
    std::string label;
    float confidence = 0.0F;
};

struct FreshnessPrediction {
    std::string label;
    float confidence = 0.0F;
    float score = 0.0F;
    std::array<float, 3> probabilities{};
    double inference_ms = 0.0;
};

struct Recognition {
    Detection detection;
    FreshnessPrediction freshness;
    fs::path crop_path;
    int image_width = 0;
    int image_height = 0;
    double total_inference_ms = 0.0;
};

struct Frame {
    long long id = 0;
    std::string image_path;
};

const std::vector<std::string> kDetectorClasses = {
    "Apple_fresh", "Apple_rotten", "Banana_fresh", "Banana_rotten",
    "Carrot_fresh", "Carrot_rotten", "Cucumber_freesh", "Cucumber_rotten",
    "Orange_fresh", "Orange_rotten"
};
const std::array<std::string, 3> kFreshnessClasses = {"fresh", "mild", "rotten"};

std::string lowercase(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return value;
}

std::string species_from_label(const std::string &label) {
    const auto separator = label.find('_');
    return lowercase(label.substr(0, separator));
}

class YoloDetector {
public:
    explicit YoloDetector(const Options &options)
        : confidence_(options.confidence), iou_(options.iou), image_size_(options.image_size) {
        net_.opt.num_threads = std::max(1, options.threads);
        net_.opt.use_vulkan_compute = false;
        if (net_.load_param((options.detector_model / "model.ncnn.param").string().c_str()) != 0 ||
            net_.load_model((options.detector_model / "model.ncnn.bin").string().c_str()) != 0) {
            throw std::runtime_error("无法加载YOLO NCNN模型");
        }
    }

    std::vector<Detection> detect(const cv::Mat &image, double &preprocess_ms,
                                  double &forward_ms, double &postprocess_ms) {
        const auto preprocess_started = Clock::now();
        float scale = 1.0F;
        int padding_x = 0;
        int padding_y = 0;
        cv::Mat letterboxed = letterbox(image, scale, padding_x, padding_y);
        ncnn::Mat input = ncnn::Mat::from_pixels(
            letterboxed.data, ncnn::Mat::PIXEL_BGR2RGB, image_size_, image_size_);
        const float normalization[3] = {1.0F / 255.0F, 1.0F / 255.0F, 1.0F / 255.0F};
        input.substract_mean_normalize(nullptr, normalization);
        preprocess_ms = elapsed_ms(preprocess_started);

        const auto forward_started = Clock::now();
        ncnn::Extractor extractor = net_.create_extractor();
        if (extractor.input("in0", input) != 0) throw std::runtime_error("YOLO NCNN输入失败");
        ncnn::Mat ncnn_output;
        if (extractor.extract("out0", ncnn_output) != 0) throw std::runtime_error("YOLO NCNN推理失败");
        forward_ms = elapsed_ms(forward_started);

        const auto postprocess_started = Clock::now();
        if (ncnn_output.dims != 2 || ncnn_output.h != static_cast<int>(kDetectorClasses.size()) + 4) {
            throw std::runtime_error("YOLO NCNN输出形状不正确");
        }
        cv::Mat output(ncnn_output.h, ncnn_output.w, CV_32F);
        for (int channel = 0; channel < ncnn_output.h; ++channel) {
            std::copy(ncnn_output.row(channel), ncnn_output.row(channel) + ncnn_output.w,
                      output.ptr<float>(channel));
        }
        cv::Mat rows = output_to_rows(output);
        std::vector<cv::Rect> boxes;
        std::vector<float> scores;
        std::vector<int> class_ids;
        const bool has_objectness = rows.cols == static_cast<int>(kDetectorClasses.size()) + 5;
        const int class_start = has_objectness ? 5 : 4;

        for (int row_index = 0; row_index < rows.rows; ++row_index) {
            const float *row = rows.ptr<float>(row_index);
            cv::Mat class_scores(1, static_cast<int>(kDetectorClasses.size()), CV_32F,
                                 const_cast<float *>(row + class_start));
            cv::Point class_point;
            double class_score = 0.0;
            cv::minMaxLoc(class_scores, nullptr, &class_score, nullptr, &class_point);
            float score = static_cast<float>(class_score);
            if (has_objectness) {
                score *= row[4];
            }
            if (score < confidence_) {
                continue;
            }

            const float center_x = row[0];
            const float center_y = row[1];
            const float width = row[2];
            const float height = row[3];
            int left = cvRound((center_x - width / 2.0F - padding_x) / scale);
            int top = cvRound((center_y - height / 2.0F - padding_y) / scale);
            int right = cvRound((center_x + width / 2.0F - padding_x) / scale);
            int bottom = cvRound((center_y + height / 2.0F - padding_y) / scale);
            left = std::clamp(left, 0, image.cols - 1);
            top = std::clamp(top, 0, image.rows - 1);
            right = std::clamp(right, 0, image.cols);
            bottom = std::clamp(bottom, 0, image.rows);
            if (right <= left || bottom <= top) {
                continue;
            }
            boxes.emplace_back(left, top, right - left, bottom - top);
            scores.push_back(score);
            class_ids.push_back(class_point.x);
        }

        std::vector<int> selected;
        for (int class_id = 0; class_id < static_cast<int>(kDetectorClasses.size()); ++class_id) {
            std::vector<cv::Rect> class_boxes;
            std::vector<float> class_scores;
            std::vector<int> original_indices;
            for (int index = 0; index < static_cast<int>(class_ids.size()); ++index) {
                if (class_ids[index] == class_id) {
                    class_boxes.push_back(boxes[index]);
                    class_scores.push_back(scores[index]);
                    original_indices.push_back(index);
                }
            }
            std::vector<int> order(original_indices.size());
            for (int index = 0; index < static_cast<int>(order.size()); ++index) order[index] = index;
            std::sort(order.begin(), order.end(), [&](int a, int b) { return class_scores[a] > class_scores[b]; });
            while (!order.empty()) {
                const int local_index = order.front();
                selected.push_back(original_indices[local_index]);
                order.erase(order.begin());
                order.erase(std::remove_if(order.begin(), order.end(), [&](int other) {
                    const cv::Rect intersection = class_boxes[local_index] & class_boxes[other];
                    const float union_area = static_cast<float>(class_boxes[local_index].area() +
                        class_boxes[other].area() - intersection.area());
                    return union_area > 0.0F && static_cast<float>(intersection.area()) / union_area > iou_;
                }), order.end());
            }
        }
        std::sort(selected.begin(), selected.end(), [&](int left, int right) {
            return scores[left] > scores[right];
        });

        std::vector<Detection> detections;
        detections.reserve(selected.size());
        for (int index : selected) {
            const std::string &label = kDetectorClasses[class_ids[index]];
            detections.push_back({boxes[index], species_from_label(label), label, scores[index]});
        }
        postprocess_ms = elapsed_ms(postprocess_started);
        return detections;
    }

private:
    cv::Mat letterbox(const cv::Mat &image, float &scale, int &padding_x, int &padding_y) const {
        scale = std::min(static_cast<float>(image_size_) / image.cols,
                         static_cast<float>(image_size_) / image.rows);
        const int resized_width = std::max(1, cvRound(image.cols * scale));
        const int resized_height = std::max(1, cvRound(image.rows * scale));
        cv::Mat resized;
        cv::resize(image, resized, cv::Size(resized_width, resized_height));
        padding_x = (image_size_ - resized_width) / 2;
        padding_y = (image_size_ - resized_height) / 2;
        cv::Mat canvas(image_size_, image_size_, CV_8UC3, cv::Scalar(114, 114, 114));
        resized.copyTo(canvas(cv::Rect(padding_x, padding_y, resized_width, resized_height)));
        return canvas;
    }

    static cv::Mat output_to_rows(const cv::Mat &output) {
        cv::Mat flat;
        if (output.dims == 3) {
            const int rows = output.size[1];
            const int columns = output.size[2];
            flat = cv::Mat(rows, columns, CV_32F, const_cast<float *>(output.ptr<float>()));
        } else if (output.dims == 2) {
            flat = output;
        } else {
            throw std::runtime_error("YOLO输出维度不受支持");
        }
        const int expected = static_cast<int>(kDetectorClasses.size()) + 4;
        const int expected_objectness = expected + 1;
        if (flat.rows == expected || flat.rows == expected_objectness) {
            cv::Mat transposed;
            cv::transpose(flat, transposed);
            flat = transposed;
        }
        if (flat.cols != expected && flat.cols != expected_objectness) {
            throw std::runtime_error("YOLO输出列数与类别数量不匹配");
        }
        return flat;
    }

    ncnn::Net net_;
    float confidence_;
    float iou_;
    int image_size_;
};

class FreshnessClassifier {
public:
    explicit FreshnessClassifier(const Options &options) {
        net_.opt.num_threads = std::max(1, options.threads);
        net_.opt.use_vulkan_compute = false;
        if (net_.load_param((options.freshness_model / "model.ncnn.param").string().c_str()) != 0 ||
            net_.load_model((options.freshness_model / "model.ncnn.bin").string().c_str()) != 0) {
            throw std::runtime_error("无法加载新鲜度NCNN模型");
        }
    }

    FreshnessPrediction predict(const cv::Mat &image, double &preprocess_ms) {
        const auto preprocess_started = Clock::now();
        cv::Mat rgb;
        cv::cvtColor(image, rgb, cv::COLOR_BGR2RGB);
        int resized_width;
        int resized_height;
        if (rgb.rows <= rgb.cols) {
            resized_height = 256;
            resized_width = std::max(256, cvRound(rgb.cols * 256.0 / rgb.rows));
        } else {
            resized_width = 256;
            resized_height = std::max(256, cvRound(rgb.rows * 256.0 / rgb.cols));
        }
        cv::Mat resized;
        cv::resize(rgb, resized, cv::Size(resized_width, resized_height));
        const int top = (resized_height - 224) / 2;
        const int left = (resized_width - 224) / 2;
        cv::Mat cropped = resized(cv::Rect(left, top, 224, 224));
        ncnn::Mat input = ncnn::Mat::from_pixels(cropped.data, ncnn::Mat::PIXEL_RGB, 224, 224);
        const float mean[3] = {0.485F * 255.0F, 0.456F * 255.0F, 0.406F * 255.0F};
        const float normalization[3] = {
            1.0F / (0.229F * 255.0F), 1.0F / (0.224F * 255.0F),
            1.0F / (0.225F * 255.0F)};
        input.substract_mean_normalize(mean, normalization);
        preprocess_ms = elapsed_ms(preprocess_started);

        const auto inference_started = Clock::now();
        ncnn::Extractor extractor = net_.create_extractor();
        if (extractor.input("in0", input) != 0) throw std::runtime_error("新鲜度NCNN输入失败");
        ncnn::Mat logits;
        if (extractor.extract("out0", logits) != 0) throw std::runtime_error("新鲜度NCNN推理失败");
        const double inference_ms = elapsed_ms(inference_started);
        if (logits.total() != 3) {
            throw std::runtime_error("新鲜度模型输出不是3个logit");
        }
        const float *values = logits;
        const float maximum = *std::max_element(values, values + 3);
        std::array<float, 3> probabilities{};
        float sum = 0.0F;
        for (int index = 0; index < 3; ++index) {
            probabilities[index] = std::exp(values[index] - maximum);
            sum += probabilities[index];
        }
        for (float &probability : probabilities) {
            probability /= sum;
        }
        const int best = static_cast<int>(std::distance(
            probabilities.begin(), std::max_element(probabilities.begin(), probabilities.end())));
        return {kFreshnessClasses[best], probabilities[best],
                probabilities[0] + 0.5F * probabilities[1], probabilities, inference_ms};
    }

private:
    ncnn::Net net_;
};

void check_sqlite(int code, sqlite3 *database, const std::string &operation) {
    if (code != SQLITE_OK && code != SQLITE_DONE && code != SQLITE_ROW) {
        throw std::runtime_error(operation + ": " + sqlite3_errmsg(database));
    }
}

class Repository {
public:
    explicit Repository(const fs::path &db_path) {
        check_sqlite(sqlite3_open(db_path.string().c_str(), &database_), database_, "打开数据库失败");
        sqlite3_busy_timeout(database_, 5000);
    }

    ~Repository() {
        if (database_ != nullptr) {
            sqlite3_close(database_);
        }
    }

    bool next_frame(Frame &frame) {
        const char *sql = "SELECT id,image_path FROM pending_frames WHERE status='pending' ORDER BY id LIMIT 1";
        sqlite3_stmt *statement = nullptr;
        check_sqlite(sqlite3_prepare_v2(database_, sql, -1, &statement, nullptr), database_, "查询待处理帧失败");
        const int result = sqlite3_step(statement);
        if (result == SQLITE_ROW) {
            frame.id = sqlite3_column_int64(statement, 0);
            frame.image_path = reinterpret_cast<const char *>(sqlite3_column_text(statement, 1));
            sqlite3_finalize(statement);
            return true;
        }
        sqlite3_finalize(statement);
        return false;
    }

    void save(long long frame_id, const std::vector<Recognition> &results) {
        execute("BEGIN IMMEDIATE");
        try {
            for (const auto &result : results) {
                const long long produce_id = resolve_produce(result.detection.species);
                insert_result(frame_id, produce_id, result);
            }
            sqlite3_stmt *statement = nullptr;
            const char *sql = "UPDATE pending_frames SET status=?,processed_at=datetime('now','localtime'),last_error=? WHERE id=?";
            check_sqlite(sqlite3_prepare_v2(database_, sql, -1, &statement, nullptr), database_, "更新帧状态失败");
            const std::string status = results.empty() ? "discarded" : "processed";
            const std::string message = results.empty() ? "未检测到支持的果蔬目标" : "";
            sqlite3_bind_text(statement, 1, status.c_str(), -1, SQLITE_TRANSIENT);
            sqlite3_bind_text(statement, 2, message.c_str(), -1, SQLITE_TRANSIENT);
            sqlite3_bind_int64(statement, 3, frame_id);
            check_sqlite(sqlite3_step(statement), database_, "更新帧状态失败");
            sqlite3_finalize(statement);
            execute("COMMIT");
        } catch (...) {
            execute("ROLLBACK");
            throw;
        }
    }

    void fail(long long frame_id, const std::string &error) {
        sqlite3_stmt *statement = nullptr;
        const char *sql = "UPDATE pending_frames SET attempt_count=attempt_count+1,last_error=?,"
                          "status=CASE WHEN attempt_count+1>=3 THEN 'discarded' ELSE 'pending' END WHERE id=?";
        check_sqlite(sqlite3_prepare_v2(database_, sql, -1, &statement, nullptr), database_, "记录失败状态失败");
        sqlite3_bind_text(statement, 1, error.substr(0, 500).c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_int64(statement, 2, frame_id);
        check_sqlite(sqlite3_step(statement), database_, "记录失败状态失败");
        sqlite3_finalize(statement);
    }

private:
    struct ProduceInfo {
        std::string name;
        std::string category;
        int shelf_life_days;
        std::string unit;
    };

    static ProduceInfo produce_info(const std::string &species) {
        const std::map<std::string, ProduceInfo> catalog = {
            {"apple", {"苹果", "水果", 14, "个"}},
            {"banana", {"香蕉", "水果", 7, "根"}},
            {"carrot", {"胡萝卜", "蔬菜", 14, "根"}},
            {"cucumber", {"黄瓜", "蔬菜", 7, "根"}},
            {"orange", {"橙子", "水果", 14, "个"}},
        };
        return catalog.at(species);
    }

    long long resolve_produce(const std::string &species) {
        const ProduceInfo info = produce_info(species);
        sqlite3_stmt *statement = nullptr;
        check_sqlite(sqlite3_prepare_v2(database_, "SELECT id FROM produce_info WHERE name=? AND category=? ORDER BY id LIMIT 1", -1, &statement, nullptr), database_, "查询果蔬失败");
        sqlite3_bind_text(statement, 1, info.name.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_text(statement, 2, info.category.c_str(), -1, SQLITE_TRANSIENT);
        if (sqlite3_step(statement) == SQLITE_ROW) {
            const long long id = sqlite3_column_int64(statement, 0);
            sqlite3_finalize(statement);
            return id;
        }
        sqlite3_finalize(statement);
        const char *sql = "INSERT INTO produce_info(name,category,shelf_life_days,unit,location) VALUES(?,?,?,?,'AI识别区')";
        check_sqlite(sqlite3_prepare_v2(database_, sql, -1, &statement, nullptr), database_, "创建果蔬失败");
        sqlite3_bind_text(statement, 1, info.name.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_text(statement, 2, info.category.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_int(statement, 3, info.shelf_life_days);
        sqlite3_bind_text(statement, 4, info.unit.c_str(), -1, SQLITE_TRANSIENT);
        check_sqlite(sqlite3_step(statement), database_, "创建果蔬失败");
        sqlite3_finalize(statement);
        return sqlite3_last_insert_rowid(database_);
    }

    void insert_result(long long frame_id, long long produce_id, const Recognition &result) {
        const std::string bbox = "{\"x1\":" + std::to_string(result.detection.box.x) +
            ",\"y1\":" + std::to_string(result.detection.box.y) +
            ",\"x2\":" + std::to_string(result.detection.box.x + result.detection.box.width) +
            ",\"y2\":" + std::to_string(result.detection.box.y + result.detection.box.height) +
            ",\"image_width\":" + std::to_string(result.image_width) +
            ",\"image_height\":" + std::to_string(result.image_height) + "}";
        const auto &p = result.freshness.probabilities;
        const std::string probabilities = "{\"fresh\":" + std::to_string(p[0]) +
            ",\"mild\":" + std::to_string(p[1]) + ",\"rotten\":" + std::to_string(p[2]) + "}";
        const char *sql = "INSERT INTO inventory_log(produce_id,action_type,quantity,freshness_level,"
                          "freshness_score,confidence,image_path,sync_status,source_frame_id,detector_label,"
                          "detector_confidence,freshness_confidence,bbox_json,freshness_probabilities_json,"
                          "inference_latency_ms,model_version) VALUES(?,'IN',1,?,?,?,?,'local',?,?,?,?,?,?,?,?)";
        sqlite3_stmt *statement = nullptr;
        check_sqlite(sqlite3_prepare_v2(database_, sql, -1, &statement, nullptr), database_, "写入识别结果失败");
        sqlite3_bind_int64(statement, 1, produce_id);
        sqlite3_bind_text(statement, 2, result.freshness.label.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_double(statement, 3, result.freshness.score);
        sqlite3_bind_double(statement, 4, result.freshness.confidence);
        sqlite3_bind_text(statement, 5, result.crop_path.string().c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_int64(statement, 6, frame_id);
        sqlite3_bind_text(statement, 7, result.detection.label.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_double(statement, 8, result.detection.confidence);
        sqlite3_bind_double(statement, 9, result.freshness.confidence);
        sqlite3_bind_text(statement, 10, bbox.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_text(statement, 11, probabilities.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_double(statement, 12, result.total_inference_ms);
        sqlite3_bind_text(statement, 13, "yolo-best+shufflenet-v4-cpp", -1, SQLITE_STATIC);
        check_sqlite(sqlite3_step(statement), database_, "写入识别结果失败");
        sqlite3_finalize(statement);
    }

    void execute(const char *sql) {
        char *error = nullptr;
        const int code = sqlite3_exec(database_, sql, nullptr, nullptr, &error);
        if (code != SQLITE_OK) {
            const std::string message = error == nullptr ? sqlite3_errmsg(database_) : error;
            sqlite3_free(error);
            throw std::runtime_error(message);
        }
    }

    sqlite3 *database_ = nullptr;
};

Options parse_options(int argc, char **argv) {
    Options options;
    for (int index = 1; index < argc; ++index) {
        const std::string key = argv[index];
        auto value = [&]() -> std::string {
            if (index + 1 >= argc) {
                throw std::runtime_error("缺少参数值: " + key);
            }
            return argv[++index];
        };
        if (key == "--db") options.db_path = value();
        else if (key == "--detector") options.detector_model = value();
        else if (key == "--freshness") options.freshness_model = value();
        else if (key == "--crop-dir") options.crop_dir = value();
        else if (key == "--confidence") options.confidence = std::stof(value());
        else if (key == "--iou") options.iou = std::stof(value());
        else if (key == "--size") options.image_size = std::stoi(value());
        else if (key == "--threads") options.threads = std::stoi(value());
        else if (key == "--poll-ms") options.poll_ms = std::stoi(value());
        else if (key == "--once") options.once = true;
        else throw std::runtime_error("未知参数: " + key);
    }
    return options;
}

cv::Rect padded_box(const cv::Rect &box, const cv::Size &image_size) {
    const int padding_x = cvRound(box.width * 0.05);
    const int padding_y = cvRound(box.height * 0.05);
    const int left = std::max(0, box.x - padding_x);
    const int top = std::max(0, box.y - padding_y);
    const int right = std::min(image_size.width, box.x + box.width + padding_x);
    const int bottom = std::min(image_size.height, box.y + box.height + padding_y);
    return {left, top, right - left, bottom - top};
}

int main(int argc, char **argv) {
    try {
        const Options options = parse_options(argc, argv);
        cv::setNumThreads(std::max(1, options.threads));
        fs::create_directories(options.crop_dir);
        const auto load_started = Clock::now();
        YoloDetector detector(options);
        FreshnessClassifier classifier(options);
        Repository repository(options.db_path);
        std::cout << "C++ AI服务启动，模型加载 " << elapsed_ms(load_started) << " ms\n";

        while (true) {
            Frame frame;
            if (!repository.next_frame(frame)) {
                if (options.once) break;
                std::this_thread::sleep_for(std::chrono::milliseconds(options.poll_ms));
                continue;
            }
            try {
                const auto total_started = Clock::now();
                const auto decode_started = Clock::now();
                cv::Mat image = cv::imread(frame.image_path, cv::IMREAD_COLOR);
                const double decode_ms = elapsed_ms(decode_started);
                if (image.empty()) throw std::runtime_error("图片无法读取: " + frame.image_path);

                double yolo_pre_ms = 0.0;
                double yolo_forward_ms = 0.0;
                double yolo_post_ms = 0.0;
                std::vector<Detection> detections = detector.detect(
                    image, yolo_pre_ms, yolo_forward_ms, yolo_post_ms);
                std::vector<Recognition> results;
                double classify_pre_ms = 0.0;
                double classify_forward_ms = 0.0;
                for (int index = 0; index < static_cast<int>(detections.size()); ++index) {
                    const cv::Rect crop_box = padded_box(detections[index].box, image.size());
                    if (crop_box.width < 16 || crop_box.height < 16) continue;
                    cv::Mat crop = image(crop_box).clone();
                    double preprocessing = 0.0;
                    FreshnessPrediction prediction = classifier.predict(crop, preprocessing);
                    classify_pre_ms += preprocessing;
                    classify_forward_ms += prediction.inference_ms;
                    const fs::path crop_path = options.crop_dir /
                        ("frame_" + std::to_string(frame.id) + "_target_" + std::to_string(index) +
                         "_" + detections[index].species + ".jpg");
                    if (!cv::imwrite(crop_path.string(), crop)) {
                        throw std::runtime_error("裁剪图保存失败: " + crop_path.string());
                    }
                    results.push_back({detections[index], prediction, crop_path, image.cols, image.rows,
                                       yolo_pre_ms + yolo_forward_ms + yolo_post_ms +
                                       preprocessing + prediction.inference_ms});
                }
                const auto db_started = Clock::now();
                repository.save(frame.id, results);
                const double db_ms = elapsed_ms(db_started);
                std::cout << "frame=" << frame.id << " targets=" << results.size()
                          << " decode=" << decode_ms
                          << " yolo_pre=" << yolo_pre_ms
                          << " yolo_forward=" << yolo_forward_ms
                          << " yolo_post=" << yolo_post_ms
                          << " cls_pre=" << classify_pre_ms
                          << " cls_forward=" << classify_forward_ms
                          << " db=" << db_ms
                          << " total=" << elapsed_ms(total_started) << " ms\n";
            } catch (const std::exception &error) {
                repository.fail(frame.id, error.what());
                std::cerr << "frame=" << frame.id << " 处理失败: " << error.what() << '\n';
            }
            if (options.once) break;
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "AI服务启动失败: " << error.what() << '\n';
        return 1;
    }
}
