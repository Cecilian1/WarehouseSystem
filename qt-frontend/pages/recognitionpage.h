#ifndef RECOGNITIONPAGE_H
#define RECOGNITIONPAGE_H

#include <QWidget>

class QLabel;

// 实时识别页：优先展示 C++ AI 服务写入 inventory_log 的最新识别结果；
// 在尚未产生识别记录时，回退展示最新待处理帧的状态。
class RecognitionPage : public QWidget
{
    Q_OBJECT
public:
    explicit RecognitionPage(QWidget *parent = nullptr);

public slots:
    // 连接到PollingTimer::dataMayHaveChanged，轮询最新识别记录和待处理帧。
    void refresh();

    // 供未来推送式识别结果接入使用；当前由 refresh() 轮询数据库。
    void onRecognitionResultAvailable(int frameId, const QString &category, float confidence);

private:
    QLabel *m_imageLabel;
    QLabel *m_statusLabel;
};

#endif // RECOGNITIONPAGE_H
