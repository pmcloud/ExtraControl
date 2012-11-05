//
// Copyright (c) 2006 Cosmin Luta
//
// Permission is hereby granted, free of charge, to any person obtaining
// a copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so, subject to
// the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
// IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
// CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
// TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//

#ifndef __OPTION_PARSER_H
#define __OPTION_PARSER_H

#include <vector>
#include <map>
#include <string>

#ifdef _UNICODE
	typedef std::wstring String;
	typedef wchar_t TCHAR;
	#define	IS_ALPHA(x) iswalpha(x)
#else
	typedef std::string String;
	typedef char TCHAR;
	#define IS_ALPHA(x) isalpha(x)
#endif

#ifndef _T
    #ifdef _UNICODE
        #define _T(x) L##x
    #else
        #define _T(x) x
    #endif
#endif

//
// OptParser's error codes
//
#define E_OK			0	///< Success
#define E_ERROR   		1	///< Generic error
#define E_OPT_UNKNOWN		2 	///< Unknown switch/option
#define E_OPT_MISSING 		4 	///< Mandatory option was missing
#define E_OPT_DUPLICATE 	8 	///< Duplicate option (when adding an option)
#define E_ARG_EXPECTED 		16 	///< Expected argument missing
#define E_ARG_INVALID		32 	///< Argument was not validated
#define E_INVALID 		64  	///< Invalid parameter given to function
#define E_OPT_TMO		128	///< Too many occurences of this switch
 
#define CB_OPT_UNKNOWN	1		///< An unknown switch has been found on the commandline
#define CB_OPT_MALFORMED 2		///< Malformed option: either it has an argument that wasn't expected
#define CB_OPT_MISSING  3		///< A required option was missing
#define CB_ARG_MISSING  4		///< Argument missing
#define CB_ARG_INVALID  5		///< Argument is invalid (has validator, not validated)
#define CB_OPT_TMO 6			///< Too many occurences of this switch

 
//
// Flags for addOption. Can be OR'ed together.
//
#define OPT_NONE 	0		///< This option has no flags
#define OPT_REQUIRED 	1		///< Option required for the command line to be valid
#define OPT_NEEDARG  	2		///< Option needs an argument
#define OPT_MULTI	4		///< Switch can appear multiple times (not compatible with NEEDARG)
#define OPT_HELP	8		///< This is the help switch, will invoke help callback for every defined option

//
// Flags for the parser
//
#define OPT_PARSE_INCLUDE_ARGV0 1   	///< Include argv[0] in the list of free args
#define OPT_PARSE_QUOTED_ARGS	2	///< Allow quoted args like --s="asd asd" and "asd asd"
#define OPT_PARSE_UNQUOTE_ARGS	4	///< Unquote quoted args "asd asd" --> asd asd -- must be set with the previous flag

// NOT IMPLEMENTED YET
#define OPT_PARSE_AUTO_VERSION  16	///< Automatically generate -v and --version
#define OPT_PARSE_AUTO_HELP     32	///< Automatically generate -h and --help


/**
 * @brief Options class, stores all options and helps parsing.
 */
class Options
{
	friend class Parser;
    
public:
	//! Callback used to impose constraints on options
	typedef bool (*option_validator)(const String&);
	typedef int  (*generic_callback)(int, const String&);	///< Generic callback type
	typedef int  (*help_callback)(const String&, const String&, const String&, int);

	Options();
	~Options();
    
	/**
	 * @param p_short String describing the short form of this option, e.g "-s"
	 * @param p_long String describing the long form of this option, e.g. "--start"
	 * @param p_help Documentation for this parameter, e.g. "Start the server"
	 * @param p_flags Flags for this option
	 * @param p_validator Callback used to validate the value of the argument (NULL if no validation required or no argument for this opt)
	 * @return E_ERROR when there was a failure allocating memory
	 * @return E_INVALID if both option strings are empty or the option was given a validator even if not needed
	 * @return E_OPT_DUPLICATE if there was another option by this name
	 * @return E_OK if everything went ok
	 */
	int addOption(const String& p_short, const String& p_long, const String& p_help, int p_flags, option_validator p_validator);
    
	/**
	 * @param p_opt String containing the option whose argument is to be retrieved
	 * @return Argument given on the commandline to the requested option
	 * @return Empty string in case the option is invalid or missing or no argument was found
	 */
	String asString(const String& p_opt);
    
