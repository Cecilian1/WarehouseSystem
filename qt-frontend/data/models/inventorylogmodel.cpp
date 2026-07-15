#include "inventorylogmodel.h"

#include "../databasemanager.h"

#include <QSqlError>
#include <QSqlQuery>

InventoryLogModel::InventoryLogModel(QObject *parent)
    : QAbstractTableModel(parent)
{
}

int InventoryLogModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    return m_rows.size();
}

int InventoryLogModel::columnCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    return ColCount;
}

QVariant InventoryLogModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() >= m_rows.size() || role != Qt::DisplayRole)
        return QVariant();

    const InventoryLogRow &row = m_rows.at(index.row());
    switch (index.column()) {
    case ColCreatedAt:
        return row.createdAt;
    case ColProduceName:
        return row.produceName;
    case ColActionType:
        return row.actionType;
    case ColQuantity:
        return row.quantity;
    case ColFreshness:
        return row.freshnessLevel;
    default:
        return QVariant();
    }
}

QVariant InventoryLogModel::headerData(int section, Qt::Orientation orientation, int role) const
{
    if (role != Qt::DisplayRole || orientation != Qt::Horizontal)
        return QVariant();

    switch (section) {
    case ColCreatedAt:
        return QStringLiteral("时间");
    case ColProduceName:
        return QStringLiteral("果蔬");
    case ColActionType:
        return QStringLiteral("类型");
    case ColQuantity:
        return QStringLiteral("数量");
    case ColFreshness:
        return QStringLiteral("新鲜度");
    default:
        return QVariant();
    }
}

void InventoryLogModel::refresh(const QString &filterCategory, const QString &startDate, const QString &endDate)
{
    beginResetModel();
    m_rows.clear();

    QString sql =
        "SELECT l.id, COALESCE(p.name, '未知'), l.action_type, l.quantity, "
        "       COALESCE(l.freshness_level, ''), l.created_at "
        "FROM inventory_log l "
        "LEFT JOIN produce_info p ON p.id = l.produce_id "
        "WHERE 1=1 ";

    if (!filterCategory.isEmpty())
        sql += "AND p.category = :category ";
    if (!startDate.isEmpty())
        sql += "AND l.created_at >= :startDate ";
    if (!endDate.isEmpty())
        sql += "AND l.created_at <= :endDate ";
    sql += "ORDER BY l.created_at DESC";

    QSqlQuery query(DatabaseManager::database());
    query.prepare(sql);
    if (!filterCategory.isEmpty())
        query.bindValue(":category", filterCategory);
    if (!startDate.isEmpty())
        query.bindValue(":startDate", startDate);
    if (!endDate.isEmpty())
        query.bindValue(":endDate", endDate);

    if (!query.exec()) {
        qWarning("InventoryLogModel::refresh 查询失败: %s", qPrintable(query.lastError().text()));
        endResetModel();
        return;
    }

    while (query.next()) {
        InventoryLogRow row;
        row.id = query.value(0).toInt();
        row.produceName = query.value(1).toString();
        row.actionType = query.value(2).toString();
        row.quantity = query.value(3).toDouble();
        row.freshnessLevel = query.value(4).toString();
        row.createdAt = query.value(5).toString();
        m_rows.append(row);
    }

    endResetModel();
}
