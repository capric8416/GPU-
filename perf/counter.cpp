// self
#include "counter.h"



#if defined(_WIN32)


PerfCounters::PerfCounters(QString path)
    : m_path(path)
    , m_hQuery(nullptr)
    , m_hCounter(nullptr)
    , m_pCounterValues(new PDH_FMT_COUNTERVALUE_ITEM[1])
{
    Setup();
}


PerfCounters::~PerfCounters()
{
    Teardown();
}


unsigned long PerfCounters::Collect()
{
    // Collect
    PdhCollectQueryData(m_hQuery);

    // Format
    PDH_STATUS status = ERROR_SUCCESS;
    DWORD valCount = 0;
    DWORD counterSize = 0;
    while ((status = PdhGetFormattedCounterArray(m_hCounter, PDH_FMT_LONG, &counterSize, &valCount, m_pCounterValues)) == PDH_MORE_DATA) {
        delete[] m_pCounterValues;
        m_pCounterValues = new PDH_FMT_COUNTERVALUE_ITEM[(counterSize / sizeof(PDH_FMT_COUNTERVALUE_ITEM)) + 1];
    }

    return valCount;
}


void PerfCounters::Setup()
{
    // Set data source
    PdhSetDefaultRealTimeDataSource(DATA_SOURCE_WBEM);

    // Open query
    if (PdhOpenQuery(NULL, 0, &m_hQuery) == ERROR_SUCCESS)
    {
        // Add counter
        PdhAddCounter(m_hQuery, m_path.toStdWString().c_str(), 0, &m_hCounter);

        PdhCollectQueryData(m_hQuery);
    }
}


void PerfCounters::Teardown()
{
    if (m_pCounterValues != nullptr) {
        delete[] m_pCounterValues;
        m_pCounterValues = nullptr;
    }

    if (m_hQuery != nullptr) {
        PdhCloseQuery(m_hQuery);
        m_hQuery = nullptr;
    }
}


#else
#error "Unsupported platform"
#endif


