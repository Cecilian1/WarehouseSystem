#include "recognitionpage.h"

#include <QDateTime>
#include <QFileInfo>
#include <QLabel>
#include <QPixmap>
#include <QSettings>
#include <QVBoxLayout>

RecognitionPage::RecognitionPage(QWidget *parent)
    : QWidget(parent), m_imageLabel(new QLabel(this)), m_statusLabel(new QLabel(this))
{
    m_imageLabel->setAlignment(Qt::AlignCenter);
    m_imageLabel->setMinimumHeight(320);
    m_imageLabel->setText(QStringLiteral("暂无摄像头画面"));
    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setText(QStringLiteral("等待摄像头采集"));
    auto *layout = new QVBoxLayout(this);
    layout->addWidget(m_imageLabel, 1);
    layout->addWidget(m_statusLabel);
    refresh();
}

void RecognitionPage::refresh()
{
    QSettings settings(QStringLiteral("config/frontend.ini"), QSettings::IniFormat);
    const QString imagePath = settings.value(
        QStringLiteral("camera/latest_frame_path"),
        QStringLiteral("/data/warehousekeeper/frames/latest.jpg")).toString();
    const QFileInfo imageFile(imagePath);
    const QPixmap pixmap(imagePath);
    if (!pixmap.isNull()) {
        m_imageLabel->setPixmap(pixmap.scaled(
            m_imageLabel->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation));
        m_statusLabel->setText(QStringLiteral("摄像头当前画面 · 最近采集：%1")
            .arg(imageFile.lastModified().toString(QStringLiteral("yyyy-MM-dd HH:mm:ss"))));
    } else {
        m_imageLabel->setText(QStringLiteral("暂无摄像头画面: %1").arg(imagePath));
        m_statusLabel->setText(QStringLiteral("请检查 camera-service 是否正常运行"));
    }
}

void RecognitionPage::onRecognitionResultAvailable(int frameId, const QString &category, float confidence)
{
    Q_UNUSED(frameId);
    Q_UNUSED(category);
    Q_UNUSED(confidence);
}
