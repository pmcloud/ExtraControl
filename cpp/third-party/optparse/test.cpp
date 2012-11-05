//
// Part of the OptParse package
//

#include <cstdio>
#include <cstdlib>
#include <cassert>
#include "optparse.h"

#ifdef _UNICODE
#define print wprintf
#else
#define print printf
#endif

#define ASSERT_TEST(x) { print("(%s) : ", #x); \
	if (x) { print("passed.\n"); } else { print("failed.\n"); } }


///////////////////////////////////////////////////////////////////////////////
// Testing
///////////////////////////////////////////////////////////////////////////////

int error_callback(int error, const String& arg)
{
    switch (error)
    {
        case CB_OPT_UNKNOWN:
            print(_T("\nERROR: Unknown option: %s"), arg.c_str());
            break;
            
        case CB_OPT_MALFORMED:
            print(_T("\nERROR: Option malformed: %s"), arg.c_str());
            break;
            
        case CB_OPT_MISSING:
            print(_T("\nERROR: Req. option missing: %s"), arg.c_str());
            break;
            
        case CB_ARG_MISSING:
            print(_T("\nERROR: Argument missing for opt: %s"), arg.c_str());
            break;
            
        case CB_ARG_INVALID:
            print(_T("\nERROR: Argument not validated for opt: %s"), arg.c_str());
            break;
            
        default:
            print(_T("\nERROR: Unknown error code."));
    }
	return 0;
}

bool portValidator(const String& p_str)
{
	//
	// You can perform any kind of checks on the argument here, for example
	// you can impose range constraints.
	//
	
#ifdef _UNICODE
	long val = wcstol( p_str.c_str(), NULL, 10 );
#else
	long val = strtol( p_str.c_str(), NULL, 10 );
#endif

	return ( (val > 0 && val < 65536 ) );
}


#ifdef RUN_TESTS
int	test_1()
{
	Options o;
	int err;

	print("\nNormal option: ");
	err = o.addOption(_T("-v"), _T("--version"), _T("Version"), OPT_NONE, NULL);
	ASSERT_TEST( err == E_OK );

	print("\nNo options: ");
	err = o.addOption(_T(""), _T(""), _T(""), OPT_NONE, NULL);
	ASSERT_TEST( err == E_INVALID );

	print("\nInvalid long option: ");
	err = o.addOption(_T(""),_T("-version"),_T(""), OPT_NONE, NULL);
	ASSERT_TEST( err != E_OK );

	print("\nShort duplicate option: ");
	err = o.addOption(_T("-v"), _T(""), _T("Version"), OPT_NONE, NULL);
	ASSERT_TEST( err == E_OPT_DUPLICATE );

	print("\nLong duplicate option: ");
	err = o.addOption(_T(""), _T("--version"), _T("Version"), OPT_NONE, NULL);
	ASSERT_TEST( err == E_OPT_DUPLICATE );

	return 0;
}
#endif

int main(int argc, TCHAR** argv)
{
	#ifdef RUN_TESTS
	test_1();
	return 0;
	#else
	
	Options o;
    
    o.addOption(_T("-s"), _T("--server"), _T("Server to connect to"), 
    		OPT_REQUIRED | OPT_NEEDARG, NULL );
    
    //
    // Add an option with validation of the value ( val in [ 1, 65535 ] )
    //
    o.addOption(_T("-t"), _T("--port"), _T("Destination port"), 
    		OPT_NEEDARG | OPT_REQUIRED, portValidator);

    o.addOption(_T("-p"), _T("--path"), _T("Specify the path to list"), 
			OPT_NEEDARG, NULL );

    o.addOption(_T("-v"), _T("--version"), _T("Version switch"), 
    		OPT_NONE, NULL);
    
    // This should cause duplicate error
    o.addOption(_T("-v"), _T(""), _T(""), OPT_NONE, NULL );
                          
	#ifdef _DEBUG
    o.addOption(_T("-d"), _T("--dump"), _T("Dump options"), OPT_NONE, NULL );
    #endif

    
    // Error callback for this options set
    o.setErrorCallback( error_callback );
    
    
    Parser p;

	//
	// Set parser flags:
	// - QUOTED_ARGS  to allow quoted parameters with spaces inside, like "hello world"
	// - UNQUOTE_ARGS for the quoted args to have the surrounding quotes removed "hello world" --> hello world
	//    
	p.setFlags( OPT_PARSE_QUOTED_ARGS | OPT_PARSE_UNQUOTE_ARGS | OPT_PARSE_AUTO_HELP );
    
	
	int retcode = p.parse(argc, argv, o);
    
    //int retcode = p.parse("-s localhost.google.com -t 100000 -p asd free1 free2 --long=\"test \\\" me\" \"test multi string\"", o);
    
    if ( E_OK == retcode )
    {
        print(_T("\n---- PARSING SUCCESSFUL ----\n"));
    }
    else 
    {	if ( retcode & E_OPT_MISSING )
    	{
    		print(_T("\n---- MISSING REQUIRED OPTION ----\n"));
    		return -1;
    	}
    	
    	if ( retcode & E_OPT_UNKNOWN )
    	{
    		print(_T("\n---- UNKNOWN OPTION SPECIFIED ----\n"));
    		return -1;
    	}
    	
    	if ( retcode & E_ERROR )
    	{
    		print(_T("\n---- GENERIC ERROR ----\n"));
    		return -1;	
    	}
    	
    	if ( retcode & E_ARG_EXPECTED )
    	{
    		print(_T("\n---- ARGUMENT EXPECTED ----\n"));
    		return -1;	
    	}
    	
    	if ( retcode & E_ARG_INVALID )
    	{
    		print(_T("\n---- ARGUMENT NOT VALID ----\n"));
    		return -1;	
    	}
    }

	#ifdef _DEBUG
	//
	// Dump options? 
	//
	if ( o.isSet( _T("-d")) )
	{
		o.dump_options();
	}
	#endif
    
    print(_T("\nArgument of -s: [%s]\n"), o.asString(_T("-s")).c_str());
    print(_T("Argument of -t: [%s]\n"), o.asString(_T("-t")).c_str());
    
    return 0;
#endif
}
