#ifndef PRODUCEMODEL_H
#define PRODUCEMODEL_H

#include <QAbstractTableModel>
#include <QVector>

// 对接 produce_info + stock_summary 联合查询，供库存看板/信息查询录入页使用。
struct ProduceRow
{
    int id = 0;
    QString name;
    QString category;
    int shelfLifeDays = 0;
    QString idealTempRange;
    QString iconUrl;
    double currentQty = 0.0;
    QString earliestExpireDate;
};

class ProduceModel : public QAbstractTableModel
{
    Q_OBJECT
public:
    enum Column { ColName = 0, ColCategory, ColQty, ColExpireDate, ColCount };

    explicit ProduceModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    int columnCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation orientation, int role) const override;

    // 从数据库重新查询全部果蔬+库存汇总数据
    void refresh();

    const ProduceRow &rowAt(int row) const;

    // 新增/编辑一条果蔬基本信息（对应"触摸信息查询与录入"页面的写操作）
    bool upsertProduce(const ProduceRow &row);

private:
    QVector<ProduceRow> m_rows;
};

#endif // PRODUCEMODEL_H
