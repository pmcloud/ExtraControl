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


//
// CHANGELOG
//
// v0.2 - First beta
// 	* added support for help callbacks
// 	* bugfixes
//
// v0.1 - Initial release - November 30, 2006
//
//      * supports short options (like -s, -r) and long options (--file, --save=readme.txt)
//      * error callbacks for invalid options
//


//
// Possible problems:
// - Unicode handling: help displaying.
//
// TODO:
// [ -- ] Parameter defaults and optional arguments for longopts ? --short[=default]
// [ -- ] Allow one-of type of switches, i.e. require either -y or -n
// [ -- ] Allow groups of switches in which all options are requested (perhaps 
//        same as above, but with an option to specify AND instead of OR
// [ -- ] Flag in the parser, to stop after the first error or to continue
// BUGS:
//
//

#include <cstdio>
#include <cassert>

#if defined(_LINUX)
#include <cwchar>
#endif

#include "optparse.h"

using namespace std;

#define ERROR_CALLBACK(err, msg) if ( m_errorCallback ) (*m_errorCallback)(err, msg)

///////////////////////////////////////////////////////////////////////////////
//
// Options
//
///////////////////////////////////////////////////////////////////////////////


Options::Options() 
	: m_waitingArg(NULL)
	, m_errorCallback(NULL)
	, m_helpCallback(NULL)
{}

Options::~Options()
{
	reset();
}

///////////////////////////////////////////////////////////////////////////////
// Options - PUBLIC functions
///////////////////////////////////////////////////////////////////////////////

void Options::reset()
{
	//
	// Both maps contain the same pointers, so we'll delete only from one
	//
	vector<_option*>::iterator it = m_orderedOpts.begin();
    
	for ( ; it != m_orderedOpts.end(); ++it )
	{
		delete *it;
	}
    
	m_shortOpts.clear();
	m_longOpts.clear();
	m_orderedOpts.clear();
}

//
// Set callback for invalid options
//
void Options::setErrorCallback( generic_callback p_callback )
{
	m_errorCallback = p_callback;
}

//
// Set callback for help generation
//
void Options::setHelpCallback( help_callback p_callback )
{
	m_helpCallback = p_callback;
}

//
// Add new option to the Options object
//
int Options::addOption(const String& p_short, const String& p_long,
                       const String& p_help, int p_flags, 
                       option_validator p_validator)
{
	if ( p_short.empty() && p_long.empty() )
	{
		return E_INVALID;
	}
    
	//
	// Basic sanity checks.
	//
	if ( (p_flags & OPT_NEEDARG)==0 && p_validator != NULL )
	{
		// Option doesn't need argument, but validator set
		return E_INVALID;    	
	}

	if ( (p_flags & OPT_MULTI) && (p_flags & OPT_NEEDARG) )
	{
		// Not allowing multiple occurences and arguments at this time.
		return E_INVALID;
	}

	//
	// TODO: Option name validators, i.e. only '-'char is valid for short opts and -- 
	// something for long
	//
    
	_option* ptr = new (nothrow) _option(p_short, p_long, p_help, 
						p_flags, p_validator);
    
	if (!ptr)
	{
		return E_ERROR;
	}
    
	bool accepted 	= false;
	bool duplicate 	= false;
    
	if ( !p_short.empty() )
	{
		if ( !_validShortOpt(p_short) )
		{
			return E_INVALID;
		}

		if ( E_OPT_DUPLICATE == _insertOption(m_shortOpts, p_short, ptr) )
		{
			duplicate = true;
		}
		else
		{
        		accepted = true;
		}
	}
    
	if ( !p_long.empty() )
	{
		if ( !_validLongOpt(p_long) )
		{
			return E_INVALID;
		}

		if ( E_OPT_DUPLICATE == _insertOption(m_longOpts, p_long, ptr) )
		{
			duplicate = true;
		}
		else
		{
			accepted = true;
		} 
	}
    
	if ( !accepted || duplicate )
	{
		// Free memory, because this option wasn't accepted
		delete ptr;
	}
	else
	{
		m_orderedOpts.push_back(ptr);
	}
    
	return (duplicate) ? E_OPT_DUPLICATE : E_OK ;
}

