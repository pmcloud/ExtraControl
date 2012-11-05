// ExtraControl - Aruba Cloud Computing ExtraControl
// Copyright (C) 2012 Aruba S.p.A.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

#include "packet.hpp"
#include "utils/beginend.hpp"
#include "utils/tostring.hpp"
#include "third-party/crc32/crc.h"
#include <cstddef>
#include <cassert>
#include <vector>
#include <sstream>
#include <algorithm>
#include <functional>
#include <cctype>
#include <iostream>

#if ! defined _MSC_VER
const std::size_t
Packet::header_size;

const std::size_t
Packet::footer_size;

const char
Packet::header_magic;

const char
Packet::footer_magic;
#endif

const char *
Packet::command_names[] =
	{ "COMMAND", "ACK", "RECEIVED", "AUTHRESPONSE", "RESPONSE" };

const char *
Packet::response_strings[] =
    { "Success", "Error", "TimeOut"};

Packet::Packet(Packet::CommandType t, const std::string & guid,
               const std::string & body,
               uint32_t number, uint32_t count)
{
	_header._magic_char = header_magic;
	_header._command = t;
	_header._guid = guid;
	_header._packet_number = number;
	_header._packet_count = count;
	_body = body;
	_header._body_size = _body.size();
}

uint32_t unmarshalUint32(const char * start)
{
	const unsigned char * p = reinterpret_cast<
	    const unsigned char*>(start);
	return (static_cast<uint32_t>(p[0])      ) |
	       (static_cast<uint32_t>(p[1]) << 8 ) |
	       (static_cast<uint32_t>(p[2]) << 16) |
	       (static_cast<uint32_t>(p[3]) << 24)
	       ;
}

std::vector<char> marshalUint32(uint32_t x)
{
	std::vector<char> result(4);
	result[0] =  x        & 0xFF;
	result[1] = (x >> 8 ) & 0xFF;
	result[2] = (x >> 16) & 0xFF;
	result[3] = (x >> 24) & 0xFF;
	return result;
}

std::string escape(const std::string & s)
{
    std::stringstream out;
    for (int i=0; i < static_cast<int>(s.size()); ++i)
    {
        switch (s[i])
        {
        case '&':
            out << "&amp;";
            break;
        case '<':
            out << "&lt;";
            break;
        case '>':
            out << "&gt;";
            break;
        default:
            out << s[i];
            break;
        }
    }
    return out.str();
}

bool Packet::commandTypeIsValid(CommandType t)
{
	return Packet::Command <= t && t <= Packet::Response;
}

std::string Packet::commandTypeToString(CommandType t)
{
	assert(commandTypeIsValid(t));
	return command_names[static_cast<int>(t)];
}

Packet::CommandType
Packet::stringToCommandType(const std::string & s)
{
	const char ** p = std::find(begin(command_names), end(command_names), s);
	if (p == end(command_names)) {
		throw std::runtime_error("Invalid command field");
	}
	return static_cast<CommandType>(p - begin(command_names));
}

std::string Packet::responseTypeToString(ResponseType rt)
{
	return response_strings[static_cast<int>(rt)];
}


bool guidIsValid(const std::string & s)
{
	for (std::string::const_iterator it = s.begin(); it != s.end(); ++it) {
		if (!std::isxdigit(static_cast<unsigned char>(*it))) {
			return false;
		}
	}
	return true;
}


Packet::Packet(const std::vector<char> & bytes)
{
	assert(hasRoomForFullPacket(bytes));
    _header = Packet::extractHeader(bytes);
	const uint32_t recv_crc= unmarshalUint32(&bytes[header_size + _header._body_size]);
    const uint32_t calc_crc = Crc32().
            AddData(&bytes[0], bytes.size() - footer_size).
            GetCrc32();

	if (recv_crc != calc_crc) {
		throw std::runtime_error("CRC error");
	}

	_body.resize(_header._body_size);
    std::copy(&bytes[header_size], &bytes[header_size] + _header._body_size, begin(_body));
}

std::vector<char> Packet::toVector() const
{
	std::string s;
	s += header_magic;
	std::string ct = commandTypeToString(_header._command);
	ct.resize(Packet::header::command_len);
	s += ct;
	s += _header._guid;
	std::vector<char> m = marshalUint32(_header._packet_number);
	s.append(&m[0], m.size());
	m = marshalUint32(_header._packet_count);
	s.append(&m[0], m.size());

	const std::string reserved(Packet::header::reserved_len, '\0');
	s += reserved;
	m = marshalUint32(_header._body_size);
	s.append(&m[0], m.size());
	s += _body;

    const uint32_t crc = Crc32().AddData(s.c_str(), s.size()).GetCrc32();
	m = marshalUint32(crc);
	s.append(&m[0], m.size());
	s += footer_magic;
	return std::vector<char>(s.begin(), s.end());
}

