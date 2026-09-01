#include "onscreenkeyboardwidget.h"

#include <QGridLayout>
#include <QGuiApplication>
#include <QInputMethod>
#include <QLineEdit>
#include <QPushButton>
#include <QSizePolicy>

namespace {
// 简化的数字+字母布局；果蔬名称多为中文，实际中文录入建议仍走系统输入法
// (若板端已配置)，本键盘主要覆盖数字/字母/常用符号的手动录入场景。
const char *kRows[] = {
    "1234567890",
    "QWERTYUIOP",
    "ASDFGHJKL",
    "ZXCVBNM",
};
}

OnScreenKeyboardWidget::OnScreenKeyboardWidget(QWidget *parent)
    : QWidget(parent)
{
    buildLayout();
}

void OnScreenKeyboardWidget::attachTarget(QLineEdit *target)
{
    m_target = target;
}

void OnScreenKeyboardWidget::buildLayout()
{
    auto *layout = new QGridLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->setSpacing(2);
    for (int column = 0; column < 10; ++column)
        layout->setColumnStretch(column, 1);

    const auto configureKey = [](QPushButton *button) {
        // 信息录入页右侧只有约 400px 宽。Ignored 允许十列按实际宽度收缩，
        // 避免 QScrollArea 产生横向滚动条而把前半键裁掉。
        button->setMinimumHeight(34);
        button->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Fixed);
        button->setFocusPolicy(Qt::NoFocus);
    };

    int row = 0;
    for (const char *rowChars : kRows) {
        int col = 0;
        for (const char *p = rowChars; *p; ++p) {
            const QString ch{QChar(*p)};
            auto *btn = new QPushButton(ch, this);
            configureKey(btn);
            connect(btn, &QPushButton::clicked, this, [this, ch]() { appendChar(ch); });
            layout->addWidget(btn, row, col);
            ++col;
        }
        ++row;
    }

    auto *spaceBtn = new QPushButton(QStringLiteral("空格"), this);
    configureKey(spaceBtn);
    connect(spaceBtn, &QPushButton::clicked, this, [this]() { appendChar(QStringLiteral(" ")); });
    layout->addWidget(spaceBtn, row, 0, 1, 4);

    auto *backspaceBtn = new QPushButton(QStringLiteral("退格"), this);
    configureKey(backspaceBtn);
    connect(backspaceBtn, &QPushButton::clicked, this, &OnScreenKeyboardWidget::backspace);
    layout->addWidget(backspaceBtn, row, 4, 1, 4);

    auto *chineseInputBtn = new QPushButton(QStringLiteral("中文键盘"), this);
    configureKey(chineseInputBtn);
    chineseInputBtn->setToolTip(QStringLiteral("使用系统拼音输入法输入中文"));
    connect(chineseInputBtn, &QPushButton::clicked,
            this, &OnScreenKeyboardWidget::showSystemInputMethod);
    layout->addWidget(chineseInputBtn, row, 8, 1, 2);
}

void OnScreenKeyboardWidget::appendChar(const QString &ch)
{
    if (m_target)
        m_target->insert(ch);
}

void OnScreenKeyboardWidget::backspace()
{
    if (!m_target)
        return;
    m_target->backspace();
}

void OnScreenKeyboardWidget::showSystemInputMethod()
{
    if (!m_target)
        return;

    // 点击自绘按键后焦点会落在按钮上；先恢复到文本框，否则输入法的候选字会
    // 没有接收目标。QInputMethod 会使用板端实际安装的输入法插件。
    m_target->setFocus(Qt::OtherFocusReason);
    m_target->setAttribute(Qt::WA_InputMethodEnabled, true);
    QGuiApplication::inputMethod()->update(Qt::ImQueryAll);
    QGuiApplication::inputMethod()->show();
}
