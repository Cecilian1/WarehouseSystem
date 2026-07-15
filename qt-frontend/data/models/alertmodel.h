#ifndef ALERTMODEL_H
#define ALERTMODEL_H

#include <QAbstractTableModel>
#include <QVector>

// 对接 alert_record 表，供"预警提醒页"展示。alert_type包括
// 'expiring'/'expired'（临近过期/已过期，未来由AI+保质期计算写入）
// 与 'device_abnormal'（env_service在温度持续异常时写入，本次任务已实现）。
struct AlertRow
{
    int id = 0;
    QString produceName;  // device_abnormal类型时为空
    QString alertType;
    QString expireDate;   // device_abnormal类型时为空
    bool isRead = false;
    QString createdAt;
};

class AlertModel : public QAbstractTableModel
{
    Q_OBJECT
public:
    enum Column { ColCreatedAt = 0, ColType, ColProduceName, ColExpireDate, ColRead, ColCount };

    explicit AlertModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    int columnCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation orientation, int role) const override;

    void refresh();

    const AlertRow &rowAt(int row) const;

    // 触摸卡片"标记已处理"
    bool markAsRead(int alertId);

private:
    QVector<AlertRow> m_rows;
};

#endif // ALERTMODEL_H
