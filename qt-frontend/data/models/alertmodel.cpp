#include "alertmodel.h"

#include "../databasemanager.h"

#include <QSqlError>
#include <QSqlQuery>
#include <QVariant>

AlertModel::AlertModel(QObject *parent)
    : QAbstractTableModel(parent)
{
}

int AlertModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    return m_rows.size();
}

int AlertModel::columnCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    return ColCount;
}

QVariant AlertModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() >= m_rows.size() || role != Qt::DisplayRole)
        return QVariant();

    const AlertRow &row = m_rows.at(index.row());
    switch (index.column()) {
    case ColCreatedAt:
        return row.createdAt;
    case ColType:
        return row.alertType;
    case ColProduceName:
        return row.produceName;
    case ColExpireDate:
        return row.expireDate;
    case ColRead:
        return row.isRead ? QStringLiteral("已处理") : QStringLiteral("未处理");
    default:
        return QVariant();
    }
}

QVariant AlertModel::headerData(int section, Qt::Orientation orientation, int role) const
{
    if (role != Qt::DisplayRole || orientation != Qt::Horizontal)
        return QVariant();

    switch (section) {
    case ColCreatedAt:
        return QStringLiteral("时间");
    case ColType:
        return QStringLiteral("类型");
    case ColProduceName:
        return QStringLiteral("果蔬");
    case ColExpireDate:
        return QStringLiteral("过期日期");
    case ColRead:
        return QStringLiteral("状态");
    default:
        return QVariant();
    }
}

void AlertModel::refresh()
{
    beginResetModel();
    m_rows.clear();

    QSqlQuery query(DatabaseManager::database());
    query.prepare(
        "SELECT a.id, COALESCE(p.name, ''), a.alert_type, COALESCE(a.expire_date, ''), "
        "       a.is_read, a.created_at "
        "FROM alert_record a "
        "LEFT JOIN produce_info p ON p.id = a.produce_id "
        "ORDER BY a.is_read ASC, a.created_at DESC");

    if (!query.exec()) {
        qWarning("AlertModel::refresh 查询失败: %s", qPrintable(query.lastError().text()));
        endResetModel();
        return;
    }

    while (query.next()) {
        AlertRow row;
        row.id = query.value(0).toInt();
        row.produceName = query.value(1).toString();
        row.alertType = query.value(2).toString();
        row.expireDate = query.value(3).toString();
        row.isRead = query.value(4).toInt() != 0;
        row.createdAt = query.value(5).toString();
        m_rows.append(row);
    }

    endResetModel();
}

const AlertRow &AlertModel::rowAt(int row) const
{
    return m_rows.at(row);
}

bool AlertModel::markAsRead(int alertId)
{
    QSqlQuery query(DatabaseManager::database());
    query.prepare("UPDATE alert_record SET is_read = 1 WHERE id = ?");
    query.addBindValue(alertId);

    if (!query.exec()) {
        qWarning("AlertModel::markAsRead 失败: %s", qPrintable(query.lastError().text()));
        return false;
    }

    refresh();
    return true;
}
