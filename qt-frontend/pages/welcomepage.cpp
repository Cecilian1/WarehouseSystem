#include "welcomepage.h"

#include <QColor>
#include <QFont>
#include <QKeyEvent>
#include <QLabel>
#include <QLinearGradient>
#include <QList>
#include <QMouseEvent>
#include <QPainter>
#include <QVBoxLayout>

WelcomePage::WelcomePage(QWidget *parent)
    : QWidget(parent)
{
    // linuxfb 无窗口合成器，明确保证本页每次刷新都会覆盖 framebuffer 的
    // 全部像素，避免上一界面的内容透出或残留。
    setAttribute(Qt::WA_OpaquePaintEvent, true);
    setFocusPolicy(Qt::StrongFocus);
    setAccessibleName(QStringLiteral("芯鲜管家欢迎界面，轻触任意位置进入"));

    auto *eyebrow = new QLabel(QStringLiteral("ATK-DL2K0300 · 智慧冷藏终端"), this);
    eyebrow->setObjectName(QStringLiteral("welcomeEyebrow"));
    eyebrow->setAlignment(Qt::AlignCenter);

    auto *title = new QLabel(QStringLiteral("芯鲜管家"), this);
    title->setObjectName(QStringLiteral("welcomeTitle"));
    title->setAlignment(Qt::AlignCenter);

    auto *subtitle = new QLabel(QStringLiteral("果蔬识别 · 库存管理 · 环境监测"), this);
    subtitle->setObjectName(QStringLiteral("welcomeSubtitle"));
    subtitle->setAlignment(Qt::AlignCenter);

    auto *prompt = new QLabel(QStringLiteral("轻触屏幕任意位置进入"), this);
    prompt->setObjectName(QStringLiteral("welcomePrompt"));
    prompt->setAlignment(Qt::AlignCenter);
    prompt->setMinimumSize(300, 58);
    prompt->setMaximumWidth(360);

    const QList<QWidget *> passiveWidgets{eyebrow, title, subtitle, prompt};
    for (QWidget *widget : passiveWidgets)
        widget->setAttribute(Qt::WA_TransparentForMouseEvents);

    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(48, 42, 48, 42);
    layout->addStretch(3);
    layout->addWidget(eyebrow, 0, Qt::AlignHCenter);
    layout->addSpacing(18);
    layout->addWidget(title, 0, Qt::AlignHCenter);
    layout->addSpacing(14);
    layout->addWidget(subtitle, 0, Qt::AlignHCenter);
    layout->addStretch(2);
    layout->addWidget(prompt, 0, Qt::AlignHCenter);
    layout->addStretch(1);

    setStyleSheet(QStringLiteral(R"(
        QLabel#welcomeEyebrow {
            color: #90CAF9;
            font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Microsoft YaHei";
            font-size: 17px;
            font-weight: 600;
        }
        QLabel#welcomeTitle {
            color: #FFFFFF;
            font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Microsoft YaHei";
            font-size: 54px;
            font-weight: 700;
        }
        QLabel#welcomeSubtitle {
            color: #D7E9FA;
            font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Microsoft YaHei";
            font-size: 22px;
        }
        QLabel#welcomePrompt {
            color: #0D47A1;
            background-color: #F7FBFF;
            border: 2px solid #90CAF9;
            border-radius: 29px;
            font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Microsoft YaHei";
            font-size: 20px;
            font-weight: 600;
            padding: 0 28px;
        }
    )"));
}

void WelcomePage::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event)

    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, true);

    QLinearGradient background(0, 0, width(), height());
    background.setColorAt(0.0, QColor(QStringLiteral("#0B3C6F")));
    background.setColorAt(0.55, QColor(QStringLiteral("#1565C0")));
    background.setColorAt(1.0, QColor(QStringLiteral("#0D47A1")));
    painter.setCompositionMode(QPainter::CompositionMode_Source);
    painter.fillRect(rect(), background);
    painter.setCompositionMode(QPainter::CompositionMode_SourceOver);

    // 轻量蓝色“储鲜环”：纯绘制、无图片和动画，适合无 GPU 的 linuxfb 环境。
    painter.setPen(Qt::NoPen);
    painter.setBrush(QColor(144, 202, 249, 48));
    painter.drawEllipse(QPointF(width() * 0.84, height() * 0.27), 190, 190);
    painter.setBrush(QColor(100, 181, 246, 44));
    painter.drawEllipse(QPointF(width() * 0.89, height() * 0.22), 112, 112);
    painter.setBrush(QColor(179, 229, 252, 54));
    painter.drawEllipse(QPointF(width() * 0.08, height() * 0.82), 72, 72);
}

void WelcomePage::mousePressEvent(QMouseEvent *event)
{
    if (event->button() == Qt::LeftButton) {
        emit continueRequested();
        event->accept();
        return;
    }
    QWidget::mousePressEvent(event);
}

void WelcomePage::keyPressEvent(QKeyEvent *event)
{
    if (event->key() == Qt::Key_Return || event->key() == Qt::Key_Enter
        || event->key() == Qt::Key_Space) {
        emit continueRequested();
        event->accept();
        return;
    }
    QWidget::keyPressEvent(event);
}
