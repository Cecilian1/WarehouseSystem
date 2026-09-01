#include "produceinfopage.h"

#include "../data/models/producemodel.h"
#include "../widgets/onscreenkeyboardwidget.h"

#include <QApplication>
#include <QDate>
#include <QDateEdit>
#include <QDoubleSpinBox>
#include <QFormLayout>
#include <QFrame>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLineEdit>
#include <QPushButton>
#include <QScrollArea>
#include <QSpinBox>
#include <QTableView>
#include <QTimer>
#include <QVBoxLayout>

ProduceInfoPage::ProduceInfoPage(QWidget *parent)
    : QWidget(parent)
    , m_model(new ProduceModel(this))
    , m_tableView(new QTableView(this))
    , m_nameEdit(new QLineEdit(this))
    , m_categoryEdit(new QLineEdit(this))
    , m_shelfLifeSpin(new QSpinBox(this))
    , m_idealTempEdit(new QLineEdit(this))
    , m_quantitySpin(new QDoubleSpinBox(this))
    , m_expireDateEdit(new QDateEdit(this))
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
    // 保持系统输入法的默认策略，不限制为数字/拉丁字符；名称、分类和温湿度
    // 区间均可通过“中文输入”按钮调用板端拼音输入法。
    m_nameEdit->setInputMethodHints(Qt::ImhNone);
    m_categoryEdit->setInputMethodHints(Qt::ImhNone);
    m_idealTempEdit->setInputMethodHints(Qt::ImhNone);
    m_quantitySpin->setRange(0, 1000000);
    m_quantitySpin->setDecimals(2);
    m_expireDateEdit->setCalendarPopup(true);
    m_expireDateEdit->setDisplayFormat(QStringLiteral("yyyy-MM-dd"));
    m_expireDateEdit->setDate(QDate::currentDate());

    auto *formLayout = new QFormLayout();
    formLayout->addRow(QStringLiteral("名称"), m_nameEdit);
    formLayout->addRow(QStringLiteral("分类"), m_categoryEdit);
    formLayout->addRow(QStringLiteral("保质期(天)"), m_shelfLifeSpin);
    formLayout->addRow(QStringLiteral("建议温湿度区间"), m_idealTempEdit);
    formLayout->addRow(QStringLiteral("当前库存"), m_quantitySpin);
    formLayout->addRow(QStringLiteral("最早过期日期"), m_expireDateEdit);

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

    auto *rightWidget = new QWidget(this);
    rightWidget->setLayout(formContainer);
    auto *rightScroll = new QScrollArea(this);
    rightScroll->setWidgetResizable(true);
    rightScroll->setFrameShape(QFrame::NoFrame);
    rightScroll->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    rightScroll->setWidget(rightWidget);

    auto *mainLayout = new QHBoxLayout(this);
    mainLayout->addWidget(m_tableView, 3);
    mainLayout->addWidget(rightScroll, 2);

    // 哪个文本输入框获得焦点，屏幕键盘就写入哪个输入框。
    connect(qApp, &QApplication::focusChanged, this, [this](QWidget *, QWidget *now) {
        auto *lineEdit = qobject_cast<QLineEdit *>(now);
        if (lineEdit == m_nameEdit || lineEdit == m_categoryEdit || lineEdit == m_idealTempEdit) {
            m_keyboard->attachTarget(lineEdit);
            // 让触摸文本框成为唤起输入法的唯一动作，无需先点自绘英文键盘。
            QTimer::singleShot(0, m_keyboard, [this]() { m_keyboard->showSystemInputMethod(); });
        }
    });
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
    m_quantitySpin->setValue(row.currentQty);
    const QDate expireDate = QDate::fromString(row.earliestExpireDate, Qt::ISODate);
    m_expireDateEdit->setDate(expireDate.isValid() ? expireDate : QDate::currentDate());
}

void ProduceInfoPage::onNewClicked()
{
    m_editingId = 0;
    m_nameEdit->clear();
    m_categoryEdit->clear();
    m_shelfLifeSpin->setValue(0);
    m_idealTempEdit->clear();
    m_quantitySpin->setValue(0);
    m_expireDateEdit->setDate(QDate::currentDate());
}

void ProduceInfoPage::onSaveClicked()
{
    ProduceRow row;
    row.id = m_editingId;
    row.name = m_nameEdit->text();
    row.category = m_categoryEdit->text();
    row.shelfLifeDays = m_shelfLifeSpin->value();
    row.idealTempRange = m_idealTempEdit->text();
    row.currentQty = m_quantitySpin->value();
    row.earliestExpireDate = m_expireDateEdit->date().toString(Qt::ISODate);

    if (m_model->upsertProduce(row)) {
        onNewClicked();  // 保存成功后清空表单，回到"新增"状态
    }
}
