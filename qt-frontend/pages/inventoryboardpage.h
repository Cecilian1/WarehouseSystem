#ifndef INVENTORYBOARDPAGE_H
#define INVENTORYBOARDPAGE_H

#include <QWidget>

class ProduceModel;
class QTableView;

// 实时库存看板：以表格形式（卡片式列表的简化实现）分类展示当前各种果蔬
// 库存数量与新鲜度状态，支持触摸滑动浏览（QTableView自带触摸滚动）。
//
// 骨架阶段用QTableView展示ProduceModel，而非逐个绘制卡片Widget——
// 数据驱动的表格视图更易维护，且Qt的QTableView触摸滑动体验已经足够，
// 卡片式视觉效果可后续通过自定义QStyledItemDelegate美化，不改变数据层。
class InventoryBoardPage : public QWidget
{
    Q_OBJECT
public:
    explicit InventoryBoardPage(QWidget *parent = nullptr);

public slots:
    // 连接到PollingTimer::dataMayHaveChanged，刷新数据
    void refresh();

private:
    ProduceModel *m_model;
    QTableView *m_tableView;
};

#endif // INVENTORYBOARDPAGE_H
