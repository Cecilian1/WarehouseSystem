#include "navigationbar.h"

#include <QHBoxLayout>
#include <QPushButton>

NavigationBar::NavigationBar(QWidget *parent)
    : QWidget(parent)
{
    const QStringList labels = {
        QStringLiteral("库存看板"),
        QStringLiteral("实时识别"),
        QStringLiteral("信息录入"),
        QStringLiteral("历史记录"),
        QStringLiteral("预警提醒"),
    };

    auto *layout = new QHBoxLayout(this);
    for (int i = 0; i < labels.size(); ++i) {
        auto *btn = new QPushButton(labels.at(i), this);
        btn->setMinimumHeight(56);  // 触摸友好的按钮高度
        connect(btn, &QPushButton::clicked, this, [this, i]() { emit pageRequested(i); });
        layout->addWidget(btn);
    }
}
