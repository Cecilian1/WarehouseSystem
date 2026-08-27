#ifndef ONSCREENKEYBOARDWIDGET_H
#define ONSCREENKEYBOARDWIDGET_H

#include <QWidget>

class QLineEdit;

// 虚拟键盘兜底方案：纯QWidget网格按钮矩阵，点击时向绑定的QLineEdit插入字符。
//
// 首选方案是Qt Virtual Keyboard模块（若交叉工具链已包含该模块，可用
// QQuickView形式的InputPanel嵌入本Widgets应用，届时可用该模块替代本类，
// 不需要改动ProduceInfoPage等调用方的接口）。
// 本类作为不依赖额外模块的兜底实现：无联想输入/无多语言输入法能力，
// 但满足果蔬名称/数量等简短字段的手动录入需求。
class OnScreenKeyboardWidget : public QWidget
{
    Q_OBJECT
public:
    explicit OnScreenKeyboardWidget(QWidget *parent = nullptr);

    // 将键盘输出绑定到指定的输入框；传nullptr表示解绑（键盘输入被忽略）
    void attachTarget(QLineEdit *target);

private:
    void buildLayout();
    void appendChar(const QString &ch);
    void backspace();

    QLineEdit *m_target = nullptr;
};

#endif // ONSCREENKEYBOARDWIDGET_H
