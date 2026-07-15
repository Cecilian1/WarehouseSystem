#include "alertpage.h"

#include "../data/models/alertmodel.h"

#include <QHeaderView>
#include <QPushButton>
#include <QTableView>
#include <QVBoxLayout>

AlertPage::AlertPage(QWidget *parent)
    : QWidget(parent)
    , m_model(new AlertModel(this))
    , m_tableView(new QTableView(this))
{
    m_tableView->setModel(m_model);
    m_tableView->horizontalHeader()->setStretchLastSection(true);
    m_tableView->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_tableView->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_tableView->verticalHeader()->setDefaultSectionSize(48);

    auto *markReadBtn = new QPushButton(QStringLiteral("标记选中项为已处理"), this);
    connect(markReadBtn, &QPushButton::clicked, this, &AlertPage::onMarkReadClicked);

    auto *layout = new QVBoxLayout(this);
    layout->addWidget(m_tableView);
    layout->addWidget(markReadBtn);

    refresh();
}

void AlertPage::refresh()
{
    m_model->refresh();
}

void AlertPage::onMarkReadClicked()
{
    const QModelIndexList selected = m_tableView->selectionModel()->selectedRows();
    for (const QModelIndex &index : selected) {
        const AlertRow &row = m_model->rowAt(index.row());
        m_model->markAsRead(row.id);
    }
}
