#pragma once

// project
#include "counter.h"



#if defined(_WIN32)


class CpuPerfCounters : public PerfCounters
{
public:
    CpuPerfCounters();

    virtual long Get();
};






#else
#error "Unsupported platform"
#endif


