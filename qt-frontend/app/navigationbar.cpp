#include "navigationbar.h"

#include <QHBoxLayout>
#include <QPushButton>
#include <QSizePolicy>

NavigationBar::NavigationBar(QWidget *parent)
    : QWidget(parent)
{
    // Keep the navigation inside the fixed 600 px framebuffer even when the
    // current page adds controls with a larger size hint.
    setFixedHeight(56);
    setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);

    const QStringList labels = {
        QStringLiteral("库存看板"),
        QStringLiteral("实时识别"),
        QStringLiteral("信息录入"),
        QStringLiteral("历史记录"),
        QStringLiteral("预警提醒"),
    };

    auto *layout = new QHBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->setSpacing(6);
    for (int i = 0; i < labels.size(); ++i) {
        auto *btn = new QPushButton(labels.at(i), this);
        btn->setFixedHeight(56);  // 触摸友好的按钮高度
        connect(btn, &QPushButton::clicked, this, [this, i]() { emit pageRequested(i); });
        layout->addWidget(btn);
    }
}
