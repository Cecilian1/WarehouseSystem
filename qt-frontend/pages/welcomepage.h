#ifndef WELCOMEPAGE_H
#define WELCOMEPAGE_H

#include <QWidget>

class QKeyEvent;
class QMouseEvent;
class QPaintEvent;

// 开机欢迎页：整屏均可触摸，触摸或按 Enter/Space 后进入主业务界面。
class WelcomePage : public QWidget
{
    Q_OBJECT
public:
    explicit WelcomePage(QWidget *parent = nullptr);

signals:
    void continueRequested();

protected:
    void paintEvent(QPaintEvent *event) override;
    void mousePressEvent(QMouseEvent *event) override;
    void keyPressEvent(QKeyEvent *event) override;
};

#endif // WELCOMEPAGE_H
