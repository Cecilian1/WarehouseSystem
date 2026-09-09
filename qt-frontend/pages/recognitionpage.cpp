#include "recognitionpage.h"

#include "../data/databasemanager.h"

#include <QDateTime>
#include <QFileInfo>
#include <QHBoxLayout>
#include <QLabel>
#include <QPixmap>
#include <QPushButton>
#include <QSettings>
#include <QSizePolicy>
#include <QSqlError>
#include <QSqlQuery>
#include <QStringList>
#include <QVBoxLayout>

RecognitionPage::RecognitionPage(QWidget *parent)
    : QWidget(parent)
    , m_imageLabel(new QLabel(this))
    , m_statusLabel(new QLabel(this))
    , m_doorStatusLabel(new QLabel(this))
    , m_doorButton(new QPushButton(this))
{
    m_imageLabel->setAlignment(Qt::AlignCenter);
    // The 7-inch display is only 600 px high. Do not give the preview a large
    // minimum height: the top status card, door controls and bottom navigation
    // must always remain visible. The preview receives all remaining space.
    m_imageLabel->setMinimumHeight(0);
    m_imageLabel->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Expanding);
    m_imageLabel->setText(QStringLiteral("暂无摄像头画面"));
    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setText(QStringLiteral("等待摄像头采集"));
    m_doorStatusLabel->setAlignment(Qt::AlignCenter);
    m_doorStatusLabel->setWordWrap(true);
    m_doorStatusLabel->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
    m_doorButton->setMinimumSize(220, 44);
    m_doorButton->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    connect(m_doorButton, &QPushButton::clicked,
            this, &RecognitionPage::onDoorButtonClicked);

    auto *doorLayout = new QHBoxLayout();
    doorLayout->setContentsMargins(0, 0, 0, 0);
    doorLayout->setSpacing(8);
    doorLayout->addWidget(m_doorStatusLabel, 1);
    doorLayout->addWidget(m_doorButton, 0, Qt::AlignVCenter);

    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(8, 4, 8, 4);
    layout->setSpacing(4);
    layout->addWidget(m_imageLabel, 1);
    layout->addWidget(m_statusLabel);
    layout->addLayout(doorLayout);
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

    QSqlQuery activeQuery(DatabaseManager::database());
    activeQuery.prepare(
        "SELECT id, status, frame_id, retry_count, last_error, is_baseline "
        "FROM door_cycle "
        "WHERE status NOT IN ('completed', 'failed') "
        "ORDER BY id DESC LIMIT 1");
    if (activeQuery.exec() && activeQuery.next()) {
        const QString status = activeQuery.value(1).toString();
        if (status == QStringLiteral("open")) {
            m_doorButton->setText(QStringLiteral("关闭冰箱门并盘点"));
            m_doorButton->setEnabled(true);
            m_doorStatusLabel->setText(QStringLiteral("冰箱门已开启，板载 LED 已点亮；完成取放后请关门"));
        } else {
            m_doorButton->setEnabled(false);
            if (status == QStringLiteral("open_requested")) {
                m_doorButton->setText(QStringLiteral("正在开启冰箱门…"));
                m_doorStatusLabel->setText(QStringLiteral("正在等待 camera-service 点亮板载 LED"));
            } else if (status == QStringLiteral("recapture_requested")) {
                m_doorButton->setText(QStringLiteral("正在自动复拍…"));
                m_doorStatusLabel->setText(QStringLiteral("本次未识别到物品，正在执行空箱保护复拍"));
            } else if (status == QStringLiteral("capturing") || status == QStringLiteral("close_requested")) {
                m_doorButton->setText(QStringLiteral("正在拍照…"));
                m_doorStatusLabel->setText(QStringLiteral("冰箱门已关闭，板载 LED 已熄灭，正在采集画面"));
            } else {
                m_doorButton->setText(QStringLiteral("正在识别…"));
                m_doorStatusLabel->setText(QStringLiteral("边缘 AI 正在识别并计算出入库差量"));
            }
        }
        return;
    }

    m_doorButton->setText(QStringLiteral("开启冰箱门"));
    m_doorButton->setEnabled(true);

    QSqlQuery latestQuery(DatabaseManager::database());
    latestQuery.prepare(
        "SELECT id, status, frame_id, is_baseline, last_error "
        "FROM door_cycle ORDER BY id DESC LIMIT 1");
    if (!latestQuery.exec() || !latestQuery.next()) {
        m_doorStatusLabel->setText(QStringLiteral("尚未进行冰箱盘点"));
        return;
    }
    const QString latestStatus = latestQuery.value(1).toString();
    if (latestStatus == QStringLiteral("failed")) {
        m_doorStatusLabel->setText(
            QStringLiteral("上次盘点失败：%1").arg(latestQuery.value(4).toString()));
        return;
    }
    if (latestQuery.value(3).toInt() != 0) {
        m_doorStatusLabel->setText(QStringLiteral("首次盘点完成：库存基线已建立，未生成出入库流水"));
        return;
    }

    const qlonglong frameId = latestQuery.value(2).toLongLong();
    QSqlQuery movementQuery(DatabaseManager::database());
    movementQuery.prepare(
        "SELECT COALESCE(p.name, '未知果蔬'), l.action_type, l.quantity "
        "FROM inventory_log l LEFT JOIN produce_info p ON p.id=l.produce_id "
        "WHERE l.source_frame_id=:frameId AND COALESCE(l.bbox_json, '')='' "
        "ORDER BY l.id");
    movementQuery.bindValue(":frameId", frameId);
    QStringList movements;
    if (movementQuery.exec()) {
        while (movementQuery.next()) {
            const QString action = movementQuery.value(1).toString() == QStringLiteral("IN")
                ? QStringLiteral("入库") : QStringLiteral("出库");
            movements << QStringLiteral("%1 %2 %3")
                .arg(movementQuery.value(0).toString(), action, movementQuery.value(2).toString());
        }
    }
    m_doorStatusLabel->setText(movements.isEmpty()
        ? QStringLiteral("本次盘点完成：库存无变化")
        : QStringLiteral("本次盘点完成：%1").arg(movements.join(QStringLiteral("；"))));
}

