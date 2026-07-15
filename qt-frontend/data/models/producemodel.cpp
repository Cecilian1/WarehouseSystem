#include "producemodel.h"

#include "../databasemanager.h"

#include <QSqlError>
#include <QSqlQuery>
#include <QVariant>

ProduceModel::ProduceModel(QObject *parent)
    : QAbstractTableModel(parent)
{
}

int ProduceModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    return m_rows.size();
}

int ProduceModel::columnCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    return ColCount;
}

QVariant ProduceModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() >= m_rows.size())
        return QVariant();

    if (role != Qt::DisplayRole)
        return QVariant();

    const ProduceRow &row = m_rows.at(index.row());
    switch (index.column()) {
    case ColName:
        return row.name;
    case ColCategory:
        return row.category;
    case ColQty:
        return row.currentQty;
    case ColExpireDate:
        return row.earliestExpireDate;
    default:
        return QVariant();
    }
}

QVariant ProduceModel::headerData(int section, Qt::Orientation orientation, int role) const
{
    if (role != Qt::DisplayRole || orientation != Qt::Horizontal)
        return QVariant();

    switch (section) {
    case ColName:
        return QStringLiteral("名称");
    case ColCategory:
        return QStringLiteral("分类");
    case ColQty:
        return QStringLiteral("库存数量");
    case ColExpireDate:
        return QStringLiteral("最早过期日期");
    default:
        return QVariant();
    }
}

void ProduceModel::refresh()
{
    beginResetModel();
    m_rows.clear();

    QSqlQuery query(DatabaseManager::database());
    query.prepare(
        "SELECT p.id, p.name, p.category, p.shelf_life_days, p.ideal_temp_range, p.icon_url, "
        "       COALESCE(s.current_qty, 0), s.earliest_expire_date "
        "FROM produce_info p "
        "LEFT JOIN stock_summary s ON s.produce_id = p.id "
        "ORDER BY p.name");

    if (!query.exec()) {
        qWarning("ProduceModel::refresh 查询失败: %s", qPrintable(query.lastError().text()));
        endResetModel();
        return;
    }

    while (query.next()) {
        ProduceRow row;
        row.id = query.value(0).toInt();
        row.name = query.value(1).toString();
        row.category = query.value(2).toString();
        row.shelfLifeDays = query.value(3).toInt();
        row.idealTempRange = query.value(4).toString();
        row.iconUrl = query.value(5).toString();
        row.currentQty = query.value(6).toDouble();
        row.earliestExpireDate = query.value(7).toString();
        m_rows.append(row);
    }

    endResetModel();
}

const ProduceRow &ProduceModel::rowAt(int row) const
{
    return m_rows.at(row);
}

bool ProduceModel::upsertProduce(const ProduceRow &row)
{
    QSqlQuery query(DatabaseManager::database());

    if (row.id > 0) {
        query.prepare(
            "UPDATE produce_info SET name=?, category=?, shelf_life_days=?, "
            "ideal_temp_range=?, icon_url=? WHERE id=?");
        query.addBindValue(row.name);
        query.addBindValue(row.category);
        query.addBindValue(row.shelfLifeDays);
        query.addBindValue(row.idealTempRange);
        query.addBindValue(row.iconUrl);
        query.addBindValue(row.id);
    } else {
        query.prepare(
            "INSERT INTO produce_info (name, category, shelf_life_days, ideal_temp_range, icon_url) "
            "VALUES (?, ?, ?, ?, ?)");
        query.addBindValue(row.name);
        query.addBindValue(row.category);
        query.addBindValue(row.shelfLifeDays);
        query.addBindValue(row.idealTempRange);
        query.addBindValue(row.iconUrl);
    }

    if (!query.exec()) {
        qWarning("ProduceModel::upsertProduce 失败: %s", qPrintable(query.lastError().text()));
        return false;
    }

    refresh();
    return true;
}
