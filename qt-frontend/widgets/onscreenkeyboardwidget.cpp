#include "onscreenkeyboardwidget.h"

#include <QGridLayout>
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
            const QString ch(QChar(*p));
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
