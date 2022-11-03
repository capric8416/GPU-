// self
#include "net.h"



NetReceivedPerfCounters::NetReceivedPerfCounters()
    : PerfCounters("\\Network Interface(*)\\Bytes Received/sec")
{
}


long NetReceivedPerfCounters::Get()
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