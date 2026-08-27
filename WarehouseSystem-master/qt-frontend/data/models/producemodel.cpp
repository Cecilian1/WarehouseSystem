#include "producemodel.h"

#include "../databasemanager.h"

#include <QSqlDatabase>
#include <QSqlError>
#include <QSqlQuery>
#include <QVariant>
#include <QtGlobal>

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
    QSqlDatabase db = DatabaseManager::database();
    if (!db.transaction()) {
        qWarning("ProduceModel::upsertProduce 无法开始事务: %s", qPrintable(db.lastError().text()));
        return false;
    }

    double oldQuantity = 0.0;
    if (row.id != 0) {
        QSqlQuery stockQuery(db);
        stockQuery.prepare("SELECT COALESCE(current_qty, 0) FROM stock_summary WHERE produce_id=?");
        stockQuery.addBindValue(row.id);
        if (!stockQuery.exec()) {
            qWarning("ProduceModel::upsertProduce 查询旧库存失败: %s",
                     qPrintable(stockQuery.lastError().text()));
            db.rollback();
            return false;
        }
        if (stockQuery.next())
            oldQuantity = stockQuery.value(0).toDouble();
    }

    QSqlQuery query(db);
    int produceId = row.id;
    if (row.id != 0) {
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
        qWarning("ProduceModel::upsertProduce 保存商品失败: %s", qPrintable(query.lastError().text()));
        db.rollback();
        return false;
    }

    if (row.id == 0)
        produceId = query.lastInsertId().toInt();
    if (produceId == 0) {
        qWarning("ProduceModel::upsertProduce 未获得有效商品ID");
        db.rollback();
        return false;
    }

    QSqlQuery stockQuery(db);
    stockQuery.prepare(
        "INSERT INTO stock_summary "
        "(produce_id, current_qty, earliest_expire_date, last_updated) "
        "VALUES (?, ?, ?, datetime('now', 'localtime')) "
        "ON CONFLICT(produce_id) DO UPDATE SET "
        "current_qty=excluded.current_qty, "
        "earliest_expire_date=excluded.earliest_expire_date, "
        "last_updated=excluded.last_updated");
    stockQuery.addBindValue(produceId);
    stockQuery.addBindValue(row.currentQty);
    stockQuery.addBindValue(row.earliestExpireDate);
    if (!stockQuery.exec()) {
        qWarning("ProduceModel::upsertProduce 保存库存失败: %s",
                 qPrintable(stockQuery.lastError().text()));
        db.rollback();
        return false;
    }

    const double quantityDelta = row.currentQty - oldQuantity;
    if (!qFuzzyIsNull(quantityDelta)) {
        QSqlQuery logQuery(db);
        logQuery.prepare(
            "INSERT INTO inventory_log "
            "(produce_id, action_type, quantity, sync_status) "
            "VALUES (?, ?, ?, 'local')");
        logQuery.addBindValue(produceId);
        logQuery.addBindValue(quantityDelta > 0 ? QStringLiteral("IN") : QStringLiteral("OUT"));
        logQuery.addBindValue(qAbs(quantityDelta));
        if (!logQuery.exec()) {
            qWarning("ProduceModel::upsertProduce 写入库存历史失败: %s",
                     qPrintable(logQuery.lastError().text()));
            db.rollback();
            return false;
        }
    }

    if (!db.commit()) {
        qWarning("ProduceModel::upsertProduce 提交事务失败: %s", qPrintable(db.lastError().text()));
        db.rollback();
        return false;
    }

    refresh();
    return true;
}
