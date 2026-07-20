#include "app/mainwindow.h"
#include "data/databasemanager.h"

#include <QApplication>
#include <QDebug>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    // frontend.ini路径相对于程序运行时的工作目录（部署时约定为可执行文件
    // 同级的config/frontend.ini，见 docs/build-and-deploy.md）
    if (!DatabaseManager::openConnection(QStringLiteral("config/frontend.ini"))) {
        qCritical() << "数据库连接失败，程序退出";
        return 1;
    }

    // 标记前端已启动
    DatabaseManager::setFrontendActive(true);

    MainWindow w;
    w.show();

    const int result = a.exec();

    // 标记前端已停止
    DatabaseManager::setFrontendActive(false);
    DatabaseManager::closeConnection();
    return result;
}
