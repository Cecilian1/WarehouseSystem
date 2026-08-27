#ifndef HISTORYPAGE_H
#define HISTORYPAGE_H

#include <QWidget>

class InventoryLogModel;
class QTableView;
class QLineEdit;
class QDateEdit;

// 操作时间与保质期数据管理：按时间倒序展示每笔入/出库操作记录，
// 支持按种类、日期区间触摸筛选查询。
class HistoryPage : public QWidget
{
    Q_OBJECT
public:
    explicit HistoryPage(QWidget *parent = nullptr);

public slots:
    void refresh();

private slots:
    void onFilterApplied();

private:
    InventoryLogModel *m_model;
    QTableView *m_tableView;

    QLineEdit *m_categoryFilterEdit;
    QDateEdit *m_startDateEdit;
    QDateEdit *m_endDateEdit;
};

#endif // HISTORYPAGE_H
