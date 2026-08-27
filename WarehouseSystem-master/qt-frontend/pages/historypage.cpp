#include "historypage.h"

#include "../data/models/inventorylogmodel.h"

#include <QDateEdit>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QTableView>
#include <QVBoxLayout>

HistoryPage::HistoryPage(QWidget *parent)
    : QWidget(parent)
    , m_model(new InventoryLogModel(this))
    , m_tableView(new QTableView(this))
    , m_categoryFilterEdit(new QLineEdit(this))
    , m_startDateEdit(new QDateEdit(this))
    , m_endDateEdit(new QDateEdit(this))
{
    m_tableView->setModel(m_model);
    m_tableView->horizontalHeader()->setStretchLastSection(true);
    m_tableView->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_tableView->verticalHeader()->setDefaultSectionSize(44);

    m_startDateEdit->setCalendarPopup(true);
    m_endDateEdit->setCalendarPopup(true);
    m_startDateEdit->setDate(QDate::currentDate().addMonths(-1));
    m_endDateEdit->setDate(QDate::currentDate());

    m_categoryFilterEdit->setPlaceholderText(QStringLiteral("按分类筛选（留空=全部）"));

    auto *applyBtn = new QPushButton(QStringLiteral("查询"), this);
    connect(applyBtn, &QPushButton::clicked, this, &HistoryPage::onFilterApplied);

    auto *filterLayout = new QHBoxLayout();
    filterLayout->addWidget(new QLabel(QStringLiteral("分类:"), this));
    filterLayout->addWidget(m_categoryFilterEdit);
    filterLayout->addWidget(new QLabel(QStringLiteral("从:"), this));
    filterLayout->addWidget(m_startDateEdit);
    filterLayout->addWidget(new QLabel(QStringLiteral("到:"), this));
    filterLayout->addWidget(m_endDateEdit);
    filterLayout->addWidget(applyBtn);

    auto *layout = new QVBoxLayout(this);
    layout->addLayout(filterLayout);
    layout->addWidget(m_tableView);

    refresh();
}

void HistoryPage::refresh()
{
    onFilterApplied();
}

void HistoryPage::onFilterApplied()
{
    const QString category = m_categoryFilterEdit->text();
    const QString startDate = m_startDateEdit->date().toString(Qt::ISODate);
    const QString endDate = m_endDateEdit->date().toString(Qt::ISODate);
    m_model->refresh(category, startDate, endDate);
}