std::auto_ptr<Packet> Packet::createWithCommand(const std::string & guid,
												const std::string & command,
                                                const std::string & data)
{
    std::ostringstream cmd("<command>");
    cmd << "<commandString>" << escape(command) << "</commandString>";
    if (!data.empty())
        cmd << "<binaryData>" << data << "</binaryData>";
    cmd << "</command>";
    return std::auto_ptr<Packet>( new Packet(Packet::Command, guid, cmd.str()) );
}

std::auto_ptr<Packet> Packet::createWithAck(const std::string & guid)
{
	return std::auto_ptr<Packet>(new Packet(Packet::Ack, guid, ""));
}

std::auto_ptr<Packet> Packet::createWithReceived(std::string guid, uint32_t number,
                                 uint32_t count, bool timeout)
{
	std::string body = timeout
		? "<responseType>TimeOut</responseType>"
		: "<responseType>Success</responseType>";
	return std::auto_ptr<Packet>(new Packet(Packet::Received, guid, body, number, count));
}

std::auto_ptr<Packet> Packet::createWithAuthResponse(const std::string & guid)
{
	return std::auto_ptr<Packet>(new Packet(Packet::AuthResponse, guid));
}

std::auto_ptr<Packet> Packet::createWithResponse(const std::string & guid,
        ResponseType r, const std::string & command_name, const std::string & output_string,
        int return_code, const std::string & result_message)
{
	assert( r == Packet::Success || r == Packet::Error || r == Packet::TimeOut);

	const std::string rt = "<responseType>" + responseTypeToString(r) + "</responseType>";
	const std::string rc = "<resultCode>" + ::toString(return_code) + "</resultCode>";
	const std::string rm = "<resultMessage>" + escape(result_message) + "</resultMessage>";
	const std::string cn = "<commandName>" + escape(command_name) + "</commandName>";
	const std::string os = "<outputString>" + escape(output_string) + "</outputString>";
	const std::string body = "<response>" + rt + rc + rm + cn + os + "</response>";
	return std::auto_ptr<Packet>(new Packet(Packet::Response, guid, body));
}

Packet::header Packet::extractHeader(const std::vector<char>& bytes)
{
    header h;
    if (bytes[0] != Packet::header_magic) {
        throw std::runtime_error("no magic number");
    }

    h._magic_char = bytes[0];
    std::size_t index = 1;
    h._command = Packet::stringToCommandType(
        std::string(&bytes[index]));

    index += header::command_len;
    h._guid = std::string(&bytes[index], header::guid_len);

    if (!guidIsValid(h._guid)) {
        throw std::runtime_error("invalid GUID");
    }

    index += header::guid_len;
    h._packet_number = unmarshalUint32(&bytes[index]);
    index += sizeof(h._packet_number);
    h._packet_count = unmarshalUint32(&bytes[index]);
    index += sizeof(h._packet_count);

    if (h._packet_number > h._packet_count) {
        throw std::runtime_error("packet number greater than packet count");
    }

    index += header::reserved_len;
    h._body_size = unmarshalUint32(&bytes[index]);
    return h;
}

bool Packet::hasHeader(const std::vector<char> & v)
{
    return v.size() >= Packet::header_size;
}

bool Packet::hasHeaderAndFooter(const std::vector<char>& buffer)
{
    Packet::header h = Packet::extractHeader(buffer);
    return buffer.size() >= Packet::header_size + h._body_size + Packet::footer_size;
}

bool Packet::hasRoomForFullPacket(const std::vector<char> & v)
{
	if (v.size() >= (Packet::header_size + Packet::footer_size)) {
		const std::size_t pos = Packet::header_size - sizeof header()._body_size;
		return v.size() >= Packet::header_size + unmarshalUint32(&v[pos]) + Packet::footer_size;
	} else {
		return false;
	}
}

Packet::CommandType Packet::command() const
{
	return _header._command;
}
std::string Packet::guid() const
{
	return _header._guid;
}

std::size_t Packet::number() const
{
	return _header._packet_number;
}

std::size_t Packet::count() const
{
	return _header._packet_count;
}

std::string Packet::body() const
{
	return _body;
}

size_t Packet::size() const
{
    return Packet::header_size + _header._body_size + Packet::footer_size;
}

bool Packet::isSinglePacket() const
{
    return count() == 1 && number() == 1;
}

// vim: set ft=cpp noet ts=4 sts=4 sw=4:
