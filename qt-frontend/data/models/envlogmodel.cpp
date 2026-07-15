#include "envlogmodel.h"

#include "../databasemanager.h"

#include <QSqlError>
#include <QSqlQuery>

EnvLogModel::EnvLogModel(QObject *parent)
    : QObject(parent)
{
}

EnvLatestReading EnvLogModel::fetchLatest() const
{
    EnvLatestReading reading;

    QSqlQuery query(DatabaseManager::database());
    query.prepare(
        "SELECT temperature, humidity, is_abnormal, recorded_at "
        "FROM env_log ORDER BY id DESC LIMIT 1");

    if (!query.exec()) {
        qWarning("EnvLogModel::fetchLatest 查询失败: %s", qPrintable(query.lastError().text()));
        return reading;
    }

    if (query.next()) {
        reading.valid = true;
        reading.temperature = query.value(0).toDouble();
        reading.humidity = query.value(1).toDouble();
        reading.isAbnormal = query.value(2).toInt() != 0;
        reading.recordedAt = query.value(3).toString();
    }

    return reading;
}