//
// Return the argument of the option as a string
//
String Options::asString(const String& p_opt)
{
    _option* opt = _getOptionByName(p_opt);
    
    if (opt)
    {
        // m_arg will be empty if the option was not present on the commandline
        // thus being equivalent to return ""
        return opt->m_arg;
    }
        
    return _T("");
}

//
// Return true if an option was present or false if not
//
bool Options::isSet(const String& p_opt)
{
    _option* opt = _getOptionByName(p_opt);
    
    return ( opt ) ? (opt->m_count>0) : false;
}


#ifdef _DEBUG
void Options::dump_options()
{
    OptionMap::const_iterator it;
    
    for ( it = m_shortOpts.begin(); it != m_shortOpts.end(); ++it )
    {
        _option* p = it->second;
        
        printf("\nOptions [%s] at %p", it->first.c_str(), p);
        printf("\n\tRequired: %d", p->m_flags & OPT_REQUIRED);
		printf("\n\tNeedsArg: %d", p->m_flags & OPT_NEEDARG);
        printf("\n\tCount   : %d", p->m_count);
        printf("\n\tArg     : %s", p->m_arg.c_str());
        printf("\n\tValid   : %d", p->m_validArg);
        printf("\n\tOptValid: %p", p->m_optionValidator);
        printf("\n\tHelp    : %s", p->m_help.c_str());
        printf("\n");
    }
    
    printf("\nFree arguments: ");
    
    vector<String>::const_iterator it2 = m_freeArgs.begin();
    
    for ( ; it2 != m_freeArgs.end(); ++it2 )
    {
        printf("%s ", (*it2).c_str());
    }
        
    printf("\n");
    
}
#endif

///////////////////////////////////////////////////////////////////////////////
//
// PRIVATE
//
///////////////////////////////////////////////////////////////////////////////

//
// Insert option to the an optionmap
//
int Options::_insertOption(OptionMap& p_map, const String& p_name, _option* p_optPtr)
{
	OptionMap::const_iterator it = p_map.find(p_name);
	
	if ( it != p_map.end() )
	{
		return E_OPT_DUPLICATE;
	}
	
	p_map.insert( make_pair<String, _option*>( p_name, p_optPtr ) );
	
	return E_OK;
}

bool Options::_validShortOpt(const String& p_arg)
{
	return ( p_arg.size() == 2 && p_arg[0] == _T('-') && IS_ALPHA(p_arg[1]) );
}

bool Options::_validLongOpt(const String& p_arg)
{
	return ( p_arg.size() >= 3 && p_arg[0] == _T('-') && p_arg[1] == _T('-') && IS_ALPHA(p_arg[2]) );
}

int Options::_defaultHelpCallback(const String& p_short, const String& p_long, const String& p_desc, int flags)
{
	String buf;

	if (!p_short.empty())
	{
		buf.append(p_short);
		buf.append(" ");
		if (flags & OPT_NEEDARG)
			buf.append("arg");
	}

	if (!p_long.empty())
	{
		if (buf.size() > 0)
			buf.append(", ");

		buf.append(p_long);
		if (flags & OPT_NEEDARG)
			buf.append("=arg");
	}

	buf.append("\t\t");
	buf.append(p_desc);

	printf("\n%s", buf.c_str());

	return E_OK;
}

int Options::_generateHelp()
{
	std::vector<_option*>::const_iterator it = m_orderedOpts.begin(), end = m_orderedOpts.end();

	help_callback callback = ( m_helpCallback ) ? m_helpCallback : (help_callback)_defaultHelpCallback;

	for ( ; it != end; ++it )
	{
		callback( (*it)->m_shortName, (*it)->m_longName, (*it)->m_help, (*it)->m_flags );
	}

	return E_OK;
}

