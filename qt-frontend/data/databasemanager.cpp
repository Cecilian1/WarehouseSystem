#include "databasemanager.h"

#include <QDebug>
#include <QSettings>
#include <QSqlError>
#include <QSqlQuery>

const QString DatabaseManager::kConnectionName = QStringLiteral("warehousekeeper_main");

bool DatabaseManager::openConnection(const QString &iniConfigPath)
{
    QSettings settings(iniConfigPath, QSettings::IniFormat);
    const QString dbPath = settings.value("database/path", "/data/warehousekeeper/warehousekeeper.db").toString();

    QSqlDatabase db = QSqlDatabase::addDatabase("QSQLITE", kConnectionName);
    db.setDatabaseName(dbPath);

    if (!db.open()) {
        qWarning() << "打开数据库失败:" << db.lastError().text();
        return false;
    }

    // 与Python侧backend/common/db.py保持一致的并发安全配置
    QSqlQuery query(db);
    if (!query.exec("PRAGMA journal_mode=WAL;")) {
        qWarning() << "设置WAL模式失败:" << query.lastError().text();
    }
    if (!query.exec("PRAGMA busy_timeout=3000;")) {
        qWarning() << "设置busy_timeout失败:" << query.lastError().text();
    }

    return true;
}

QSqlDatabase DatabaseManager::database()
{
    return QSqlDatabase::database(kConnectionName);
}

void DatabaseManager::closeConnection()
{
    if (QSqlDatabase::contains(kConnectionName)) {
        QSqlDatabase::database(kConnectionName).close();
        QSqlDatabase::removeDatabase(kConnectionName);
    }
}
