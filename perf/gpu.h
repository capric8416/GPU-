#pragma once

// project
#include "counter.h"



#if defined(_WIN32)


class GpuPerfCounters : public PerfCounters
{
public:
    // 
    // engtype_3D
    // engtype_VideoDecode
    GpuPerfCounters(QString type = "");

    virtual long Get();
};






#else
#error "Unsupported platform"
#endif


