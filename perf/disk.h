#pragma once

// project
#include "counter.h"



class DiskWritePerfCounters : public PerfCounters
{
public:
    DiskWritePerfCounters();

    virtual long Get();
}