	/**
	 * Example:  bool b = isOptionSet("-s");
	 * @param p_opt String containing the option to look for.
	 * @return true If the option was specified on the command line
	 * @return false Otherwise
	 */
	bool isSet(const String& p_opt);
    
    
	/**
	 * Sets callback for invalid command line options encountered
	 * @param p_callback Pointer to function to call on invalid opts
	 */
	void setErrorCallback( generic_callback p_callback );

	/**
	 * Sets callback for help generation (invoked when encountered) -h or --help.
	 * If not set, default will be used 
	 * @param p_callback Pointer to function to call on help generation.
	 */
	void setHelpCallback( help_callback p_callback );
    
	/**
	 * Reset the options object
	 */
	void reset();
    
	#ifdef _DEBUG
	void dump_options();
	#endif

private:

	////////////////////////////////////////////////////////////////////
	// Variables and Data Structures
	////////////////////////////////////////////////////////////////////
    
	//! Internal structure for keeping option settings
	struct _option          
	{
		_option(const String& p_short,
			const String& p_long,
			const String& p_help,
			int p_flags,
			option_validator p_option)
				: m_count(0)
				, m_validArg(true)
				, m_flags(p_flags)
				, m_help(p_help)
				, m_shortName(p_short)
				, m_longName(p_long)
				, m_optionValidator(p_option)
		{
			//
			// We don't want to throw an exception, but set m_optionValidator
			// to NULL if the option doesn't require an argument.
			//
			if (!(m_flags & OPT_REQUIRED)) 
			{
				m_optionValidator = NULL;
			}
	        }
        
		int	m_count;		///< How many times this has been found

		//
		// Internal flags
		//
		int m_validArg;			///< Option's argument is valid
		int m_flags;			///< Flags for this option
        
		String m_arg;       		///< Matched arg
		String m_help;      		///< Help description for this option
		String m_shortName;		///< Short option name
		String m_longName;		///< Long option name
		option_validator m_optionValidator; ///< Callback for validating options
	};
    
	typedef std::map<String, _option*> OptionMap;
    
	//
	// Map for short options (one dash) -- for fast searching, instead of linear in a vector
	//
	OptionMap m_shortOpts;
    
	// 
	// Map for long options (two dashes) -- for fast searching, instead of linear in a vector
	//
	OptionMap m_longOpts;
    
	//
	// Vector to keep all the options in order. Needed for help generation and resource de-allocation.
	//    
	std::vector<_option*> m_orderedOpts;
    
	//
	// Pointer to the _option structure who's argument should be next on
	// the commandline.
	//
	_option* m_waitingArg; 
    
	//
	// Vector for free arguments
	//
	std::vector<String> m_freeArgs;
    
	//
	// Callbacks
	//
	generic_callback m_errorCallback;	// Invalid argument
	help_callback m_helpCallback;		// Called when encountering -h or --help
    
    
	////////////////////////////////////////////////////////////////////
	// Functions
	////////////////////////////////////////////////////////////////////

	static int _defaultHelpCallback(const String&, const String&, const String&, int flags);

	/**
	 * This is called when a OPT_HELP type option is encountered
	 */
	int _generateHelp();
	
	//! Returns an error code reflecting the state of the option parser
	int _validateState();
  
	/**
	 * Internal helper function. Give it the a short option (e.g. "-s")
	 * from the commandline and it will properly set flags inside the 
	 * structures.
	 * 
	 * @param p_opt Option from the commandline
	 * @return E_OK if the handling was ok
	 * @return E_ERROR if the string was empty
	 * @return E_OPT_UNKNOWN if the given option was not known
	 */
	int _handleShortOption(const String& p_opt);
    
	/**
	 * Internal helper function. Give it the a long option (e.g. "--start")
	 * from the commandline and it will properly set flags inside the 
	 * structures.
	 * 
	 * @param p_opt Option from the commandline
	 * @return E_OK if the handling was ok
	 * @return E_OPT_UNKNOWN if the given option was not known
	 * @return E_ERROR if the option was empty or invalid somehow (e.g. "--=asd" or argument given if not expected)
	 * @return E_ARG_EXPECTED if the option needs an argument and none given (e.g --start instead of --start=now) 
	 */
	int _handleLongOption(const String& p_opt);
    
	/**
	 * Internal helper function. Called by the Parser class for each argument on the
	 * command line.
	 * 
	 * @param p_arg Argument from the commandline
	 * @warning Can return bitmask!
	 * @return E_OK if the handling was ok
	 * @return E_OPT_UNKNOWN if the given option was not known
	 * @return E_ERROR if the option was empty or invalid somehow (e.g. "--=asd" or argument given if not expected)
	 * @return E_ARG_EXPECTED if the option needs an argument and none given (e.g --start instead of --start=now)
	 */
	int _processArg(const String& p_arg);
    
	/**
	 * Returns true if the string is a valid short option, in the current options context
	 */
	bool _validShortOpt(const String& p_arg);

	/**
	 * Returns true if the string is a valid long option, in the current options context
	 */
	bool _validLongOpt(const String& p_arg);
	
	/**
	 * Inserts an option into one of the maps while checking for duplicates.
	 * @param p_map The map to insert option into
	 * @param p_name The name of the option
	 * @param p_optPtr Pointer to the option structure to be inserted
	 * @return E_OPT_DUPLICATE if there is another entry with this name in the map
	 * @return E_OK if everything went ok
	 */
	int _insertOption(OptionMap& p_map, const String& p_name, _option* p_optPtr);
    
	_option* _getOptionByName(const String& p_opt, const OptionMap& p_map) const
	{
		OptionMap::const_iterator it = p_map.find(p_opt);
		return ( it != p_map.end() ) ? it->second : NULL;
	}
    
	_option* _getShortOptionByname(const String& p_opt) const
	{
		return _getOptionByName(p_opt, m_shortOpts);
	}
    
	_option* _getLongOptionByname(const String& p_opt) const
	{
		return _getOptionByName(p_opt, m_longOpts);
	}
    
	_option* _getOptionByName(const String& p_opt) const
	{
		if ( p_opt.size() == 2 && p_opt[0] == _T('-') )
		{
			return _getShortOptionByname(p_opt);
		}
		else if ( p_opt.size() >= 3 && p_opt.find( _T("--"),0,2) == 0 )
		{
			return _getLongOptionByname(p_opt);
		}
        
		//TODO: Error callback because of invalid option ?
		return NULL;
	}
};

/**
 * @brief Parser class
 */
class Parser
{
public:
   
	Parser();
	~Parser();
    
	/**
	 * Parse command line arguments given in the classical form of (argc, argv).
	 * @param p_argc Number of arguments including program name (argv[0])
	 * @param p_argv Array of TCHAR* containing the arguments
	 * @param p_opts Options class containing the expected options
	 * @warning Can return bitmasked answer!
	 * @return E_OK if the parsing was successfull and all required options and args were ok
	 * @return E_OPT_UNKNOWN if the given option was not known
	 * @return E_ERROR if the option was empty or invalid somehow (e.g. "--=asd" or argument given if not expected)
	 * @return E_ARG_EXPECTED if the option needs an argument and none given (e.g --start instead of --start=now)
	 * @return E_ARG_INVALID if one of the options with argument validators wasn't validated :)
	 * 
	 */
	int parse(int p_argc, TCHAR** p_argv, Options& p_opts);
    
	/**
	 * Parse command line arguments given in the windows GetCommandLine() form.
	 * @param p_cmdLine Commandline string
	 * @param p_opts Options class containing the expected options
	 * @warning Can return bitmasked answer!
	 * @return E_OK if the parsing was successfull and all required options and args were ok
	 * @return E_OPT_UNKNOWN if the given option was not known
	 * @return E_ERROR if the option was empty or invalid somehow (e.g. "--=asd" or argument given if not expected)
	 * @return E_ARG_EXPECTED if the option needs an argument and none given (e.g --start instead of --start=now)
	 * @return E_ARG_INVALID if one of the options with argument validators wasn't validated :)
	 */
	int parse(const TCHAR* p_cmdLine, Options& p_opts);
    
	/**
	 * Sets flags for the parser
	 */
	void setFlags(int p_flags);
    
private:
	// Internal methods used to parse windows style command line
	int _state_handle_space(String& p_opt, TCHAR c, int& current_state, Options& p_opts);
	int _state_handle_quote(String& p_opt, TCHAR c, int& current_state);
	int _state_handle_escape(String& p_opt, TCHAR c, int& current_state);
	int _state_handle_other(String& p_opt, TCHAR c, int& current_state);
	int pre_parse(Options&);

	enum { S_NORMAL, S_ESCAPE, S_QUOTED, S_DELIMITER };

private:
	// Variables
	int m_flags;
};

#endif