//
// Helper function for handling short options.
// 
int Options::_handleShortOption(const String& p_str)
{
	_option* opt = _getShortOptionByname(p_str);

    if ( opt != NULL )
    {
		// See if it's a help option
		if ( opt->m_flags & OPT_HELP )
		{
			//TODO: Possibility of completely exiting if help is encountered. 
			_generateHelp();
			return E_OK;
		}

		if ( ++opt->m_count > 1 && !(opt->m_flags & OPT_MULTI) )
		{
			ERROR_CALLBACK(CB_OPT_TMO, p_str);
		}

		if ( opt->m_flags & OPT_NEEDARG )
        {
            m_waitingArg = opt;
        }
        return E_OK;
    }
    
    ERROR_CALLBACK(CB_OPT_UNKNOWN, p_str);
    return E_OPT_UNKNOWN;
}

//
// Helper function for handling long options
//
int Options::_handleLongOption(const String& p_str)
{
    //
    // p_str can be one of two things:
    // 1) --start            A single option (switch)
    // 2) --dir=something    An option with a parameter
    //
    String::size_type pos = p_str.find(_T("="));
    
    String str_opt;
    String str_arg;
    
    if ( pos == String::npos )
    {
        str_opt.assign( p_str );
    }
    else
    {
        str_opt.assign( p_str, 0, pos );
        str_arg.assign( p_str, pos+1, String::npos );
    }
    
    if ( str_opt.empty() )
    {
    	//
    	// The option is empty. Invoke callback
    	//
    	ERROR_CALLBACK(CB_OPT_MALFORMED, _T(""));
        return E_ERROR;
    }
    
    _option* opt = _getLongOptionByname(str_opt);
    
    if ( !opt ) 
    {
        ERROR_CALLBACK(CB_OPT_UNKNOWN, str_opt);
    	return E_OPT_UNKNOWN;
    }
    
	if ( opt->m_flags & OPT_HELP )
	{
		//TODO: Possibility of completely exiting if help is encountered. 
		_generateHelp();
		return E_OK;
	}

    if ( (opt->m_flags & OPT_NEEDARG) && str_arg.empty() )
    {
        ERROR_CALLBACK(CB_ARG_MISSING, str_opt);
        return E_ARG_EXPECTED;
    }
    else if ( !(opt->m_flags & OPT_NEEDARG) && !str_arg.empty() )
    {
        ERROR_CALLBACK(CB_OPT_MALFORMED, str_opt);
        return E_ERROR;
    }
    
    // Mark that we've found the option and assign the argument, even if empty
    opt->m_count++;
    opt->m_arg.assign(str_arg);
    
    return E_OK;
}

//
// Validate option's final state.
//
int Options::_validateState()
{
    int retcode = E_OK; 
    
    if ( m_waitingArg != NULL )
    {
        // It seems that our command line ended up with a short option
        // which expects an argument. Invoke error callback.
        ERROR_CALLBACK(CB_ARG_MISSING, _T("")); 
        retcode = E_ARG_EXPECTED; 
    }
    
    // See if there are any options which are required and haven't been found yet
    vector<_option*>::const_iterator it = m_orderedOpts.begin();
    
    for ( ; it != m_orderedOpts.end(); ++it )
    {
		_option* opt = *it;

        if ( opt->m_count == 0 && (opt->m_flags & OPT_REQUIRED) )
		{
				// Required option has not been found
				ERROR_CALLBACK(CB_OPT_MISSING, 
					((opt->m_shortName.empty()) ? opt->m_longName : opt->m_shortName));

				retcode |= E_OPT_MISSING;
				break;
		}

		if ( opt->m_count == 1 && !opt->m_validArg )
		{
			// This argument has a validator and it seems it's not a valid arg.
			// TODO: Report the invalid argument too ?
			ERROR_CALLBACK(CB_ARG_INVALID, 
				((opt->m_shortName.empty())?opt->m_longName:opt->m_shortName));

			retcode |= E_ARG_INVALID;
			//
			// TODO:
			// Break out of the for. But we can configure this to continue for 
			// all options, invoking callbacks.
			//
			break;	
		}
		
		if ( opt->m_count > 1 && (opt->m_flags & OPT_MULTI) )
		{
			retcode |= E_OPT_TMO;
			ERROR_CALLBACK(CB_OPT_TMO, 
				((opt->m_shortName.empty()) ? opt->m_longName : opt->m_shortName));

			break;
		}

    } // for
    
    return retcode;
}

