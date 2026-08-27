#include "recognitionpage.h"

#include "../data/databasemanager.h"

#include <QLabel>
#include <QPixmap>
#include <QSqlError>
#include <QSqlQuery>
#include <QVBoxLayout>
#include <QVariant>

RecognitionPage::RecognitionPage(QWidget *parent)
    : QWidget(parent)
    , m_imageLabel(new QLabel(this))
    , m_statusLabel(new QLabel(this))
{
    m_imageLabel->setAlignment(Qt::AlignCenter);
    m_imageLabel->setMinimumHeight(320);
    m_imageLabel->setText(QStringLiteral("暂无采集画面"));

    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setText(QStringLiteral("等待AI识别服务接入"));

    auto *layout = new QVBoxLayout(this);
    layout->addWidget(m_imageLabel, 1);
    layout->addWidget(m_statusLabel);

    refresh();
}

void RecognitionPage::refresh()
{
    const QString latestFramePath = QStringLiteral("/data/warehousekeeper/frames/latest.jpg");
    const auto displayImage = [this](const QString &imagePath) {
        QPixmap pixmap(imagePath);
        if (pixmap.isNull()) {
            return false;
        }
        m_imageLabel->setPixmap(
            pixmap.scaled(m_imageLabel->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation));
        return true;
    };

    QSqlQuery recognitionQuery(DatabaseManager::database());
    recognitionQuery.prepare(
        "SELECT l.id, COALESCE(p.name, '未知果蔬'), l.freshness_level, "
        "       l.confidence, l.image_path, l.created_at "
        "FROM inventory_log l "
        "LEFT JOIN produce_info p ON p.id = l.produce_id "
        "ORDER BY datetime(l.created_at) DESC, l.id DESC LIMIT 1");

    if (!recognitionQuery.exec()) {
        qWarning("RecognitionPage::refresh 查询识别记录失败: %s", qPrintable(recognitionQuery.lastError().text()));
        return;
    }

    if (recognitionQuery.next()) {
        if (!displayImage(latestFramePath)
            && !displayImage(recognitionQuery.value(4).toString())) {
            m_imageLabel->setText(QStringLiteral("实时画面暂不可用"));
        }

        const QString freshness = recognitionQuery.value(2).toString().isEmpty()
            ? QStringLiteral("未标注")
            : recognitionQuery.value(2).toString();
        m_statusLabel->setText(
            QStringLiteral("最新识别：%1｜新鲜度：%2｜置信度：%3｜时间：%4")
                .arg(recognitionQuery.value(1).toString(), freshness)
                .arg(recognitionQuery.value(3).toDouble(), 0, 'f', 2)
                .arg(recognitionQuery.value(5).toString()));
        return;
    }

    QSqlQuery frameQuery(DatabaseManager::database());
    frameQuery.prepare(
        "SELECT image_path, status FROM pending_frames ORDER BY id DESC LIMIT 1");
    if (!frameQuery.exec()) {
        qWarning("RecognitionPage::refresh 查询待处理帧失败: %s", qPrintable(frameQuery.lastError().text()));
        return;
    }

    if (!frameQuery.next()) {
        m_imageLabel->setText(QStringLiteral("暂无采集画面"));
        m_statusLabel->setText(QStringLiteral("等待摄像头采集与AI识别"));
        return;
    }

    const QString status = frameQuery.value(1).toString();

    if (!displayImage(latestFramePath)
        && !displayImage(frameQuery.value(0).toString())) {
        m_imageLabel->setText(QStringLiteral("实时画面暂不可用"));
    }

    if (status == QStringLiteral("processed")) {
        m_statusLabel->setText(QStringLiteral("该帧已处理，但尚未写入可展示的识别结果"));
    } else {
        m_statusLabel->setText(QStringLiteral("等待AI识别（当前状态: %1）").arg(status));
    }
}

void RecognitionPage::onRecognitionResultAvailable(int frameId, const QString &category, float confidence)
{
    // TODO(AI服务模块): 当前无调用方触发本槽函数。接入后应在此更新m_statusLabel
    // 展示真实类别与置信度，例如:
    //   m_statusLabel->setText(QString("frame#%1 识别为%2，置信度%3")
    //       .arg(frameId).arg(category).arg(confidence));
    Q_UNUSED(frameId);
    Q_UNUSED(category);
    Q_UNUSED(confidence);
}
