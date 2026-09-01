#include "app/mainwindow.h"
#include "data/databasemanager.h"

#include <QApplication>
#include <QDebug>

int main(int argc, char *argv[])
{
    // 嵌入式触摸屏没有物理键盘。必须在创建 QApplication 之前选择输入法插件，
    // 否则 QInputMethod::show() 只会请求默认（通常为空）的输入法上下文，中文
    // 拼音候选键盘不会出现。允许部署环境通过 QT_IM_MODULE 覆盖这个默认值。
    if (qEnvironmentVariableIsEmpty("QT_IM_MODULE"))
        qputenv("QT_IM_MODULE", "qtvirtualkeyboard");
    // 出厂镜像提供了 Qt Virtual Keyboard。优先选择简体中文布局，用户仍可在
    // 键盘中切换语言；部署环境可通过同名变量保留其他默认语言。
    if (qEnvironmentVariableIsEmpty("QT_VIRTUALKEYBOARD_LOCALE"))
        qputenv("QT_VIRTUALKEYBOARD_LOCALE", "zh_CN");

    QApplication a(argc, argv);

    // frontend.ini路径相对于程序运行时的工作目录（部署时约定为可执行文件
    // 同级的config/frontend.ini，见 docs/build-and-deploy.md）
    if (!DatabaseManager::openConnection(QStringLiteral("config/frontend.ini"))) {
        qCritical() << "数据库连接失败，程序退出";
        return 1;
    }

    MainWindow w;
    w.show();

    const int result = a.exec();

    DatabaseManager::closeConnection();
    return result;
}