int Options::_processArg(const String& p_str)
{
    int retcode = E_OK;
    
    //
    // If m_waitingArg is not NULL, the last option was requiring an argument.
    // This is the arg, store it.
    //
    if ( m_waitingArg )
    {
        m_waitingArg->m_arg.assign(p_str);
        //
        // Check to see if the option has a validator callback and invoke it,
        // if so.
        //
        // TODO?: Allow the possibility of changing behaviour on invalid arg,
        // like immediate exiting with error?
        //
        if ( m_waitingArg->m_optionValidator )
        {
        	// The validity of the argument will be checked after parsing everything.
        	// TODO: - Error callback on not validated arg ?
        	m_waitingArg->m_validArg = m_waitingArg->m_optionValidator( m_waitingArg->m_arg ); 
        }
        m_waitingArg = NULL;
    }
    else
    {
    	int r;
    	//TODO: I'll need to modify this when I'll allow multiple switches like -vv
        if ( p_str.size() == 2 && p_str[0] == _T('-') )
        {
            if ((r = _handleShortOption(p_str)) != E_OK )
            {
                retcode |= r;
            }
        }
        //TODO: Add proper validation for long options
        else if ( p_str.size() >= 3 && p_str.find(_T("--"),0,2) == 0 )
        {
            if ((r = _handleLongOption(p_str)) != E_OK )
            {
            	retcode |= r;
            }
        }
        else
        {
            // Free argument
            m_freeArgs.push_back(p_str);
        }
    }
    
    return retcode;
}

///////////////////////////////////////////////////////////////////////////////
//
// PARSER
//
///////////////////////////////////////////////////////////////////////////////
Parser::Parser()
        : m_flags(0)
{}

Parser::~Parser()
{}

int Parser::pre_parse(Options& p_opt)
{
	// Help generation?
	if ( m_flags & OPT_PARSE_AUTO_HELP )
	{
		//TODO: Possibility to alter -h, --help and "Display usage" - custom values needed
		if ( E_OK != p_opt.addOption( _T("-h"), _T("--help"), _T("Display usage"), OPT_HELP, NULL ) )
		{
			// This flag can be already there... thus, ignore it
		}
	}
	return E_OK;
}

void Parser::setFlags(int p_flags)
{
    m_flags |= p_flags;
}

int Parser::parse(int p_argc, TCHAR** p_argv, Options& p_opt)
{
	pre_parse(p_opt);

    int retcode = E_OK;
    
	// Include argv[0] if specified. It will be the first free arg
	int i = ( m_flags & OPT_PARSE_INCLUDE_ARGV0 ) ? 0 : 1;
	    
    for ( ; i < p_argc; ++i )
    {
   		retcode |= p_opt._processArg( p_argv[i] );
    }
    
    return (retcode | p_opt._validateState());
}

///////////////////////////////////////////////////////////////////////////////
// State handlers
///////////////////////////////////////////////////////////////////////////////
int Parser::_state_handle_space(String& opt, TCHAR c, int& current_state, Options& o)
{
	int retcode = E_OK;
	
	if ( m_flags & OPT_PARSE_QUOTED_ARGS )
	{
		switch (current_state)
		{
			case S_QUOTED:
				if ( c == _T('\0'))
				{
					// Unended quotes
					retcode = E_ERROR;
					break;
				}
				opt.append(1, c);		// Just add it, because we're inside quotes
			
			// Fallthrough...
			case S_DELIMITER:
				return E_OK;
				
			case S_NORMAL:
				current_state = S_DELIMITER;
				retcode |= o._processArg(opt);
				opt.clear();
				break;
				
			case S_ESCAPE:
				return E_ERROR;
				
			default:
				assert(false);
		}
	}
	else
	{
		current_state = S_DELIMITER;
		retcode |= o._processArg(opt);
		opt.clear();
	}			
	
	return retcode;
}

