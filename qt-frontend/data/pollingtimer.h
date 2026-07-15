#ifndef POLLINGTIMER_H
#define POLLINGTIMER_H

#include <QObject>
#include <QTimer>

// 用QTimer轮询增量数据，替代docx里提到的WebSocket实时推送方案。
// 本次任务不引入WebSocket服务；这个类是未来若要换成真正的事件推送时
// 唯一需要替换的隔离点——各页面只依赖 dataMayHaveChanged() 信号，
// 不关心信号是轮询触发还是推送触发。
class PollingTimer : public QObject
{
    Q_OBJECT
public:
    explicit PollingTimer(int intervalMs, QObject *parent = nullptr);

    void start();
    void stop();

signals:
    // 每个轮询周期触发一次，各页面/模型收到后自行查询表判断是否有新增数据
    void dataMayHaveChanged();

private:
    QTimer m_timer;
};

#endif // POLLINGTIMER_H
