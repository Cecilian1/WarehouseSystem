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

    connect(this, &RecognitionPage::recognitionResultAvailable,
            this, &RecognitionPage::onRecognitionResultAvailable);

    refresh();
}

void RecognitionPage::refresh()
{
    QSqlQuery query(DatabaseManager::database());
    query.prepare(
        "SELECT image_path, status, change_ratio FROM pending_frames "
        "ORDER BY id DESC LIMIT 1");

    if (!query.exec()) {
        qWarning("RecognitionPage::refresh 查询失败: %s", qPrintable(query.lastError().text()));
        return;
    }

    if (!query.next()) {
        m_imageLabel->setText(QStringLiteral("暂无采集画面"));
        m_statusLabel->setText(QStringLiteral("等待AI识别服务接入"));
        return;
    }

    const QString imagePath = query.value(0).toString();
    const QString status = query.value(1).toString();

    QPixmap pixmap(imagePath);
    if (!pixmap.isNull()) {
        m_imageLabel->setPixmap(pixmap.scaled(m_imageLabel->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation));
    } else {
        m_imageLabel->setText(QStringLiteral("图片加载失败: %1").arg(imagePath));
    }

    if (status == QStringLiteral("processed")) {
        m_statusLabel->setText(QStringLiteral("已处理（等待AI服务模块提供具体结果）"));
    } else {
        m_statusLabel->setText(QStringLiteral("等待AI识别服务接入（当前状态: %1）").arg(status));
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