int Parser::_state_handle_quote(String& opt, TCHAR c, int& current_state)
{
	// We've got a quote, see (first of all) if the flag for quoted args is on
	if ( m_flags & OPT_PARSE_QUOTED_ARGS )
	{
		switch (current_state)
		{
			case S_ESCAPE:
				// S_ESCAPE is valid only inside quotes!
				current_state = S_QUOTED;
				opt.append(1, c);
				break;
				
			case S_DELIMITER:
			case S_NORMAL:
				current_state = S_QUOTED;
				if ( (m_flags & OPT_PARSE_UNQUOTE_ARGS) == 0 )
				{
					opt.append(1, c);
				}
				break;
				
			case S_QUOTED:
				current_state = S_NORMAL;
				if ( (m_flags & OPT_PARSE_UNQUOTE_ARGS) == 0 )
				{
					opt.append(1, c);
				}
				break;
				
			default: 
				assert(false);
				
		}
	}
	else
	{
		opt.append(1, c);
	}	

	return E_OK;	
}

int Parser::_state_handle_escape(String& opt, TCHAR c, int& current_state)
{
	if ( m_flags & OPT_PARSE_QUOTED_ARGS )
	{
		switch (current_state)
		{
			case S_NORMAL:
			case S_DELIMITER:
				// TODO: We'll consider this invalid, though we could have cases like:
				// --show=\"asd\" , the parameter being "asd". There are ways around this
				return E_ERROR;
				
			case S_ESCAPE:
				// For double escapes \\ :)
				opt.append(1, c);
				break;
			case S_QUOTED:
				current_state = S_ESCAPE;
				break;
			default:
				assert(false);
		}
	}
	else
	{
		opt.append(1, c);
	}
	
	return E_OK;
}

int Parser::_state_handle_other(String& opt, TCHAR c, int& current_state)
{
	if ( m_flags & OPT_PARSE_QUOTED_ARGS )
	{
		switch (current_state)
		{
			case S_NORMAL:
			case S_QUOTED:
				opt.append(1, c);
				break;
				
			case S_DELIMITER:
				opt.append(1, c);
				current_state = S_NORMAL;
				break;
			
			case S_ESCAPE:
				// No other escapes allowed but " and \  :) 
				return E_ERROR;
				
			default:
                assert(false);		
		}
	}
	else
	{
		opt.append(1, c);	
	}
	
	return E_OK;
}


int Parser::parse(const TCHAR* p_cmdLine, Options& p_opt)
{
	if ( !p_cmdLine )
	{
		return E_ERROR;
	}
	
	const TCHAR* c 		= p_cmdLine; 
	int current_state 	= S_DELIMITER;
	int retcode 		= E_OK;
	bool completed		= false;
	
	String opt;

	pre_parse(p_opt);
	
	while (!completed && *c)
	{
		switch ( *c )
		{
			case _T('\0'):
						completed = true;
			// Fallthrough...						
			case _T(' '):
			case _T('\t'):
						retcode |= _state_handle_space(opt, *c, current_state, p_opt);
						break;
						
			case _T('"'):
						retcode |= _state_handle_quote(opt, *c, current_state);
						break;
						
			case _T('\\'):
						retcode |= _state_handle_escape(opt, *c, current_state);
						break;
			default:
						retcode |= _state_handle_other(opt, *c, current_state);
		}
		
		++c;
	}
	
	return (retcode | p_opt._validateState());
}




