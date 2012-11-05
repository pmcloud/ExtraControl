#ifndef DEVELER_CRC32_GP_20120716
#define DEVELER_CRC32_GP_20120716
#include "sized_integers.hpp"

extern const uint32_t kCrc32Table[256];

class Crc32
{
public:

    Crc32() { Reset(); }
    ~Crc32() {}

    void Reset() { _crc = (uint32_t)~0; }

    const Crc32& AddData(const char* pData, const uint32_t length)
    {
        const char* pCur = pData;
        uint32_t remaining = length;
        for (; remaining--; ++pCur)
            _crc = ( _crc >> 8 ) ^ kCrc32Table[(_crc ^ *pCur) & 0xff];
        return *this;
    }

    uint32_t GetCrc32() const { return ~_crc; }

private:
    uint32_t _crc;
};

#endif
