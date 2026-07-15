#include "produceinfopage.h"

#include "../data/models/producemodel.h"
#include "../widgets/onscreenkeyboardwidget.h"

#include <QFormLayout>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLineEdit>
#include <QPushButton>
#include <QSpinBox>
#include <QTableView>
#include <QVBoxLayout>

ProduceInfoPage::ProduceInfoPage(QWidget *parent)
    : QWidget(parent)
    , m_model(new ProduceModel(this))
    , m_tableView(new QTableView(this))
    , m_nameEdit(new QLineEdit(this))
    , m_categoryEdit(new QLineEdit(this))
    , m_shelfLifeSpin(new QSpinBox(this))
    , m_idealTempEdit(new QLineEdit(this))
    , m_keyboard(new OnScreenKeyboardWidget(this))
{
    buildLayout();
    refresh();
}

void ProduceInfoPage::buildLayout()
{
    m_tableView->setModel(m_model);
    m_tableView->horizontalHeader()->setStretchLastSection(true);
    m_tableView->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_tableView->setEditTriggers(QAbstractItemView::NoEditTriggers);
    connect(m_tableView, &QTableView::clicked, this, &ProduceInfoPage::onRowSelected);

    m_shelfLifeSpin->setRange(0, 3650);

    auto *formLayout = new QFormLayout();
    formLayout->addRow(QStringLiteral("名称"), m_nameEdit);
    formLayout->addRow(QStringLiteral("分类"), m_categoryEdit);
    formLayout->addRow(QStringLiteral("保质期(天)"), m_shelfLifeSpin);
    formLayout->addRow(QStringLiteral("建议温湿度区间"), m_idealTempEdit);

    auto *newBtn = new QPushButton(QStringLiteral("新增"), this);
    auto *saveBtn = new QPushButton(QStringLiteral("保存"), this);
    connect(newBtn, &QPushButton::clicked, this, &ProduceInfoPage::onNewClicked);
    connect(saveBtn, &QPushButton::clicked, this, &ProduceInfoPage::onSaveClicked);

    auto *btnLayout = new QHBoxLayout();
    btnLayout->addWidget(newBtn);
    btnLayout->addWidget(saveBtn);

    auto *formContainer = new QVBoxLayout();
    formContainer->addLayout(formLayout);
    formContainer->addLayout(btnLayout);
    formContainer->addWidget(m_keyboard);

    auto *mainLayout = new QHBoxLayout(this);
    mainLayout->addWidget(m_tableView, 2);

    auto *rightWidget = new QWidget(this);
    rightWidget->setLayout(formContainer);
    mainLayout->addWidget(rightWidget, 1);

    // 触摸获得焦点的输入框成为虚拟键盘的当前目标
    connect(m_nameEdit, &QLineEdit::returnPressed, this, [this]() { m_keyboard->attachTarget(m_nameEdit); });
    // 简化处理：进入编辑区域时默认绑定名称输入框，开发者可后续用
    // QApplication::focusChanged信号做到"哪个输入框获焦就绑定哪个"的完整体验
    m_keyboard->attachTarget(m_nameEdit);
}

void ProduceInfoPage::refresh()
{
    m_model->refresh();
}

void ProduceInfoPage::onRowSelected(const QModelIndex &index)
{
    if (!index.isValid())
        return;

    const ProduceRow &row = m_model->rowAt(index.row());
    m_editingId = row.id;
    m_nameEdit->setText(row.name);
    m_categoryEdit->setText(row.category);
    m_shelfLifeSpin->setValue(row.shelfLifeDays);
    m_idealTempEdit->setText(row.idealTempRange);
}

void ProduceInfoPage::onNewClicked()
{
    m_editingId = 0;
    m_nameEdit->clear();
    m_categoryEdit->clear();
    m_shelfLifeSpin->setValue(0);
    m_idealTempEdit->clear();
}

void ProduceInfoPage::onSaveClicked()
{
    ProduceRow row;
    row.id = m_editingId;
    row.name = m_nameEdit->text();
    row.category = m_categoryEdit->text();
    row.shelfLifeDays = m_shelfLifeSpin->value();
    row.idealTempRange = m_idealTempEdit->text();

    if (m_model->upsertProduce(row)) {
        onNewClicked();  // 保存成功后清空表单，回到"新增"状态
    }
}
