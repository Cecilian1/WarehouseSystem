#ifndef NAVIGATIONBAR_H
#define NAVIGATIONBAR_H

#include <QWidget>

// 5个页面切换按钮的导航栏（环境状态卡片常驻显示，不算导航项）。
class NavigationBar : public QWidget
{
    Q_OBJECT
public:
    explicit NavigationBar(QWidget *parent = nullptr);

signals:
    void pageRequested(int pageIndex);
};

#endif // NAVIGATIONBAR_H
