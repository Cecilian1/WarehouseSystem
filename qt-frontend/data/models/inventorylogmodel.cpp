#include "inventorylogmodel.h"

#include "../databasemanager.h"

#include <QSqlError>
#include <QSqlQuery>
#include <QVariant>

namespace {

QString localizedFreshnessLevel(const QString &value)
{
    const QString level = value.trimmed().toLower();
    if (level.isEmpty())
        return QStringLiteral("未上报");
    if (level == QStringLiteral("fresh") || level == QStringLiteral("新鲜"))
        return QStringLiteral("新鲜");
    if (level == QStringLiteral("mild") || level == QStringLiteral("warning")
        || level == QStringLiteral("warn") || level == QStringLiteral("临期")
        || level == QStringLiteral("轻度不新鲜")) {
        return QStringLiteral("轻度不新鲜");
    }
    if (level == QStringLiteral("rotten") || level == QStringLiteral("spoiled")
        || level == QStringLiteral("expired") || level == QStringLiteral("腐败")
        || level == QStringLiteral("腐败变质")) {
        return QStringLiteral("腐败变质");
    }
    return value.trimmed();
}

} // namespace

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
        "       COALESCE(NULLIF(TRIM(l.freshness_level), ''), "
        "           (SELECT r.freshness_level FROM inventory_log r "
        "            WHERE l.source_frame_id IS NOT NULL "
        "              AND r.produce_id = l.produce_id "
        "              AND r.source_frame_id <= l.source_frame_id "
        "              AND COALESCE(r.bbox_json, '') <> '' "
        "              AND NULLIF(TRIM(r.freshness_level), '') IS NOT NULL "
        "            ORDER BY r.source_frame_id DESC, "
        "                     CASE WHEN r.freshness_score IS NULL THEN 1 ELSE 0 END, "
        "                     r.freshness_score ASC, r.id DESC "
        "            LIMIT 1), ''), l.created_at "
        "FROM inventory_log l "
        "LEFT JOIN produce_info p ON p.id = l.produce_id "
        "WHERE COALESCE(l.bbox_json, '') = '' ";

    if (!filterCategory.isEmpty())
        sql += "AND p.category = :category ";
    if (!startDate.isEmpty())
        sql += "AND datetime(l.created_at) >= datetime(:startDate) ";
    if (!endDate.isEmpty())
        sql += "AND datetime(l.created_at) <= datetime(:endDate) ";
    sql += "ORDER BY datetime(l.created_at) DESC, l.id DESC";

    QSqlQuery query(DatabaseManager::database());
    query.prepare(sql);
    if (!filterCategory.isEmpty())
        query.bindValue(":category", filterCategory);
    if (!startDate.isEmpty())
        query.bindValue(":startDate", startDate + QStringLiteral(" 00:00:00"));
    if (!endDate.isEmpty())
        query.bindValue(":endDate", endDate + QStringLiteral(" 23:59:59"));

    if (!query.exec()) {
        qWarning("InventoryLogModel::refresh 查询失败: %s", qPrintable(query.lastError().text()));
        endResetModel();
        return;
    }

    while (query.next()) {
        InventoryLogRow row;
        row.id = query.value(0).toInt();
        row.produceName = query.value(1).toString();
        const QString actionType = query.value(2).toString();
        row.actionType = actionType == QStringLiteral("IN")
            ? QStringLiteral("入库")
            : actionType == QStringLiteral("OUT") ? QStringLiteral("出库") : actionType;
        row.quantity = query.value(3).toDouble();
        row.freshnessLevel = localizedFreshnessLevel(query.value(4).toString());
        row.createdAt = query.value(5).toString();
        m_rows.append(row);
    }

    endResetModel();
}
