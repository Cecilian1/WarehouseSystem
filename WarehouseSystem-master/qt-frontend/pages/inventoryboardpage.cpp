#include "inventoryboardpage.h"

#include "../data/models/producemodel.h"

#include <QHeaderView>
#include <QTableView>
#include <QVBoxLayout>

InventoryBoardPage::InventoryBoardPage(QWidget *parent)
    : QWidget(parent)
    , m_model(new ProduceModel(this))
    , m_tableView(new QTableView(this))
{
    m_tableView->setModel(m_model);
    m_tableView->horizontalHeader()->setStretchLastSection(true);
    m_tableView->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_tableView->setEditTriggers(QAbstractItemView::NoEditTriggers);
    // 触摸友好：增大行高，方便手指点选
    m_tableView->verticalHeader()->setDefaultSectionSize(48);

    auto *layout = new QVBoxLayout(this);
    layout->addWidget(m_tableView);

    refresh();
}

void InventoryBoardPage::refresh()
{
    m_model->refresh();
}
