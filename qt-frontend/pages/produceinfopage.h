#ifndef PRODUCEINFOPAGE_H
#define PRODUCEINFOPAGE_H

#include <QWidget>

class ProduceModel;
class QTableView;
class QLineEdit;
class QSpinBox;
class OnScreenKeyboardWidget;

// 触摸信息查询与录入：点击列表中的果蔬查看/编辑详情（名称、分类、保质期天数、
// 图标），通过屏幕虚拟键盘手动补录/修改。
class ProduceInfoPage : public QWidget
{
    Q_OBJECT
public:
    explicit ProduceInfoPage(QWidget *parent = nullptr);

public slots:
    void refresh();

private slots:
    void onRowSelected(const QModelIndex &index);
    void onSaveClicked();
    void onNewClicked();

private:
    void buildLayout();

    ProduceModel *m_model;
    QTableView *m_tableView;

    QLineEdit *m_nameEdit;
    QLineEdit *m_categoryEdit;
    QSpinBox *m_shelfLifeSpin;
    QLineEdit *m_idealTempEdit;

    OnScreenKeyboardWidget *m_keyboard;

    int m_editingId = 0;  // 0表示"新增"
};

#endif // PRODUCEINFOPAGE_H
