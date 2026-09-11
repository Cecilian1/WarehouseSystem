#include "alertpage.h"

#include "../data/models/alertmodel.h"

#include <QFontMetrics>
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
    auto *header = m_tableView->horizontalHeader();
    header->setStretchLastSection(false);
    header->setSectionResizeMode(QHeaderView::Fixed);
    header->setSectionResizeMode(AlertModel::ColProduceName, QHeaderView::Stretch);

    const QFontMetrics tableFontMetrics(m_tableView->font());
    m_tableView->setColumnWidth(
        AlertModel::ColCreatedAt,
        tableFontMetrics.horizontalAdvance(QStringLiteral("2026-09-11 23:59:59")) + 32);
    m_tableView->setColumnWidth(
        AlertModel::ColType,
        tableFontMetrics.horizontalAdvance(QStringLiteral("即将过期")) + 32);
    m_tableView->setColumnWidth(
        AlertModel::ColExpireDate,
        tableFontMetrics.horizontalAdvance(QStringLiteral("2026-09-11")) + 32);
    m_tableView->setColumnWidth(
        AlertModel::ColRead,
        tableFontMetrics.horizontalAdvance(QStringLiteral("未处理")) + 32);
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