void RecognitionPage::onDoorButtonClicked()
{
    QSqlDatabase database = DatabaseManager::database();
    QSqlQuery transaction(database);
    if (!transaction.exec("BEGIN IMMEDIATE")) {
        m_doorStatusLabel->setText(
            QStringLiteral("锁定门状态失败：%1").arg(transaction.lastError().text()));
        return;
    }

    QString errorMessage;
    QSqlQuery query(database);
    query.prepare(
        "SELECT id, status FROM door_cycle "
        "WHERE status NOT IN ('completed', 'failed') ORDER BY id DESC LIMIT 1");
    if (!query.exec()) {
        errorMessage = QStringLiteral("读取门状态失败：%1").arg(query.lastError().text());
    } else if (!query.next()) {
        QSqlQuery insert(database);
        if (!insert.exec(
                "INSERT INTO door_cycle(status, opened_at) "
                "VALUES('open_requested', datetime('now', 'localtime'))")) {
            errorMessage = QStringLiteral("提交开门请求失败：%1").arg(insert.lastError().text());
        }
    } else if (query.value(1).toString() == QStringLiteral("open")) {
        QSqlQuery close(database);
        close.prepare(
            "UPDATE door_cycle SET status='close_requested', "
            "close_requested_at=datetime('now', 'localtime'), last_error='' "
            "WHERE id=:id AND status='open'");
        close.bindValue(":id", query.value(0));
        if (!close.exec()) {
            errorMessage = QStringLiteral("提交关门请求失败：%1").arg(close.lastError().text());
        }
    }

    QSqlQuery finish(database);
    if (!errorMessage.isEmpty()) {
        finish.exec(QStringLiteral("ROLLBACK"));
        m_doorStatusLabel->setText(errorMessage);
        return;
    }
    if (!finish.exec(QStringLiteral("COMMIT"))) {
        const QString commitError = finish.lastError().text();
        finish.exec(QStringLiteral("ROLLBACK"));
        m_doorStatusLabel->setText(
            QStringLiteral("保存门状态失败：%1").arg(commitError));
        return;
    }
    refresh();
}

void RecognitionPage::onRecognitionResultAvailable(int frameId, const QString &category, float confidence)
{
    Q_UNUSED(frameId);
    Q_UNUSED(category);
    Q_UNUSED(confidence);
}
