// self
#include "gpu.h"

// c/c++
#include <map>



#if defined(_WIN32)


GpuPerfCounters::GpuPerfCounters(QString type)
    : PerfCounters(QString("\\GPU Engine(*%1)\\Utilization Percentage").arg(type))
{
}


long GpuPerfCounters::Get()
{
    // Collect
    DWORD valCount = Collect();

    // Sum
    std::map<std::wstring, long> data;
    for (unsigned int i = 0; i < valCount && m_pCounterValues[i].szName != NULL; i++) {
        if ((m_pCounterValues[i].FmtValue.CStatus == PDH_CSTATUS_VALID_DATA)) {
            std::wstring path = std::wstring(m_pCounterValues[i].szName);
            size_t begin = path.find(L"_engtype_");
            std::wstring key = path.substr(begin + 9, path.size() - begin - 9);
            if (data.find(key) == data.end()) {
                data[key] = 0;
            }
            data[key] += m_pCounterValues[i].FmtValue.longValue;
        }
    }

    // Find max
    long percentage = 0;
    for (auto iter = data.begin(); iter != data.end(); iter++) {
        if (iter->second > percentage) {
            percentage = iter->second;
        }
    }

    return percentage;
}


#else
#error "Unsupported platform"
#endif


