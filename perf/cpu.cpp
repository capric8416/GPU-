// self
#include "cpu.h"



#if defined(_WIN32)


CpuPerfCounters::CpuPerfCounters()
    : PerfCounters("\\Processor Information(_Total)\\% Processor Time")
{
}



long CpuPerfCounters::Get()
{
    // Collect
    DWORD valCount = Collect();

    // Sum
    long percentage = 0;
    for (unsigned int i = 0; i < valCount && m_pCounterValues[i].szName != NULL; i++) {
        if ((m_pCounterValues[i].FmtValue.CStatus == PDH_CSTATUS_VALID_DATA)) {
            percentage += m_pCounterValues[i].FmtValue.longValue;
        }
    }

    return percentage;
}


#else
#error "Unsupported platform"
#endif


