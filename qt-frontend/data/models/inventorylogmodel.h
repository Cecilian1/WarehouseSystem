#ifndef INVENTORYLOGMODEL_H
#define INVENTORYLOGMODEL_H

#include <QAbstractTableModel>
#include <QVector>

// 对接 inventory_log 表，供"历史记录"页只读展示。
// 本次任务camera_service/env_service均不写入inventory_log（该表的写入
// 依赖AI识别结果，属于未来AI服务模块的职责），因此骨架阶段该表可能为空，
// 开发者可手动INSERT测试数据验证UI展示效果。
struct InventoryLogRow
{
    int id = 0;
    QString produceName;
    QString actionType;
    double quantity = 0.0;
    QString freshnessLevel;
    QString createdAt;
};

class InventoryLogModel : public QAbstractTableModel
{
    Q_OBJECT
public:
    enum Column { ColCreatedAt = 0, ColProduceName, ColActionType, ColQuantity, ColFreshness, ColCount };

    explicit InventoryLogModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    int columnCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation orientation, int role) const override;

    // filterCategory/startDate/endDate 为空字符串表示不过滤，
    // 对应"按种类、日期区间触摸筛选查询"需求
    void refresh(const QString &filterCategory = QString(),
                 const QString &startDate = QString(),
                 const QString &endDate = QString());

private:
    QVector<InventoryLogRow> m_rows;
};

#endif // INVENTORYLOGMODEL_H
