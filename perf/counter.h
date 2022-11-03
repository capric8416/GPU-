#pragma once

// windows
#include <Pdh.h>
#include <PdhMsg.h>

// qt
#include <QtCore/QString>



#if defined(_WIN32)


class PerfCounters
{
public:
    PerfCounters(QString path);
    virtual ~PerfCounters();

    unsigned long Collect();

    virtual long Get() = 0;


private:
    void Setup();
    void Teardown();


protected:
    QString m_path;
    HQUERY m_hQuery;
    HCOUNTER m_hCounter;
    PDH_FMT_COUNTERVALUE_ITEM *m_pCounterValues;
};






#else
#error "Unsupported platform"
#endif


