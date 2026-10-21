#include <iostream>
#include <string>
#include <regex>

#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <sodium.h>

using namespace std;

static const int MAX = 512;                                // MAX input data-message size of 512 bits to hashed using hmac-sha512
static void      sprintkey( unsigned char*, const char* ); // Converts hexadecimal char* to a MPI represented as an unsigned char sequence

enum class Curve { undefined, ed25519, secp256k1, nistp256 };

/** 
    From libgcrypt-1.8.5/cipher/ecc-curves.c:

    --ed25519   = apply Bernstein's ed25519 curve   ( order = 0x1000000000000000000000000000000014DEF9DEA2F79CD65812631A5CF5D3ED }
    --secp256k1 = apply the Bitcoin secp256k1 curve { order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141 }
    --nistp256  = apply the NIST nistp256 curve     { oder  = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551 }
**/

int main( const int   argc, 
          const char *argv[] )
{
  const char    *root_chaincode_ed25519   = "656432353531392073656564",     // "ed25519 seed"
                *root_chaincode_secp256k1 = "426974636f696e2073656564",     // "Bitcoin seed";
                *root_chaincode_nistp256  = "4e69737432353670312073656564"; // "Nist256p1 seed";

  string         line;
  smatch         matches;
  regex          pattern_help1{     R"(-h)"          },         // help
                 pattern_help2{     R"(--help)"      },         // help
                 pattern_index1{    R"(-i)"          },         // index
                 pattern_index2{    R"(--index)"     },         // index
                 pattern_index_val{ R"([0-9]{1,10})" },         // extracts integer index to be treated as hardened
                 pattern_ed25519{   R"(--ed25519)"   },         // sets SLIP 10 defined          chaincode of root for the ed25519 curve
                 pattern_secp256k1{ R"(--secp256k1)" },         // sets SLIP 10 & BIP 32 defined chaincode of root for the secp256k1 curve
                 pattern_nistp256{  R"(--nistp256)"  },         // sets SLIP 10 defined          chaincode of root for the nistp256 curve
                 pattern_hexdata1{  R"([0-9a-fA-F]{128})"    }, // ensures data          is a       128 digit hexadecimal number
                 pattern_hexdata2{  R"([0-9a-fA-F]{32,128})" }; // ensures data          is a 32 to 128 digit hexadecimal number

  static char    data[(MAX/4+1)], chaincode[(MAX/8+1)];

  int            ii         = 0,   // Cycles across the main()'s input arguments.
                 index10    = 0,   // Index in base 10 between 0 to 2147483647 inclusive                    
                 at_root    = 0,
                 have_index = 0, 
                 have_data  = 0;

  Curve          curve = Curve::undefined; //  Default curve at root is set to ed25519 with root_chaincode_ed25519 copied to chaincode


  if( argc == 1 )
  {
    usage:

    cout << "\nUsage: " << endl << endl
         << "                                  " << argv[0] << " [ --help | -h ] " << endl
         << "                                  " << argv[0] << " [ --ed25519 | --secp256k1 | --nistp256 ] 32_to_128_hex_digits " << endl // no index specified for root
         << "   stdin:: 32_to_128_hex_digits | " << argv[0] << " [ --ed25519 | --secp256k1 | --nistp256 ] "                      << endl // no index specified for root
         << "   stdin::       128_hex_digits | " << argv[0] << " -i decimal_index "                                              << endl // below root when index is specified
         << "                                  " << argv[0] << " -i decimal_index 128_hex_digits "                       << endl << endl // below root when index is specified

         << "   -h | --help  = " << "help"                                         << endl
         << "   -i | --index = " << "0 to 2147483647 (2^32 - 1) in base10" << endl << endl

         << "   Can select only one of the following elliptic curve types:" << endl << endl

         << "     --ed25519   sets the root's chaincode to that for ed25519, the default curve" << endl
         << "     --secp256k1 sets the root's chaincode to that for secp256k1"                  << endl
         << "     --nistp256  sets the root's chaincode to that for nistp256"           << endl << endl;

/**
Five elaborate computational Test Vectors:

1% echo 000102030405060708090a0b0c0d0e0f | ./hd_hmac --ed25519 | ./hd_hmac -i 0 | ./hd_hmac -i 1 | ./hd_hmac -i 2 | ./hd_hmac -i 2 | ./hd_hmac -i 1000000000 | cut -c 1-64
  8f94d394a8e8fd6b1bc2f3f49f5c47e385281d5c17e65324b0f62483e37e8793 

2% echo 000102030405060708090a0b0c0d0e0f | ./hd_hmac --ed25519 | ./hd_hmac -i 0 | ./hd_mhac -i 1 | ./hd_hmac -i 2 | ./hd_hmac -i 2 | ./hd_hmac -i 1000000000 | cut -c 65-128
  68789923a0cac2cd5a29172a475fe9e0fb14cd6adb5ad98a3fa70333e7afa230

3% echo fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542 | ./hd_hmac --ed25519 | ./hd_hmac -i 0 | ./hd_hmac -i 2147483647 | ./hd_hmac -i 1 | ./hd_hmac -i 2147483646 | ./hd_hmac -i 2 | cut -c 1-64
551d333177df541ad876a60ea71f00447931c0a9da16f227c11ea080d7391b8d

4% echo fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542 | ./hd_hmac --ed25519 | ./hd_hmac -i 0 | ./hd_hmac -i 2147483647 | ./hd_hmac -i 1 | ./hd_hmac -i 2147483646 | ./hd_hmac -i 2 | cut -c 65-128
5d70af781f3a37b829f0d060924d5e960bdc02e85423494afc0b1a41bbe196d4

5% echo "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" | bx mnemonic-to-seed -p "" | ./hd_hmac --ed25519 |  ./hd_hmac -i 44 | ./hd_hmac -i 128 | ./hd_hmac -i 0 | cut -c 1-64 | sc_reduce32
  8f2d521d4334f4d5d174c47aacb346e7633516416fae089d74ecfd0c389a6b08
**/
    return( 0 );
  }

  // parses input arguments from main
  for( ii = 1 ; ii < argc ; ii++ )
  {
    if( std::regex_search( (string)argv[ii], matches, pattern_help1 ) ||
        std::regex_search( (string)argv[ii], matches, pattern_help2 )    )
        goto usage;

    else if( std::regex_search( (string)argv[ii], matches, pattern_ed25519 ) )
        curve = Curve::ed25519;         //  Curve is ed25519

    else if( std::regex_search( (string)argv[ii], matches, pattern_secp256k1 ) )
        curve = Curve::secp256k1;       //  Curve is secp256k1

    else if( std::regex_search( (string)argv[ii], matches, pattern_nistp256 ) )
        curve = Curve::nistp256;       //  Curve is nistp256

    else if(   !have_index && 
             ( std::regex_search( (string)argv[ii], matches, pattern_index1 ) ||
               std::regex_search( (string)argv[ii], matches, pattern_index2 )    ) )
    {
      if( ++ii < argc )
      {
        if( std::regex_search( (string)argv[ii], matches, pattern_index_val ) )
        {
          // Range check index
          if( sscanf( argv[ii], "%d", &index10 ) != 1 )
          {
            cerr << "Error: calling program " << argv[0] <<  " internal sscanf() #A failed !" << endl;
            return( 1 );
          }
          if( index10 < 0 || index10 > 2147483647 )
          {
            cerr << "Error: calling program " << argv[0] <<  " decimal index \"" << index10 << "\" is out of range !" << endl;
            return( 1 );
          }

          index10   += 2147483648; // Sets the upper most bitflag to indicate the path is hardened
          have_index = 1;          // Successful parsing of hardened index
        }
        else
        {
          cerr << "Error: calling program " << argv[0] << " !" << endl;
          cerr << "  Expecting a decimal integer number between 0 and 2147483647 (2^32 - 1) to follow the [ -i | --index ] flag." << endl;
          return( 1 );
        }
      }
      else
      {
        cerr << "Error: calling program " << argv[0] << endl;
        cerr << "  Missing a decimal integer number between 0 and 2147483647 (2^32 - 1) following the [ -i | --index ] flag." << endl;
        cerr << "  Try: \"" << argv[0] << " --help\"" << endl;
        return( 1 );
      }
    }
    else if( !have_data &&  have_index && std::regex_search( (string)argv[ii], matches, pattern_hexdata1 ) ) // not root, input is always 512 bits
    {                                                                                                        // assumes index is specified prior to data
       if( !strcpy( data, (const char*)((string)matches[0]).c_str() ) )
       {
           cerr << "Error: calling program " << argv[0] <<  "internal strcpy() #B failed !" << endl;
           return( 1 );
       }

       have_data = 1;  // Successful parsing of data/message containing 128 hexadecimal digits
    }
    else if( !have_data && !have_index && std::regex_search( (string)argv[ii], matches, pattern_hexdata2 ) ) // root, input seed size is 128 to 512 bits
    {                                                                                                        // assumes index is specified prior to data
       if( !strcpy( data, (const char*)((string)matches[0]).c_str() ) )
       {
           cerr << "Error: calling program " << argv[0] <<  "internal strcpy() #C failed !" << endl;
           return( 1 );
       }

       have_data = 1;  // Successful parsing of data/message containing 32 to 128 hexadecimal digits
    }
    else
    {
      cerr << "Error: calling program " << argv[0] << " argv[" << ii << "] = " << argv[ii] <<  " slipped into the logic catch all bucket. " << endl;
      cerr << "  Try: \"" << argv[0] << " --help\"" << endl;
      return( 1 );
    }
  }

  if( !have_data )
  {
    std::getline( std::cin, line );  // Reads piped hex data/message from the standard input

    if( have_index ) // HD chaincode determination is NOT at root level, requires 128 hex digits for input data
    {
      if( std::regex_search( line, matches, pattern_hexdata1 ) ) 
      {   
         if( !strcpy( data, (const char*)((string)matches[0]).c_str() ) ) 
         {   
           cerr << "Error: calling program " << argv[0] <<  "internal strcpy() #D failed !" << endl;
           return( 1 );
         }   
      }   
      else
      {   
        cerr << "Error: calling program " << argv[0]  << endl;
        cerr << "  Expecting a 128 digit hexadecimal number to be supplied from the standard input." << endl;
        cerr << "  Try: \"" << argv[0] << " --help\"" << endl;
        return( 1 );
      }   
    }
    else             // HD chaincode determination is at root level, seed is 128 to 512 bits in size
    {
      if( std::regex_search( line, matches, pattern_hexdata2 ) ) 
      {   
         if( !strcpy( data, (const char*)((string)matches[0]).c_str() ) ) 
         {   
           cerr << "Error: calling program " << argv[0] <<  "internal strcpy() #E failed !" << endl;
           return( 1 );
         }   
      }   
      else
      {   
        cerr << "Error: calling program " << argv[0]  << endl;
        cerr << "  Expecting a 32 to 128 digit hexadecimal number to be supplied from the standard input." << endl;
        cerr << "  Try: \"" << argv[0] << " --help\"" << endl;
        return( 1 );
      }   
    }

    have_data = 1;
  }

  if( !have_index )  // Only occurs at root level where index is not specified and SLIP 10 defined chaincode is applied
  {
    if(      curve == Curve::secp256k1 )
      strcpy( chaincode, root_chaincode_secp256k1 );

    else if( curve == Curve::nistp256 )
      strcpy( chaincode, root_chaincode_nistp256 );

    else
    {
      strcpy( chaincode, root_chaincode_ed25519 );   // default curve until hardened secp256k1 and  nistp256 are bith fully functional
      curve = Curve::ed25519;
    }

    at_root = 1;
  }

  if( !have_data )
  {
    cerr << "Error: calling program " << argv[0]  << endl;
    cerr << "  Input data was never provided or curve remains to be defined." << endl;
    cerr << "  Try: \"" << argv[0] << " --help\"" << endl;
    return( 1 );
  }


  static char           message[MAX/4+1];

  if( !at_root )  // message and chaincode must be initialized here
  {
    // If not at HD root, the message is comprised of the prefix (0x00),
    // the parent's private key (1st 64 hex digits of "data" above) and the hardened hex index. 
    // The chaincode is the last 64 hex digits of "data".

    static char temp[65];

    strncpy( temp, data, 64 );
    sprintf( message,   "00%s%8x", &temp[0], index10 );
    sprintf( chaincode, "%s",      &data[64] ); 
  }
  else           // message remains to be initialized
  {
    // If at root, the chaincode was previously initialized the message
    // is all of the R"([0-9a-fA-F]{32,128})" data that was parsed and checked.

    sprintf( message,   "%s", data );
  }

//fprintf( stderr, "Message   = %s\n", message );
//fprintf( stderr, "Chaincode = %s\n", chaincode );
//fflush(  stderr );

  
  static unsigned char  msg[MAX/8],
                        hash[crypto_auth_hmacsha512_BYTES],
                        key[ crypto_auth_hmacsha512_KEYBYTES];
  static char           hex_hash[(MAX/4)+1];
  int                   msg_length;
 
  if( sodium_init() < 0 )
  {
    cerr << "Error: executable " << argv[0] << " could not call sodium_init() !" << endl;
    return( 1 );
  }

  sprintkey( msg, message   );
  sprintkey( key, chaincode );
  
  msg_length = strlen( message )/2;

// https://libsodium.gitbook.io/doc/advanced/hmac-sha2#hmac-sha-512
  (void)crypto_auth_hmacsha512( hash, msg, msg_length, key );

  (void)sodium_bin2hex( hex_hash, sizeof(hex_hash), hash, sizeof(hash) );

  cout << hex_hash << endl;

  return( 0 );
}


static void sprintkey( unsigned char *key, const char *input )
{
  unsigned int hex, hex_even, hex_odd;

  if( input )
  {
    for( int ii = 0 ; input[ii] != 0 ; ii++ )
    {
      switch( tolower( input[ii] ) )
      {
        case '0': hex = 0;
                  break;
        case '1': hex = 1;
                  break;
        case '2': hex = 2;
                  break;
        case '3': hex = 3;
                  break;
        case '4': hex = 4;
                  break;
        case '5': hex = 5;
                  break;
        case '6': hex = 6;
                  break;
        case '7': hex = 7;
                  break;
        case '8': hex = 8;
                  break;
        case '9': hex = 9;
                  break;
        case 'a': hex = 10;
                  break;
        case 'b': hex = 11;
                  break;
        case 'c': hex = 12;
                  break;
        case 'd': hex = 13;
                  break;
        case 'e': hex = 14;
                  break;
        case 'f': hex = 15;
                  break;
        default:
                 cerr << "Error in sprintkey() " << endl;
                 exit( 1 );
      }

      if( ii%2 )
      {
        hex_odd = hex;
        hex = (hex_even << 4) | hex_odd;
        key[ii/2] = hex;
      } 
      else
        hex_even = hex;
    }   
  } 
}
