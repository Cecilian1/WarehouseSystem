#ifndef ENVLOGMODEL_H
#define ENVLOGMODEL_H

#include <QObject>
#include <QString>

// 对接 env_log 表，仅供"环境状态卡片"读取最新一条记录，
// 不需要完整的QAbstractTableModel（不做表格展示），用简单的POD+查询方法即可。
struct EnvLatestReading
{
    bool valid = false;
    double temperature = 0.0;
    double humidity = 0.0;
    bool isAbnormal = false;
    QString recordedAt;
};

class EnvLogModel : public QObject
{
    Q_OBJECT
public:
    explicit EnvLogModel(QObject *parent = nullptr);

    // 查询env_log最新一条记录
    EnvLatestReading fetchLatest() const;
};

#endif // ENVLOGMODEL_H
