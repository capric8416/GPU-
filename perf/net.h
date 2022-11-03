#pragma once

// project
#include "counter.h"



class NetReceivedPerfCounters : public PerfCounters
{
public:
    NetReceivedPerfCounters();

    virtual long Get();
}
