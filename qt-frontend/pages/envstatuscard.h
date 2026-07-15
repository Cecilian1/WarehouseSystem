#ifndef ENVSTATUSCARD_H
#define ENVSTATUSCARD_H

#include <QWidget>

class EnvLogModel;
class QLabel;

// 环境状态卡片：实时显示冰箱内温度、湿度数值及设备运行状态（正常/异常），
// 异常时高亮提示。作为MainWindow顶部常驻组件，而非可切换的独立页面
// （docx描述为"实时显示"，常驻更贴合语义）。
class EnvStatusCard : public QWidget
{
    Q_OBJECT
public:
    explicit EnvStatusCard(QWidget *parent = nullptr);

public slots:
    // 连接到PollingTimer::dataMayHaveChanged
    void refresh();

private:
    EnvLogModel *m_model;
    QLabel *m_tempLabel;
    QLabel *m_humidityLabel;
    QLabel *m_statusLabel;
};

#endif // ENVSTATUSCARD_H
