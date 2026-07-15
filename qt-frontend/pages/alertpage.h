#ifndef ALERTPAGE_H
#define ALERTPAGE_H

#include <QWidget>

class AlertModel;
class QTableView;
class QModelIndex;

// 预警提醒页：高亮展示即将过期/已过期商品及设备异常告警，
// 触摸卡片（此处简化为表格行+按钮）即可标记已处理。
class AlertPage : public QWidget
{
    Q_OBJECT
public:
    explicit AlertPage(QWidget *parent = nullptr);

public slots:
    void refresh();

private slots:
    void onMarkReadClicked();

private:
    AlertModel *m_model;
    QTableView *m_tableView;
};

#endif // ALERTPAGE_H
