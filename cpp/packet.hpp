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

#ifndef DEVELER_PACKET_GP_20120716
#define DEVELER_PACKET_GP_20120716

#include "sized_integers.hpp"
#include "utils/beginend.hpp"
#include "utils/count.hpp"
#include <string>
#include <cstddef>
#include <vector>
#include <stdexcept>
#include <algorithm>
#include <memory>
#include <iosfwd>

// class Packet
// -------------
//
// Represents a packet received from/sent to the serial port.
//
class Packet
{
public:
	// NOTE: keep this enum in sync with the array command_names[]
	//	    (see implementation file).
    enum CommandType { Command = 0, Ack, Received, AuthResponse, Response };
	static const char * command_names[];

    struct header
    {
        header() {}

        enum { command_len = 30, guid_len = 32, reserved_len = 16 };
        char _magic_char;
        CommandType _command;
        std::string _guid;
        uint32_t _packet_number;
        uint32_t _packet_count;
//		char _reserved[reserved_len];
        uint32_t _body_size;
    };

    static const std::size_t header_size =
        sizeof header()._magic_char + header::command_len + header::guid_len
            + sizeof header()._packet_number + sizeof header()._packet_count
            + header::reserved_len + sizeof header()._body_size;

	static bool commandTypeIsValid(CommandType);
	static std::string commandTypeToString(CommandType);
	static CommandType stringToCommandType(const std::string &);

	// NOTE: keep the enum in sync with the array
	enum ResponseType { Success, Error, TimeOut };
	static const char * response_strings[];
	static std::string responseTypeToString(ResponseType t);

public:

	Packet() {} // only used for std::map's requirements

	explicit Packet(const std::vector<char> & bytes);
	         Packet(CommandType t, const std::string & guid,
	        const std::string & body = "",
	        uint32_t number = 1, uint32_t count = 1);

	std::vector<char> toVector() const;

	static std::auto_ptr<Packet> createWithCommand(const std::string & guid, const std::string & command,
                                    const std::string & data);
	static std::auto_ptr<Packet> createWithAck(const std::string & guid);
	static std::auto_ptr<Packet> createWithReceived(std::string guid, uint32_t number =1,
	                                uint32_t count=1, bool timeout = false);
	static std::auto_ptr<Packet> createWithAuthResponse(const std::string & guid);
	static std::auto_ptr<Packet> createWithResponse(const std::string & guid,
	    ResponseType rt, const std::string & command_name="", const std::string & output_string="",
	    int return_code=0, const std::string & result_message = "");
    static header extractHeader(const std::vector<char>& bytes);

    static bool	hasHeader(const std::vector<char>& buffer);
    static bool hasHeaderAndFooter(const std::vector<char>& buffer);
    static bool hasRoomForFullPacket(const std::vector<char> &buffer);

	CommandType command() const;
	std::string guid() const;
	
	std::size_t number() const;
	std::size_t count() const;

	std::string body() const;

    size_t size() const;
    bool isSinglePacket() const;

public:
	static const char header_magic = '\x2';
	static const char footer_magic = '\x3';

    struct footer
    {
        uint32_t _crc32;
        char _magic_char;
    };

    static const std::size_t footer_size =
        sizeof footer()._crc32 + sizeof footer()._magic_char;
private:

	header _header;
	std::string _body;
	//footer _footer;
};

std::ostream &
operator <<(std::ostream & out, const Packet & p);

#endif
// vim: set ft=cpp noet ts=4 sts=4 sw=4:
