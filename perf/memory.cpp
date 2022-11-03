// self
#include "memory.h"


#if defined(_WIN32)

// windows
#include <Windows.h>




MemPerfCounters::MemPerfCounters()
{
}


MemPerfCounters::~MemPerfCounters()
{
}


unsigned long MemPerfCounters::Get()
{
    MEMORYSTATUSEX statex;
    statex.dwLength = sizeof(statex);

    GlobalMemoryStatusEx(&statex);

    return statex.dwMemoryLoad;
}


#else
#error "Unsupported platform"
#endif
