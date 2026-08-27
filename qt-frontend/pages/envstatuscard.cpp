#include "envstatuscard.h"

#include "../data/models/envlogmodel.h"

#include <QHBoxLayout>
#include <QLabel>

EnvStatusCard::EnvStatusCard(QWidget *parent)
    : QWidget(parent)
    , m_model(new EnvLogModel(this))
    , m_tempLabel(new QLabel(this))
    , m_humidityLabel(new QLabel(this))
    , m_statusLabel(new QLabel(this))
{
    m_tempLabel->setText(QStringLiteral("温度: --"));
    m_humidityLabel->setText(QStringLiteral("湿度: --"));
    m_statusLabel->setText(QStringLiteral("状态: --"));

    auto *layout = new QHBoxLayout(this);
    layout->addWidget(m_tempLabel);
    layout->addWidget(m_humidityLabel);
    layout->addWidget(m_statusLabel);
    layout->addStretch();

    refresh();
}

void EnvStatusCard::refresh()
{
    const EnvLatestReading reading = m_model->fetchLatest();

    if (!reading.valid) {
        m_tempLabel->setText(QStringLiteral("温度: 暂无数据"));
        m_humidityLabel->setText(QStringLiteral("湿度: 暂无数据"));
        m_statusLabel->setText(QStringLiteral("状态: 暂无数据"));
        return;
    }

    m_tempLabel->setText(QStringLiteral("温度: %1℃").arg(reading.temperature, 0, 'f', 1));
    m_humidityLabel->setText(QStringLiteral("湿度: %1%RH").arg(reading.humidity, 0, 'f', 1));

    if (reading.isAbnormal) {
        m_statusLabel->setText(QStringLiteral("状态: 异常"));
        m_statusLabel->setStyleSheet(QStringLiteral("color: white; background-color: #d9534f; padding: 2px 8px;"));
    } else {
        m_statusLabel->setText(QStringLiteral("状态: 正常"));
        m_statusLabel->setStyleSheet(QStringLiteral("color: white; background-color: #5cb85c; padding: 2px 8px;"));
    }
}
