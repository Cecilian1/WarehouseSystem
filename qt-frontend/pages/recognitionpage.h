#ifndef RECOGNITIONPAGE_H
#define RECOGNITIONPAGE_H

#include <QWidget>

class QLabel;

// 实时识别页：本次任务不实现AI推理，只做两件事：
// 1. 展示pending_frames表最新一条记录的image_path静态图（模拟"摄像头画面"）
// 2. 展示mock识别结果占位文本，根据pending_frames.status切换展示状态
//
// 预留信号recognitionResultAvailable，当前没有任何代码触发它；
// 未来AI服务模块接入时，只需要决定"谁来emit这个信号"（例如新增一个
// 轮询pending_frames.status变化的组件），不需要改动本页面的槽函数逻辑。
class RecognitionPage : public QWidget
{
    Q_OBJECT
public:
    explicit RecognitionPage(QWidget *parent = nullptr);

public slots:
    // 连接到PollingTimer::dataMayHaveChanged，查询pending_frames最新一条并刷新展示
    void refresh();

    // TODO(AI服务模块): 未来由AI推理结果驱动的槽函数，当前无调用方。
    void onRecognitionResultAvailable(int frameId, const QString &category, float confidence);

signals:
    // TODO(AI服务模块): 预留信号，当前无代码emit。
    void recognitionResultAvailable(int frameId, const QString &category, float confidence);

private:
    QLabel *m_imageLabel;
    QLabel *m_statusLabel;
};

#endif // RECOGNITIONPAGE_H
