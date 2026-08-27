QT += core gui sql

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++17

TARGET = WarehouseKeeper
TEMPLATE = app

SOURCES += \
    main.cpp \
    app/mainwindow.cpp \
    app/navigationbar.cpp \
    pages/inventoryboardpage.cpp \
    pages/recognitionpage.cpp \
    pages/produceinfopage.cpp \
    pages/historypage.cpp \
    pages/alertpage.cpp \
    pages/envstatuscard.cpp \
    widgets/onscreenkeyboardwidget.cpp \
    data/databasemanager.cpp \
    data/pollingtimer.cpp \
    data/models/producemodel.cpp \
    data/models/inventorylogmodel.cpp \
    data/models/alertmodel.cpp \
    data/models/envlogmodel.cpp

HEADERS += \
    app/mainwindow.h \
    app/navigationbar.h \
    pages/inventoryboardpage.h \
    pages/recognitionpage.h \
    pages/produceinfopage.h \
    pages/historypage.h \
    pages/alertpage.h \
    pages/envstatuscard.h \
    widgets/onscreenkeyboardwidget.h \
    data/databasemanager.h \
    data/pollingtimer.h \
    data/models/producemodel.h \
    data/models/inventorylogmodel.h \
    data/models/alertmodel.h \
    data/models/envlogmodel.h

RESOURCES += \
    resources/warehousekeeper.qrc

# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target
