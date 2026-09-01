#include "onscreenkeyboardwidget.h"

#include <QGridLayout>
#include <QGuiApplication>
#include <QInputMethod>
#include <QLineEdit>
#include <QPushButton>

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
    layout->setSpacing(4);

    int row = 0;
    for (const char *rowChars : kRows) {
        int col = 0;
        for (const char *p = rowChars; *p; ++p) {
            const QString ch{QChar(*p)};
            auto *btn = new QPushButton(ch, this);
            btn->setMinimumSize(48, 48);
            connect(btn, &QPushButton::clicked, this, [this, ch]() { appendChar(ch); });
            layout->addWidget(btn, row, col);
            ++col;
        }
        ++row;
    }

    auto *spaceBtn = new QPushButton(QStringLiteral("空格"), this);
    spaceBtn->setMinimumSize(120, 48);
    connect(spaceBtn, &QPushButton::clicked, this, [this]() { appendChar(QStringLiteral(" ")); });
    layout->addWidget(spaceBtn, row, 0, 1, 4);

    auto *backspaceBtn = new QPushButton(QStringLiteral("退格"), this);
    backspaceBtn->setMinimumSize(120, 48);
    connect(backspaceBtn, &QPushButton::clicked, this, &OnScreenKeyboardWidget::backspace);
    layout->addWidget(backspaceBtn, row, 4, 1, 4);

    auto *chineseInputBtn = new QPushButton(QStringLiteral("中文输入"), this);
    chineseInputBtn->setMinimumSize(120, 48);
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
    QGuiApplication::inputMethod()->show();
}
