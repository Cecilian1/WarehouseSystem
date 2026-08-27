#include "pollingtimer.h"

PollingTimer::PollingTimer(int intervalMs, QObject *parent)
    : QObject(parent)
{
    m_timer.setInterval(intervalMs);
    connect(&m_timer, &QTimer::timeout, this, &PollingTimer::dataMayHaveChanged);
}

void PollingTimer::start()
{
    m_timer.start();
}

void PollingTimer::stop()
{
    m_timer.stop();
}
