#include "mainwindow.h"

#include "navigationbar.h"

#include "../data/pollingtimer.h"
#include "../pages/alertpage.h"
#include "../pages/envstatuscard.h"
#include "../pages/historypage.h"
#include "../pages/inventoryboardpage.h"
#include "../pages/produceinfopage.h"
#include "../pages/recognitionpage.h"

#include <QSettings>
#include <QStackedWidget>
#include <QVBoxLayout>
#include <QWidget>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , m_stackedWidget(new QStackedWidget(this))
    , m_navigationBar(new NavigationBar(this))
    , m_envStatusCard(new EnvStatusCard(this))
    , m_pollingTimer(nullptr)
    , m_inventoryBoardPage(new InventoryBoardPage(this))
    , m_recognitionPage(new RecognitionPage(this))
    , m_produceInfoPage(new ProduceInfoPage(this))
    , m_historyPage(new HistoryPage(this))
    , m_alertPage(new AlertPage(this))
{
    buildUi();
    connectPolling();
}

MainWindow::~MainWindow() = default;

void MainWindow::buildUi()
{
    setWindowTitle(QStringLiteral("芯鲜管家"));
    resize(1024, 600);  // 对应7寸LCD 1024x600分辨率

    m_stackedWidget->addWidget(m_inventoryBoardPage);
    m_stackedWidget->addWidget(m_recognitionPage);
    m_stackedWidget->addWidget(m_produceInfoPage);
    m_stackedWidget->addWidget(m_historyPage);
    m_stackedWidget->addWidget(m_alertPage);

    connect(m_navigationBar, &NavigationBar::pageRequested,
            m_stackedWidget, &QStackedWidget::setCurrentIndex);

    auto *central = new QWidget(this);
    auto *layout = new QVBoxLayout(central);
    layout->addWidget(m_envStatusCard);
    layout->addWidget(m_stackedWidget, 1);
    layout->addWidget(m_navigationBar);

    setCentralWidget(central);
}

void MainWindow::connectPolling()
{
    QSettings settings(QStringLiteral("config/frontend.ini"), QSettings::IniFormat);
    const int intervalMs = settings.value("polling/interval_ms", 2000).toInt();

    m_pollingTimer = new PollingTimer(intervalMs, this);
    qDebug("MainWindow::connectPolling PollingTimer created with interval=%dms", intervalMs);

    connect(m_pollingTimer, &PollingTimer::dataMayHaveChanged, m_inventoryBoardPage, &InventoryBoardPage::refresh);
    connect(m_pollingTimer, &PollingTimer::dataMayHaveChanged, m_recognitionPage, &RecognitionPage::refresh);
    connect(m_pollingTimer, &PollingTimer::dataMayHaveChanged, m_historyPage, &HistoryPage::refresh);
    connect(m_pollingTimer, &PollingTimer::dataMayHaveChanged, m_alertPage, &AlertPage::refresh);
    connect(m_pollingTimer, &PollingTimer::dataMayHaveChanged, m_envStatusCard, &EnvStatusCard::refresh);
    // ProduceInfoPage不订阅轮询：编辑表单期间不希望被后台刷新打断用户输入，
    // 该页面数据在切换到本页/保存后手动refresh()

    m_pollingTimer->start();
    qDebug("MainWindow::connectPolling PollingTimer started");
}
