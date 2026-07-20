#include "app/mainwindow.h"
#include "data/databasemanager.h"

#include <QApplication>
#include <QDebug>
#include <signal.h>
#include <stdlib.h>

static void signalHandler(int signum)
{
    qDebug() << "收到信号" << signum << "，执行清理...";
    DatabaseManager::setFrontendActive(false);
    DatabaseManager::closeConnection();
    exit(0);
}

int main(int argc, char *argv[])
{
    // 注册信号处理器，确保Ctrl+C时能执行cleanup
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    QApplication a(argc, argv);

    // frontend.ini路径相对于程序运行时的工作目录（部署时约定为可执行文件
    // 同级的config/frontend.ini，见 docs/build-and-deploy.md）
    if (!DatabaseManager::openConnection(QStringLiteral("config/frontend.ini"))) {
        qCritical() << "数据库连接失败，程序退出";
        return 1;
    }

    // 标记前端已启动
    DatabaseManager::setFrontendActive(true);

    int result = 0;
    try {
        MainWindow w;
        w.show();
        result = a.exec();
    } catch (...) {
        qWarning() << "程序异常，但仍尝试cleanup";
    }

    // 无论如何都要执行cleanup
    qDebug() << "前端正在关闭，设置frontend_active=false";
    DatabaseManager::setFrontendActive(false);
    DatabaseManager::closeConnection();
    return result;
}
