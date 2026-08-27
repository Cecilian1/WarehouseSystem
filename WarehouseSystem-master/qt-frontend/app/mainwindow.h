#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

class NavigationBar;
class PollingTimer;
class InventoryBoardPage;
class RecognitionPage;
class ProduceInfoPage;
class HistoryPage;
class AlertPage;
class EnvStatusCard;
class QStackedWidget;

// 应用主窗口：顶部常驻EnvStatusCard + 中部QStackedWidget承载5个可切换页面
// + 底部NavigationBar。所有页面共用一个PollingTimer做"伪实时"数据刷新
// （替代docx提到的WebSocket方案，见 data/pollingtimer.h 的说明）。
class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

private:
    void buildUi();
    void connectPolling();

    QStackedWidget *m_stackedWidget;
    NavigationBar *m_navigationBar;
    EnvStatusCard *m_envStatusCard;
    PollingTimer *m_pollingTimer;

    InventoryBoardPage *m_inventoryBoardPage;
    RecognitionPage *m_recognitionPage;
    ProduceInfoPage *m_produceInfoPage;
    HistoryPage *m_historyPage;
    AlertPage *m_alertPage;
};

#endif // MAINWINDOW_H
