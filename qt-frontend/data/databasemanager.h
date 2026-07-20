#ifndef DATABASEMANAGER_H
#define DATABASEMANAGER_H

#include <QSqlDatabase>
#include <QString>

// QSqlDatabase封装：负责打开到本地SQLite文件的连接，并设置WAL模式与
// busy_timeout，保证与camera_service/env_service两个Python进程并发写入
// 同一个.db文件时不会因为"database is locked"直接报错。
//
// Qt5.15的QSQLITE驱动不直接暴露PRAGMA配置接口，因此在openConnection()
// 内部通过QSqlQuery手动执行这两条PRAGMA。
class DatabaseManager
{
public:
    // iniConfigPath: frontend.ini路径，读取[database]/path项
    static bool openConnection(const QString &iniConfigPath);

    static QSqlDatabase database();

    static void closeConnection();

    // 更新device_status.frontend_active标记（1=前端正在运行，0=前端已停止）
    static void setFrontendActive(bool active);

private:
    static const QString kConnectionName;
};

#endif // DATABASEMANAGER_H
